"""Integration helpers for image enhancement workflows."""

import streamlit as st
from PIL import Image
import os
import tempfile

# Import standard and deep enhancers
from modules.image.image_processing import enhance_image
from modules.image.deep_enhance import DeepImageEnhancer

# Singleton enhancer instance
_deep_enhancer = None

def get_deep_enhancer():
    """Get or create the deep enhancer singleton"""
    global _deep_enhancer
    if _deep_enhancer is None:
        _deep_enhancer = DeepImageEnhancer()
    return _deep_enhancer

def smart_enhance_image(image, use_deep_enhance=False, boost_factor=1.5, 
                       resolution_boost=True, denoise=True):
    """
    Smart image enhancement using either standard or deep learning methods
    
    Args:
        image: PIL Image to enhance
        use_deep_enhance: Whether to use deep learning enhancement
        boost_factor: Color boost factor for standard enhancement
        resolution_boost: Whether to boost resolution (deep enhance only)
        denoise: Whether to apply denoising (deep enhance only)
        
    Returns:
        Enhanced PIL Image
    """
    if use_deep_enhance:
        # Use deep learning enhancement
        enhancer = get_deep_enhancer()
        return enhancer.enhance(
            image, 
            resolution_boost=resolution_boost,
            remove_noise=denoise,
            sharpen=True
        )
    else:
        # Use standard enhancement
        return enhance_image(image, boost_factor=boost_factor)

def batch_enhance_images(images, progress_callback=None, **kwargs):
    """
    Enhance a batch of images with progress reporting
    
    Args:
        images: List of PIL Images
        progress_callback: Callback for reporting progress
        **kwargs: Parameters for smart_enhance_image
        
    Returns:
        List of enhanced PIL Images
    """
    enhanced_images = []
    total = len(images)
    
    for i, img in enumerate(images):
        if progress_callback:
            progress_callback(i / total, f"Enhancing image {i+1}/{total}")
            
        enhanced = smart_enhance_image(img, **kwargs)
        enhanced_images.append(enhanced)
        
    if progress_callback:
        progress_callback(1.0, "Enhancement complete")
        
    return enhanced_images
