"""Image processing functions for satellite and street view images."""

from typing import Optional, Tuple
import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageColor
from io import BytesIO

def enhance_image(image: Image.Image, boost_factor: float = 1.5) -> Image.Image:
    """
    Enhances the quality of an image using various techniques like color enhancement,
    noise reduction, and sharpening.

    Args:
        image: The input PIL Image.
        boost_factor: Factor to boost saturation (default: 1.5).

    Returns:
        An enhanced PIL Image or the original image if enhancement fails.
    """
    try:
        if isinstance(image, Image.Image):
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        else:
            img_cv = image.copy()
            
        # Check if image is grayscale
        is_grayscale = len(img_cv.shape) == 2 or (len(img_cv.shape) == 3 and img_cv.shape[2] == 1)
        
        # Convert to LAB color space for better color enhancement
        if not is_grayscale:
            lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            
            # Merge channels
            lab = cv2.merge((l,a,b))
            img_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Apply denoising
        img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)
        
        # Enhance sharpness
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        img_cv = cv2.filter2D(img_cv, -1, kernel)
        
        # Boost saturation if needed
        if boost_factor > 1.0:
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV).astype("float32")
            (h, s, v) = cv2.split(hsv)
            s = np.clip(s * boost_factor, 0, 255)
            v = np.clip(v * 1.1, 0, 255)  # Slight brightness boost
            hsv = cv2.merge([h, s, v])
            img_cv = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
        
        # Convert back to PIL Image
        enhanced_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        return enhanced_pil
    except Exception as e:
        st.warning(f"Image enhancement failed: {e}")
        return image


def recognize_objects(image: Image.Image) -> Optional[list]:
    """
    Attempts to recognize objects within an image using a basic object detection model.
    
    Args:
        image: The PIL Image to process.
    
    Returns:
        A list of recognized objects (if any), or None if recognition fails or no objects are found.
    """
    try:
        # Convert PIL image to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Load YOLO model (this is a simplified example; in real use, load a pretrained model)
        # Example: Using a dummy class labels and model config
        class_labels = ["building", "car", "tree"]
        # Replace 'your_model.weights' and 'your_model.cfg' with actual paths to your model weights and config files
        # net = cv2.dnn.readNet("your_model.weights", "your_model.cfg")
        
        # Preprocess the image for the model
        blob = cv2.dnn.blobFromImage(img_cv, 1/255.0, (416, 416), swapRB=True, crop=False)
        # net.setInput(blob)
        
        # Get the layer names and outputs
        # layer_names = net.getLayerNames()
        # output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
        # detections = net.forward(output_layers)
        
        # Simulate detection results
        detections = [
            # format: [x_center, y_center, width, height, confidence, class_id]
            (0.2, 0.3, 0.1, 0.2, 0.9, 0), # Example detection: building
            (0.5, 0.6, 0.05, 0.1, 0.8, 1), # Example detection: car
            (0.8, 0.2, 0.1, 0.2, 0.7, 2), # Example detection: tree
        ]
        
        # Parse detections
        detected_objects = []
        for x_center, y_center, width, height, confidence, class_id in detections:
            if confidence > 0.5:
                label = class_labels[int(class_id)]
                detected_objects.append({
                    "label": label,
                    "confidence": confidence
                })
                
        if not detected_objects:
            return None
        return detected_objects
    except Exception as e:
        st.warning(f"Object recognition failed: {e}")
        return None

def handle_api_response(response: requests.Response, enhance_colors: bool, color_boost: float) -> Optional[Image.Image]:
    """
    Handles the API response from Google Maps and returns a PIL Image.

    Args:
        response: The response object from the API call.
        enhance_colors: Whether to enhance colors.
        color_boost: The factor to boost colors if enhancing.

    Returns:
        A PIL Image or None if the response failed or image processing failed.
    """
    if response.status_code == 200:
        try:
            img = Image.open(BytesIO(response.content))
            if enhance_colors:
                img = enhance_image(img, color_boost)
            return img
        except Exception as e:
            st.error(f"Error processing image data: {e}")
            return None
    else:
        st.error(f"Failed to fetch image: {response.status_code}")
        return None

def fetch_satellite_image(
    address: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    zoom: int = 18,
    size: str = "640x640",
    maptype: str = "satellite",
) -> Optional[Image.Image]:
    """
    Fetches a satellite image from the Google Maps Static API.

    Args:
        address: Address string (if lat/lng not provided).
        lat: Latitude (preferred if provided).
        lng: Longitude (preferred if provided).
        zoom: Zoom level (15-20).
        size: Image size (width x height).
        maptype: Map type (satellite, hybrid, roadmap).

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
        response: requests.Response = requests.get(base_url, params=params)
        enhance_colors: bool = st.session_state.get("enhance_colors", True)
        color_boost: float = st.session_state.get("color_boost", 1.5)
        img: Optional[Image.Image] = handle_api_response(response, enhance_colors, color_boost)
        return img
    except Exception as e:
        st.error(f"Error fetching satellite image: {str(e)}")
        return None


def fetch_street_view_image(
    address: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    size: str = "640x640",
    fov: int = 90,
    heading: int = 0,
    pitch: int = 0,
) -> Optional[Image.Image]:
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
        response: requests.Response = requests.get(base_url, params=params)
        enhance_colors: bool = st.session_state.get("enhance_colors", True)
        color_boost: float = st.session_state.get("color_boost", 1.5)
        img: Optional[Image.Image] = handle_api_response(response, enhance_colors, color_boost)
        return img
    except Exception as e:
        st.warning(f"Error fetching street view: {str(e)}")
        return None


def draw_property_border(
    image: Image.Image,
    color: str,
    width: int = 3,
    border_ratio: float = 0.2,
) -> Image.Image:
    """
    Draw a border on a property image.
    
    Args:
        image: PIL Image object.
        color: Border color as hex string (#RRGGBB).
        width: Border line width.
        border_ratio: Ratio of border inset from edges (0.0-0.5).
    
    Returns:
        PIL Image with a drawn border.
    """
    try:
        ImageColor.getrgb(color)
    except ValueError:
        raise ValueError("Invalid color string provided. Color must be in hex format (#RRGGBB).")

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

