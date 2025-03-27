import gradio as gr
import sys
import os
import logging
import numpy as np
from pathlib import Path
import tempfile
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import environment loader early
from shortGPT.utils.env_loader import load_environment
load_environment()

# Now import the modules that need the environment variables
from shortGPT.modules.map_imagery import (
    fetch_satellite_image, 
    fetch_street_view_image, 
    apply_manual_border,
    highlight_property_area
)
from shortGPT.modules.geo_utils import get_coordinates_from_address, get_nearby_places
from PIL import Image

def search_location(address):
    """Search for a location and return map data"""
    if not address:
        return None, None, "Please enter an address", []
    
    logger.info(f"Searching for address: {address}")
    lat, lng, formatted_address = get_coordinates_from_address(address)
    
    if not lat or not lng:
        return None, None, "Could not find location", []
    
    logger.info(f"Found coordinates: {lat}, {lng}")
    
    # Get satellite image
    sat_img = fetch_satellite_image(lat, lng)
    
    # Get nearby places
    nearby = get_nearby_places(lat, lng, radius=1000)
    nearby_info = ""
    for place in nearby[:5]:
        nearby_info += f"- {place['name']} ({place['type']}): {place['distance']}m\n"
    
    return sat_img, f"{lat}, {lng}", formatted_address, nearby_info

def process_drawn_mask(image, mask_data):
    """Process the drawn mask data from the sketch component"""
    if image is None or mask_data is None:
        return None
    
    # Convert the mask to a numpy array
    mask = np.array(mask_data)
    
    # Find contours in the mask
    gray = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image
    
    # Use the largest contour
    contour = max(contours, key=cv2.contourArea)
    
    # Extract points from the contour
    points = [tuple(point[0]) for point in contour]
    
    # Highlight the selected area
    result = highlight_property_area(image, points)
    
    return result

def handle_manual_border(image, points_json):
    """Apply a manually drawn border to an image"""
    if image is None:
        return None
    
    try:
        points = json.loads(points_json) if points_json else []
        if not points:
            return image
        
        return highlight_property_area(image, points)
    except Exception as e:
        logger.error(f"Error applying manual border: {e}")
        return image

def create_ui():
    """Create a test UI for real estate features"""
    with gr.Blocks(title="Real Estate Feature Test") as demo:
        gr.Markdown("# Real Estate Video Feature Test")
        gr.Markdown("Test the core functionality of your real estate integration")
        
        # Display environment status at the top
        api_key = "✅ Set" if os.environ.get("GOOGLE_MAPS_API_KEY") else "❌ Not Set"
        gr.Markdown(f"**Google Maps API Key Status:** {api_key}")
        
        with gr.Tab("Location Search"):
            address_input = gr.Textbox(label="Property Address", placeholder="Enter an address...")
            search_button = gr.Button("Search Location")
            
            with gr.Row():
                with gr.Column():
                    image_output = gr.Image(label="Satellite Image", type="pil")
                    coords_output = gr.Textbox(label="Coordinates")
                with gr.Column():
                    address_output = gr.Textbox(label="Formatted Address")
                    nearby_output = gr.Textbox(label="Nearby Places", lines=8)
            
            search_button.click(
                search_location,
                inputs=[address_input],
                outputs=[image_output, coords_output, address_output, nearby_output]
            )
        
        with gr.Tab("Manual Property Border"):
            gr.Markdown("### Draw the property border manually")
            gr.Markdown("Upload or search for a satellite image, then use the drawing tool to mark the property boundaries.")
            
            with gr.Row():
                with gr.Column():
                    # Input image
                    input_image = gr.Image(label="Property Image", type="pil")
                    
                    # Drawing interface
                    drawing_interface = gr.Image(
                        label="Draw Property Boundaries", 
                        tool="sketch", 
                        type="pil",
                        brush_radius=3,
                        interactive=True,
                        elem_id="drawing_canvas"
                    )
                    
                    save_button = gr.Button("Apply Boundary")
                
                with gr.Column():
                    # Output image with boundaries
                    output_image = gr.Image(label="Result with Property Boundary", type="pil")
                    
                    # Save result
                    save_output = gr.Button("Save Result")
            
            # Logic for drawing input image to drawing interface
            input_image.change(
                lambda x: x if x is not None else None,
                inputs=[input_image],
                outputs=[drawing_interface]
            )
            
            # Apply the drawn boundary
            save_button.click(
                process_drawn_mask,
                inputs=[input_image, drawing_interface],
                outputs=[output_image]
            )
            
            # Save the result
            save_output.click(
                lambda x: x.save(os.path.join(tempfile.gettempdir(), "property_boundary.png")) or "Image saved to temporary directory",
                inputs=[output_image],
                outputs=[gr.Textbox(label="Save Status")]
            )
            
        with gr.Tab("Point-Based Property Border"):
            gr.Markdown("### Mark property boundaries by selecting points")
            gr.Markdown("Click on the image to add points that define the property boundary.")
            
            with gr.Row():
                with gr.Column():
                    # Input image for point selection
                    point_input_image = gr.Image(label="Property Image", type="pil")
                    
                    # Text area to show and edit points
                    points_text = gr.Textbox(
                        label="Property Boundary Points (JSON)", 
                        placeholder='[[x1,y1], [x2,y2], ...]',
                        lines=3
                    )
                    
                    apply_points_button = gr.Button("Apply Points")
                
                with gr.Column():
                    # Output image with point boundaries
                    point_output_image = gr.Image(label="Result with Property Boundary", type="pil")
                    
                    # Color picker for the boundary
                    color_picker = gr.ColorPicker(label="Boundary Color", value="#FF0000")
                    
                    clear_points_button = gr.Button("Clear Points")
            
            # JavaScript for point selection
            point_input_image.select(
                lambda img, evt: json.dumps(json.loads(evt.target.value or '[]') + [[evt.index_x, evt.index_y]]),
                inputs=[point_input_image, points_text],
                outputs=[points_text]
            )
            
            # Apply the points
            apply_points_button.click(
                handle_manual_border,
                inputs=[point_input_image, points_text],
                outputs=[point_output_image]
            )
            
            # Clear points
            clear_points_button.click(
                lambda: "[]",
                outputs=[points_text]
            )
        
        with gr.Tab("System Info"):
            gr.Markdown("## Environment Information")
            
            # Check API keys
            google_key = "✅ Set" if os.environ.get("GOOGLE_MAPS_API_KEY") else "❌ Not Set"
            openai_key = "✅ Set" if os.environ.get("OPENAI_API_KEY") else "❌ Not Set"
            elevenlabs_key = "✅ Set" if os.environ.get("ELEVENLABS_API_KEY") else "❌ Not Set"
            
            gr.Markdown(f"**Google Maps API Key:** {google_key}")
            gr.Markdown(f"**OpenAI API Key:** {openai_key}")
            gr.Markdown(f"**ElevenLabs API Key:** {elevenlabs_key}")
            
            # Check modules
            modules = [
                "shortGPT.modules.map_imagery",
                "shortGPT.modules.geo_utils",
                "shortGPT.engine.realestate_video_engine"
            ]
            
            gr.Markdown("**Module Status:**")
            for module in modules:
                try:
                    __import__(module)
                    gr.Markdown(f"- {module}: ✅ Imported successfully")
                except ImportError as e:
                    gr.Markdown(f"- {module}: ❌ Import failed - {str(e)}")
    
    return demo

if __name__ == "__main__":
    # Ensure environment is loaded before creating UI
    load_environment()
    
    # Log the current working directory and .env path for debugging
    logger.info(f"Current working directory: {os.getcwd()}")
    env_path = os.path.join(os.getcwd(), '.env')
    logger.info(f"Checking for .env at: {env_path} (exists: {os.path.exists(env_path)})")
    
    # Log API key status (without showing the key)
    if os.getenv("GOOGLE_MAPS_API_KEY"):
        logger.info("GOOGLE_MAPS_API_KEY is set in environment")
    else:
        logger.warning("GOOGLE_MAPS_API_KEY is NOT set in environment")
    
    # Import cv2 only when needed (for image processing)
    try:
        import cv2
        logger.info("OpenCV (cv2) is available")
    except ImportError:
        logger.error("OpenCV (cv2) is not installed. Install with: pip install opencv-python")
        print("Error: OpenCV is required for image processing. Install with: pip install opencv-python")
        sys.exit(1)
    
    # Create and launch the UI
    demo = create_ui()
    demo.launch()
