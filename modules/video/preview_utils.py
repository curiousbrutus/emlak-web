"""Utilities for generating video previews."""

import streamlit as st
import tempfile
import os
from PIL import Image
import numpy as np
import io
import base64

def create_gif_preview(images, duration=500, max_size=(400, 300)):
    """
    Create a GIF preview from a list of images.
    
    Args:
        images: List of PIL images
        duration: Milliseconds per frame
        max_size: Maximum dimensions (width, height)
        
    Returns:
        Path to generated GIF file
    """
    try:
        # Resize images to consistent size
        resized_images = []
        for img in images:
            # Make a copy to avoid modifying original
            img_copy = img.copy()
            img_copy.thumbnail(max_size, Image.LANCZOS)
            resized_images.append(img_copy)
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        gif_path = os.path.join(temp_dir, "preview.gif")
        
        # Save as GIF
        resized_images[0].save(
            gif_path,
            save_all=True,
            append_images=resized_images[1:],
            optimize=True,
            duration=duration,
            loop=0
        )
        
        return gif_path
    except Exception as e:
        st.error(f"GIF önizleme oluşturma hatası: {str(e)}")
        return None

def show_video_preview(images, audio_path=None):
    """
    Show a preview of what the video will look like.
    
    Args:
        images: List of images to include in the preview
        audio_path: Optional path to audio file
    """
    st.subheader("Video Önizleme")
    
    # Create tabs for different preview options
    preview_tab, images_tab = st.tabs(["Animasyon Önizleme", "Tüm Görüntüler"])
    
    with preview_tab:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if len(images) > 1:
                # Create and display GIF preview
                gif_path = create_gif_preview(images[:min(8, len(images))])
                if gif_path:
                    st.image(gif_path, use_container_width=True)
                    st.caption("Animasyon örneği (gerçek video daha yüksek kalitede olacak)")
            else:
                st.image(images[0], use_container_width=True)
                st.caption("Önizleme için en az 2 görüntü gereklidir")
        
        with col2:
            st.write("**Video İçeriği:**")
            st.write(f"- {len(images)} görüntü")
            if audio_path:
                st.write("- Sesli anlatım")
                st.audio(audio_path)
            
            transition_type = st.session_state.get('transition_type', 'Yakınlaşma')
            st.write(f"- Geçiş efekti: {transition_type}")
            
            quality = "1080p" if st.session_state.get('video_quality') == "high" else "720p"
            st.write(f"- Çözünürlük: {quality}")
    
    with images_tab:
        # Show all images in a grid
        cols = st.columns(4)
        for i, img in enumerate(images):
            with cols[i % 4]:
                st.image(img, caption=f"Görüntü {i+1}", use_container_width=True)
