import streamlit as st
from PIL import Image
from modules.image.image_processing import (
    fetch_satellite_image,
    fetch_street_view_image,
    draw_property_border,
    enhance_image
)

class ImageController:
    """Controller for image collection and processing"""
    
    def show(self):
        """Display image collection interface"""
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
        """Show map and satellite images section"""
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
    
    def _show_custom_images(self):
        """Show custom image upload section"""
        st.subheader("Özel Görüntüler")
        
        uploaded_files = st.file_uploader(
            "Kendi görsellerinizi ekleyin:",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="En fazla 5 görsel ekleyebilirsiniz.",
        )
        
        if uploaded_files:
            self._process_uploaded_images(uploaded_files[:5])
