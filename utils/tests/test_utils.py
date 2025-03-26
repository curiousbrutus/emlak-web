import unittest
from unittest.mock import patch
import os
import tempfile
from utils.utils import (
    create_directory_if_not_exists,
    get_file_extension,
    is_valid_file_path,
    is_valid_directory_path,
    remove_directory,
    remove_file,
    read_text_file,
    write_text_file,
)

class TestUtils(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test.txt")

    def tearDown(self):
        remove_directory(self.temp_dir)

    def test_create_directory_if_not_exists(self):
        new_dir = os.path.join(self.temp_dir, "new_dir")
        create_directory_if_not_exists(new_dir)
        self.assertTrue(os.path.exists(new_dir))

        # Test creating a directory that already exists
        create_directory_if_not_exists(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_get_file_extension(self):
        self.assertEqual(get_file_extension("test.txt"), "txt")
        self.assertEqual(get_file_extension("test.tar.gz"), "gz")
        self.assertEqual(get_file_extension("test"), "")
        self.assertEqual(get_file_extension(""), "")

    def test_is_valid_file_path(self):
        # Test with valid file path
        with open(self.temp_file, "w") as f:
            f.write("test")
        self.assertTrue(is_valid_file_path(self.temp_file))

        # Test with invalid file path
        self.assertFalse(is_valid_file_path(os.path.join(self.temp_dir, "nonexistent.txt")))

    def test_is_valid_directory_path(self):
        # Test with valid directory path
        self.assertTrue(is_valid_directory_path(self.temp_dir))
        # Test with invalid directory path
        self.assertFalse(is_valid_directory_path(os.path.join(self.temp_dir, "nonexistent_dir")))

    def test_remove_directory(self):
        # Test with existing directory
        new_dir = os.path.join(self.temp_dir, "new_dir")
        os.mkdir(new_dir)
        remove_directory(new_dir)
        self.assertFalse(os.path.exists(new_dir))

    def test_remove_file(self):
        # Test with existing file
        with open(self.temp_file, "w") as f:
            f.write("test")
        remove_file(self.temp_file)
        self.assertFalse(os.path.exists(self.temp_file))

    def test_read_text_file(self):
         with open(self.temp_file, "w") as f:
            f.write("test content")
         self.assertEqual(read_text_file(self.temp_file), "test content")

    def test_write_text_file(self):
        write_text_file(self.temp_file, "new content")
        with open(self.temp_file, "r") as f:
            self.assertEqual(f.read(), "new content")

    def test_write_text_file_fails_with_invalid_path(self):
        invalid_file_path = os.path.join(self.temp_dir, "not_created", "new_content.txt")
        self.assertFalse(write_text_file(invalid_file_path, "new content"))