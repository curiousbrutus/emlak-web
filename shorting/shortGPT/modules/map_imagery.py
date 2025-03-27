import requests
from PIL import Image
import io
import numpy as np
import cv2
import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import environment loader
from shortGPT.utils.env_loader import load_environment
load_environment()

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def _save_image_to_file(img, filepath):
    """Safely save an image to file, converting modes if necessary"""
    try:
        # Check if the image is in palette mode (P)
        if img.mode == 'P':
            img = img.convert('RGB')
        
        # Determine appropriate format based on file extension
        img.save(filepath)
        return True
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False

def fetch_satellite_image(lat, lng, zoom=18, maptype="satellite", size="600x600"):
    """Fetch satellite image from Google Maps API"""
    url = f"https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "center": f"{lat},{lng}",
        "zoom": zoom,
        "size": size,
        "maptype": maptype,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        logger.info(f"Fetching satellite image at {lat}, {lng}, zoom {zoom}")
        response = requests.get(url, params=params)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            logger.info(f"Successfully fetched image: {img.size} pixels")
            return img
        else:
            logger.error(f"Error fetching satellite image: {response.status_code}")
            logger.debug(f"Response: {response.text}")
            return None
    except Exception as e:
        logger.exception(f"Exception in fetch_satellite_image: {str(e)}")
        return None

def fetch_street_view_image(lat, lng, heading=0, pitch=0, fov=90, size="600x400"):
    """Fetch street view image from Google Maps API"""
    url = f"https://maps.googleapis.com/maps/api/streetview"
    params = {
        "location": f"{lat},{lng}",
        "size": size,
        "heading": heading,
        "pitch": pitch,
        "fov": fov,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            return img
        else:
            print(f"Error fetching street view image: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception in fetch_street_view_image: {str(e)}")
        return None

def draw_property_border(image, color="#FF0000", width=3, border_ratio=0.2):
    """Draw property border on an image"""
    # Convert PIL image to OpenCV format
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    h, w = img_cv.shape[:2]
    
    # Calculate border coordinates based on ratio
    border_x = int(w * border_ratio)
    border_y = int(h * border_ratio)
    border_w = w - 2 * border_x
    border_h = h - 2 * border_y
    
    # Parse color
    if isinstance(color, str) and color.startswith('#'):
        color = color.lstrip('#')
        color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        color = (color[2], color[1], color[0])  # Convert RGB to BGR
    
    # Draw rectangle
    cv2.rectangle(img_cv, (border_x, border_y), (border_x + border_w, border_y + border_h), color, width)
    
    # Convert back to PIL
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)

def apply_manual_border(image, points, color="#FF0000", width=3, closed=True):
    """
    Apply a manually drawn border to an image
    
    Args:
        image (PIL.Image): The input image
        points (list): List of (x, y) points defining the border
        color (str): Border color as hex string
        width (int): Border width in pixels
        closed (bool): Whether to close the polygon
        
    Returns:
        PIL.Image: Image with border drawn
    """
    if not points or len(points) < 2:
        logger.warning("Not enough points to draw a border")
        return image
    
    # Convert PIL image to OpenCV format
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Parse color
    if isinstance(color, str) and color.startswith('#'):
        color = color.lstrip('#')
        color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        color = (color[2], color[1], color[0])  # Convert RGB to BGR
    
    # Draw lines between points
    points = np.array(points, np.int32)
    points = points.reshape((-1, 1, 2))
    
    if closed and len(points) >= 3:
        # Draw closed polygon
        cv2.polylines(img_cv, [points], True, color, width)
    else:
        # Draw open polyline
        cv2.polylines(img_cv, [points], False, color, width)
    
    # Convert back to PIL
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)

def highlight_property_area(image, points, color="#FF0000", alpha=0.3):
    """
    Highlight the property area with a semi-transparent fill
    
    Args:
        image (PIL.Image): The input image
        points (list): List of (x, y) points defining the area
        color (str): Fill color as hex string
        alpha (float): Transparency level (0-1)
        
    Returns:
        PIL.Image: Image with highlighted area
    """
    if not points or len(points) < 3:
        logger.warning("Not enough points to highlight area")
        return image
    
    # Convert PIL image to OpenCV format
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Create mask for the polygon
    mask = np.zeros_like(img_cv)
    
    # Parse color
    if isinstance(color, str) and color.startswith('#'):
        color = color.lstrip('#')
        color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        color = (color[2], color[1], color[0])  # Convert RGB to BGR
    
    # Fill the polygon
    points_array = np.array(points, np.int32)
    cv2.fillPoly(mask, [points_array], color)
    
    # Apply the mask with transparency
    result = cv2.addWeighted(img_cv, 1, mask, alpha, 0)
    
    # Draw the border
    cv2.polylines(result, [points_array.reshape((-1, 1, 2))], True, color, 2)
    
    # Convert back to PIL
    img_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)
