"""Custom cache utilities for storing and retrieving data."""

import os
import pickle
import hashlib
import time
import shutil
import functools
import streamlit as st
from pathlib import Path

# Create cache directory in user's home directory
CACHE_DIR = Path.home() / ".emlak_web_cache"
CACHE_DIR.mkdir(exist_ok=True)

# In-memory cache dictionary
_memory_cache = {}

def _get_cache_key(func_name, args, kwargs):
    """Generate a unique cache key based on function name and arguments."""
    key_parts = [func_name]
    
    # Add stringified args and kwargs
    for arg in args:
        key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    # Create a hash from the key parts
    key_string = "_".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached_data(ttl=3600):
    """
    Decorator to cache function results in memory and on disk.
    
    Args:
        ttl: Time to live for cache entries in seconds (default: 1 hour)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate a unique key for this function call
            cache_key = _get_cache_key(func.__name__, args, kwargs)
            
            # Check memory cache first
            if cache_key in _memory_cache:
                value, timestamp = _memory_cache[cache_key]
                if time.time() - timestamp < ttl:
                    return value
            
            # Check disk cache if not in memory or expired
            cache_file = CACHE_DIR / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        value, timestamp = pickle.load(f)
                        if time.time() - timestamp < ttl:
                            # Store in memory for faster access next time
                            _memory_cache[cache_key] = (value, timestamp)
                            return value
                except (pickle.PickleError, EOFError):
                    # If any error loading from disk, just regenerate
                    pass
            
            # Cache miss or expired - call the function
            value = func(*args, **kwargs)
            
            # Store result in both memory and disk cache
            current_time = time.time()
            _memory_cache[cache_key] = (value, current_time)
            
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump((value, current_time), f)
            except Exception:
                # If disk cache fails, we still have the memory cache
                pass
                
            return value
        return wrapper
    return decorator

def clear_cache():
    """Clear the in-memory cache."""
    _memory_cache.clear()
    st.success("Memory cache cleared!")

def clear_disk_cache():
    """Clear the disk cache."""
    try:
        for file in CACHE_DIR.glob("*.pkl"):
            file.unlink()
        st.success("Disk cache cleared!")
    except Exception as e:
        st.error(f"Error clearing disk cache: {str(e)}")
