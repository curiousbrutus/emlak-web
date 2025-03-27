import sys
import os
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import environment loader
from shortGPT.utils.env_loader import load_environment
load_environment()

def check_dependencies():
    """Check if all required dependencies are installed"""
    
    required_packages = [
        "tinydb", "yt_dlp", "dotenv", "opencv-python", "pillow", 
        "requests", "numpy", "pydub"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            package_name = package.replace("-", "_")
            __import__(package_name)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is not installed")
    
    return missing_packages

def check_shortgpt_core():
    """Check if ShortGPT core modules are importable"""
    
    core_modules = [
        "shortGPT.config.languages",
        "shortGPT.audio.voice_module",
        "shortGPT.database.content_database",
        "shortGPT.engine.abstract_content_engine"
    ]
    
    failing_modules = []
    
    for module in core_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} imported successfully")
        except ImportError as e:
            failing_modules.append((module, str(e)))
            logger.error(f"❌ {module} import failed: {e}")
    
    return failing_modules

def check_api_keys():
    """Check if necessary API keys are set"""
    
    required_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ELEVENLABS_API_KEY": "ElevenLabs",
        "GOOGLE_MAPS_API_KEY": "Google Maps"
    }
    
    missing_keys = []
    
    for key, service in required_keys.items():
        if os.environ.get(key):
            logger.info(f"✅ {service} API key is set")
        else:
            missing_keys.append(service)
            logger.error(f"❌ {service} API key is not set")
    
    return missing_keys

if __name__ == "__main__":
    print("==== Testing ShortGPT Core Functionality ====\n")
    
    # Check dependencies
    print("\n== Checking Dependencies ==")
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
    else:
        print("\n✅ All required packages are installed")
    
    # Check core modules
    print("\n== Checking ShortGPT Core Modules ==")
    failing_modules = check_shortgpt_core()
    if failing_modules:
        print("\n❌ Some core modules could not be imported:")
        for module, error in failing_modules:
            print(f"  - {module}: {error}")
    else:
        print("\n✅ All core modules imported successfully")
    
    # Check API keys
    print("\n== Checking API Keys ==")
    missing_keys = check_api_keys()
    if missing_keys:
        print(f"\n❌ Missing API keys for: {', '.join(missing_keys)}")
        print("Please add these to your .env file")
    else:
        print("\n✅ All required API keys are set")
    
    # Summary
    if not missing_packages and not failing_modules and not missing_keys:
        print("\n✅ ShortGPT core functionality appears to be working correctly")
    else:
        print("\n⚠️ Some issues need to be fixed before ShortGPT will work properly")
