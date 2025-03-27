import unittest
from unittest.mock import patch, MagicMock
import os
from PIL import Image
import numpy as np

# Assuming image_processing.py is in the same directory or accessible in your Python path
try:
    from modules.image import image_processing
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from modules.image import image_processing

class TestImageProcessing(unittest.TestCase):

    def setUp(self):
        # Create a dummy image for testing
        self.dummy_image = Image.new('RGB', (100, 100), color = 'red')
        self.dummy_image_path = 'test_image.png'
        self.dummy_image.save(self.dummy_image_path)

    def tearDown(self):
        # Clean up the dummy image
        if os.path.exists(self.dummy_image_path):
            os.remove(self.dummy_image_path)

    def test_resize_image(self):
        resized_image = image_processing.resize_image(self.dummy_image_path, (50, 50))
        self.assertEqual(resized_image.size, (50, 50))

    def test_convert_to_grayscale(self):
        grayscale_image = image_processing.convert_to_grayscale(self.dummy_image_path)
        self.assertEqual(grayscale_image.mode, 'L')

    def test_rotate_image(self):
        rotated_image = image_processing.rotate_image(self.dummy_image_path, 90)
        self.assertNotEqual(rotated_image, None)

    def test_apply_filter(self):
        # Test a valid filter
        filtered_image = image_processing.apply_filter(self.dummy_image_path, 'BLUR')
        self.assertNotEqual(filtered_image, None)
        
        # Test an invalid filter
        with self.assertRaises(ValueError):
             image_processing.apply_filter(self.dummy_image_path, "INVALID_FILTER")

    def test_adjust_brightness(self):
        # Assuming adjust_brightness does not raise errors for valid inputs
        brightened_image = image_processing.adjust_brightness(self.dummy_image_path, 1.5)
        self.assertNotEqual(brightened_image, None)

    def test_crop_image(self):
        cropped_image = image_processing.crop_image(self.dummy_image_path, (10, 10, 50, 50))
        self.assertEqual(cropped_image.size, (40, 40))

    def test_load_image_valid_path(self):
      loaded_image = image_processing.load_image(self.dummy_image_path)
      self.assertIsNotNone(loaded_image)
      self.assertTrue(isinstance(loaded_image,Image.Image))
      
    def test_load_image_invalid_path(self):
      with self.assertRaises(FileNotFoundError):
        image_processing.load_image("invalid_path.jpg")
    
    def test_save_image(self):
      output_path = "test_output_image.jpg"
      try:
        image_processing.save_image(self.dummy_image,output_path)
        self.assertTrue(os.path.exists(output_path))
      finally:
        if os.path.exists(output_path):
          os.remove(output_path)

if __name__ == '__main__':
    unittest.main()