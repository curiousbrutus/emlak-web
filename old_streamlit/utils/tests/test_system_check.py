import unittest
from unittest.mock import patch
import os
import platform
import psutil
from utils.system_check import SystemChecker

class TestSystemChecker(unittest.TestCase):

    def setUp(self):
        self.checker = SystemChecker()

    @patch('platform.system')
    def test_get_os_info(self, mock_platform_system):
        mock_platform_system.return_value = "Linux"
        self.assertEqual(self.checker.get_os_info(), "Linux")

        mock_platform_system.return_value = "Windows"
        self.assertEqual(self.checker.get_os_info(), "Windows")

        mock_platform_system.return_value = "Darwin"
        self.assertEqual(self.checker.get_os_info(), "macOS")
        
    @patch('platform.release')
    def test_get_os_version(self, mock_platform_release):
        mock_platform_release.return_value = "5.10.0-1044-aws"
        self.assertEqual(self.checker.get_os_version(), "5.10.0-1044-aws")

    @patch('psutil.cpu_count')
    def test_get_cpu_count(self, mock_cpu_count):
        mock_cpu_count.return_value = 8
        self.assertEqual(self.checker.get_cpu_count(), 8)

    @patch('psutil.virtual_memory')
    def test_get_memory_info(self, mock_virtual_memory):
        mock_virtual_memory.return_value.total = 16 * 1024**3
        mock_virtual_memory.return_value.available = 8 * 1024**3
        expected_total = "16.00 GB"
        expected_available = "8.00 GB"
        total, available = self.checker.get_memory_info()
        self.assertEqual(total, expected_total)
        self.assertEqual(available, expected_available)

    @patch('psutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage):
        mock_disk_usage.return_value.total = 100 * 1024**3
        mock_disk_usage.return_value.free = 50 * 1024**3
        expected_total = "100.00 GB"
        expected_free = "50.00 GB"
        total, free = self.checker.get_disk_usage()
        self.assertEqual(total, expected_total)
        self.assertEqual(free, expected_free)

    def test_get_python_version(self):
        version = self.checker.get_python_version()
        self.assertIsNotNone(version)
        self.assertIsInstance(version, str)
        self.assertGreater(len(version), 0)

    @patch('psutil.cpu_percent')
    def test_get_cpu_usage(self, mock_cpu_percent):
        mock_cpu_percent.return_value = 50.0
        self.assertEqual(self.checker.get_cpu_usage(), 50.0)

    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        mock_virtual_memory.return_value.percent = 30.0
        self.assertEqual(self.checker.get_memory_usage(), 30.0)

    @patch('os.path.exists')
    def test_check_file_exists(self, mock_exists):
        mock_exists.return_value = True
        self.assertTrue(self.checker.check_file_exists("test_file.txt"))
        mock_exists.return_value = False
        self.assertFalse(self.checker.check_file_exists("test_file.txt"))

    def test_check_internet_connection(self):
        # This test is hard to mock reliably, so we'll just check that it returns True or False
        result = self.checker.check_internet_connection()
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()