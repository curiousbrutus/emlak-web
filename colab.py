"""
Real Estate Drone Video Generator using Google Maps and Earth Studio
Run this script in Google Colab
"""

# Required installations - uncomment these in Colab
# !pip install google-cloud-storage earthengine-api opencv-python-headless pillow moviepy folium streamlit-folium

import os
import cv2
import numpy as np
from PIL import Image
import requests
import tempfile
from google.colab import files
from moviepy.editor import VideoFileClip, ImageSequenceClip, concatenate_videoclips, AudioFileClip
import folium
from IPython.display import HTML, Image as IPImage
import io
import time
from typing import List, Optional, Tuple, Dict
from geopy.geocoders import Nominatim  # Add this import at the top

class DroneVideoGenerator:
    def __init__(self, api_key: str):
        """Türkçe drone video oluşturucu başlatıcı"""
        self.api_key = api_key
        self.temp_dir = tempfile.mkdtemp()
        self.geolocator = Nominatim(user_agent="emlak_video_generator")
        print("Drone Video Oluşturucu başlatıldı")
    
    def get_coordinates_from_address(self, address: str) -> Tuple[float, float]:
        """Adresten koordinatları al"""
        try:
            location = self.geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            raise ValueError("Adres bulunamadı")
        except Exception as e:
            raise ValueError(f"Adres çözümlenirken hata oluştu: {str(e)}")

    def get_satellite_images(self, lat: float, lng: float, zoom: int = 18, 
                           views: int = 4) -> List[Image.Image]:
        """Uydu görüntülerini Google Maps Static API'den al"""
        images = []
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        for heading in range(0, 360, int(360/views)):
            params = {
                "center": f"{lat},{lng}",
                "zoom": zoom,
                "size": "640x640",
                "maptype": "satellite",
                "key": self.api_key,
                "heading": heading
            }
            
            try:
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    images.append(img)
                    print(f"{heading}° açısından görüntü başarıyla alındı")
            except Exception as e:
                print(f"Uydu görüntüsü alınırken hata: {str(e)}")
                
        return images

    def get_street_view_images(self, lat: float, lng: float, 
                             radius: int = 50) -> List[Image.Image]:
        """Fetch street view images from Google Street View API"""
        images = []
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        
        # Get street view from different angles
        for angle in range(0, 360, 90):
            params = {
                "location": f"{lat},{lng}",
                "size": "640x640",
                "key": self.api_key,
                "heading": angle,
                "radius": radius,
                "pitch": 10
            }
            
            try:
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    images.append(img)
                    print(f"Successfully fetched street view image at {angle}°")
            except Exception as e:
                print(f"Error fetching street view: {str(e)}")
                
        return images

    def enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality"""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Apply enhancements
        # 1. Increase contrast
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        # 2. Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        return Image.fromarray(enhanced)

    def create_transition(self, img1: Image.Image, img2: Image.Image, 
                        frames: int = 30) -> List[Image.Image]:
        """Create smooth transition between images"""
        transition_frames = []
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        
        for i in range(frames):
            alpha = i / frames
            blended = cv2.addWeighted(img1_array, 1-alpha, img2_array, alpha, 0)
            transition_frames.append(Image.fromarray(blended))
            
        return transition_frames

    def create_drone_effect(self, image: Image.Image, frames: int = 60, 
                          effect_type: str = "zoom") -> List[Image.Image]:
        """Create drone-like movement effect"""
        effect_frames = []
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        if effect_type == "zoom":
            for i in range(frames):
                scale = 1 + (i/frames * 0.3)  # Zoom up to 30%
                M = cv2.getRotationMatrix2D((w/2, h/2), 0, scale)
                frame = cv2.warpAffine(img_array, M, (w, h))
                effect_frames.append(Image.fromarray(frame))
                
        elif effect_type == "pan":
            for i in range(frames):
                shift = int((i/frames) * w * 0.2)  # Pan 20% of width
                M = np.float32([[1, 0, shift], [0, 1, 0]])
                frame = cv2.warpAffine(img_array, M, (w, h))
                effect_frames.append(Image.fromarray(frame))
                
        return effect_frames

    def generate_video(self, images: List[Image.Image], output_path: str, 
                      fps: int = 30, audio_path: Optional[str] = None) -> str:
        """Generate final video with all effects"""
        # Create frames with effects
        all_frames = []
        for i, img in enumerate(images):
            # Enhance image
            enhanced = self.enhance_image(img)
            
            # Add drone effect
            effect_type = "zoom" if i % 2 == 0 else "pan"
            effect_frames = self.create_drone_effect(enhanced, effect_type=effect_type)
            all_frames.extend(effect_frames)
            
            # Add transition to next image
            if i < len(images) - 1:
                transition = self.create_transition(enhanced, self.enhance_image(images[i+1]))
                all_frames.extend(transition)
        
        # Create video
        clip = ImageSequenceClip(all_frames, fps=fps)
        
        # Add audio if provided
        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            clip = clip.set_audio(audio)
        
        # Write video file
        clip.write_videofile(output_path, codec='libx264', fps=fps)
        print(f"Video saved to {output_path}")
        return output_path

def main():
    """Colab'da çalıştırılacak ana fonksiyon"""
    # API anahtarını al
    api_key = input("Google Maps API anahtarınızı girin: ")
    generator = DroneVideoGenerator(api_key)
    
    # Adresi al ve koordinatlara çevir
    while True:
        try:
            address = input("Emlak adresini girin (örn: Atatürk Mah. Cumhuriyet Cad. No:1, İstanbul): ")
            lat, lng = generator.get_coordinates_from_address(address)
            print(f"Adres bulundu! Koordinatlar: {lat}, {lng}")
            break
        except ValueError as e:
            print(f"Hata: {str(e)}")
            retry = input("Tekrar denemek ister misiniz? (E/H): ")
            if retry.lower() != 'e':
                print("Program sonlandırılıyor...")
                return
    
    print("Uydu görüntüleri alınıyor...")
    satellite_images = generator.get_satellite_images(lat, lng)
    
    print("Sokak görünümü görüntüleri alınıyor...")
    street_view_images = generator.get_street_view_images(lat, lng)
    
    # Tüm görüntüleri birleştir
    all_images = satellite_images + street_view_images
    
    # Özel görüntüleri yükle
    print("Özel görüntülerinizi yükleyin (isteğe bağlı)...")
    try:
        uploaded = files.upload()
        for filename in uploaded.keys():
            img = Image.open(io.BytesIO(uploaded[filename]))
            all_images.append(img)
    except:
        print("Özel görüntü yüklenmedi")
    
    # Video oluştur
    output_path = "emlak_video.mp4"
    generator.generate_video(all_images, output_path)
    
    # Videoyu indir
    files.download(output_path)

# Colab'da çalıştır
if __name__ == "__main__":
    print("Google Colab Kurulum Talimatları:")
    print("1. !pip install geopy opencv-python-headless pillow moviepy folium komutlarını çalıştırın")
    print("2. GPU çalışma zamanını etkinleştirin: Çalışma Zamanı -> Çalışma zamanı türünü değiştir -> GPU")
    print("3. Scripti çalıştırın")
    
    main()