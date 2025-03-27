import os
import sys
import time
import json
import logging
import tempfile
from enum import Enum
from pathlib import Path

import gradio as gr
import numpy as np

from gui.asset_components import AssetComponentsUtils
from gui.ui_abstract_component import AbstractComponentUI
from shortGPT.audio.edge_voice_module import EdgeTTSVoiceModule
from shortGPT.audio.eleven_voice_module import ElevenLabsVoiceModule
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.config.languages import Language, EDGE_TTS_VOICENAME_MAPPING, ELEVEN_SUPPORTED_LANGUAGES
from shortGPT.engine.realestate_video_engine import RealEstateVideoEngine
from shortGPT.modules.map_imagery import (
    fetch_satellite_image,
    fetch_street_view_image,
    draw_property_border,
    highlight_property_area
)
from shortGPT.modules.geo_utils import get_coordinates_from_address, get_nearby_places
from shortGPT.utils.env_loader import load_environment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_environment()

class Chatstate(Enum):
    ASK_LOCATION = 1
    SHOW_PROPERTY_FORM = 2
    ASK_VOICE_MODULE = 3 
    ASK_LANGUAGE = 4
    ASK_PROPERTY_TYPE = 5
    GENERATE_SCRIPT = 6
    ASK_SATISFACTION = 7
    MAKE_VIDEO = 8
    ASK_CORRECTION = 9

# Property type templates - each contains optimal settings for that property type
PROPERTY_TEMPLATES = {
    "luxury_residence": {
        "name": "Luxury Residence",
        "description": "High-end properties with premium features",
        "script_style": "elegant and sophisticated",
        "pacing": "slow and cinematic",
        "music_style": "sophisticated",
    },
    "commercial_property": {
        "name": "Commercial Property",
        "description": "Office spaces, retail and investment opportunities",
        "script_style": "professional and data-driven",
        "pacing": "moderate and informative",
        "music_style": "corporate",
    },
    "residential_standard": {
        "name": "Standard Residential",
        "description": "Standard homes and apartments",
        "script_style": "friendly and inviting",
        "pacing": "balanced",
        "music_style": "upbeat",
    },
    "vacation_property": {
        "name": "Vacation Property",
        "description": "Holiday homes and rental opportunities",
        "script_style": "exciting and lifestyle-focused",
        "pacing": "upbeat",
        "music_style": "cheerful",
    },
    "land_development": {
        "name": "Land/Development",
        "description": "Vacant land and development opportunities",
        "script_style": "focused on potential and opportunity",
        "pacing": "steady",
        "music_style": "inspirational",
    }
}

class RealEstateVideoUI(AbstractComponentUI):
    def __init__(self, shortGptUI: gr.Blocks):
        self.shortGptUI = shortGptUI
        self.state = Chatstate.ASK_LOCATION
        self.location = None
        self.property_data = {}
        self.voice_module = None
        self.language = None
        self.script = ""
        self.map_images = []
        self.video_html = ""
        self.videoVisible = False
        self.realestate_tab = None
        self.chatbot = None
        self.msg = None
        self.restart_button = None
        self.video_folder = None
        self.errorHTML = None
        self.outHTML = None
        self.property_template = "residential_standard"

    # ... existing code ...

    def initialize_conversation(self):
        self.state = Chatstate.ASK_LOCATION
        self.location = None
        self.language = None
        self.script = ""
        self.video_html = ""
        self.videoVisible = False
        return [[None, "🏠 Welcome to the Real Estate Video Generator! I'll help you create professional property videos.\n\nLet's start by entering the property address. Please provide the full address of the property."]]

    def reset_conversation(self):
        self.state = Chatstate.ASK_LOCATION
        self.location = None
        self.property_data = {}
        self.language = None
        self.script = ""
        self.map_images = []
        self.video_html = ""
        self.videoVisible = False

    def create_ui(self):
        with gr.Row(visible=False) as self.realestate_tab:
            with gr.Column(scale=2):
                # Property information section
                with gr.Group():
                    gr.Markdown("### 📍 Property Location")
                    self.address_input = gr.Textbox(
                        label="Property Address",
                        placeholder="Enter full property address (e.g., 123 Main St, Anytown, USA)",
                    )
                    self.get_location_button = gr.Button("Get Location Data")
                    self.location_status = gr.Markdown("")
                    self.map_view = gr.HTML("", visible=False)
                
                # Property details section
                with gr.Group(visible=False) as self.property_form:
                    gr.Markdown("### 🏠 Property Details")
                    with gr.Row():
                        self.property_type = gr.Dropdown(
                            choices=["Apartment", "House", "Villa", "Land", "Office", "Retail"], 
                            label="Property Type"
                        )
                        self.rooms = gr.Number(label="Bedrooms", precision=0, minimum=0)
                    with gr.Row():
                        self.bathrooms = gr.Number(label="Bathrooms", precision=0, minimum=0)
                        self.area = gr.Number(label="Area (sq. meters)", precision=0, minimum=1)
                    with gr.Row():
                        self.price = gr.Number(label="Price", precision=0, minimum=0)
                        self.year_built = gr.Number(label="Year Built", precision=0, minimum=1900)
                    
                    self.special_features = gr.Textbox(
                        label="Special Features",
                        placeholder="Sea view, swimming pool, garden, security, etc.",
                        lines=2
                    )
                    self.template_select = gr.Radio(
                        choices=[t["name"] for t in PROPERTY_TEMPLATES.values()],
                        label="Video Template",
                        value="Standard Residential"
                    )
                    self.generate_script_button = gr.Button("Generate Script", variant="primary")
                
                # Script and voice section
                with gr.Group(visible=False) as self.script_form:
                    gr.Markdown("### 📝 Property Script")
                    self.script_output = gr.Textbox(label="Generated Script", lines=5)
                    self.edit_script = gr.Checkbox(label="Edit Script", value=False)
                    self.script_edit = gr.Textbox(label="Edit Script", lines=5, visible=False)
                    
                    gr.Markdown("### 🎤 Voice Selection")
                    with gr.Row():
                        self.voice_provider = gr.Radio(
                            choices=["EdgeTTS", "ElevenLabs"],
                            label="Voice Provider",
                            value="EdgeTTS"
                        )
                        self.language_selector = gr.Dropdown(
                            choices=["English", "Spanish", "French", "German", "Turkish"],
                            label="Language",
                            value="English"
                        )
                    
                    self.voice_options = gr.Dropdown(label="Voice", choices=[])
                
                # Generate video button
                with gr.Group(visible=False) as self.video_form:
                    gr.Markdown("### 🎬 Generate Video")
                    self.generate_video_button = gr.Button("Create Real Estate Video", variant="primary")
                    self.video_status = gr.Markdown("")
                
            # Right column for preview and results
            with gr.Column(scale=1):
                self.preview_html = gr.HTML(label="Preview")
                self.results_gallery = gr.Gallery(label="Generated Images", visible=False)
                self.video_output = gr.Video(label="Generated Video", visible=False)
                self.download_button = gr.Button("Download Video", visible=False)
        
        # Connect event handlers
        self.get_location_button.click(
            fn=self.fetch_location_data,
            inputs=[self.address_input],
            outputs=[self.location_status, self.map_view, self.property_form]
        )
        
        self.generate_script_button.click(
            fn=self.generate_property_script,
            inputs=[
                self.property_type, self.rooms, self.bathrooms, self.area,
                self.price, self.year_built, self.special_features, self.template_select
            ],
            outputs=[self.script_output, self.script_form]
        )
        
        self.edit_script.change(
            fn=lambda x, y: (gr.update(visible=x), y if not x else y),
            inputs=[self.edit_script, self.script_output],
            outputs=[self.script_edit, self.script_edit]
        )
        
        self.voice_provider.change(
            fn=self.update_voice_options,
            inputs=[self.voice_provider, self.language_selector],
            outputs=[self.voice_options]
        )
        
        self.language_selector.change(
            fn=self.update_voice_options,
            inputs=[self.voice_provider, self.language_selector],
            outputs=[self.voice_options]
        )
        
        self.script_output.change(
            fn=lambda x: gr.update(visible=True),
            inputs=[self.script_output],
            outputs=[self.video_form]
        )
        
        self.generate_video_button.click(
            fn=self.generate_video,
            inputs=[
                self.address_input, self.property_type, self.script_output, self.script_edit,
                self.edit_script, self.voice_provider, self.voice_options, self.template_select
            ],
            outputs=[self.video_status, self.results_gallery, self.video_output, self.download_button]
        )
        
        return self.realestate_tab
    
    def fetch_location_data(self, address):
        """Fetch location data for the given address"""
        if not address:
            return "Please enter an address", gr.update(visible=False), gr.update(visible=False)
        
        try:
            # Get coordinates using the geo_utils module
            lat, lng, formatted_address = get_coordinates_from_address(address)
            
            if not lat or not lng:
                return "Unable to find this location. Please enter a valid address.", gr.update(visible=False), gr.update(visible=False)
            
            # Store location data
            self.property_data["location"] = {
                "lat": lat,
                "lng": lng,
                "address": formatted_address
            }
            
            # Create map HTML
            map_html = f"""
            <div style="text-align: center;">
                <iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"
                src="https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"></iframe>
            </div>
            """
            
            # Get nearby places
            nearby_places = get_nearby_places(lat, lng, radius=1000)
            self.property_data["nearby_places"] = nearby_places
            
            return f"📍 Found: {formatted_address}", gr.update(value=map_html, visible=True), gr.update(visible=True)
            
        except Exception as e:
            return f"Error: {str(e)}", gr.update(visible=False), gr.update(visible=False)
    
    def generate_property_script(self, property_type, rooms, bathrooms, area, price, year_built, special_features, template):
        """Generate script for property"""
        if not self.property_data.get("location"):
            return "Please enter a valid location first", gr.update(visible=False)
        
        # Update property data
        self.property_data.update({
            "property_type": property_type,
            "rooms": rooms,
            "bathrooms": bathrooms,
            "area": area,
            "price": price,
            "year_built": year_built,
            "special_features": special_features,
            "template": template
        })
        
        # Map template name to template key
        template_key = next((k for k, v in PROPERTY_TEMPLATES.items() if v["name"] == template), "residential_standard")
        self.property_data["template_key"] = template_key
        
        try:
            # Generate script using ShortGPT's content generation
            from shortGPT.gpt import gpt_chat_video
            
            # Format the prompt with property details
            nearby_text = ""
            if self.property_data.get("nearby_places"):
                places = self.property_data["nearby_places"]
                nearby_text = ", ".join([f"{p['name']} ({p['distance']}m)" for p in places[:3]])
            
            # Use the template from the realestate_prompt_template.yaml
            script = gpt_chat_video.generate_real_estate_script(
                address=self.property_data["location"]["address"],
                property_type=property_type,
                rooms=int(rooms) if rooms else 0,
                bathrooms=int(bathrooms) if bathrooms else 0,
                area=int(area) if area else 0,
                price=int(price) if price else 0,
                year_built=int(year_built) if year_built else 0,
                special_features=special_features,
                nearby_places=nearby_text
            )
            
            self.script = script
            return script, gr.update(visible=True)
            
        except Exception as e:
            return f"Error generating script: {str(e)}", gr.update(visible=False)
    
    def update_voice_options(self, provider, language):
        """Update available voice options based on provider and language"""
        # Here you'd integrate with ShortGPT's voice module logic
        if provider == "EdgeTTS":
            # Get voice options from Edge TTS
            language_code = {"English": "en", "Spanish": "es", "French": "fr", "German": "de", "Turkish": "tr"}.get(language, "en")
            voices = [v for k, v in EDGE_TTS_VOICENAME_MAPPING.items() if k.startswith(language_code)]
            return gr.update(choices=voices, value=voices[0] if voices else None)
        else:
            # Get voice options from ElevenLabs
            # This is a placeholder, you'd need to implement actual ElevenLabs voice fetching
            voices = [f"Voice {i}" for i in range(1, 6)]
            return gr.update(choices=voices, value=voices[0] if voices else None)
    
    def generate_video(self, address, property_type, script, edited_script, use_edited, voice_provider, voice, template):
        """Generate real estate video"""
        try:
            # Use edited script if specified
            final_script = edited_script if use_edited and edited_script else script
            
            # Map template name to key
            template_key = next((k for k, v in PROPERTY_TEMPLATES.items() if v["name"] == template), "residential_standard")
            
            # Get satellite and street view images
            satellite_image = fetch_satellite_image(
                self.property_data["location"]["lat"], 
                self.property_data["location"]["lng"]
            )
            
            street_images = []
            for heading in [0, 90, 180, 270]:
                img = fetch_street_view_image(
                    self.property_data["location"]["lat"],
                    self.property_data["location"]["lng"],
                    heading=heading
                )
                if img:
                    street_images.append(img)
            
            # Setup voice module
            if voice_provider == "EdgeTTS":
                voice_module = EdgeTTSVoiceModule(voice)
            else:
                # You'd need to implement ElevenLabs voice handling
                voice_module = ElevenLabsVoiceModule(voice)
            
            # Create and run the real estate video engine
            engine = RealEstateVideoEngine(
                property_data=self.property_data,
                voice_module=voice_module,
                script=final_script,
                template=template_key
            )
            
            # Start content generation
            progress_data = []
            for step_num, step_info in engine.makeContent():
                progress_data.append(f"Step {step_num}: {step_info}")
            
            # Get all generated images for gallery
            all_images = satellite_image + street_images + engine.get_generated_images()
            
            # Get video output path
            video_path = engine.get_video_output_path()
            
            return (
                "✅ Video generation complete!",
                gr.update(value=all_images, visible=True),
                gr.update(value=video_path, visible=True),
                gr.update(visible=True)
            )
            
        except Exception as e:
            return f"Error generating video: {str(e)}", None, None, gr.update(visible=False)

def create_realestate_tab():
    """Create the real estate video tab interface"""
    
    with gr.Column():
        gr.Markdown("## 🏠 Real Estate Video Generator")
        gr.Markdown("Create professional aerial-style videos of properties using satellite imagery, AI narration, and dynamic editing.")
        
        # Check if API keys are set
        api_keys_warning = ""
        if not os.environ.get("GOOGLE_MAPS_API_KEY"):
            api_keys_warning += "⚠️ **Google Maps API Key** is missing. Map features won't work.\n\n"
        if not os.environ.get("ELEVENLABS_API_KEY"):
            api_keys_warning += "⚠️ **ElevenLabs API Key** is missing. Voice narration will use basic TTS.\n\n"
        
        if api_keys_warning:
            gr.Markdown(f"### API Key Warnings\n{api_keys_warning}")
            gr.Markdown("Set these keys in your .env file to enable all features.")
        
        # Create property details form
        with gr.Group():
            gr.Markdown("### Step 1: Property Information")
            
            # Property location
            with gr.Row():
                with gr.Column(scale=3):
                    address_input = gr.Textbox(
                        label="Property Address",
                        placeholder="Enter full address (e.g., 123 Main St, New York, NY)"
                    )
                    location_status = gr.Markdown("Enter an address and click 'Find Location'")
                
                with gr.Column(scale=1):
                    find_location_btn = gr.Button("Find Location")
            
            # Property details
            with gr.Row():
                with gr.Column():
                    property_type = gr.Dropdown(
                        label="Property Type",
                        choices=["Apartment", "House", "Villa", "Land", "Commercial", "Office"],
                        value="Apartment",
                        interactive=True
                    )
                    rooms = gr.Number(label="Number of Rooms", value=3, precision=0)
                    bathrooms = gr.Number(label="Number of Bathrooms", value=2, precision=0)
                    
                with gr.Column():
                    area = gr.Number(label="Area (m²)", value=120)
                    price = gr.Number(label="Price", value=500000)
                    year_built = gr.Number(label="Year Built", value=2010, precision=0)
            
            special_features = gr.Textbox(
                label="Special Features",
                placeholder="E.g., swimming pool, garden, sea view, renovated kitchen...",
                lines=2
            )
            
            # Location coordinates (hidden)
            lat_input = gr.Textbox(visible=False)
            lng_input = gr.Textbox(visible=False)
        
        # Map visualization
        with gr.Group(visible=False) as map_group:
            gr.Markdown("### Step 2: Location Imagery")
            
            with gr.Row():
                with gr.Column():
                    satellite_img = gr.Image(label="Satellite View", type="pil")
                    with gr.Row():
                        fetch_images_btn = gr.Button("Fetch Property Images")
                        fetch_multiple_btn = gr.Button("Fetch Multiple Views")
                
                with gr.Column():
                    street_img = gr.Image(label="Street View", type="pil")
                    nearby_places_md = gr.Markdown("Nearby places will appear here")
            
            # Property boundary feature
            with gr.Accordion("Property Boundary Tools", open=False):
                with gr.Row():
                    with gr.Column():
                        boundary_img = gr.Image(
                            label="Mark Property Boundaries", 
                            tool="sketch", 
                            type="pil",
                            brush_radius=3
                        )
                        border_type = gr.Radio(
                            ["Auto Border", "Manual Drawing"],
                            label="Border Type",
                            value="Auto Border"
                        )
                        
                    with gr.Column():
                        result_img = gr.Image(label="Result with Boundary", type="pil")
                        apply_boundary_btn = gr.Button("Apply Property Boundary")
            
            # Image gallery for multiple views
            with gr.Accordion("Multiple Property Views", open=False) as multiple_views_group:
                gr.Markdown("Select images to include in your video")
                image_gallery = gr.Gallery(label="Available Views", selected_index=None)
                selected_images = gr.Textbox(label="Selected Images", visible=False)
                
                with gr.Row():
                    select_all_btn = gr.Button("Select All")
                    clear_selection_btn = gr.Button("Clear Selection")
        
        # Video creation
        with gr.Group(visible=False) as video_group:
            gr.Markdown("### Step 3: Generate Video")
            
            with gr.Row():
                with gr.Column():
                    script_input = gr.Textbox(
                        label="Video Script",
                        placeholder="AI-generated script will appear here. You can edit it.",
                        lines=5
                    )
                    generate_script_btn = gr.Button("Generate Script")
                
                with gr.Column():
                    voice_option = gr.Dropdown(
                        label="Narration Voice",
                        choices=["Professional Male", "Professional Female", "Casual Male", "Casual Female"]
                    )
                    
                    # Voice language and emotion settings
                    with gr.Row():
                        voice_language = gr.Dropdown(
                            label="Language",
                            choices=["English", "Spanish", "French", "German", "Chinese", "Japanese"],
                            value="English"
                        )
                        voice_emotion = gr.Dropdown(
                            label="Voice Emotion",
                            choices=["Neutral", "Enthusiastic", "Professional", "Friendly", "Serious"],
                            value="Professional"
                        )
                        
                        # Advanced video settings in accordion
                        with gr.Accordion("Advanced Video Settings", open=False):
                            with gr.Row():
                                transition_type = gr.Dropdown(
                                    label="Transition Type",
                                    choices=["Fade", "Dissolve", "Wipe", "Slide", "Zoom"],
                                    value="Fade"
                                )
                                video_duration = gr.Slider(
                                    minimum=30, 
                                    maximum=180, 
                                    value=60, 
                                    step=15, 
                                    label="Video Duration (seconds)"
                                )
                            
                            with gr.Row():
                                video_resolution = gr.Dropdown(
                                    label="Resolution",
                                    choices=["720p", "1080p", "4K"],
                                    value="1080p"
                                )
                                music_type = gr.Dropdown(
                                    label="Background Music",
                                    choices=["None", "Upbeat", "Professional", "Luxurious", "Calm", "Custom"],
                                    value="Professional"
                                )
                            
                            # Custom music upload (conditionally visible)
                            custom_music_file = gr.File(
                                label="Upload Custom Music (MP3)",
                                file_types=[".mp3"],
                                visible=False
                            )
                    
                    # Style customization
                    with gr.Accordion("Style Customization", open=False):
                        with gr.Row():
                            video_template = gr.Dropdown(
                                label="Video Template",
                                choices=[t["name"] for t in PROPERTY_TEMPLATES.values()],
                                value="Standard Residential"
                            )
                            color_scheme = gr.Dropdown(
                                label="Color Scheme",
                                choices=["Modern", "Classic", "Vibrant", "Minimal", "Elegant"],
                                value="Modern"
                            )
                        
                        with gr.Row():
                            watermark_enabled = gr.Checkbox(label="Add Watermark", value=False)
                            watermark_text = gr.Textbox(
                                label="Watermark Text",
                                placeholder="Your Agency Name",
                                visible=False
                            )
                            watermark_position = gr.Dropdown(
                                label="Watermark Position",
                                choices=["Bottom Right", "Bottom Left", "Top Right", "Top Left"],
                                value="Bottom Right",
                                visible=False
                            )
                
                # Generate and download buttons
                with gr.Row():
                    create_video_btn = gr.Button("Create Video", variant="primary")
                    progress_status = gr.Markdown("Click 'Create Video' to start generation")
                
                # Video output and download
                video_output = gr.Video(label="Generated Video", visible=False)
                download_btn = gr.Button("Download Video", visible=False)