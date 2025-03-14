"""General utility functions for the application."""

from math import radians, sin, cos, sqrt, atan2
import shutil
import os
import streamlit as st  # Eksik import eklendi

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the distance between two coordinates in meters.
    
    Args:
        lat1, lng1: Latitude and longitude of first point
        lat2, lng2: Latitude and longitude of second point
        
    Returns:
        Distance in meters
    """
    # Approximate radius of earth in km
    R = 6373.0
    
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    dlon = lng2 - lng1
    dlat = lat2 - lat1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    
    return round(distance * 1000)  # Convert to meters

def cleanup_temp_files(filepath):
    """Clean up temporary files and directories."""
    try:
        if filepath and os.path.exists(filepath):
            temp_dir = os.path.dirname(filepath)
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        st.warning(f"Cleanup warning: {str(e)}")
