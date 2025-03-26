import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Assuming wizard_utils.py is in the same directory or in sys.path
# If not, you'll need to adjust this
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import wizard_utils

class TestWizardUtils(unittest.TestCase):

    @patch('builtins.input', side_effect=['Test Project', 'Description', ''])
    def test_collect_project_details(self, mock_input):
        details = wizard_utils.collect_project_details()
        self.assertEqual(details['name'], 'Test Project')
        self.assertEqual(details['description'], 'Description')
        self.assertFalse(details['use_defaults'])

    @patch('builtins.input', side_effect=['', ''])
    def test_collect_project_details_empty_name_description(self, mock_input):
        details = wizard_utils.collect_project_details()
        self.assertIsNone(details['name'])
        self.assertIsNone(details['description'])
        self.assertFalse(details['use_defaults'])

    @patch('builtins.input', side_effect=['y'])
    def test_collect_project_details_use_defaults(self, mock_input):
        details = wizard_utils.collect_project_details()
        self.assertTrue(details['use_defaults'])

    @patch('utils.wizard_utils.collect_project_details', return_value={'name': 'Test Project', 'description': 'Description', 'use_defaults': False})
    def test_initialize_project_valid(self, mock_collect_details):
      
      result = wizard_utils.initialize_project()
      self.assertTrue(result)

    @patch('utils.wizard_utils.collect_project_details', return_value={'name': None, 'description': 'Description', 'use_defaults': False})
    def test_initialize_project_name_invalid(self, mock_collect_details):
      
      result = wizard_utils.initialize_project()
      self.assertFalse(result)
    

    @patch('utils.wizard_utils.collect_project_details', return_value={'name': 'Test Project', 'description': None, 'use_defaults': False})
    def test_initialize_project_description_invalid(self, mock_collect_details):
      
      result = wizard_utils.initialize_project()
      self.assertFalse(result)

    
if __name__ == '__main__':
    unittest.main()