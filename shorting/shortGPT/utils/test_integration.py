import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import environment loader early
from shortGPT.utils.env_loader import load_environment
load_success = load_environment()
logger.info(f"Environment loaded successfully: {load_success}")

# Now import the modules that need the environment variables
from shortGPT.modules.map_imagery import fetch_satellite_image, fetch_street_view_image, draw_property_border
from shortGPT.modules.geo_utils import get_coordinates_from_address, get_nearby_places

# Check if required package yt_dlp is installed
try:
    import yt_dlp
    logger.info("yt_dlp module is available")
except ImportError:
    logger.error("yt_dlp module is not installed. Please install it with: pip install yt-dlp")
    print("\n❌ ERROR: Missing required package 'yt_dlp'. Install it with:")
    print("pip install yt-dlp\n")
    sys.exit(1)

# Now import modules that depend on yt_dlp
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.engine.realestate_video_engine import RealEstateVideoEngine

def test_map_imagery():
    """Test map imagery functions"""
    print("Testing map imagery functions...")
    # Test location (example: Empire State Building)
    lat, lng = 40.748817, -73.985428
    
    # Test satellite image
    satellite_img = fetch_satellite_image(lat, lng)
    if satellite_img:
        print("✅ Satellite image fetched successfully")
        
        # Check if image needs conversion before saving
        if satellite_img.mode == 'P':
            satellite_img = satellite_img.convert('RGB')
        
        satellite_img.save("test_satellite.jpg")
        print(f"Saved test image to {os.path.abspath('test_satellite.jpg')}")
        
        # Test property border
        bordered_img = draw_property_border(satellite_img)
        if bordered_img:
            print("✅ Property border drawn successfully")
            # Convert if needed before saving
            if bordered_img.mode == 'P':
                bordered_img = bordered_img.convert('RGB')
            bordered_img.save("test_bordered.jpg")
    else:
        print("❌ Failed to fetch satellite image")
    
    # Test street view
    street_img = fetch_street_view_image(lat, lng)
    if street_img:
        print("✅ Street view image fetched successfully")
        # Convert if needed before saving
        if street_img.mode == 'P':
            street_img = street_img.convert('RGB')
        street_img.save("test_street_view.jpg")
    else:
        print("❌ Failed to fetch street view image")

def test_geo_utils():
    """Test geo utility functions"""
    print("\nTesting geo utility functions...")
    address = "Empire State Building, New York"
    
    # Test geocoding
    lat, lng, formatted_address = get_coordinates_from_address(address)
    if lat and lng:
        print(f"✅ Address geocoded successfully: {formatted_address} ({lat}, {lng})")
        
        # Test nearby places
        nearby = get_nearby_places(lat, lng, radius=500)
        if nearby:
            print(f"✅ Found {len(nearby)} nearby places")
            for i, place in enumerate(nearby[:3]):
                print(f"  - {place['name']} ({place['type']}): {place['distance']}m")
        else:
            print("❌ Failed to find nearby places")
    else:
        print("❌ Failed to geocode address")

def test_realestate_engine():
    """Test the real estate video engine"""
    print("\nTesting real estate video engine...")
    
    # Test property data
    property_data = {
        "address": "Empire State Building, New York",
        "property_type": "Commercial",
        "price": "$100,000,000",
        "area": "250,000 sq ft",
        "images": []  # We'll populate this
    }
    
    # Get test images
    lat, lng, _ = get_coordinates_from_address(property_data["address"])
    if lat and lng:
        property_data["images"] = [
            fetch_satellite_image(lat, lng),
            fetch_satellite_image(lat, lng, zoom=17),
            fetch_street_view_image(lat, lng),
            fetch_street_view_image(lat, lng, heading=90)
        ]
        property_data["images"] = [img for img in property_data["images"] if img]
        print(f"✅ Added {len(property_data['images'])} test images")
    
    # Initialize voice module (using default)
    voice_module = VoiceModule()
    
    # Create test script
    test_script = "Welcome to this magnificent commercial property in the heart of New York City. The iconic Empire State Building offers breathtaking views and unparalleled prestige."
    
    try:
        # Initialize engine (without rendering)
        engine = RealEstateVideoEngine(
            property_data=property_data,
            voice_module=voice_module,
            script=test_script,
            render_video=False
        )
        
        # Test initialize
        print("✅ RealEstateVideoEngine initialized successfully")
        
        # Test script preparation
        script = engine._prepare_property_script()
        print(f"✅ Script prepared: '{script[:50]}...'")
        
        print("✅ All engine tests passed")
    except Exception as e:
        print(f"❌ Engine test failed: {str(e)}")

if __name__ == "__main__":
    print("Starting integration tests...\n")
    
    # Check and log environment variables
    google_maps_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if google_maps_key:
        key_preview = google_maps_key[:5] + "..." + google_maps_key[-5:]
        print(f"✅ GOOGLE_MAPS_API_KEY is set: {key_preview}")
    else:
        print("⚠️ WARNING: GOOGLE_MAPS_API_KEY environment variable not set")
        print("Set it using: export GOOGLE_MAPS_API_KEY='your-key-here'")
        print("Or create a .env file in the project root with this key")
    
    # Run tests
    test_map_imagery()
    test_geo_utils()
    test_realestate_engine()
    
    print("\nTests completed!")
