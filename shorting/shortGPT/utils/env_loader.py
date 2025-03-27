import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_environment():
    """
    Load environment variables from .env files in multiple potential locations.
    Returns True if successful, False otherwise.
    """
    # List of potential .env file locations in order of preference
    potential_locations = [
        # Current directory
        os.path.join(os.getcwd(), '.env'),
        # Project root
        os.path.join(Path(__file__).parent.parent.parent, '.env'),
        # Parent directory (shorts folder)
        os.path.join(Path(__file__).parent.parent.parent.parent, '.env'),
    ]
    
    # Try to load from each location
    for env_path in potential_locations:
        if os.path.exists(env_path):
            logger.info(f"Loading environment from: {env_path}")
            load_dotenv(env_path)
            
            # Verify key variables were loaded
            if os.getenv("GOOGLE_MAPS_API_KEY"):
                logger.info("GOOGLE_MAPS_API_KEY loaded successfully")
                return True
    
    # If we got here, no .env file with the required variables was found
    logger.warning("Could not load environment variables from any .env file")
    return False

# Try to load the environment when this module is imported
load_success = load_environment()
