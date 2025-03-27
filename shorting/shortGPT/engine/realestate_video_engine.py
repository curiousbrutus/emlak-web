from shortGPT.engine.content_video_engine import ContentVideoEngine
from shortGPT.config.languages import Language
from shortGPT.audio.voice_module import VoiceModule
import os
import tempfile
from PIL import Image
import time

class RealEstateVideoEngine(ContentVideoEngine):
    def __init__(
        self,
        property_data,
        voice_module,
        script="",
        template="residential_standard",
        background_music_name=None,
        language=Language.ENGLISH,
        render_video=True,
        debug_mode=False  # Added debug_mode parameter
    ):
        """
        Initialize the Real Estate Video Engine
        
        Args:
            property_data (dict): Property information including location, details, etc.
            voice_module (VoiceModule): Voice module for narration
            script (str): Pre-generated script (if available)
            template (str): Real estate template type
            background_music_name (str, optional): Background music
            language (Language): Script language
            render_video (bool): Whether to render video automatically
            debug_mode (bool): Enable debug mode for testing
        """
        # Initialize base engine
        super().__init__(
            voice_module=voice_module,
            background_music_name=background_music_name,
            language=language
        )
        
        # Set real estate specific properties
        self.property_data = property_data
        self.template = template
        self.script = script
        self.real_estate_images = []
        self.debug_mode = debug_mode
        
        # Modify step dictionary to include real estate specific steps
        self.stepDict = {
            1: self._prepare_property_script,
            2: self._generate_temp_audio,
            3: self._time_captions,
            4: self._prepare_property_imagery,
            5: self._prepare_background_assets,
            6: self._edit_and_render_video
        }
        
        # Start with a temporary directory for assets
        self.temp_dir = tempfile.mkdtemp()
        
        # If in debug mode, save info for testing
        if self.debug_mode:
            print(f"RealEstateVideoEngine initialized in debug mode")
            print(f"Template: {self.template}")
            print(f"Temp directory: {self.temp_dir}")
        
    def _prepare_property_script(self):
        """Prepare the property script for narration"""
        if not self.script:
            # If no script provided, generate one
            self._update_progress(1, f"Generating script for {self.property_data.get('property_type', 'property')}")
            # You would implement script generation logic here
            
            # This is a placeholder - you'd use gpt_chat_video to generate real script
            self.script = f"Welcome to this amazing {self.property_data.get('property_type', 'property')}."
        else:
            self._update_progress(1, "Using provided script")
        
        # Save script to content database
        self.content_db_dict["script"] = self.script
        return self.script
    
    def _prepare_property_imagery(self):
        """Prepare property images for video"""
        self._update_progress(4, "Preparing property imagery")
        
        # Get map images if available in property_data
        # These would be fetched using map_imagery module before engine initialization
        if "images" in self.property_data:
            self.real_estate_images = self.property_data["images"]
        
        # Save images with timing based on audio
        total_duration = self.content_db_dict.get("voiceover_duration", 30)
        images_count = len(self.real_estate_images)
        
        if images_count > 0:
            # Calculate timing for each image
            segment_duration = total_duration / images_count
            
            # Save images with timing
            for i, img in enumerate(self.real_estate_images):
                start_time = i * segment_duration
                end_time = (i + 1) * segment_duration
                
                # Save image metadata
                self.content_db_dict[f"image_{i}"] = {
                    "path": self._save_image_to_temp(img, f"property_img_{i}.jpg"),
                    "start_time": start_time,
                    "end_time": end_time
                }
        
        self._update_progress(4, f"Prepared {len(self.real_estate_images)} property images")
        return "Prepared property imagery"
    
    def _edit_and_render_video(self):
        """Edit and render the final video"""
        self._update_progress(6, "Rendering real estate video")
        
        # Create editing flow based on template
        editing_steps = []
        
        # Different templates would have different editing styles
        if self.template == "luxury_residence":
            # Luxury template might have specific transitions and effects
            # This is simplified
            editing_steps = [
                {"type": "add_background_music", "music": "elegant"},
                {"type": "add_voiceover"},
                {"type": "show_property_images", "transition": "fade"},
                {"type": "add_captions", "style": "elegant"}
            ]
        elif self.template == "commercial_property":
            # Commercial template might be more data-focused
            editing_steps = [
                {"type": "add_background_music", "music": "corporate"},
                {"type": "add_voiceover"},
                {"type": "show_property_images", "transition": "slide"},
                {"type": "add_data_overlays"},
                {"type": "add_captions", "style": "professional"}
            ]
        else:
            # Default template
            editing_steps = [
                {"type": "add_background_music", "music": "standard"},
                {"type": "add_voiceover"},
                {"type": "show_property_images", "transition": "zoom"},
                {"type": "add_captions", "style": "standard"}
            ]
        
        # In a real implementation, you would:
        # 1. Use ShortGPT's EditingEngine to create the video
        # 2. Apply template-specific editing steps
        # 3. Handle transitions between images
        
        # This is a placeholder for the actual video rendering
        self.video_path = os.path.join(self.temp_dir, "real_estate_video.mp4")
        
        # Simulate rendering time
        self._update_progress(6, "Finalizing video")
        time.sleep(2)  # Remove this in actual implementation
        
        self._update_progress(6, "Video rendering complete")
        return "Video created successfully"
    
    def _save_image_to_temp(self, img, filename):
        """Save an image to the temporary directory"""
        if isinstance(img, Image.Image):
            path = os.path.join(self.temp_dir, filename)
            img.save(path)
            return path
        return img  # If it's already a path
    
    def get_generated_images(self):
        """Get all generated/used images"""
        return self.real_estate_images

    def test_run(self):
        """Run a test sequence without generating the full video"""
        results = {}
        
        try:
            # Run script preparation
            results["script"] = self._prepare_property_script()
            
            # Run imagery preparation if images exist
            if "images" in self.property_data and self.property_data["images"]:
                self._prepare_property_imagery()
                results["image_count"] = len(self.real_estate_images)
            
            # Return success status
            results["status"] = "success"
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            
        return results
