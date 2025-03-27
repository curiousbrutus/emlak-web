"""Music library and audio mixing utilities."""

import os
import tempfile
import requests
import streamlit as st
from pydub import AudioSegment
from pathlib import Path
import shutil

# Base directory for local music files
BASE_DIR = Path(__file__).parent.parent.parent
MUSIC_DIR = BASE_DIR / "static" / "music"
os.makedirs(MUSIC_DIR, exist_ok=True)

# Copy default music files from sample_music to music directory if they don't exist
def initialize_music_library():
    """Initialize music library by using local music files."""
    sample_dir = BASE_DIR / "static" / "sample_music"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Define sample music files - these should be placed in the sample_music directory
    sample_files = {
        "elegant": "elegant_corporate.mp3",
        "inspiring": "inspiring_ambient.mp3", 
        "modern": "modern_corporate.mp3",
        "relaxing": "relaxing_ambient.mp3",
        "nature": "nature_sounds.mp3"
    }
    
    # Create simple empty sample files if they don't exist
    for key, filename in sample_files.items():
        sample_path = sample_dir / filename
        dest_path = MUSIC_DIR / filename
        
        # Copy if source exists and destination doesn't
        if not dest_path.exists():
            if sample_path.exists():
                shutil.copy2(sample_path, dest_path)
                st.info(f"Müzik dosyası kopyalandı: {filename}")
            else:
                # Create a simple silent MP3 as a placeholder
                create_silent_audio(dest_path)
                st.info(f"Örnek müzik dosyası oluşturuldu: {filename}")

def create_silent_audio(filepath, duration=10):
    """Create a silent audio file."""
    try:
        silent = AudioSegment.silent(duration=duration * 1000)  # duration in milliseconds
        silent.export(filepath, format="mp3")
    except Exception as e:
        st.warning(f"Ses dosyası oluşturma hatası: {str(e)}")

# Voice options dictionary
MUSIC_OPTIONS = {
    "elegant": "Elegant Corporate",
    "inspiring": "İlham Verici",
    "modern": "Modern Kurumsal",
    "relaxing": "Rahatlatıcı", 
    "nature": "Doğa Sesleri",
    "custom": "Kendi Müziğiniz",
    "no_music": "Müzik Yok"
}

def get_music_options():
    """
    Get available music options for background music.
    
    Returns:
        Dictionary with music options
    """
    return MUSIC_OPTIONS

def download_music(music_type):
    """
    Get the path to the music file.
    
    Args:
        music_type: Music type key from MUSIC_OPTIONS
        
    Returns:
        Path to music file or None if failed
    """
    if music_type not in MUSIC_OPTIONS or music_type in ["custom", "no_music"]:
        return None
        
    filename = f"{music_type}_music.mp3"
    # Map the key to actual filename based on our naming convention
    if music_type == "elegant":
        filename = "elegant_corporate.mp3"
    elif music_type == "inspiring":
        filename = "inspiring_ambient.mp3"
    elif music_type == "modern":
        filename = "modern_corporate.mp3"
    elif music_type == "relaxing":
        filename = "relaxing_ambient.mp3"
    elif music_type == "nature":
        filename = "nature_sounds.mp3"
    
    file_path = MUSIC_DIR / filename
    
    # If the file doesn't exist locally, create a simple silent file
    if not file_path.exists():
        try:
            create_silent_audio(file_path)
            st.info(f"Müzik dosyası oluşturuldu: {filename}")
        except Exception as e:
            st.error(f"Müzik dosyası hazırlanamadı: {str(e)}")
            return None
    
    return str(file_path)

def mix_audio(voice_path, music_path, music_volume=0.2):
    """
    Mix voice narration with background music.
    
    Args:
        voice_path: Path to voice audio file
        music_path: Path to music audio file
        music_volume: Music volume level (0.0-1.0)
        
    Returns:
        Path to mixed audio file or None if failed
    """
    try:
        # Load audio files
        voice = AudioSegment.from_file(voice_path)
        music = AudioSegment.from_file(music_path)
        
        # Adjust music volume
        music = music - (10 - int(music_volume * 10))  # Adjust volume level
        
        # Loop music to match voice duration if needed
        voice_duration_ms = len(voice)
        music_duration_ms = len(music)
        
        if voice_duration_ms > music_duration_ms:
            # Loop music to match voice length
            repeats = int(voice_duration_ms / music_duration_ms) + 1
            music = music * repeats
        
        # Trim music to voice length
        music = music[:voice_duration_ms]
        
        # Mix voice and music
        mixed = voice.overlay(music)
        
        # Save mixed audio
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "mixed_audio.mp3")
        mixed.export(output_path, format="mp3")
        
        return output_path
    except Exception as e:
        st.error(f"Ses karıştırma hatası: {str(e)}")
        return None

# Initialize music library at module import time
initialize_music_library()
