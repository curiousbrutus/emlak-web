import streamlit as st
from modules.audio.audio_generation import generate_audio_from_text, get_audio_duration
from config.config import VOICE_OPTIONS, DEFAULT_VOICE

class AudioController:
    """Controller for audio generation and management"""
    
    def show(self):
        """Display audio generation interface"""
        st.header("Sesli Anlatım Oluştur")
        
        if "property_text" not in st.session_state:
            st.warning("Lütfen önce emlak bilgilerini girin!")
            return
            
        st.write(st.session_state["property_text"])
        
        # Voice selection
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
        """Generate audio from text"""
        with st.spinner("Ses oluşturuluyor..."):
            audio_path = generate_audio_from_text(
                st.session_state["property_text"],
                st.session_state.get("voice_id", DEFAULT_VOICE)
            )
            
            if audio_path:
                st.session_state["audio_path"] = audio_path
                st.session_state["audio_duration"] = get_audio_duration(audio_path)
                st.success("Sesli anlatım başarıyla oluşturuldu!")
                st.audio(audio_path)
