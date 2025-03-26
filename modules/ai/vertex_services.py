"""Vertex AI service integrations."""

import base64
from io import BytesIO
from PIL import Image
import numpy as np
from google.cloud import aiplatform
from config.google_cloud_config import ENDPOINTS

class VertexAIService:
    @staticmethod
    def process_image(image: Image.Image) -> Image.Image:
        """Process an image using Vertex AI."""
        try:
            # Convert image to bytes
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_bytes = base64.b64encode(buffered.getvalue()).decode()
            
            # Get endpoint
            endpoint = aiplatform.Endpoint(ENDPOINTS["image_processing"])
            
            # Make prediction
            response = endpoint.predict(
                instances=[{"image": image_bytes}]
            )
            
            # Process response and convert back to PIL Image
            processed_bytes = base64.b64decode(response.predictions[0]["image"])
            return Image.open(BytesIO(processed_bytes))
            
        except Exception as e:
            print(f"Vertex AI image processing error: {e}")
            return image
    
    @staticmethod
    def generate_property_description(property_data: dict) -> str:
        """Generate property description using Vertex AI."""
        try:
            endpoint = aiplatform.Endpoint(ENDPOINTS["text_generation"])
            
            # Format the prompt
            prompt = f"""
            Create a professional property description in Turkish:
            Type: {property_data['property_type']}
            Rooms: {property_data['rooms']}
            Area: {property_data['area']}m²
            Price: {property_data['price']}TL
            Features: {property_data['special_features']}
            """
            
            response = endpoint.predict(
                instances=[{"prompt": prompt}]
            )
            
            return response.predictions[0]["text"]
            
        except Exception as e:
            print(f"Vertex AI text generation error: {e}")
            return None
