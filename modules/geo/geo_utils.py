"""Geographic utilities for address geocoding and nearby place search."""

import streamlit as st
import requests
from utils.utils import calculate_distance  # Doğrudan import edilebilir modüller için

def get_coordinates_from_address(address):
    """
    Get geographic coordinates from an address using Google Maps Geocoding API.
    
    Args:
        address: String address to geocode
        
    Returns:
        Tuple of (latitude, longitude, formatted_address) or (None, None, None) if failed
    """
    try:
        if not st.session_state.get("GOOGLE_MAPS_API_KEY"):
            st.error("Google Maps API key required!")
            return None, None, None
            
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": st.session_state["GOOGLE_MAPS_API_KEY"]
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"], data["results"][0]["formatted_address"]
        else:
            st.error(f"Geocoding error: {data['status']}")
            return None, None, None
    except Exception as e:
        st.error(f"Error getting coordinates: {str(e)}")
        return None, None, None

def get_nearby_places(lat, lng, radius=1500, types=None):
    """
    Find nearby places of interest using Google Places API.
    
    Args:
        lat, lng: Coordinates to search around
        radius: Search radius in meters
        types: Types of places to find
        
    Returns:
        List of place dictionaries with name, type, distance, and rating
    """
    # Relatif import yerine doğrudan import kullanıyoruz
    # Önceki: from utils.utils import calculate_distance
    
    if not st.session_state.get("GOOGLE_PLACES_API_KEY"):
        return []
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "key": st.session_state["GOOGLE_PLACES_API_KEY"]
        }
        
        if types:
            params["type"] = types
            
        response = requests.get(url, params=params)
        data = response.json()
        
        places = []
        if data["status"] == "OK":
            for place in data["results"][:10]:  # Limit to top 10 places
                places.append({
                    "name": place.get("name", ""),
                    "type": place.get("types", [""])[0],
                    "distance": calculate_distance(lat, lng, 
                                             place["geometry"]["location"]["lat"], 
                                             place["geometry"]["location"]["lng"]),
                    "rating": place.get("rating", 0)
                })
        return places
    except Exception as e:
        st.warning(f"Error fetching nearby places: {str(e)}")
        return []
