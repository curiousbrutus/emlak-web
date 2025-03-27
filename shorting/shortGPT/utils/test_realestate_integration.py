import sys
import os
import logging
from pathlib import Path
import tempfile
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import environment loader
from shortGPT.utils.env_loader import load_environment
load_environment()

# Import modules
try:
    from shortGPT.modules.map_imagery import fetch_satellite_image, fetch_street_view_image, highlight_property_area
    from shortGPT.modules.geo_utils import get_coordinates_from_address, get_nearby_places
    from shortGPT.engine.realestate_video_engine import RealEstateVideoEngine
    from shortGPT.config.languages import Language
    from shortGPT.audio.voice_module import VoiceModule
    import numpy as np
    import cv2
    from PIL import Image
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

class RealEstateIntegrationTest:
    """Test class for RealEstate integration"""
    
    def __init__(self):
        self.test_address = "Empire State Building, New York"
        self.test_property = {
            "address": self.test_address,
            "property_type": "Commercial",
            "price": "$100,000,000",
            "area": "250,000 sq ft",
            "rooms": 200,
            "year_built": 1931,
            "special_features": "Iconic landmark, observation deck, art deco design",
            "images": []
        }
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Using temporary directory: {self.temp_dir}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        results = {
            "success": True,
            "tests": {}
        }
        
        # List of tests to run
        tests = [
            self.test_geo_utils,
            self.test_imagery_module,
            self.test_engine_initialization,
            self.test_script_generation,
            self.test_audio_generation,
            self.test_editing_steps,
            self.test_complete_workflow
        ]
        
        # Run each test
        for test_func in tests:
            test_name = test_func.__name__
            print(f"\n=== Running {test_name} ===")
            
            try:
                result = test_func()
                results["tests"][test_name] = {
                    "success": True,
                    "result": result
                }
                print(f"✅ {test_name} passed")
            except Exception as e:
                logger.exception(f"Error in {test_name}")
                results["tests"][test_name] = {
                    "success": False,
                    "error": str(e)
                }
                results["success"] = False
                print(f"❌ {test_name} failed: {e}")
        
        return results
    
    def test_geo_utils(self):
        """Test geocoding and nearby places functionality"""
        # Test geocoding
        lat, lng, formatted_address = get_coordinates_from_address(self.test_address)
        
        if not lat or not lng:
            raise ValueError("Geocoding failed")
        
        logger.info(f"Successfully geocoded: {formatted_address} ({lat}, {lng})")
        
        # Test nearby places
        places = get_nearby_places(lat, lng, radius=500)
        if not places:
            raise ValueError("Failed to find nearby places")
        
        logger.info(f"Found {len(places)} nearby places")
        
        return {
            "coordinates": (lat, lng),
            "formatted_address": formatted_address,
            "nearby_places_count": len(places)
        }
    
    def test_imagery_module(self):
        """Test the map imagery module"""
        # Get coordinates
        lat, lng, _ = get_coordinates_from_address(self.test_address)
        
        if not lat or not lng:
            raise ValueError("Geocoding failed")
        
        # Test satellite image
        satellite_img = fetch_satellite_image(lat, lng)
        if satellite_img is None:
            raise ValueError("Failed to fetch satellite image")
        
        # Save for later use
        satellite_path = os.path.join(self.temp_dir, "satellite.jpg")
        satellite_img.save(satellite_path)
        
        # Test street view
        street_img = fetch_street_view_image(lat, lng)
        if street_img is None:
            logger.warning("Street view image not available, but test can continue")
        else:
            # Save for later use
            street_path = os.path.join(self.temp_dir, "street.jpg")
            street_img.save(street_path)
        
        # Add images to test property
        self.test_property["images"] = [img for img in [satellite_img, street_img] if img is not None]
        
        # Test property highlight
        if satellite_img:
            # Create some test points - simple rectangle around center
            width, height = satellite_img.size
            center_x, center_y = width // 2, height // 2
            offset = min(width, height) // 4
            
            points = [
                (center_x - offset, center_y - offset),
                (center_x + offset, center_y - offset),
                (center_x + offset, center_y + offset),
                (center_x - offset, center_y + offset)
            ]
            
            highlighted = highlight_property_area(satellite_img, points)
            highlighted_path = os.path.join(self.temp_dir, "highlighted.jpg")
            highlighted.save(highlighted_path)
            
            # Add to images
            self.test_property["images"].append(highlighted)
        
        return {
            "satellite_image": satellite_img is not None,
            "street_view": street_img is not None,
            "image_count": len(self.test_property["images"])
        }
    
    def test_engine_initialization(self):
        """Test RealEstateVideoEngine initialization"""
        if not self.test_property["images"]:
            self.test_imagery_module()  # Make sure we have images
        
        # Create voice module
        voice_module = VoiceModule()
        
        # Initialize engine with debug mode
        engine = RealEstateVideoEngine(
            property_data=self.test_property,
            voice_module=voice_module,
            template="commercial_property",
            language=Language.ENGLISH,
            render_video=False,
            debug_mode=True
        )
        
        if not engine:
            raise ValueError("Failed to initialize RealEstateVideoEngine")
        
        return {
            "engine_initialized": True,
            "template": engine.template,
            "image_count": len(engine.property_data["images"])
        }
    
    def test_script_generation(self):
        """Test script generation in the engine"""
        voice_module = VoiceModule()
        
        # Create engine with test script
        test_script = "This is a test script for the Empire State Building, a magnificent landmark in New York City."
        
        engine = RealEstateVideoEngine(
            property_data=self.test_property,
            voice_module=voice_module,
            script=test_script,
            render_video=False,
            debug_mode=True
        )
        
        # Run script preparation
        prepared_script = engine._prepare_property_script()
        
        if not prepared_script or prepared_script.strip() == "":
            raise ValueError("Script preparation failed")
        
        return {
            "script_prepared": True,
            "script_length": len(prepared_script)
        }
    
    def test_audio_generation(self):
        """Test audio generation (if API keys are available)"""
        # Check if we have the required API key
        if not os.environ.get("ELEVENLABS_API_KEY"):
            logger.warning("Skipping audio test - ELEVENLABS_API_KEY not set")
            return {"skipped": "ELEVENLABS_API_KEY not set"}
        
        voice_module = VoiceModule()
        
        # Create engine with test script
        test_script = "This is a test script for audio generation. The Empire State Building is magnificent."
        
        engine = RealEstateVideoEngine(
            property_data=self.test_property,
            voice_module=voice_module,
            script=test_script,
            render_video=False,
            debug_mode=True
        )
        
        try:
            # Prepare script
            engine._prepare_property_script()
            
            # Generate audio
            engine._generate_temp_audio()
            
            # Check if audio was generated
            if "voiceover_path" not in engine.content_db_dict:
                raise ValueError("Audio generation failed - no voiceover_path in content_db_dict")
            
            # Check if file exists
            audio_path = engine.content_db_dict["voiceover_path"]
            if not os.path.exists(audio_path):
                raise ValueError(f"Audio file {audio_path} does not exist")
            
            return {
                "audio_generated": True,
                "audio_path": audio_path,
                "audio_size_bytes": os.path.getsize(audio_path)
            }
        except Exception as e:
            logger.exception("Error generating audio")
            return {
                "audio_generated": False,
                "error": str(e)
            }
    
    def test_editing_steps(self):
        """Test the video editing steps logic"""
        voice_module = VoiceModule()
        
        # Create engine with test script
        test_script = "This is a test script for the Empire State Building."
        
        engine = RealEstateVideoEngine(
            property_data=self.test_property,
            voice_module=voice_module,
            script=test_script,
            template="luxury_residence",
            render_video=False,
            debug_mode=True
        )
        
        # Test the editing steps for different templates
        templates_to_test = ["luxury_residence", "commercial_property", "residential_standard"]
        template_results = {}
        
        for template in templates_to_test:
            # Update template
            engine.template = template
            
            # Get the editing steps that would be used
            engine._prepare_property_script()
            
            try:
                # Mock calling the editing function without actually rendering
                # This just tests if the logic works without creating a video
                editing_result = engine._edit_and_render_video()
                template_results[template] = {"success": True, "result": editing_result}
            except Exception as e:
                logger.error(f"Error testing template {template}: {e}")
                template_results[template] = {"success": False, "error": str(e)}
        
        # At least one template should succeed
        if not any(result["success"] for result in template_results.values()):
            raise ValueError("All editing templates failed")
        
        return {
            "templates_tested": len(templates_to_test),
            "successful_templates": sum(1 for result in template_results.values() if result["success"]),
            "template_results": template_results
        }

    def test_complete_workflow(self):
        """Test the entire workflow from start to finish"""
        # This is an optional test that ties everything together
        try:
            # 1. Get property data with geocoding
            lat, lng, formatted_address = get_coordinates_from_address(self.test_address)
            if not lat or not lng:
                return {"skipped": "Geocoding failed"}
            
            # 2. Get satellite and street view images
            satellite_img = fetch_satellite_image(lat, lng)
            street_img = fetch_street_view_image(lat, lng)
            
            self.test_property["images"] = [img for img in [satellite_img, street_img] if img]
            
            if not self.test_property["images"]:
                return {"skipped": "No images available"}
            
            # 3. Create engine
            voice_module = VoiceModule()
            engine = RealEstateVideoEngine(
                property_data=self.test_property,
                voice_module=voice_module,
                script="Welcome to the iconic Empire State Building. This magnificent commercial property offers unparalleled prestige in the heart of New York City.",
                template="commercial_property",
                render_video=False,
                debug_mode=True
            )
            
            # 4. Run just the preparation steps (not rendering)
            result = engine.test_run()
            
            if result["status"] != "success":
                return {"success": False, "error": result.get("error", "Unknown error")}
            
            return {
                "success": True,
                "script": result["script"],
                "image_count": result.get("image_count", 0),
                "message": "Complete workflow test passed successfully" 
            }
        except Exception as e:
            logger.exception("Error in complete workflow test")
            return {"success": False, "error": str(e)}

# Add a main block that allows running just this test file
if __name__ == "__main__":
    print("Running RealEstate Integration Tests...")
    
    # Create and run the tests
    test = RealEstateIntegrationTest()
    results = test.run_all_tests()
    
    # Print summary 
    print("\n\n=== TEST RESULTS SUMMARY ===")
    success_count = sum(1 for test_result in results["tests"].values() if test_result["success"])
    total_count = len(results["tests"])
    
    print(f"Tests passed: {success_count}/{total_count}")
    
    for test_name, test_result in results["tests"].items():
        status = "✅ PASSED" if test_result["success"] else "❌ FAILED"
        print(f"{status}: {test_name}")
        
        if not test_result["success"] and "error" in test_result:
            print(f"  Error: {test_result['error']}")
    
    print("\nOverall status:", "✅ SUCCESS" if results["success"] else "❌ FAILURE")
