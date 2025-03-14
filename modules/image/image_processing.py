"""Image processing functions for satellite and street view images."""

import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

def enhance_image(image, boost_factor=1.5, preserve_colors=True):
    """
    Enhance colors and vibrancy of an image while maintaining color stability.
    Also checks if image is grayscale and converts to color if needed.
    
    Args:
        image: PIL image to enhance
        boost_factor: Factor to boost saturation
        preserve_colors: If True, preserves original colors without heavy enhancement
        
    Returns:
        Enhanced PIL image
    """
    try:
        # Convert PIL Image to OpenCV format if needed
        if isinstance(image, Image.Image):
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            img_cv = image.copy()
            
        # Check if image is grayscale
        is_grayscale = len(img_cv.shape) == 2 or (len(img_cv.shape) == 3 and img_cv.shape[2] == 1)
        if is_grayscale:
            # Convert grayscale to color
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR)
        
        # For colored images, enhance them
        # Convert to HSV to manipulate saturation
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV).astype("float32")
        
        # Increase saturation - even for previously grayscale images to add some color
        (h, s, v) = cv2.split(hsv)
        
        if is_grayscale:
            # Apply stronger enhancement for grayscale images
            s = np.clip(s + 50, 0, 255)  # Add base saturation
        else:
            # For already colored images
            s = np.clip(s * boost_factor, 0, 255)
            
        # Enhance brightness slightly
        v = np.clip(v * 1.1, 0, 255)
        
        # Merge and convert back to BGR
        hsv = cv2.merge([h, s, v])
        enhanced = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
        
        # Subtle sharpening
        kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to PIL Image
        enhanced_pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
        return enhanced_pil
    except Exception as e:
        st.warning(f"Image enhancement failed: {e}")
        return image  # Return original image if enhancement fails

def fetch_satellite_image(address=None, lat=None, lng=None, zoom=18, size="640x640", maptype="satellite"):
    """
    Fetch satellite image from Google Maps Static API.
    
    Args:
        address: Address string (used if lat/lng not provided)
        lat, lng: Coordinates (preferred over address if provided)
        zoom: Zoom level (15-20)
        size: Image size (width x height)
        maptype: Map type (satellite, hybrid, roadmap)
        
    Returns:
        PIL Image object or None if failed
    """
    if not st.session_state.get("GOOGLE_MAPS_API_KEY"):
        st.error("Google Maps API key required!")
        return None
        
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    
    if lat is not None and lng is not None:
        location = f"{lat},{lng}"
    else:
        location = address
        
    params = {
        "center": location,
        "zoom": zoom,
        "size": size,
        "maptype": maptype,
        "key": st.session_state["GOOGLE_MAPS_API_KEY"]
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            enhance_colors = st.session_state.get('enhance_colors', True)
            color_boost = st.session_state.get('color_boost', 1.5)
            if enhance_colors:
                img = enhance_image(img, color_boost, preserve_colors=True)
            return img
        else:
            st.error(f"Failed to fetch satellite image: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching satellite image: {str(e)}")
        return None

def fetch_street_view_image(address=None, lat=None, lng=None, size="640x640", fov=90, heading=0, pitch=0):
    """
    Fetch street view image from Google Street View API.
    
    Args:
        address: Address string (used if lat/lng not provided)
        lat, lng: Coordinates (preferred over address if provided)
        size: Image size (width x height)
        fov: Field of view (degrees)
        heading: Camera heading (0-360)
        pitch: Camera pitch (-90 to 90)
        
    Returns:
        PIL Image object or None if failed
    """
    if not st.session_state.get("GOOGLE_MAPS_API_KEY"):
        return None
        
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    
    if lat is not None and lng is not None:
        location = f"{lat},{lng}"
    else:
        location = address
        
    params = {
        "location": location,
        "size": size,
        "fov": fov,
        "heading": heading,
        "pitch": pitch,
        "key": st.session_state["GOOGLE_MAPS_API_KEY"]
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            enhance_colors = st.session_state.get('enhance_colors', True)
            color_boost = st.session_state.get('color_boost', 1.5)
            if enhance_colors:
                img = enhance_image(img, color_boost, preserve_colors=True)
            return img
        else:
            return None
    except Exception as e:
        st.warning(f"Error fetching street view: {str(e)}")
        return None

def draw_property_border(image, color, width=3, border_ratio=0.2):
    """
    Draw a border on a property image.
    
    Args:
        image: PIL Image object
        color: Border color as hex string (#RRGGBB)
        width: Border line width
        border_ratio: Ratio of border inset from edges (0.0-0.5)
    
    Returns:
        PIL Image with drawn border
    """
    img_array = np.array(image)
    h, w = img_array.shape[:2]
    
    # Convert hex color to RGB
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    
    # Draw rectangle (border_ratio inset from edges)
    x1, y1 = int(w * border_ratio), int(h * border_ratio)
    x2, y2 = int(w * (1 - border_ratio)), int(h * (1 - border_ratio))
    
    img_with_border = img_array.copy()
    cv2.rectangle(img_with_border, (x1, y1), (x2, y2), (b, g, r), width)
    
    return Image.fromarray(img_with_border)
