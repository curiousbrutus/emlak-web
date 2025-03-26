import streamlit as st
from modules.controllers.property_controller import PropertyController
from modules.controllers.audio_controller import AudioController
from modules.controllers.image_controller import ImageController
from modules.controllers.video_controller import VideoController

class WizardController:
    """Controller for wizard-style interface"""
    
    def __init__(self, task_manager):
        self.task_manager = task_manager
        self.current_step = 0
        self.steps = [
            {
                "title": "1. Emlak Bilgileri",
                "description": "Emlak detaylarını girin ve açıklama oluşturun",
                "controller": PropertyController()
            },
            {
                "title": "2. Sesli Anlatım",
                "description": "Açıklamayı sesli anlatıma dönüştürün",
                "controller": AudioController()
            },
            {
                "title": "3. Görüntüler",
                "description": "Emlak görüntülerini ekleyin",
                "controller": ImageController()
            },
            {
                "title": "4. Video Oluştur",
                "description": "Video ayarlarını yapın ve oluşturun",
                "controller": VideoController(task_manager)
            }
        ]

    def show(self):
        """Display the wizard interface"""
        st.title("🎯 Adım Adım Video Oluşturma")

        # Show progress bar
        progress = self.current_step / (len(self.steps) - 1)
        st.progress(progress)

        # Show current step
        current = self.steps[self.current_step]
        st.header(current["title"])
        st.write(current["description"])

        # Step content
        with st.container():
            current["controller"].show()

        # Navigation buttons
        self._show_navigation()

        # Show step indicators
        self._show_step_indicators()

    def _show_navigation(self):
        """Show navigation buttons"""
        cols = st.columns([1, 1, 3, 1])

        with cols[0]:
            if self.current_step > 0:
                if st.button("⬅️ Önceki"):
                    self._go_to_previous_step()

        with cols[1]:
            if st.button("🏠 Ana Sayfa"):
                st.session_state["current_view"] = "tabs"
                st.experimental_rerun()

        with cols[3]:
            if self.current_step < len(self.steps) - 1:
                if st.button("Sonraki ➡️"):
                    if self._validate_current_step():
                        self._go_to_next_step()
            else:
                if st.button("🎬 Tamamla", type="primary"):
                    if self._validate_current_step():
                        st.success("Video oluşturma tamamlandı!")
                        st.balloons()

    def _show_step_indicators(self):
        """Show step progress indicators"""
        st.write("---")
        cols = st.columns(len(self.steps))
        
        for i, step in enumerate(self.steps):
            with cols[i]:
                if i < self.current_step:
                    st.markdown(f"<div style='text-align: center; color: green;'>✓<br>{step['title']}</div>", 
                              unsafe_allow_html=True)
                elif i == self.current_step:
                    st.markdown(f"<div style='text-align: center; font-weight: bold;'>●<br>{step['title']}</div>", 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center; color: gray;'>○<br>{step['title']}</div>", 
                              unsafe_allow_html=True)

    def _validate_current_step(self):
        """Validate current step requirements"""
        current = self.steps[self.current_step]
        
        if current["title"] == "1. Emlak Bilgileri":
            if "property_text" not in st.session_state:
                st.warning("Lütfen emlak metnini oluşturun!")
                return False
        
        elif current["title"] == "2. Sesli Anlatım":
            if "audio_path" not in st.session_state:
                st.warning("Lütfen sesli anlatım oluşturun!")
                return False
        
        elif current["title"] == "3. Görüntüler":
            if not ("maps_images" in st.session_state or "user_images" in st.session_state):
                st.warning("Lütfen en az bir görüntü ekleyin!")
                return False
        
        return True

    def _go_to_next_step(self):
        """Proceed to next step"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            st.experimental_rerun()

    def _go_to_previous_step(self):
        """Go back to previous step"""
        if self.current_step > 0:
            self.current_step -= 1
            st.experimental_rerun()
