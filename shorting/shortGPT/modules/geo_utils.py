import requests
import os
from dotenv import load_dotenv
import math
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our custom environment loader
from shortGPT.utils.env_loader import load_environment

# Make sure environment is loaded
load_environment()

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Log the API key status (without showing the key itself)
if GOOGLE_MAPS_API_KEY:
    logger.info("GOOGLE_MAPS_API_KEY is set")
else:
    logger.warning("GOOGLE_MAPS_API_KEY is not set!")

def get_coordinates_from_address(address):
    """Get latitude and longitude from address using Google Maps Geocoding API"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        logger.info(f"Geocoding address: {address}")
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK" and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            formatted_address = data["results"][0]["formatted_address"]
            return location["lat"], location["lng"], formatted_address
        else:
            logger.error(f"Geocoding error: {data['status']}")
            logger.debug(f"Full response: {data}")
            return None, None, None
    except Exception as e:
        logger.exception(f"Exception in get_coordinates_from_address: {str(e)}")
        return None, None, None

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in meters (Haversine formula)"""
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Differences
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return int(distance)  # Return distance as integer meters

def get_nearby_places(lat, lng, radius=1000, types=None):
    """Get nearby places using Google Places API"""
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    if types is None:
        types = ["school", "hospital", "shopping_mall", "park", "restaurant", "transit_station"]
    
    if isinstance(types, list):
        types = "|".join(types)
    
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": types,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        places = []
        if data["status"] == "OK":
            for place in data["results"][:15]:  # Limit to first 15 results
                # Calculate distance (approximate)
                place_lat = place["geometry"]["location"]["lat"]
                place_lng = place["geometry"]["location"]["lng"]
                distance = calculate_distance(lat, lng, place_lat, place_lng)
                
                places.append({
                    "name": place["name"],
                    "type": place["types"][0] if place["types"] else "unknown",
                    "distance": distance,
                    "lat": place_lat,
                    "lng": place_lng
                })
            
            # Sort by distance
            places.sort(key=lambda x: x["distance"])
            return places
        else:
            print(f"Places API error: {data['status']}")
            return []
    except Exception as e:
        print(f"Exception in get_nearby_places: {str(e)}")
        return []

