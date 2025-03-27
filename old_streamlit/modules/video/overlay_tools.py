"""Video overlay tools for adding text, logos and watermarks."""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import os
import tempfile

def add_text_overlay(image, text, position="bottom", font_size=24, color=(255, 255, 255), 
                    bg_opacity=0.5, padding=10, font_path=None):
    """
    Görüntüye metin ekler
    
    Args:
        image: PIL görüntüsü
        text: Eklenecek metin
        position: Metin konumu ("top", "bottom", "top-left", etc.)
        font_size: Yazı tipi boyutu
        color: RGB olarak yazı rengi
        bg_opacity: Arka plan opaklığı (0-1)
        padding: Metin etrafındaki dolgu miktarı
        font_path: Özel yazı tipi dosya yolu (None ise varsayılan)
        
    Returns:
        Metin eklenmiş PIL görüntüsü
    """
    # Orijinal görüntü boyutları
    img = image.copy()
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # Yazı tipini ayarla
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, font_size)
        else:
            # Varsayılan yazı tipi
            font = ImageFont.load_default()
            font_size = 16  # Varsayılan yazı tipi için küçült
    except Exception as e:
        st.warning(f"Yazı tipi yüklenemedi, varsayılan kullanılıyor: {str(e)}")
        font = ImageFont.load_default()
        font_size = 16
    
    # Metin boyutunu hesapla
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (font_size * len(text) * 0.6, font_size * 1.5)
    
    # Metin konumunu belirle
    if position == "top":
        text_position = ((width - text_width) / 2, padding)
    elif position == "bottom":
        text_position = ((width - text_width) / 2, height - text_height - padding)
    elif position == "top-left":
        text_position = (padding, padding)
    elif position == "top-right":
        text_position = (width - text_width - padding, padding)
    elif position == "bottom-left":
        text_position = (padding, height - text_height - padding)
    elif position == "bottom-right":
        text_position = (width - text_width - padding, height - text_height - padding)
    elif position == "center":
        text_position = ((width - text_width) / 2, (height - text_height) / 2)
    else:
        text_position = ((width - text_width) / 2, height - text_height - padding)
    
    # Saydam arka plan oluştur
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Metin arka planı çiz
    bg_color = (0, 0, 0, int(255 * bg_opacity))
    overlay_draw.rectangle(
        [
            text_position[0] - padding, 
            text_position[1] - padding,
            text_position[0] + text_width + padding,
            text_position[1] + text_height + padding
        ],
        fill=bg_color
    )
    
    # Metni çiz
    if hasattr(overlay_draw, 'text'):
        overlay_draw.text(text_position, text, font=font, fill=color)
    
    # Orijinal görüntüye arka planı ve metni birleştir
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    
    return img.convert('RGB')

def add_logo_overlay(image, logo_image, position="bottom-right", size_percent=15, padding=10,
                    opacity=0.8):
    """
    Görüntüye logo ekler
    
    Args:
        image: PIL görüntüsü
        logo_image: Logo PIL görüntüsü
        position: Logo konumu
        size_percent: Görüntü boyutunun yüzdesi olarak logo boyutu
        padding: Logo kenarları ile görüntü kenarı arasındaki dolgu
        opacity: Logo opaklığı (0-1)
        
    Returns:
        Logo eklenmiş PIL görüntüsü
    """
    # Orijinal görüntü ve logo boyutları
    img = image.copy()
    width, height = img.size
    logo = logo_image.copy()
    
    # Logo boyutunu ayarla
    logo_width = int(width * size_percent / 100)
    logo_height = int(logo.height * logo_width / logo.width)
    logo = logo.resize((logo_width, logo_height), Image.LANCZOS)
    
    # Logo konumunu belirle
    if position == "top-left":
        logo_position = (padding, padding)
    elif position == "top-right":
        logo_position = (width - logo_width - padding, padding)
    elif position == "bottom-left":
        logo_position = (padding, height - logo_height - padding)
    elif position == "bottom-right":
        logo_position = (width - logo_width - padding, height - logo_height - padding)
    elif position == "center":
        logo_position = ((width - logo_width) / 2, (height - logo_height) / 2)
    else:
        logo_position = (width - logo_width - padding, height - logo_height - padding)
    
    # Logo opaklığını ayarla
    if logo.mode != 'RGBA':
        logo = logo.convert('RGBA')
    
    # RGBA kanallarını ayır
    r, g, b, a = logo.split()
    
    # Alfa kanalını opaklık ile çarp
    a = a.point(lambda x: x * opacity)
    
    # Kanalları yeniden birleştir
    logo = Image.merge('RGBA', (r, g, b, a))
    
    # Orijinal görüntüye logoyu ekle
    img_with_logo = img.copy().convert('RGBA')
    img_with_logo.paste(logo, (int(logo_position[0]), int(logo_position[1])), logo)
    
    return img_with_logo.convert('RGB')

def apply_overlays_to_video_frames(frames, text=None, text_options=None, logo=None, logo_options=None):
    """
    Video karelerine metin ve/veya logo ekler
    
    Args:
        frames: İşlenecek video kareleri listesi
        text: Eklenecek metin (None ise metin eklenmez)
        text_options: Metin ekleme seçenekleri sözlüğü
        logo: Logo görüntüsü (None ise logo eklenmez)
        logo_options: Logo ekleme seçenekleri sözlüğü
        
    Returns:
        Düzenlenmiş video kareleri listesi
    """
    if text is None and logo is None:
        return frames
        
    processed_frames = []
    
    for frame in frames:
        # NumPy dizisini PIL görüntüsüne dönüştür
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Metin ekle
        if text is not None:
            text_opts = text_options or {}
            pil_frame = add_text_overlay(pil_frame, text, **text_opts)
        
        # Logo ekle
        if logo is not None:
            logo_opts = logo_options or {}
            pil_frame = add_logo_overlay(pil_frame, logo, **logo_opts)
        
        # PIL görüntüsünü NumPy dizisine geri dönüştür
        processed_frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
        processed_frames.append(processed_frame)
    
    return processed_frames
