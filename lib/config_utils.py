"""
Configuration and Cache Management Utilities for UnQTube

This module provides utilities for reading and updating configuration files,
as well as managing the caching system for improved performance.
"""

import os
import json
import time
import pickle
import hashlib

def read_config_file(config_file='config.txt'):
    """
    Read a configuration file and return its contents as a dictionary.
    
    Args:
        config_file: The name of the configuration file to read.
        
    Returns:
        dict: A dictionary containing the configuration values.
    """
    config = {}
    try:
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        # Return empty config if file doesn't exist
        pass
    except Exception as e:
        print(f"Error reading config file: {e}")
    return config

def update_config_file(config_file, key, value):
    """
    Update a key-value pair in a configuration file.
    
    Args:
        config_file: The name of the configuration file to update.
        key: The key to update.
        value: The new value for the key.
    """
    config = read_config_file(config_file)
    config[key] = value
    
    try:
        with open(config_file, 'w') as f:
            for k, v in config.items():
                f.write(f"{k} = {v}\n")
    except Exception as e:
        print(f"Error updating config file: {e}")

class CacheManager:
    """
    Manages caching for various aspects of the video generation process.
    This improves performance by avoiding redundant operations.
    """
    
    def __init__(self, cache_dir=None, max_age=86400*7):  # Default cache expiration: 7 days
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files. If None, use 'cache' in current directory.
            max_age: Maximum age of cache entries in seconds before they expire.
        """
        self.cache_dir = cache_dir or 'cache'
        self.max_age = max_age
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, key_data):
        """
        Generate a cache key based on input data.
        
        Args:
            key_data: Data to use for generating the cache key.
            
        Returns:
            str: A string representation of the cache key.
        """
        if isinstance(key_data, str):
            data_str = key_data
        elif isinstance(key_data, dict):
            # Sort dictionary to ensure consistent hashing
            data_str = json.dumps(key_data, sort_keys=True)
        elif isinstance(key_data, list) or isinstance(key_data, tuple):
            data_str = json.dumps(list(key_data))
        else:
            data_str = str(key_data)
            
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, cache_key, category=None):
        """
        Generate the file path for a cache entry.
        
        Args:
            cache_key: The cache key for the entry.
            category: Optional category for organizing cache entries.
            
        Returns:
            str: The file path for the cache entry.
        """
        if category:
            category_dir = os.path.join(self.cache_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            return os.path.join(category_dir, f"{cache_key}.cache")
        else:
            return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def get(self, key_data, category=None):
        """
        Get a value from the cache.
        
        Args:
            key_data: Data to use for generating the cache key.
            category: Optional category for organizing cache entries.
            
        Returns:
            The cached value, or None if the key is not in the cache or the entry has expired.
        """
        cache_key = self._get_cache_key(key_data)
        cache_path = self._get_cache_path(cache_key, category)
        
        try:
            # Check if cache file exists and is not expired
            if os.path.exists(cache_path):
                file_age = time.time() - os.path.getmtime(cache_path)
                
                # Return None if the cache entry has expired
                if file_age > self.max_age:
                    return None
                
                # Read the cache entry
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error reading cache entry: {e}")
            
        return None
    
    def set(self, key_data, value, category=None):
        """
        Set a value in the cache.
        
        Args:
            key_data: Data to use for generating the cache key.
            value: Value to store in the cache.
            category: Optional category for organizing cache entries.
            
        Returns:
            bool: True if the value was successfully stored in the cache, False otherwise.
        """
        cache_key = self._get_cache_key(key_data)
        cache_path = self._get_cache_path(cache_key, category)
        
        try:
            # Write the cache entry
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            return True
        except Exception as e:
            print(f"Error writing cache entry: {e}")
            return False
    
    def clear(self, category=None, max_age=None):
        """
        Clear expired cache entries.
        
        Args:
            category: Optional category to clear. If None, clear all categories.
            max_age: Maximum age of cache entries to keep in seconds.
                     If None, use the default max_age.
        """
        max_age = max_age or self.max_age
        
        try:
            if category:
                # Clear expired entries in a specific category
                category_dir = os.path.join(self.cache_dir, category)
                if os.path.exists(category_dir):
                    self._clear_dir(category_dir, max_age)
            else:
                # Clear expired entries in all categories
                self._clear_dir(self.cache_dir, max_age)
                
                # Also clear subdirectories
                for item in os.listdir(self.cache_dir):
                    item_path = os.path.join(self.cache_dir, item)
                    if os.path.isdir(item_path):
                        self._clear_dir(item_path, max_age)
        except Exception as e:
            print(f"Error clearing cache: {e}")
    
    def _clear_dir(self, directory, max_age):
        """
        Clear expired cache entries in a directory.
        
        Args:
            directory: Directory to clear expired entries from.
            max_age: Maximum age of cache entries to keep in seconds.
        """
        current_time = time.time()
        
        for item in os.listdir(directory):
            if item.endswith('.cache'):
                item_path = os.path.join(directory, item)
                file_age = current_time - os.path.getmtime(item_path)
                
                # Delete the file if it has expired
                if file_age > max_age:
                    try:
                        os.remove(item_path)
                    except Exception as e:
                        print(f"Error removing cache file {item}: {e}")

# Create a global instance of the cache manager
cache_manager = CacheManager()

def get_cache_manager():
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager: The global cache manager instance.
    """
    return cache_manager 