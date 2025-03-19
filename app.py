# IMPORTANT: This must be the first Streamlit command in the app
import streamlit as st

st.set_page_config(
    page_title="Sanal Drone Emlak Video Oluşturucu",
    layout="wide",
    initial_sidebar_state="expanded",
)

"""Emlak Video Oluşturucu - Ana Uygulama"""

from PIL import Image
import gc
import os
import folium
import time
import sys
from pathlib import Path

# Add the project root to path to fix imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import local modules
from config.config import (
    initialize_session_state,
    VOICE_OPTIONS,
    DEFAULT_VOICE,
    VIDEO_DIR,
)
from modules.text.text_generation import generate_property_description
from modules.audio.audio_generation import generate_audio_from_text, get_audio_duration
from modules.image.image_processing import (
    fetch_satellite_image,
    fetch_street_view_image,
    draw_property_border,
    enhance_image,
)
from modules.video.video_generation import generate_video
from modules.geo.geo_utils import get_coordinates_from_address, get_nearby_places
from utils.utils import calculate_distance, cleanup_temp_files
from streamlit_folium import st_folium

# Yeni durum yönetimi ve arka plan görevleri modüllerini içe aktar
from utils.state_manager import StateManager
from utils.background_tasks import BackgroundTaskManager, generate_video_in_background

# Add missing imports
import cv2
import numpy as np
import tempfile

# Import overlay and music functions
from modules.video.overlay_tools import add_text_overlay, add_logo_overlay
from modules.audio.music_library import get_music_options, mix_audio, download_music
from utils.cache_utils import cached_data, clear_cache, clear_disk_cache

# Add at the top with other imports:
from utils.system_check import display_system_info
from modules.video.preview_utils import show_video_preview

# Fix the rerun function usage
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Add at the top with other imports
import os
from pathlib import Path

# Add after other constants
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

def safe_rerun():
    """Safely rerun the app"""
    try:
        st.rerun()
    except:
        # Fallback for very old Streamlit versions
        try:
            st.experimental_rerun()
        except:
            st.warning("Could not rerun the app. Please refresh the page manually.")


# Ana uygulama sınıfı
class EmlakVideoApp:
    def __init__(self):
        # Uygulama başlangıç ayarları
        self.initialize_app()

        # Durum yöneticisi ve arka plan görev yöneticisi oluştur
        self.state_manager = StateManager()
        self.task_manager = BackgroundTaskManager()

    def initialize_app(self):
        """Uygulamayı başlat ve gerekli dizinleri oluştur"""
        initialize_session_state()
        # st.set_page_config was moved to the top of the file

    def run(self):
        """Ana uygulama akışını çalıştır"""
        # Başlık ve sidebar'ı ayarla
        self.setup_header()
        self.setup_sidebar()

        # Emlak adres girişi (ana ekranda her zaman görünür)
        self.setup_address_input()

        # Arka plan görevlerini kontrol et ve görüntüle
        self.check_background_tasks()

        # Ana sekmeleri oluştur
        if "current_view" not in st.session_state:
            st.session_state["current_view"] = "tabs"  # Varsayılan görünüm: tabs

        if st.session_state["current_view"] == "tabs":
            self.show_tabbed_interface()
        else:
            # Alternatif olarak wizard arayüzü eklenebilir
            self.show_wizard_interface()

    def setup_header(self):
        """Uygulama başlığını ve üst bilgiyi ayarla"""
        st.title("🏠 Sanal Drone Emlak Video Oluşturucu")

        # Proje yönetimi butonları
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💾 Projeyi Kaydet"):
                self.save_project()

        with col2:
            if st.button("📂 Projeyi Aç"):
                self.load_project()

        with col3:
            if st.button("🧹 Önbelleği Temizle"):
                self.clear_cache()

    def setup_sidebar(self):
        """Kenar çubuğu ayarlarını oluştur"""
        with st.sidebar:
            st.header("Video Ayarları")

            # Görünüm seçimi
            st.session_state["current_view"] = st.radio(
                "Arayüz Görünümü",
                options=["tabs"],
                format_func=lambda x: "Sekmeli Görünüm"
                
            )

            # Video ayarları
            st.session_state["fps"] = st.slider(
                "Kare Hızı (FPS)", 15, 60, 30, help="Saniyedeki kare sayısı"
            )
            st.session_state["video_quality"] = st.radio(
                "Video Kalitesi",
                ["normal", "high"],
                format_func=lambda x: "Normal (720p)"
                if x == "normal"
                else "Yüksek (1080p)",
            )
            st.session_state["transition_type"] = st.selectbox(
                "Geçiş Efekti", ["Yakınlaşma", "Kaydırma", "Yakınlaşma ve Kaydırma"]
            )

            # Görüntü iyileştirme ayarları
            st.session_state["enhance_colors"] = st.checkbox(
                "Görüntü Renklerini Geliştir", value=True
            )
            st.session_state["color_boost"] = st.slider("Renk Canlılığı", 1.0, 2.5, 1.5)

            # Şablonlar menüsü
            self.show_templates()

    def show_templates(self):
        """Hazır şablonları göster ve uygula"""
        st.subheader("📋 Hazır Şablonlar")

        templates = {
            "Lüks Konut": {
                "transition_type": "Yakınlaşma ve Kaydırma",
                "fps": 30,
                "video_quality": "high",
                "color_boost": 1.8,
                "description": "Yüksek kaliteli, akıcı geçişlerle lüks konut videoları için ideal ayarlar.",
            },
            "Ticari Emlak": {
                "transition_type": "Kaydırma",
                "fps": 24,
                "video_quality": "high",
                "color_boost": 1.3,
                "description": "Ticari mülkler için profesyonel görünümlü, yüksek kalitede sunumlar.",
            },
            "Ekonomik Paket": {
                "transition_type": "Yakınlaşma",
                "fps": 24,
                "video_quality": "normal",
                "color_boost": 1.5,
                "description": "Hızlı ve verimli oluşturma için optimize edilmiş temel ayarlar.",
            },
            "Arsa/Arazi": {
                "transition_type": "Yakınlaşma ve Kaydırma",
                "fps": 30,
                "video_quality": "high",
                "color_boost": 2.0,
                "description": "Arsa ve arazi görüntülerini vurgulamak için uyarlanmış, canlı renkli ayarlar.",
            },
            "Deniz Manzaralı": {
                "transition_type": "Kaydırma",
                "fps": 30,
                "video_quality": "high",
                "color_boost": 1.7,
                "description": "Deniz ve göl manzaralarını öne çıkaran, mavi tonları vurgulayan ayarlar.",
            },
        }

        selected_template = st.selectbox(
            "Şablon Seç:", ["Özel"] + list(templates.keys())
        )

        if selected_template != "Özel":
            # Seçilen şablonun açıklamasını göster
            st.info(templates[selected_template]["description"])

            if st.button(f"'{selected_template}' Şablonunu Uygula"):
                # Seçilen şablonu uygula
                template = templates[selected_template]
                for key, value in template.items():
                    if key != "description":  # Açıklama hariç diğer özellikleri ayarla
                        st.session_state[key] = value
                st.success(f"'{selected_template}' şablonu uygulandı!")
                safe_rerun()

    def setup_address_input(self):
        """Emlak adres girişi alanını oluştur"""
        st.header("📍 Emlak Konumu")
        address = st.text_input(
            "Emlak adresi:",
            placeholder="Örnek: Atatürk Mah. Cumhuriyet Cad. No:123, İstanbul",
        )

        if address:
            # Konum verilerini al
            with st.spinner("Adres bilgileri alınıyor..."):
                lat, lng, formatted_address = get_coordinates_from_address(address)
                if lat and lng:
                    st.session_state["property_location"] = {
                        "lat": lat,
                        "lng": lng,
                        "formatted_address": formatted_address,
                    }
                    st.success(f"Konum bulundu: {formatted_address}")

                    # Harita oluştur ve göster
                    m = folium.Map(location=[lat, lng], zoom_start=15)
                    folium.Marker([lat, lng], tooltip="Emlak Konumu").add_to(m)
                    st_folium(m, width=800, height=300)
                else:
                    st.error("Adres bulunamadı. Lütfen geçerli bir adres girin.")

    def check_background_tasks(self):
        """Devam eden arka plan görevlerini kontrol et ve görüntüle"""
        # Tamamlanmış eski görevleri temizle
        self.task_manager.cleanup_completed_tasks(max_age_seconds=1800)  # 30 dakika

        # Video oluşturma görevi varsa kontrol et
        if "video_task_id" in st.session_state:
            task_id = st.session_state["video_task_id"]
            task_status = self.task_manager.get_task_status(task_id)

            if task_status:
                # Devam eden görev varsa, durumunu göster
                if task_status["status"] in [
                    "starting",
                    "running",
                    "preparing",
                    "processing_images",
                    "generating_video",
                ]:
                    st.header("🎬 Video Oluşturuluyor")
                    st.info(f"Video oluşturma işlemi devam ediyor...")

                    # Calculate stage name in Turkish
                    stage_name = {
                        "starting": "Başlatılıyor",
                        "running": "Çalışıyor",
                        "preparing": "Hazırlanıyor",
                        "processing_images": "Görüntüler İşleniyor",
                        "generating_video": "Video Oluşturuluyor",
                    }.get(task_status["status"], task_status["status"])

                    col1, col2 = st.columns([3, 1])

                    with col1:
                        progress = task_status["progress"] / 100.0
                        progress_bar = st.progress(progress)
                        st.caption(f"İşlem: {stage_name}")

                    with col2:
                        st.metric("Tamamlandı", f"%{int(progress * 100)}")

                    if "message" in task_status and task_status["message"]:
                        st.caption(f"Detay: {task_status['message']}")

                    # Her 2 saniyede bir yenile
                    time.sleep(2)
                    safe_rerun()

                # Tamamlanan görev varsa, sonucu göster
                elif task_status["status"] == "completed":
                    video_path = task_status["result"]
                    if video_path and os.path.exists(video_path):
                        st.header("🎉 Video Hazır!")
                        st.success("Video başarıyla oluşturuldu!")

                        # Video dosya bilgileri
                        video_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                        video_info = f"Video boyutu: {video_size_mb:.1f} MB"
                        st.info(video_info)

                        # Videoyu göster
                        st.video(video_path)

                        # İndirme butonu
                        with open(video_path, "rb") as file:
                            st.download_button(
                                "📥 Videoyu İndir",
                                data=file,
                                file_name="emlak_videosu.mp4",
                                mime="video/mp4",
                                help="Videoyu cihazınıza kaydedin",
                            )

                    # İşlem tamamlandığı için görev ID'sini temizle
                    del st.session_state["video_task_id"]

                # Hata durumunda göster
                elif task_status["status"] == "failed":
                    st.header("❌ Video Oluşturma Hatası")
                    st.error(
                        f"Video oluşturulurken bir hata meydana geldi: {task_status['error']}"
                    )

                    # Hata detayı
                    with st.expander("Hata Detayları"):
                        if "error_details" in task_status:
                            st.code(task_status["error_details"])
                        else:
                            st.write("Detaylı hata bilgisi mevcut değil.")

                    # Yeniden deneme butonu
                    if st.button(
                        "🔄 Yeniden Dene", help="Video oluşturmayı tekrar deneyin"
                    ):
                        del st.session_state["video_task_id"]
                        safe_rerun()

                    del st.session_state["video_task_id"]

    def save_project(self):
        """Projeyi kaydet diyalog kutusu"""
        with st.form(key="save_project_form"):
            project_name = st.text_input("Proje adı:", max_chars=50)
            overwrite = st.checkbox("Aynı isimli proje varsa üzerine yaz")

            submit_button = st.form_submit_button(label="Kaydet")

            if submit_button:
                if not project_name:
                    st.error("Proje adı boş olamaz!")
                    return

                # Proje verilerini al
                project_data = self.state_manager.get_project_data()

                # Projeyi kaydet
                success = self.state_manager.save_project(
                    project_name, project_data, overwrite
                )

                if success:
                    st.success(f"Proje '{project_name}' başarıyla kaydedildi!")
                else:
                    st.error(
                        f"Proje '{project_name}' kaydedilemedi. Aynı isimli bir proje zaten mevcut."
                    )

    def load_project(self):
        """Projeyi aç diyalog kutusu"""
        with st.form(key="load_project_form"):
            project_name = st.text_input("Açılacak proje adı:", max_chars=50)

            submit_button = st.form_submit_button(label="Aç")

            if submit_button:
                if not project_name:
                    st.error("Proje adı boş olamaz!")
                    return

                # Projeyi yükle
                project_data = self.state_manager.load_project(project_name)

                if project_data:
                    self.state_manager.set_project_data(project_data)
                    st.success(f"Proje '{project_name}' başarıyla yüklendi!")
                    safe_rerun()
                else:
                    st.error(f"Proje '{project_name}' bulunamadı.")

    def clear_cache(self):
        """Önbelleği temizle"""
        from utils.cache_utils import clear_cache as cc

        cc()  # Streamlit önbelleği temizler

        # Disk önbelleğini temizle
        from utils.cache_utils import clear_disk_cache

        clear_disk_cache()

        # Geçici dosyaları temizle
        cleanup_temp_files(None)
        st.success("Önbellek başarıyla temizlendi!")

    def show_tabbed_interface(self):
        """Sekme tabanlı arayüzü göster"""
        tabs = st.tabs(
            [
                "1. Emlak Bilgileri",
                "2. Sesli Anlatım",
                "3. Görüntüler",
                "4. Video Oluştur",
            ]
        )

        # Her sekme için ilgili controller'ı çağır
        with tabs[0]:
            property_controller = PropertyController()
            property_controller.show_property_form()

        with tabs[1]:
            audio_controller = AudioController()
            audio_controller.show_audio_generation()

        with tabs[2]:
            image_controller = ImageController()
            image_controller.show_image_collection()

        with tabs[3]:
            video_controller = VideoController(self.task_manager)
            video_controller.show_video_generation()

    def show_wizard_interface(self):
        """Adım adım sihirbaz arayüzünü göster (ileride uygulanabilir)"""
        wizard = PropertyVideoWizard()
        wizard.show()


# Controller sınıfları - Her biri uygulamanın bir yönünü kontrol eder
class PropertyController:
    """Emlak detayları ve metin oluşturma için controller"""

    def show_property_form(self):
        st.header("Emlak Bilgileri")
        if "property_location" not in st.session_state:
            st.warning("Lütfen önce emlak adresini girin!")
            return

        col1, col2 = st.columns(2)

        with col1:
            property_type = st.selectbox(
                "Emlak Tipi:",
                ["Daire", "Villa", "Müstakil Ev", "Arsa", "Ticari", "Diğer"],
            )
            rooms = st.number_input("Oda Sayısı:", min_value=0, max_value=20, value=3)
            bathrooms = st.number_input(
                "Banyo Sayısı:", min_value=0, max_value=10, value=1
            )

        with col2:
            area = st.number_input("Metrekare:", min_value=1, value=120)
            price = st.number_input("Fiyat (TL):", min_value=0, value=1500000)
            year_built = st.number_input(
                "Yapım Yılı:", min_value=1900, max_value=2025, value=2010
            )

        special_features = st.text_area(
            "Özel Özellikler:",
            placeholder="Örnek: Deniz manzarası, yüzme havuzu, güvenlik, otopark vb.",
            height=100,
        )

        # Çevre bilgilerini getir
        nearby_places = self._get_nearby_info()

        # Metin oluştur butonu
        if st.button("Emlak Metni Oluştur", type="primary"):
            self._generate_description(
                property_type,
                rooms,
                bathrooms,
                area,
                price,
                year_built,
                special_features,
                nearby_places,
            )

    def _get_nearby_info(self):
        """Yakın çevre bilgilerini getir"""
        include_nearby = st.checkbox("Yakın Çevre Bilgilerini Ekle", value=True)
        nearby_places = None

        if include_nearby:
            nearby_radius = st.slider(
                "Araştırma Yarıçapı (metre)", 500, 2000, 1000, 100
            )
            with st.spinner("Yakın çevre analizi yapılıyor..."):
                nearby_places = get_nearby_places(
                    st.session_state["property_location"]["lat"],
                    st.session_state["property_location"]["lng"],
                    radius=nearby_radius,
                    types=[
                        "school,hospital,shopping_mall,park,restaurant,subway_station,bus_station"
                    ],
                )

                if nearby_places:
                    with st.expander("Yakındaki Önemli Noktalar"):
                        for place in sorted(nearby_places, key=lambda x: x["distance"]):
                            st.write(
                                f"🏢 **{place['name']}** ({place['type'].replace('_', ' ')}) - {place['distance']}m"
                            )

        return nearby_places

    def _generate_description(
        self,
        property_type,
        rooms,
        bathrooms,
        area,
        price,
        year_built,
        special_features,
        nearby_places,
    ):
        """Emlak açıklama metni oluştur"""
        with st.spinner("Metin oluşturuluyor..."):
            property_data = {
                "address": st.session_state["property_location"]["formatted_address"],
                "property_type": property_type,
                "rooms": rooms,
                "bathrooms": bathrooms,
                "area": area,
                "price": price,
                "year_built": year_built,
                "special_features": special_features,
                "description": "",
            }

            generated_text = generate_property_description(
                property_data, nearby_places if nearby_places else None
            )

            if generated_text:
                st.session_state["property_text"] = generated_text
                st.success("Metin başarıyla oluşturuldu!")
                st.markdown("### Oluşturulan Metin:")
                st.write(generated_text)

                edited_text = st.text_area(
                    "Metni Düzenleyin (isteğe bağlı):", value=generated_text, height=200
                )

                if edited_text != generated_text:
                    st.session_state["property_text"] = edited_text


class AudioController:
    """Ses oluşturma ve yönetimi için controller"""

    def show_audio_generation(self):
        st.header("Sesli Anlatım Oluştur")

        if "property_text" not in st.session_state:
            st.warning("Lütfen önce emlak bilgilerini girin!")
            return

        st.write(st.session_state["property_text"])

        # Ses seçenekleri eklenebilir
        voice_id = st.selectbox(
            "Ses Seçin:",
            options=list(VOICE_OPTIONS.keys()),
            format_func=lambda x: VOICE_OPTIONS[x],
            index=list(VOICE_OPTIONS.keys()).index(DEFAULT_VOICE),
        )
        st.session_state["voice_id"] = voice_id

        if st.button("Sesli Anlatım Oluştur"):
            self._generate_audio()

    def _generate_audio(self):
        """Metinden ses oluştur"""
        audio_path = generate_audio_from_text(
            st.session_state["property_text"],
            st.session_state.get("voice_id", DEFAULT_VOICE),
        )

        if audio_path:
            st.session_state["audio_path"] = audio_path
            st.session_state["audio_duration"] = get_audio_duration(audio_path)
            st.success("Sesli anlatım başarıyla oluşturuldu!")
            st.audio(audio_path)


class ImageController:
    """Görüntü toplama ve işleme için controller"""

    def show_image_collection(self):
        st.header("Görüntüleri Topla")

        if "property_location" not in st.session_state:
            st.warning("Lütfen önce emlak adresini girin!")
            return

        col1, col2 = st.columns(2)

        with col1:
            self._show_map_images()

        with col2:
            self._show_custom_images()

    def _show_map_images(self):
        """Harita ve uydu görüntülerini göster"""
        st.subheader("Harita Görüntüleri")

        zoom_level = st.slider("Yakınlaştırma Seviyesi", 15, 20, 18)
        map_type = st.selectbox(
            "Harita Tipi",
            ["satellite", "hybrid", "roadmap"],
            format_func=lambda x: {
                "satellite": "Uydu",
                "hybrid": "Hibrit",
                "roadmap": "Yol Haritası",
            }[x],
        )

        if st.button("Harita Görüntülerini Getir"):
            self._fetch_map_images(zoom_level, map_type)

        # Emlak sınırı çizme özelliği
        if (
            "maps_images" in st.session_state
            and len(st.session_state["maps_images"]) > 0
        ):
            self._show_border_drawing()

    def _fetch_map_images(self, zoom_level, map_type):
        """Harita görüntülerini getir"""
        with st.spinner("Görüntüler alınıyor..."):
            lat = st.session_state["property_location"]["lat"]
            lng = st.session_state["property_location"]["lng"]

            # Uydu görüntülerini al
            satellite_images = []
            progress_bar = st.progress(0)

            main_img = fetch_satellite_image(
                lat=lat, lng=lng, zoom=zoom_level, maptype=map_type
            )
            if main_img:
                # Renk iyileştirmeyi uygula
                if st.session_state["enhance_colors"]:
                    main_img = enhance_image(
                        main_img, boost_factor=st.session_state["color_boost"]
                    )
                satellite_images.append(main_img)

                # Farklı zoom seviyelerindeki görüntüler
                zoom_levels = [zoom_level - 1, zoom_level - 2, zoom_level + 1]
                for i, zoom in enumerate(zoom_levels):
                    img = fetch_satellite_image(
                        lat=lat, lng=lng, zoom=zoom, maptype=map_type
                    )
                    if img:
                        # Renk iyileştirmeyi uygula
                        if st.session_state["enhance_colors"]:
                            img = enhance_image(
                                img, boost_factor=st.session_state["color_boost"]
                            )
                        satellite_images.append(img)
                    progress_bar.progress((i + 1) / len(zoom_levels))

            # Sokak görüntülerini al
            headings = [0, 90, 180, 270]
            street_view_images = []

            for heading in headings:
                img = fetch_street_view_image(lat=lat, lng=lng, heading=heading)
                if img:
                    street_view_images.append(img)

            # Tüm görüntüleri birleştir
            all_images = satellite_images + street_view_images
            if all_images:
                st.session_state["maps_images"] = all_images
                st.success(f"{len(all_images)} görüntü başarıyla alındı!")

                # Görüntüleri grid içinde göster
                cols = st.columns(3)
                for idx, img in enumerate(all_images):
                    with cols[idx % 3]:
                        st.image(img, caption=f"Görüntü {idx + 1}")

    def _show_border_drawing(self):
        """Emlak sınırı çizme arayüzünü göster"""
        st.subheader("Emlak Sınırı Çizme")
        st.info(
            "Uydu görüntüsü üzerinde emlak sınırını belirlemek için aşağıdaki ayarları kullanın."
        )

        # Sınır çizilecek görüntüyü seç
        image_options = [
            f"Görüntü {i + 1}" for i in range(len(st.session_state["maps_images"]))
        ]
        selected_img_idx = st.selectbox(
            "Sınır çizilecek görüntüyü seçin:",
            range(len(image_options)),
            format_func=lambda i: image_options[i],
        )

        selected_image = st.session_state["maps_images"][selected_img_idx]

        # Seçili görüntüyü göster
        st.image(selected_image, caption="Seçilen Görüntü", use_container_width=True)

        # Sınır ayarları
        col_color, col_width, col_ratio = st.columns(3)

        with col_color:
            border_colors = {
                "#FF0000": "Kırmızı",
                "#00FF00": "Yeşil",
                "#0000FF": "Mavi",
                "#FFFF00": "Sarı",
                "#FF00FF": "Mor",
                "#00FFFF": "Turkuaz",
            }
            color_key = st.selectbox(
                "Sınır Rengi:",
                list(border_colors.keys()),
                format_func=lambda x: border_colors[x],
            )

        with col_width:
            border_width = st.slider("Sınır Kalınlığı:", 1, 10, 3)

        with col_ratio:
            border_ratio = st.slider(
                "Sınır Konumu:",
                0.05,
                0.45,
                0.2,
                help="0.5'e yakın değerler sınırı merkeze, 0'a yakın değerler kenarlara yaklaştırır",
            )

        # Sınırı çiz butonu
        if st.button("Sınırı Çiz", type="primary"):
            with st.spinner("Sınır çiziliyor..."):
                bordered_image = draw_property_border(
                    selected_image, color_key, border_width, border_ratio
                )

                # Session state'te sakla
                st.session_state["bordered_property_image"] = bordered_image

                # Sonucu göster
                st.success("Sınır başarıyla çizildi!")
                st.image(
                    bordered_image,
                    caption="Sınırlı Emlak Görüntüsü",
                    use_container_width=True,
                )

                # Videoya dahil etme seçeneği
                include_in_video = st.checkbox(
                    "Bu görüntüyü videoya dahil et", value=True
                )
                if include_in_video:
                    # Orijinal görüntüyü sınırlı olanla değiştir veya yeni görüntü olarak ekle
                    new_maps_images = st.session_state["maps_images"].copy()
                    new_maps_images.insert(
                        0, bordered_image
                    )  # Sınırlı görüntüyü ilk sıraya ekle
                    st.session_state["maps_images"] = new_maps_images
                    st.info("Sınırlı görüntü video görsellerine eklendi!")

    def _show_custom_images(self):
        """Kullanıcı tarafından yüklenen özel görüntüleri göster"""
        st.subheader("Özel Görüntüler")
        uploaded_files = st.file_uploader(
            "Kendi görsellerinizi ekleyin:",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="En fazla 5 görsel ekleyebilirsiniz.",
        )

        if uploaded_files:
            user_images = []
            for file in uploaded_files[:5]:
                img = Image.open(file)
                user_images.append(img)

            st.session_state["user_images"] = user_images
            st.success(f"{len(user_images)} özel görsel eklendi!")

            for idx, img in enumerate(user_images):
                st.image(
                    img, caption=f"Özel Görsel {idx + 1}", use_container_width=True
                )


class VideoController:
    """Video oluşturma ve işleme için controller"""

    def __init__(self, task_manager):
        self.task_manager = task_manager

    def _check_requirements(self):
        """
        Videoyu oluşturmak için gerekli tüm bileşenlerin mevcut olup olmadığını kontrol eder

        Returns:
            tuple: (requirements_met, missing_components_list)
        """
        missing_components = []

        # Ses dosyası kontrol
        if "audio_path" not in st.session_state:
            missing_components.append("Sesli anlatım")

        # Görüntüleri kontrol et
        if not ("maps_images" in st.session_state or "user_images" in st.session_state):
            missing_components.append("Görüntüler")

        # En az bir görüntü var mı?
        images_count = 0
        if "maps_images" in st.session_state:
            images_count += len(st.session_state["maps_images"])
        if "user_images" in st.session_state:
            images_count += len(st.session_state["user_images"])

        if images_count == 0:
            missing_components.append("En az bir görüntü")

        # Gerekli tüm bileşenler mevcut mu?
        requirements_met = len(missing_components) == 0

        return requirements_met, missing_components

    def show_video_generation(self):
        st.header("Video Oluştur")

        # Gereksinimleri kontrol et
        requirements_met, missing_components = self._check_requirements()

        if not requirements_met:
            st.warning(f"Eksik bileşenler: {', '.join(missing_components)}")
            return

        st.success("Tüm bileşenler hazır! Videoyu oluşturabilirsiniz.")

        # Display system information (new)
        display_system_info()

        # Video gelişmiş ayarları için sekmeler
        tabs = st.tabs(["Temel Ayarlar", "Arkaplan Müziği", "Metin/Logo Ekle", "Gelişmiş Efektler"])

        with tabs[0]:
            # Mevcut video ayarları
            st.subheader("Video Ayarları")
            resolution_option = st.selectbox(
                "Video Çözünürlüğü",
                ["720p (HD)", "1080p (Full HD)"],
                index=0
                if st.session_state.get("video_quality", "normal") == "normal"
                else 1,
            )
            st.session_state["video_quality"] = (
                "normal" if "720p" in resolution_option else "high"
            )

        with tabs[1]:
            self._show_music_options()

        with tabs[2]:
            self._show_overlay_options()
            
        with tabs[3]:
            self._show_advanced_effects()

        # After all images are loaded but before video generation
        # Add a preview section (new)
        all_images = []
        if "maps_images" in st.session_state:
            all_images.extend(st.session_state["maps_images"][:8])
        if "user_images" in st.session_state:
            all_images.extend(st.session_state["user_images"][:5])

        if all_images:
            show_video_preview(all_images, st.session_state.get("audio_path", None))

        # Your existing video generation button
        if st.button("Video Oluştur", type="primary"):
            self._generate_video()

    def _show_music_options(self):
        """Arkaplan müziği seçeneklerini göster"""
        st.subheader("🎵 Arkaplan Müziği Ekle")

        music_options = get_music_options()
        selected_music = st.selectbox(
            "Müzik Türü Seçin:",
            list(music_options.keys()),
            format_func=lambda k: music_options[k],
        )

        # Özel müzik yükleme seçeneği
        if selected_music == "custom":
            uploaded_music = st.file_uploader(
                "Kendi müziğinizi yükleyin:", type=["mp3", "wav", "ogg"]
            )
            if uploaded_music:
                # Geçici dosya oluştur
                temp_dir = tempfile.mkdtemp()
                music_path = os.path.join(
                    temp_dir, f"custom_music.{uploaded_music.name.split('.')[-1]}"
                )

                with open(music_path, "wb") as f:
                    f.write(uploaded_music.getbuffer())

                st.session_state["background_music_path"] = music_path
                st.success("Müzik başarıyla yüklendi!")
                st.audio(music_path)

        elif selected_music != "no_music":
            st.info(f"Seçilen müzik: {music_options[selected_music]}")
    def _show_overlay_options(self):
        """Metin ve logo ekleme seçeneklerini göster"""
        st.subheader("✏️ Metinler ve Logolar")

        # Metin ekleme seçeneği
        use_text_overlay = st.checkbox(
            "Videoya Metin Ekle", value=st.session_state.get("use_text_overlay", False)
        )
        st.session_state["use_text_overlay"] = use_text_overlay

        if use_text_overlay:
            text_content = st.text_input(
                "Metin İçeriği:",
                value=st.session_state.get("overlay_text", ""),
                placeholder="Örn: Emlak360 - www.emlak360.com",
            )
            st.session_state["overlay_text"] = text_content

            text_position = st.selectbox(
                "Metin Konumu:",
                [
                    "bottom",
                    "top",
                    "top-left",
                    "top-right",
                    "bottom-left",
                    "bottom-right",
                ],
                index=0,
                format_func=lambda x: {
                    "bottom": "Alt Orta",
                    "top": "Üst Orta",
                    "top-left": "Sol Üst",
                    "top-right": "Sağ Üst",
                    "bottom-left": "Sol Alt",
                    "bottom-right": "Sağ Alt",
                }.get(x, x),
            )
            st.session_state["overlay_text_position"] = text_position

            text_color = st.color_picker("Metin Rengi:", "#FFFFFF")
            st.session_state["overlay_text_color"] = text_color

        # Logo ekleme seçeneği
        use_logo_overlay = st.checkbox(
            "Videoya Logo Ekle", value=st.session_state.get("use_logo_overlay", False)
        )
        st.session_state["use_logo_overlay"] = use_logo_overlay

        if use_logo_overlay:
            uploaded_logo = st.file_uploader(
                "Logo Yükleyin:", type=["png", "jpg", "jpeg"]
            )

            if uploaded_logo:
                # Logo pozisyonu ve boyutu
                logo_img = Image.open(uploaded_logo)
                st.session_state["overlay_logo"] = logo_img

                col1, col2 = st.columns(2)

                with col1:
                    st.image(logo_img, caption="Logo Önizleme", width=200)

                with col2:
                    logo_position = st.selectbox(
                        "Logo Konumu:",
                        ["bottom-right", "bottom-left", "top-right", "top-left"],
                        index=0,
                        format_func=lambda x: {
                            "bottom-right": "Sağ Alt",
                            "bottom-left": "Sol Alt",
                            "top-right": "Sağ Üst",
                            "top-left": "Sol Üst",
                        }.get(x, x),
                    )
                    st.session_state["overlay_logo_position"] = logo_position

                    logo_size = st.slider("Logo Boyutu (%):", 5, 30, 15)
                    st.session_state["overlay_logo_size"] = logo_size

                    logo_opacity = st.slider(
                        "Logo Şeffaflığı:", 0.1, 1.0, 0.8, step=0.1
                    )
                    st.session_state["overlay_logo_opacity"] = logo_opacity

    def _show_advanced_effects(self):
        """Show advanced video effect options"""
        st.subheader("🎬 Gelişmiş Video Efektleri")
        
        # Cinematic color grading options
        st.write("**Renk Efektleri**")
        cinematic_effect = st.selectbox(
            "Sinematik Efekt:",
            ["Yok", "Standart Sinematik", "Sıcak Tonlar", "Soğuk Tonlar", "Vintage"],
            format_func=lambda x: {
                "Yok": "Efekt Yok",
                "Standart Sinematik": "Standart Sinematik Görünüm",
                "Sıcak Tonlar": "Sıcak Tonlar (Emlak İç Mekan)",
                "Soğuk Tonlar": "Soğuk Tonlar (Modern Tasarım)",
                "Vintage": "Vintage/Nostaljik"
            }.get(x, x)
        )
        
        effect_map = {
            "Standart Sinematik": "cinematic",
            "Sıcak Tonlar": "warm",
            "Soğuk Tonlar": "cool",
            "Vintage": "vintage"
        }
        
        if cinematic_effect != "Yok":
            st.session_state["cinematic_effect"] = effect_map.get(cinematic_effect)
            st.success(f"'{cinematic_effect}' efekti uygulanacak")
        else:
            st.session_state.pop("cinematic_effect", None)
        
        # Stabilization option
        st.write("**Video Stabilizasyonu**")
        stabilize = st.checkbox("Video stabilizasyonu uygula (kamera titremelerini azaltır)", value=True)
        st.session_state["stabilize_video"] = stabilize
        
        if stabilize:
            st.info("Stabilizasyon, video oluşturma süresini uzatabilir ancak daha profesyonel sonuçlar sağlar.")
        
        # Deep image enhancement
        st.write("**Görüntü İyileştirme**")
        deep_enhance = st.checkbox("Yapay zeka ile görüntü kalitesini artır", value=False)
        st.session_state["deep_enhance"] = deep_enhance
        
        if deep_enhance:
            st.info("Bu özellik, görüntülerin yapay zeka ile işlenmesini sağlar ve daha keskin, detaylı sonuçlar üretir.")
            # Add deep enhancement options
            col1, col2 = st.columns(2)
            with col1:
                resolution_boost = st.checkbox("Çözünürlük artırma", value=True)
                st.session_state["deep_enhance_resolution"] = resolution_boost
            with col2:
                denoise = st.checkbox("Gürültü azaltma", value=True)
                st.session_state["deep_enhance_denoise"] = denoise

    def _generate_video(self):
        """Generate video with progress tracking"""
        try:
            # Create progress placeholder
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)
            status_text = st.empty()
            
            with st.spinner("Video oluşturma başlatılıyor..."):
                all_images = []
                if "maps_images" in st.session_state:
                    all_images.extend(st.session_state["maps_images"][:8])
                if "user_images" in st.session_state:
                    all_images.extend(st.session_state["user_images"][:5])

                if not all_images:
                    st.error("En az bir görüntü gerekli!")
                    return

                # Start background task with correct arguments
                task_id = self.task_manager.start_task(
                    generate_video_in_background,
                    task_args=(
                        all_images,
                        st.session_state["audio_path"],
                        st.session_state["transition_type"],
                        st.session_state["fps"],
                        st.session_state["video_quality"]
                    ),
                    task_name="video_generation",
                    timeout=180
                )
                
                st.session_state["video_task_id"] = task_id
                
        except Exception as e:
            st.error(f"Video oluşturma hatası: {str(e)}")
            st.exception(e)  # Show detailed error traceback in UI
            if "video_task_id" in st.session_state:
                del st.session_state["video_task_id"]


class PropertyVideoWizard:
    """Adım adım rehber arayüzü için sınıf"""

    def __init__(self):
        self.step = st.session_state.get("wizard_step", 0)
        self.steps = [
            self.address_step,
            self.property_details_step,
            self.audio_generation_step,
            self.image_collection_step,
            self.video_generation_step,
        ]
        # Task manager ekle
        self.task_manager = BackgroundTaskManager()

    def show(self):
        """Wizard arayüzünü göster"""
        # İlerleme çubuğu
        st.progress(self.step / (len(self.steps) - 1))

        # Mevcut adımı göster
        self.steps[self.step]()

        # Gezinme kontrolleri
        col1, col2 = st.columns(2)
        with col1:
            if self.step > 0:
                if st.button("⬅️ Önceki Adım"):
                    st.session_state["wizard_step"] = self.step - 1
                    safe_rerun()
        with col2:
            if self.step < len(self.steps) - 1:
                if st.button("Sonraki Adım ➡️"):
                    # İlerlemeden önce mevcut adımı doğrula
                    if self.validate_step():
                        st.session_state["wizard_step"] = self.step + 1
                        safe_rerun()

    def validate_step(self):
        """Mevcut adımın geçerli olup olmadığını kontrol et"""
        # Her adım için doğrulama mantığı burada uygulanabilir
        if self.step == 0 and "property_location" not in st.session_state:
            st.error("Devam etmek için bir adres girin!")
            return False
        elif self.step == 1 and "property_text" not in st.session_state:
            st.error("Devam etmek için emlak metnini oluşturun!")
            return False
        elif self.step == 2 and "audio_path" not in st.session_state:
            st.error("Devam etmek için sesli anlatım oluşturun!")
            return False
        elif self.step == 3 and not (
            "maps_images" in st.session_state or "user_images" in st.session_state
        ):
            st.error("Devam etmek için en az bir görüntü ekleyin!")
            return False

        return True

    # Adım uygulamaları (her biri ilgili controller'ı kullanır)
    def address_step(self):
        st.header("1. Adım: Emlak Konumunu Belirleyin")
        # PropertyController kullanılabilir burada...

    def property_details_step(self):
        st.header("2. Adım: Emlak Bilgilerini Girin")
        property_controller = PropertyController()
        property_controller.show_property_form()

    def audio_generation_step(self):
        st.header("3. Adım: Sesli Anlatım Oluşturun")
        audio_controller = AudioController()
        audio_controller.show_audio_generation()

    def image_collection_step(self):
        st.header("4. Adım: Görüntüleri Toplayın")
        image_controller = ImageController()
        image_controller.show_image_collection()

    def video_generation_step(self):
        st.header("5. Adım: Video Oluşturun")
        video_controller = VideoController(self.task_manager)
        video_controller.show_video_generation()


# Ana uygulama çalıştırma kodu
if __name__ == "__main__":
    app = EmlakVideoApp()
    app.run()
