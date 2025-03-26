import streamlit as st
from utils.background_tasks import generate_video_in_background
from modules.video.preview_utils import show_video_preview
from utils.system_check import display_system_info

class VideoController:
    """Controller for video generation and management"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager

    def show(self):
        """Show video generation interface"""
        st.header("🎬 Video Oluşturma")
        
        # Video settings in tabs
        settings_tab, preview_tab = st.tabs(["Video Ayarları", "Önizleme"])
        
        with settings_tab:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Temel Ayarlar")
                quality = st.radio(
                    "Video Kalitesi",
                    ["normal", "high"],
                    format_func=lambda x: "Normal (720p)" if x == "normal" else "Yüksek (1080p)"
                )
                fps = st.slider("Kare Hızı (FPS)", 15, 60, 30)
                transition = st.selectbox(
                    "Geçiş Efekti", 
                    ["Yakınlaşma", "Kaydırma", "Yakınlaşma ve Kaydırma"]
                )
            
            with col2:
                st.subheader("Görüntü İyileştirme")
                enhance = st.checkbox("Görüntü Kalitesini İyileştir", value=True)
                if enhance:
                    boost = st.slider("Renk Canlılığı", 1.0, 2.5, 1.5)
                    
                st.subheader("Ses Ayarları")
                music_volume = st.slider("Müzik Ses Seviyesi", 0.0, 1.0, 0.3)
                
        with preview_tab:
            self._show_preview()

        # Generate button
        if st.button("🎥 Video Oluştur", type="primary", use_container_width=True):
            self._generate_video()

    def _check_requirements(self):
        """Check if all required components are available"""
        missing_components = []

        # Check audio
        if "audio_path" not in st.session_state:
            missing_components.append("Sesli anlatım")

        # Check images
        if not ("maps_images" in st.session_state or "user_images" in st.session_state):
            missing_components.append("Görüntüler")

        # Check minimum image count
        images_count = 0
        if "maps_images" in st.session_state:
            images_count += len(st.session_state["maps_images"])
        if "user_images" in st.session_state:
            images_count += len(st.session_state["user_images"])

        if images_count == 0:
            missing_components.append("En az bir görüntü")

        return len(missing_components) == 0, missing_components

    def _generate_video(self):
        """Generate video with progress tracking"""
        try:
            with st.spinner("Video oluşturma başlatılıyor..."):
                all_images = []
                if "maps_images" in st.session_state:
                    all_images.extend(st.session_state["maps_images"][:8])
                if "user_images" in st.session_state:
                    all_images.extend(st.session_state["user_images"][:5])

                if not all_images:
                    st.error("En az bir görüntü gerekli!")
                    return

                # Start background task
                task_id = self.task_manager.start_task(
                    task_function=generate_video_in_background,
                    task_args=(
                        all_images,
                        st.session_state["audio_path"],
                        st.session_state["transition_type"],
                        st.session_state["fps"],
                        st.session_state["video_quality"]
                    ),
                    task_name="video_generation",
                    timeout=1800
                )
                
                st.session_state["video_task_id"] = task_id
                
        except Exception as e:
            st.error(f"Video oluşturma hatası: {str(e)}")
            st.exception(e)
            if "video_task_id" in st.session_state:
                del st.session_state["video_task_id"]
