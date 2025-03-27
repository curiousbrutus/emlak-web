import unittest
from modules.geo.geo_utils import calculate_distance, validate_coordinates

class TestGeoUtils(unittest.TestCase):

    def test_calculate_distance(self):
        coords1 = (40.7128, -74.0060)  # New York
        coords2 = (34.0522, -118.2437) # Los Angeles
        distance = calculate_distance(coords1, coords2)
        self.assertAlmostEqual(distance, 3935.68, places=0)

        coords3 = (51.5074, 0.1278)  # London
        coords4 = (48.8566, 2.3522)   # Paris
        distance = calculate_distance(coords3, coords4)
        self.assertAlmostEqual(distance, 343.54, places=0)
        
        coords5 = (0.0, 0.0)  # Origin
        coords6 = (0.0, 0.0)   # Origin
        distance = calculate_distance(coords5, coords6)
        self.assertAlmostEqual(distance, 0, places=0)

    def test_validate_coordinates(self):
        self.assertTrue(validate_coordinates(40.7128, -74.0060))  # Valid
        self.assertTrue(validate_coordinates(0, 0))  # Valid
        self.assertTrue(validate_coordinates(90, 180))
        self.assertTrue(validate_coordinates(-90, -180))

        self.assertFalse(validate_coordinates(91, 0))  # Invalid latitude
        self.assertFalse(validate_coordinates(-91, 0)) # Invalid latitude
        self.assertFalse(validate_coordinates(0, 181))  # Invalid longitude
        self.assertFalse(validate_coordinates(0, -181)) # Invalid longitude
        self.assertFalse(validate_coordinates(1000, -1)) # Invalid longitude and latitude
        self.assertFalse(validate_coordinates(-1000, -1)) # Invalid longitude and latitude
        self.assertFalse(validate_coordinates(-1000, 1000)) # Invalid longitude and latitude

if __name__ == '__main__':
    unittest.main()