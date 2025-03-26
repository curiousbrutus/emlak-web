# IMPORTANT: This must be the first Streamlit command in the app
import streamlit as st

st.set_page_config(
    page_title="Sanal Drone Emlak Video Oluşturucu",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add base imports
from pathlib import Path
import sys
import os
import gc
import time

# Add the project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# First initialize configs and create necessary directories
TEMP_DIR = os.path.join(project_root, 'temp')
STORAGE_DIR = os.path.join(project_root, 'storage')
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

# Import configuration and state management
from config.config import (
    initialize_session_state,
    VOICE_OPTIONS,
    DEFAULT_VOICE,
    VIDEO_DIR,
)
from utils.state_manager import StateManager
from utils.background_tasks import BackgroundTaskManager

# Import controllers after config is initialized
from modules.controllers.property_controller import PropertyController
from modules.controllers.audio_controller import AudioController
from modules.controllers.image_controller import ImageController
from modules.controllers.video_controller import VideoController
from modules.controllers.wizard_controller import WizardController

# Import UI components
from modules.ui.layouts import setup_page_config
from utils.system_check import display_system_info

# Initialize session state before anything else
initialize_session_state()

def create_nav_bar():
    """Create the top navigation bar"""
    with st.container():
        cols = st.columns([2, 1, 1, 1, 2])
        with cols[1]:
            save = st.button("💾 Projeyi Kaydet", use_container_width=True)
        with cols[2]:
            load = st.button("📂 Projeyi Aç", use_container_width=True)
        with cols[3]:
            clear = st.button("🧹 Önbelleği Temizle", use_container_width=True)
        return save, load, clear

# Main application class
class EmlakVideoApp:
    def __init__(self):
        self.state_manager = StateManager()
        self.task_manager = BackgroundTaskManager()
        self.setup_controllers()
        self.current_step = st.session_state.get('current_step', 1)
        self.total_steps = 4

    def setup_controllers(self):
        """Initialize all controllers"""
        self.property_controller = PropertyController()
        self.audio_controller = AudioController()
        self.image_controller = ImageController()
        self.video_controller = VideoController(self.task_manager)
        self.wizard_controller = WizardController(self.task_manager)

    def setup_header(self):
        """Display application header"""
        st.title("🏠 Sanal Drone Emlak Video Oluşturucu")
        save, load, clear = create_nav_bar()
        
        if save: self.save_project()
        if load: self.load_project()
        if clear: self.clear_cache()

        # Show progress bar
        progress = (self.current_step - 1) / (self.total_steps - 1)
        st.progress(progress)
        
        # Show step indicator
        st.markdown(
            f"""
            <div style='text-align: center; margin: 10px 0;'>
                Adım {self.current_step}/{self.total_steps}: 
                {self.get_step_name(self.current_step)}
            </div>
            """, 
            unsafe_allow_html=True
        )

    def setup_sidebar(self):
        """Display simplified sidebar"""
        with st.sidebar:
            st.header("Temel Ayarlar")
            
            # Project selection
            st.subheader("Proje Seçimi")
            projects = self.state_manager.get_project_list()
            if projects:
                selected_project = st.selectbox(
                    "Mevcut Projeler:",
                    ["Yeni Proje"] + projects
                )
                if selected_project != "Yeni Proje":
                    st.button("Bu Projeyi Yükle", 
                             on_click=lambda: self.load_project(selected_project))

            # System info visibility toggle
            show_system_info = st.checkbox("Sistem Bilgilerini Göster", value=False)
            
            if show_system_info:
                st.subheader("🖥️ Sistem Bilgileri")
                display_system_info(use_expander=False)

    def get_step_name(self, step):
        """Get the name of the current step"""
        return {
            1: "Emlak Konumu",
            2: "Emlak Detayları",
            3: "Görüntü ve Ses",
            4: "Video Oluşturma"
        }.get(step, "")

    def show_step_navigation(self):
        """Show step navigation buttons"""
        cols = st.columns([1, 3, 1])
        
        with cols[0]:
            if self.current_step > 1:
                if st.button("⬅️ Önceki Adım"):
                    st.session_state['current_step'] = self.current_step - 1
                    st.rerun()
                    
        with cols[2]:
            if self.current_step < self.total_steps:
                if st.button("Sonraki Adım ➡️"):
                    if self.validate_current_step():
                        st.session_state['current_step'] = self.current_step + 1
                        st.rerun()

    def validate_current_step(self):
        """Validate the current step before proceeding"""
        if self.current_step == 1:
            return "property_location" in st.session_state
        elif self.current_step == 2:
            return "property_text" in st.session_state
        elif self.current_step == 3:
            return ("maps_images" in st.session_state or 
                   "user_images" in st.session_state)
        return True

    def show_wizard_interface(self):
        """Show the step-by-step wizard interface"""
        if self.current_step == 1:
            self.show_location_step()
        elif self.current_step == 2:
            self.property_controller.show()
        elif self.current_step == 3:
            self.show_media_step()
        elif self.current_step == 4:
            self.video_controller.show()

        self.show_step_navigation()

    def show_location_step(self):
        """Show the location selection step"""
        st.header("📍 Emlak Konumu")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            address = st.text_input(
                "Emlak adresi:",
                help="Tam adresi girin (mahalle, sokak, bina no)",
                placeholder="Örnek: Atatürk Mah. Cumhuriyet Cad. No:123, İstanbul"
            )
            
            if address:
                self._process_address(address)
                
        with col2:
            st.info("""
            **Adres Girişi Hakkında:**
            - Tam ve doğru adres girişi önemlidir
            - Adres Google Maps'te bulunabilir olmalıdır
            - Bina numarası ve mahalle adı içermelidir
            """)

    def show_media_step(self):
        """Show the media collection step"""
        tabs = st.tabs(["Görüntüler", "Sesli Anlatım"])
        
        with tabs[0]:
            self.image_controller.show()
        with tabs[1]:
            self.audio_controller.show()

    def run(self):
        """Run the main application"""
        self.setup_header()
        self.setup_sidebar()
        self.show_wizard_interface()

    def _process_address(self, address):
        """Process the entered address and update location data"""
        from modules.geo.geo_utils import get_coordinates_from_address
        
        with st.spinner("Adres bilgileri alınıyor..."):
            lat, lng, formatted_address = get_coordinates_from_address(address)
            
            if lat and lng:
                st.session_state["property_location"] = {
                    "lat": lat,
                    "lng": lng,
                    "formatted_address": formatted_address,
                }
                st.success(f"Konum bulundu: {formatted_address}")

                # Show map
                import folium
                from streamlit_folium import st_folium
                
                m = folium.Map(location=[lat, lng], zoom_start=15)
                folium.Marker([lat, lng], tooltip="Emlak Konumu").add_to(m)
                st_folium(m, width=800, height=300)
            else:
                st.error("Adres bulunamadı. Lütfen geçerli bir adres girin.")

if __name__ == "__main__":
    app = EmlakVideoApp()
    app.run()
