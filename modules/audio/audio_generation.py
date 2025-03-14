"""Audio generation functions using ElevenLabs text-to-speech API."""

import os
import tempfile
import streamlit as st
import requests
from moviepy.editor import AudioFileClip

def generate_audio_from_text(text, voice_id):
    """
    Generate audio from text using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID
        
    Returns:
        Path to the generated audio file or None if failed
    """
    if not st.session_state.get("ELEVENLABS_API_KEY"):
        st.error("ElevenLabs API anahtarı gereklidir!")
        return None
            
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": st.session_state["ELEVENLABS_API_KEY"]
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            audio_path = os.path.join(temp_dir, "emlak_seslendirme.mp3")
            
            with open(audio_path, "wb") as f:
                f.write(response.content)
            
            return audio_path
        else:
            st.error(f"Ses oluşturma hatası: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Ses oluşturma hatası: {str(e)}")
        return None

def get_audio_duration(audio_path):
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        return duration
    except Exception as e:
        st.error(f"Error getting audio duration: {str(e)}")
        return 0
