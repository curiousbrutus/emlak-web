import streamlit as st

def initialize_app_state():
    """Initialize application state and default values"""
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "tabs"
        
    # Video settings defaults
    if "fps" not in st.session_state:
        st.session_state["fps"] = 30
    if "video_quality" not in st.session_state:
        st.session_state["video_quality"] = "normal"
    if "transition_type" not in st.session_state:
        st.session_state["transition_type"] = "Yakınlaşma"
    if "enhance_colors" not in st.session_state:
        st.session_state["enhance_colors"] = True
    if "color_boost" not in st.session_state:
        st.session_state["color_boost"] = 1.5
