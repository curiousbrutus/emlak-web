"""
Gelişmiş durum yönetimi (state management) için araçlar.
"""

import streamlit as st
import json
import os
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

class StateManager:
    """Emlak video uygulaması için gelişmiş durum yönetimi sınıfı"""
    
    def __init__(self, storage_dir: str = None):
        """
        StateManager başlatıcı
        
        Args:
            storage_dir: Durum verilerinin saklanacağı dizin
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Mevcut durum dosyalarını yükle
        self._project_list = self._load_project_list()
        
    def save_state(self, project_name: str, overwrite: bool = False) -> bool:
        """
        Mevcut uygulama durumunu kaydeder
        
        Args:
            project_name: Proje adı
            overwrite: True ise, mevcut projenin üzerine yazar
            
        Returns:
            İşlemin başarılı olup olmadığı
        """
        # Aynı isimde proje var mı kontrol et
        if not overwrite and project_name in self._project_list:
            return False
        
        # Saklanacak session_state anahtarlarını belirle
        keys_to_save = [
            'property_location',
            'property_text',
            'audio_path',
            'maps_images',
            'user_images',
            'bordered_property_image',
            'video_quality',
            'transition_type',
            'fps',
            'enhance_colors',
            'color_boost'
        ]
        
        # Sadece mevcut anahtarları sakla
        state_data = {}
        for key in keys_to_save:
            if key in st.session_state:
                # PIL.Image ve dosya nesneleri gibi karmaşık nesneleri işle
                if key == 'maps_images' or key == 'user_images':
                    # Görüntüleri sakla
                    images_dir = os.path.join(self.storage_dir, project_name, 'images', key)
                    os.makedirs(images_dir, exist_ok=True)
                    saved_paths = []
                    
                    for idx, img in enumerate(st.session_state[key]):
                        img_path = os.path.join(images_dir, f"image_{idx}.png")
                        img.save(img_path)
                        saved_paths.append(img_path)
                    
                    state_data[key] = saved_paths
                elif key == 'audio_path':
                    # Ses dosyasını sakla
                    if os.path.exists(st.session_state[key]):
                        audio_dir = os.path.join(self.storage_dir, project_name, 'audio')
                        os.makedirs(audio_dir, exist_ok=True)
                        audio_path = os.path.join(audio_dir, 'audio.mp3')
                        
                        with open(st.session_state[key], 'rb') as src_file:
                            with open(audio_path, 'wb') as dst_file:
                                dst_file.write(src_file.read())
                                
                        state_data[key] = audio_path
                else:
                    state_data[key] = st.session_state[key]
        
        # Proje meta verilerini ekle
        state_data['_metadata'] = {
            'saved_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0'
        }
        
        # Projeyi kaydet
        try:
            project_dir = os.path.join(self.storage_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Ana durum dosyasını kaydet
            state_path = os.path.join(project_dir, 'state.json')
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, default=str)
            
            # Proje listesini güncelle
            if project_name not in self._project_list:
                self._project_list.append(project_name)
                self._save_project_list()
                
            return True
        except Exception as e:
            st.error(f"Proje kaydedilemedi: {str(e)}")
            return False
            
    def load_state(self, project_name: str) -> bool:
        """
        Kaydedilmiş bir projeyi yükler
        
        Args:
            project_name: Yüklenecek proje adı
            
        Returns:
            İşlemin başarılı olup olmadığı
        """
        try:
            project_dir = os.path.join(self.storage_dir, project_name)
            state_path = os.path.join(project_dir, 'state.json')
            
            if not os.path.exists(state_path):
                return False
                
            # JSON durum verilerini yükle
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Görüntü ve ses dosyalarını işle
            for key, value in state_data.items():
                if key == 'maps_images' or key == 'user_images':
                    # Görüntüleri PIL nesneleri olarak yükle
                    images = []
                    for img_path in value:
                        if os.path.exists(img_path):
                            from PIL import Image
                            img = Image.open(img_path)
                            images.append(img)
                    
                    if images:
                        st.session_state[key] = images
                elif key != '_metadata':
                    # Diğer değerleri doğrudan aktar
                    st.session_state[key] = value
            
            return True
        except Exception as e:
            st.error(f"Proje yüklenemedi: {str(e)}")
            return False
            
    def get_project_list(self) -> List[str]:
        """Mevcut projelerin listesini döndürür"""
        return self._project_list
        
    def delete_project(self, project_name: str) -> bool:
        """
        Bir projeyi siler
        
        Args:
            project_name: Silinecek proje adı
            
        Returns:
            İşlemin başarılı olup olmadığı
        """
        try:
            project_dir = os.path.join(self.storage_dir, project_name)
            
            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir)
            
            # Proje listesini güncelle
            if project_name in self._project_list:
                self._project_list.remove(project_name)
                self._save_project_list()
                
            return True
        except Exception as e:
            st.error(f"Proje silinemedi: {str(e)}")
            return False
            
    def _load_project_list(self) -> List[str]:
        """Proje listesini dosyadan yükler"""
        list_path = os.path.join(self.storage_dir, 'project_list.json')
        
        if os.path.exists(list_path):
            try:
                with open(list_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        else:
            return []
            
    def _save_project_list(self) -> None:
        """Proje listesini dosyaya kaydeder"""
        list_path = os.path.join(self.storage_dir, 'project_list.json')
        
        with open(list_path, 'w', encoding='utf-8') as f:
            json.dump(self._project_list, f, ensure_ascii=False)

    def get_project_data(self):
        """
        Mevcut durumdan proje verilerini alır
        
        Returns:
            Proje verileri sözlüğü
        """
        # Saklanacak session_state anahtarlarını belirle
        keys_to_save = [
            'property_location',
            'property_text',
            'audio_path',
            'maps_images',
            'user_images',
            'bordered_property_image',
            'video_quality',
            'transition_type',
            'fps',
            'enhance_colors',
            'color_boost'
        ]
        
        # Sadece mevcut anahtarları al
        project_data = {}
        for key in keys_to_save:
            if key in st.session_state:
                project_data[key] = st.session_state[key]
        
        return project_data
        
    def set_project_data(self, project_data):
        """
        Proje verilerini mevcut duruma ayarlar
        
        Args:
            project_data: Ayarlanacak proje verileri sözlüğü
        """
        for key, value in project_data.items():
            st.session_state[key] = value
