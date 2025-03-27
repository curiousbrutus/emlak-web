"""Deep learning based image enhancement for real estate photography."""

import cv2
import numpy as np
from PIL import Image
import streamlit as st
import os
import tempfile

class DeepImageEnhancer:
    """
    Deep learning based image enhancement for real estate photography
    """
    
    def __init__(self, use_gpu=None):
        """
        Initialize the enhancer
        
        Args:
            use_gpu: Force GPU usage (None=auto-detect)
        """
        self.models_loaded = False
        self.model_sr = None  # Super resolution model
        self.model_denoise = None  # Denoising model
        
        # Auto-detect GPU
        if use_gpu is None:
            try:
                import torch
                self.use_gpu = torch.cuda.is_available()
            except ImportError:
                self.use_gpu = False
        else:
            self.use_gpu = use_gpu
            
        # Create model cache directory
        self.cache_dir = os.path.join(tempfile.gettempdir(), "deep_enhance_models")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def load_models(self):
        """Load deep learning models"""
        if self.models_loaded:
            return True
        
        try:
            # Try to load OpenCV's DNN Super Resolution model
            self.model_sr = cv2.dnn_superres.DnnSuperResImpl_create()
            
            # Download model if not in cache
            model_path = os.path.join(self.cache_dir, "ESPCN_x4.pb")
            if not os.path.exists(model_path):
                st.info("Downloading super-resolution model (first time only)...")
                import urllib.request
                urllib.request.urlretrieve(
                    "https://github.com/opencv/opencv_contrib/raw/master/modules/dnn_superres/models/ESPCN_x4.pb",
                    model_path
                )
            
            # Load the model
            self.model_sr.readModel(model_path)
            self.model_sr.setModel("espcn", 4)  # 4x upscaling
            
            # Set up denoising parameters
            self.models_loaded = True
            return True
            
        except Exception as e:
            st.warning(f"Could not load deep enhancement models: {e}")
            return False
    
    def enhance(self, image, resolution_boost=True, remove_noise=True, sharpen=True):
        """
        Enhance an image using multiple deep learning techniques
        
        Args:
            image: PIL Image or numpy array
            resolution_boost: Whether to enhance resolution
            remove_noise: Whether to remove noise
            sharpen: Whether to apply sharpening
            
        Returns:
            Enhanced PIL Image
        """
        # Convert to numpy array if PIL Image
        if isinstance(image, Image.Image):
            img = np.array(image)
            if img.shape[2] == 4:  # Handle RGBA
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        else:
            img = image.copy()
            if len(img.shape) == 2:  # Handle grayscale
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        
        # Ensure image is in RGB format for processing
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
        # Get original size for later resizing
        original_h, original_w = img.shape[:2]
        
        # 1. Apply denoising if requested
        if remove_noise:
            # Use non-local means denoising
            img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        
        # 2. Apply super resolution if requested and models are loaded
        if resolution_boost and self.load_models():
            try:
                # Resize image to a reasonable size for SR model (max 1MP)
                max_mp = 1_000_000  # 1 megapixel
                scale_factor = 1.0
                
                if original_w * original_h > max_mp:
                    scale_factor = np.sqrt(max_mp / (original_w * original_h))
                    img = cv2.resize(img, 
                                    (int(original_w * scale_factor), 
                                     int(original_h * scale_factor)), 
                                    interpolation=cv2.INTER_AREA)
                
                # Apply super-resolution
                img = self.model_sr.upsample(img)
                
                # Resize back to slightly larger than original
                boost_factor = 1.2  # 20% resolution boost
                target_w = int(original_w * boost_factor)
                target_h = int(original_h * boost_factor)
                img = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                
            except Exception as e:
                st.warning(f"Super-resolution failed, using standard processing: {e}")
                # Fallback to standard processing
                pass
        
        # 3. Apply sharpening if requested
        if sharpen:
            kernel = np.array([[-1, -1, -1],
                              [-1, 9, -1],
                              [-1, -1, -1]])
            img = cv2.filter2D(img, -1, kernel)
        
        # 4. Convert back to PIL
        return Image.fromarray(img)
