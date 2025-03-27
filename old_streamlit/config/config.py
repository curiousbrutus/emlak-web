"""Configuration settings for the Real Estate Video Generator."""

import os
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")

# Voice options - Sözlük formatına dönüştürüldü
VOICE_OPTIONS = {
    "TxGEqnHWrfWFTfGW9XjX": "Erkek Sesi", 
    "ErXwobaYiN019PkySvjV": "Kadın Sesi", 
    "21m00Tcm4TlvDq8ikWAM": "Alternatif Ses"
}
DEFAULT_VOICE = ELEVENLABS_VOICE_ID if ELEVENLABS_VOICE_ID in VOICE_OPTIONS else list(VOICE_OPTIONS.keys())[0]

# Define VOICE_LABELS (was missing)
VOICE_LABELS = VOICE_OPTIONS  # Using the same dictionary for labels

# Ensure video directory exists
VIDEO_DIR = "/home/jobbe/Desktop/Projects/emlak_web/vids"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Configure Gemini API if key is available
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Function to initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables if they don't exist."""
    if "GOOGLE_MAPS_API_KEY" not in st.session_state:
        st.session_state["GOOGLE_MAPS_API_KEY"] = GOOGLE_MAPS_API_KEY
    if "GOOGLE_PLACES_API_KEY" not in st.session_state:
        st.session_state["GOOGLE_PLACES_API_KEY"] = GOOGLE_PLACES_API_KEY
    if "GEMINI_API_KEY" not in st.session_state:
        st.session_state["GEMINI_API_KEY"] = GEMINI_API_KEY
    if "ELEVENLABS_API_KEY" not in st.session_state:
        st.session_state["ELEVENLABS_API_KEY"] = ELEVENLABS_API_KEY
    if "enhance_colors" not in st.session_state:
        st.session_state["enhance_colors"] = True
    if "color_boost" not in st.session_state:
        st.session_state["color_boost"] = 1.5
    # Add Turkish labels
    if "voice_labels" not in st.session_state:
        st.session_state["voice_labels"] = VOICE_LABELS
