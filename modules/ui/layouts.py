import streamlit as st

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Sanal Drone Emlak Video Oluşturucu",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def show_header():
    """Display application header"""
    st.title("🏠 Sanal Drone Emlak Video Oluşturucu")

def show_sidebar():
    """Display sidebar with settings"""
    with st.sidebar:
        st.header("Video Ayarları")
        show_video_settings()
        show_templates()

def show_video_settings():
    """Display video settings in sidebar"""
    st.session_state["fps"] = st.slider(
        "Kare Hızı (FPS)", 
        15, 60, 30, 
        help="Saniyedeki kare sayısı"
    )
    
    st.session_state["video_quality"] = st.radio(
        "Video Kalitesi",
        ["normal", "high"],
        format_func=lambda x: "Normal (720p)" if x == "normal" else "Yüksek (1080p)",
    )
    
    st.session_state["transition_type"] = st.selectbox(
        "Geçiş Efekti", 
        ["Yakınlaşma", "Kaydırma", "Yakınlaşma ve Kaydırma"]
    )

def show_templates():
    """Display video template options in sidebar"""
    st.subheader("📋 Hazır Şablonlar")

    templates = {
        "Lüks Konut": {
            "transition_type": "Yakınlaşma ve Kaydırma",
            "fps": 30,
            "video_quality": "high",
            "color_boost": 1.8,
            "description": "Yüksek kaliteli, akıcı geçişlerle lüks konut videoları için ideal ayarlar."
        },
        "Ticari Emlak": {
            "transition_type": "Kaydırma",
            "fps": 24,
            "video_quality": "high",
            "color_boost": 1.3,
            "description": "Ticari mülkler için profesyonel görünümlü sunumlar."
        },
        "Ekonomik Paket": {
            "transition_type": "Yakınlaşma",
            "fps": 24,
            "video_quality": "normal",
            "color_boost": 1.5,
            "description": "Hızlı ve verimli oluşturma için temel ayarlar."
        }
    }

    selected_template = st.selectbox("Şablon Seç:", ["Özel"] + list(templates.keys()))

    if selected_template != "Özel":
        st.info(templates[selected_template]["description"])
        
        if st.button(f"'{selected_template}' Şablonunu Uygula"):
            template = templates[selected_template]
            for key, value in template.items():
                if key != "description":
                    st.session_state[key] = value
            st.success(f"'{selected_template}' şablonu uygulandı!")
