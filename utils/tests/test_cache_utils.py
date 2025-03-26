import unittest
from unittest.mock import patch
import time
from utils.cache_utils import Cache

class TestCache(unittest.TestCase):
    def setUp(self):
        self.cache = Cache(ttl=1)

    def test_set_and_get(self):
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_get_nonexistent_key(self):
        self.assertIsNone(self.cache.get("nonexistent_key"))

    def test_ttl_expiration(self):
        self.cache.set("key2", "value2")
        time.sleep(2)
        self.assertIsNone(self.cache.get("key2"))

    def test_delete(self):
        self.cache.set("key3", "value3")
        self.cache.delete("key3")
        self.assertIsNone(self.cache.get("key3"))

    def test_clear(self):
        self.cache.set("key4", "value4")
        self.cache.set("key5", "value5")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key4"))
        self.assertIsNone(self.cache.get("key5"))

    def test_custom_ttl(self):
        custom_cache = Cache(ttl=3)
        custom_cache.set("key6", "value6")
        time.sleep(2)
        self.assertEqual(custom_cache.get("key6"), "value6")
        time.sleep(2)
        self.assertIsNone(custom_cache.get("key6"))
        
    def test_max_size_eviction(self):
        cache = Cache(max_size = 2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")


if __name__ == '__main__':
    unittest.main()