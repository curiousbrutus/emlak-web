"""Görüntü düzenleme ve yeniden sıralama araçları."""

import streamlit as st
from PIL import Image
import numpy as np
import base64
import io
import cv2  # Add missing import

def reorder_images(images, order=None):
    """
    Görüntüleri belirtilen sıraya göre yeniden düzenler
    
    Args:
        images: Görüntü listesi
        order: Yeni sıralama dizisi (None ise mevcut sıra korunur)
        
    Returns:
        Yeniden düzenlenmiş görüntü listesi
    """
    if order is None or len(order) != len(images):
        return images
    
    return [images[i] for i in order]

def display_draggable_images(images, key_prefix="img"):
    """
    Sürükle-bırak ile düzenlenebilir görüntü arayüzü gösterir
    
    Args:
        images: Görüntü listesi
        key_prefix: Görüntü elementleri için anahtar öneki
        
    Returns:
        Yeni görüntü sırası
    """
    st.markdown("### Görüntüleri Düzenleyin")
    st.info("Görüntüleri sürükleyip bırakarak sıralamayı değiştirebilirsiniz.")
    
    # Her görüntü için benzersiz bir id oluştur
    img_ids = [f"{key_prefix}_{i}" for i in range(len(images))]
    
    # Görüntüleri grid halinde göster
    cols = st.columns(3)
    order = list(range(len(images)))
    
    # CSS for drag and drop
    st.markdown("""
    <style>
    .draggable-img {
        cursor: move;
        border: 2px dashed transparent;
        transition: transform 0.2s;
        padding: 5px;
    }
    .draggable-img:hover {
        border-color: #0078ff;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # JavaScript for drag and drop
    js = """
    <script>
    function setupDragDrop() {
        const imageContainers = document.querySelectorAll('.draggable-img-container');
        let draggedItem = null;
        
        imageContainers.forEach(container => {
            container.addEventListener('dragstart', function() {
                draggedItem = this;
                setTimeout(() => this.style.opacity = '0.4', 0);
            });
            
            container.addEventListener('dragend', function() {
                this.style.opacity = '1';
            });
            
            container.addEventListener('dragover', function(e) {
                e.preventDefault();
            });
            
            container.addEventListener('dragenter', function() {
                this.style.border = '2px dashed #0078ff';
            });
            
            container.addEventListener('dragleave', function() {
                this.style.border = '2px dashed transparent';
            });
            
            container.addEventListener('drop', function(e) {
                e.preventDefault();
                if (draggedItem !== this) {
                    // Swap containers
                    const allContainers = Array.from(document.querySelectorAll('.draggable-img-container'));
                    const fromIndex = allContainers.indexOf(draggedItem);
                    const toIndex = allContainers.indexOf(this);
                    
                    // Update new order in hidden input for Streamlit
                    const orderInput = document.getElementById('img-order-data');
                    let currentOrder = JSON.parse(orderInput.value);
                    
                    // Swap elements in order array
                    const temp = currentOrder[fromIndex];
                    currentOrder[fromIndex] = currentOrder[toIndex];
                    currentOrder[toIndex] = temp;
                    
                    // Update the hidden input
                    orderInput.value = JSON.stringify(currentOrder);
                    
                    // Visually swap elements
                    const parentContainer = this.parentNode;
                    const beforeElement = (fromIndex < toIndex) ? this.nextSibling : this;
                    parentContainer.insertBefore(draggedItem, beforeElement);
                    
                    // Trigger order update event
                    const event = new Event('orderUpdate');
                    orderInput.dispatchEvent(event);
                }
                this.style.border = '2px dashed transparent';
            });
        });
    }
    
    document.addEventListener('DOMContentLoaded', setupDragDrop);
    </script>
    """
    
    # Create hidden input to store order
    order_data = st.empty()
    
    # Display images with drag and drop
    for i, (img, img_id) in enumerate(zip(images, img_ids)):
        with cols[i % 3]:
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # HTML for draggable image
            st.markdown(f"""
            <div class="draggable-img-container" draggable="true" id="container-{img_id}">
                <div class="draggable-img">
                    <img src="data:image/png;base64,{img_str}" width="100%" />
                    <p style="text-align:center;">Görüntü {i+1}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add JavaScript code at the end
    st.markdown(js, unsafe_allow_html=True)
    
    # Return the current order
    return order

def create_image_arranger(images):
    """
    Streamlit için görüntü düzenleyici bileşen
    
    Args:
        images: Düzenlenecek görüntü listesi
        
    Returns:
        Düzenlenmiş görüntü listesi ve değişim bayrağı
    """
    st.subheader("Görüntüleri Düzenleyin")
    
    # Düzenleme türü seçimi
    edit_mode = st.radio("Düzenleme Modu:", 
                      ["Manuel Sıralama", "Otomatik Sıralama"],
                      horizontal=True)
    
    if edit_mode == "Manuel Sıralama":
        # Görüntüleri göster ve manuel düzenleme için arayüz sağla
        image_order = display_draggable_images(images)
        
        # Sıralama butonları
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Önemli Olanları Öne Çıkar"):
                # Büyük ve daha detaylı görüntüleri öne al
                image_sizes = [img.width * img.height for img in images]
                sorted_order = sorted(range(len(images)), key=lambda i: image_sizes[i], reverse=True)
                return reorder_images(images, sorted_order), True
        
        with col2:
            if st.button("Ufak Görüntüleri Sona Al"):
                # Küçük görüntüleri sona al
                image_sizes = [img.width * img.height for img in images]
                sorted_order = sorted(range(len(images)), key=lambda i: image_sizes[i])
                return reorder_images(images, sorted_order), True
                
        with col3:
            if st.button("Orijinal Sıraya Döndür"):
                return images, True
    
    elif edit_mode == "Otomatik Sıralama":
        # Otomatik sıralama seçenekleri
        sort_option = st.selectbox(
            "Sıralama Kriteri:",
            ["En Net Olanlar Önce", "En İyi Kompozisyonlar Önce", "En Renkli Olanlar Önce"]
        )
        
        if st.button("Otomatik Sırala"):
            if sort_option == "En Net Olanlar Önce":
                # Görüntü netliğine göre sıralama (laplasyon filtresi)
                clarity_scores = []
                for img in images:
                    img_array = np.array(img.convert('L'))  # Gri tonlama
                    laplacian = cv2.Laplacian(img_array, cv2.CV_64F).var()
                    clarity_scores.append(laplacian)
                
                sorted_order = sorted(range(len(images)), key=lambda i: clarity_scores[i], reverse=True)
                return reorder_images(images, sorted_order), True
                
            elif sort_option == "En İyi Kompozisyonlar Önce":
                # Kural üçte bir kompozisyonuna göre sıralama
                composition_scores = []
                for img in images:
                    img_array = np.array(img)
                    # Basit bir kompozisyon puanı hesapla
                    h, w = img_array.shape[:2]
                    center_region = img_array[h//4:3*h//4, w//4:3*w//4]
                    center_std = np.std(center_region)
                    composition_scores.append(center_std)
                
                sorted_order = sorted(range(len(images)), key=lambda i: composition_scores[i], reverse=True)
                return reorder_images(images, sorted_order), True
                
            elif sort_option == "En Renkli Olanlar Önce":
                # Renk doygunluğuna göre sıralama
                saturation_scores = []
                for img in images:
                    img_hsv = np.array(img.convert('HSV'))
                    saturation = np.mean(img_hsv[:, :, 1])
                    saturation_scores.append(saturation)
                
                sorted_order = sorted(range(len(images)), key=lambda i: saturation_scores[i], reverse=True)
                return reorder_images(images, sorted_order), True
    
    return images, False
