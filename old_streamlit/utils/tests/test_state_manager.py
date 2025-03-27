import unittest
from unittest.mock import patch
import os
import json

from utils.state_manager import StateManager

class TestStateManager(unittest.TestCase):

    def setUp(self):
        self.state_manager = StateManager("test_state.json")

    def tearDown(self):
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def test_load_state_empty_file(self):
        with open("test_state.json", "w") as f:
            f.write("")
        state = self.state_manager.load_state()
        self.assertEqual(state, {})

    def test_load_state_invalid_json(self):
        with open("test_state.json", "w") as f:
            f.write("{invalid_json}")
        state = self.state_manager.load_state()
        self.assertEqual(state, {})

    def test_load_state_valid_json(self):
        with open("test_state.json", "w") as f:
            json.dump({"key": "value"}, f)
        state = self.state_manager.load_state()
        self.assertEqual(state, {"key": "value"})

    def test_save_state(self):
        self.state_manager.save_state({"new_key": "new_value"})
        with open("test_state.json", "r") as f:
            data = json.load(f)
        self.assertEqual(data, {"new_key": "new_value"})

    def test_get_state_key_exists(self):
        self.state_manager.save_state({"key": "value"})
        value = self.state_manager.get_state("key")
        self.assertEqual(value, "value")
    
    def test_get_state_key_does_not_exists(self):
        self.state_manager.save_state({"key": "value"})
        value = self.state_manager.get_state("key1")
        self.assertIsNone(value)

    def test_update_state(self):
        self.state_manager.save_state({"key": "value"})
        self.state_manager.update_state("key", "new_value")
        self.assertEqual(self.state_manager.get_state("key"), "new_value")
    
    def test_add_state_new_key(self):
        self.state_manager.add_state("key1","value1")
        self.assertEqual(self.state_manager.get_state("key1"),"value1")

    def test_add_state_existing_key(self):
         self.state_manager.add_state("key1","value1")
         self.state_manager.add_state("key1","value2")
         self.assertEqual(self.state_manager.get_state("key1"),"value2")

    def test_delete_state_key_exists(self):
        self.state_manager.add_state("key1","value1")
        self.state_manager.delete_state("key1")
        self.assertIsNone(self.state_manager.get_state("key1"))

    def test_delete_state_key_not_exists(self):
        self.state_manager.add_state("key1","value1")
        self.state_manager.delete_state("key2")
        self.assertEqual(self.state_manager.get_state("key1"),"value1")

    def test_file_not_exists(self):
        self.state_manager = StateManager("state_not_exists.json")
        state = self.state_manager.load_state()
        self.assertEqual(state, {})
        if os.path.exists("state_not_exists.json"):
            os.remove("state_not_exists.json")