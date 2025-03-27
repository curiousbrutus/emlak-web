import sys
import os
from pathlib import Path
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import environment loader early
from shortGPT.utils.env_loader import load_environment
load_success = load_environment()

# Import the modules we want to test
from shortGPT.modules.map_imagery import (
    fetch_satellite_image, 
    fetch_street_view_image, 
    draw_property_border,
    apply_manual_border,
    highlight_property_area
)
from shortGPT.modules.geo_utils import (
    get_coordinates_from_address,
    get_nearby_places,
    calculate_distance
)

def save_image(image, filename):
    """Safely save an image, converting to RGB if necessary"""
    try:
        # Check if image is in palette mode (P) and convert to RGB if needed
        if image.mode == 'P':
            image = image.convert('RGB')
        
        # Save the image
        image.save(filename)
        print(f"✅ Saved to: {os.path.abspath(filename)}")
        return True
    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return False

def test_geocoding(address="Empire State Building, New York"):
    """Test basic geocoding functionality"""
    print(f"\n=== Testing Geocoding with address: {address} ===")
    
    lat, lng, formatted_address = get_coordinates_from_address(address)
    
    if lat and lng:
        print(f"✅ Successfully geocoded to: {lat}, {lng}")
        print(f"✅ Formatted address: {formatted_address}")
        return lat, lng
    else:
        print("❌ Geocoding failed")
        return None, None

def test_nearby_places(lat, lng, radius=1000):
    """Test finding nearby places"""
    if not lat or not lng:
        print("❌ Cannot test nearby places without coordinates")
        return
        
    print(f"\n=== Testing Nearby Places around {lat}, {lng} ===")
    
    nearby = get_nearby_places(lat, lng, radius=radius)
    
    if nearby:
        print(f"✅ Found {len(nearby)} nearby places")
        print("Top 5 nearby places:")
        for i, place in enumerate(nearby[:5]):
            print(f"  {i+1}. {place['name']} ({place['type']}) - {place['distance']}m")
    else:
        print("❌ Failed to find nearby places")

def test_map_imagery(lat, lng):
    """Test map imagery functions"""
    if not lat or not lng:
        print("❌ Cannot test map imagery without coordinates")
        return
        
    print(f"\n=== Testing Map Imagery at {lat}, {lng} ===")
    
    # Test satellite imagery
    print("\nFetching satellite image...")
    satellite = fetch_satellite_image(lat, lng)
    
    if satellite:
        print(f"✅ Satellite image fetched successfully: {satellite.size} pixels")
        
        # Save with the safe_image function
        save_image(satellite, "test_satellite.jpg")
        
        # Test border drawing
        print("\nDrawing property border...")
        bordered = draw_property_border(satellite)
        if bordered:
            print("✅ Border drawn successfully")
            save_image(bordered, "test_bordered.jpg")
            
        # Test property area highlighting
        print("\nTesting area highlighting...")
        width, height = satellite.size
        center_x, center_y = width // 2, height // 2
        offset = min(width, height) // 4
        
        # Create simple polygon points
        points = [
            (center_x - offset, center_y - offset),
            (center_x + offset, center_y - offset),
            (center_x + offset, center_y + offset),
            (center_x - offset, center_y + offset)
        ]
        
        highlighted = highlight_property_area(satellite, points)
        if highlighted:
            print("✅ Area highlighting successful")
            save_image(highlighted, "test_highlighted.jpg")
    else:
        print("❌ Failed to fetch satellite image")
    
    # Test street view
    print("\nFetching street view image...")
    street = fetch_street_view_image(lat, lng)
    
    if street:
        print(f"✅ Street view image fetched successfully: {street.size} pixels")
        save_image(street, "test_street.jpg")
    else:
        print("❌ Failed to fetch street view image (may not be available at this location)")

def run_all_tests():
    """Run all module tests"""
    # Check API key
    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        print("⚠️ GOOGLE_MAPS_API_KEY is not set. Tests will likely fail.")
    else:
        print("✅ GOOGLE_MAPS_API_KEY is set")
    
    # First test: geocoding
    lat, lng = test_geocoding()
    
    if lat and lng:
        # If we have coordinates, run the rest of the tests
        test_nearby_places(lat, lng)
        test_map_imagery(lat, lng)
        
        print("\n=== All tests completed! ===")
    else:
        print("\n❌ Cannot proceed with further tests due to geocoding failure")

if __name__ == "__main__":
    # Allow custom address from command line
    if len(sys.argv) > 1:
        address = sys.argv[1]
        run_all_tests(address)
    else:
        run_all_tests()
