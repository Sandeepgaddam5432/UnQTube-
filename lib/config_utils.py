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
import random
import threading
from functools import lru_cache

# Global cache for API responses
_response_cache = {}
_cache_lock = threading.Lock()

# Rate limiting state
_rate_limit_state = {
    "gemini_api": {
        "last_request_time": 0,
        "backoff_time": 0.5,  # Initial backoff in seconds
        "max_backoff": 30,    # Maximum backoff in seconds
        "requests_count": 0,
        "rate_limit_hit": False
    },
    "pexels_api": {
        "last_request_time": 0,
        "backoff_time": 0.5,
        "max_backoff": 15,
        "requests_count": 0,
        "rate_limit_hit": False
    }
}
_rate_limit_lock = threading.Lock()

def read_config_file(filename="config.txt"):
    """Read configuration from file
    
    Args:
        filename (str): Path to the configuration file
        
    Returns:
        dict: Configuration values as a dictionary
    """
    config = {}
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as file:
        for line in file:
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading config file {filename}: {e}")
    return config

def update_config_file(filename, key, value):
    """Update a specific key in the configuration file
    
    Args:
        filename (str): Path to the configuration file
        key (str): Configuration key to update
        value (str): New value for the key
    """
    config = read_config_file(filename)
    config[key] = value
    
    try:
        with open(filename, "w", encoding="utf-8") as file:
            for k, v in config.items():
                file.write(f"{k} = {v}\n")
    except Exception as e:
        print(f"Error updating config file {filename}: {e}")

@lru_cache(maxsize=128)
def get_cached_config(filename="config.txt"):
    """Get cached configuration
    
    This function uses Python's lru_cache decorator to cache the configuration
    and avoid repeated file reads.
    
    Args:
        filename (str): Path to the configuration file
        
    Returns:
        dict: Configuration values as a dictionary
    """
    return read_config_file(filename)

def cache_response(key, response, ttl=3600):
    """Cache an API response
    
    Args:
        key (str): Cache key
        response: Response data to cache
        ttl (int): Time to live in seconds (default: 1 hour)
    """
    with _cache_lock:
        _response_cache[key] = {
            "data": response,
            "expires": time.time() + ttl
        }

def get_cached_response(key):
    """Get a cached API response
    
    Args:
        key (str): Cache key
        
    Returns:
        The cached response or None if not found or expired
    """
    with _cache_lock:
        if key in _response_cache:
            cache_entry = _response_cache[key]
            if time.time() < cache_entry["expires"]:
                return cache_entry["data"]
            else:
                # Remove expired entry
                del _response_cache[key]
    return None

def clear_cache():
    """Clear all cached responses"""
    with _cache_lock:
        _response_cache.clear()

def intelligent_rate_limit_handling(retry_after=None, api_type=None):
    """Handle rate limits intelligently with retry-after support
    
    This function implements a smart rate limiting strategy that:
    1. Respects server-provided retry-after headers when available
    2. Uses exponential backoff when no retry-after is provided
    3. Adds jitter to prevent thundering herd problems
    
    Args:
        retry_after (int): Retry-after value from API response header (seconds)
        api_type (str): API type identifier (e.g., 'gemini_api', 'pexels_api')
        
    Returns:
        float: The actual sleep time used (seconds)
    """
    # If no API type specified, use a default backoff
    if not api_type:
        sleep_time = retry_after if retry_after else random.uniform(1, 3)
        time.sleep(sleep_time)
        return sleep_time
        
    with _rate_limit_lock:
        if api_type not in _rate_limit_state:
            # Unknown API type, use simple backoff
            sleep_time = retry_after if retry_after else 1.0
            time.sleep(sleep_time)
            return sleep_time
            
        state = _rate_limit_state[api_type]
        state["rate_limit_hit"] = True
        
        # If we have a retry-after header, use it (with small jitter)
        if retry_after:
            # Add small jitter (±10%) to avoid thundering herd
            jitter_factor = random.uniform(0.9, 1.1)
            sleep_time = retry_after * jitter_factor
            
            # Update state to reflect this explicit backoff
            state["backoff_time"] = min(retry_after, state["max_backoff"])
        else:
            # No retry-after, use exponential backoff
            # Double the backoff time (with max limit)
            state["backoff_time"] = min(state["backoff_time"] * 2, state["max_backoff"])
            
            # Add jitter (±20%) to avoid thundering herd
            jitter_factor = random.uniform(0.8, 1.2)
            sleep_time = state["backoff_time"] * jitter_factor
        
        # Sleep for the calculated time
        print(f"Rate limit hit for {api_type}. Backing off for {sleep_time:.2f} seconds...")
        time.sleep(sleep_time)
        return sleep_time

def should_throttle_request(api_type):
    """Check if a request should be throttled based on rate limits
    
    This implements an exponential backoff strategy for rate limiting.
    
    Args:
        api_type (str): API type (e.g., 'gemini_api', 'pexels_api')
        
    Returns:
        tuple: (should_throttle, wait_time) - whether to throttle and how long to wait
    """
    with _rate_limit_lock:
        if api_type not in _rate_limit_state:
            return False, 0
            
        state = _rate_limit_state[api_type]
        current_time = time.time()
        elapsed = current_time - state["last_request_time"]
        
        # If we've hit a rate limit recently, use exponential backoff
        if state["rate_limit_hit"]:
            if elapsed < state["backoff_time"]:
                return True, state["backoff_time"] - elapsed
            else:
                # Reset rate limit hit flag but keep backoff time for next hit
                state["rate_limit_hit"] = False
        
        # Simple request counting - if we're making too many requests in a short time
        if state["requests_count"] > 10 and elapsed < 1.0:
            # Add small jitter to avoid thundering herd
            jitter = random.uniform(0.1, 0.5)
            return True, 1.0 - elapsed + jitter
            
        # Update state
        state["last_request_time"] = current_time
        state["requests_count"] += 1
        
        # Reset request count periodically
        if elapsed > 5.0:
            state["requests_count"] = 1
            
        return False, 0

def handle_rate_limit_hit(api_type):
    """Handle a rate limit being hit
    
    This increases the backoff time exponentially.
    
    Args:
        api_type (str): API type (e.g., 'gemini_api', 'pexels_api')
        
    Returns:
        float: The new backoff time in seconds
    """
    with _rate_limit_lock:
        if api_type not in _rate_limit_state:
            return 1.0
            
        state = _rate_limit_state[api_type]
        state["rate_limit_hit"] = True
        
        # Increase backoff time exponentially
        state["backoff_time"] = min(state["backoff_time"] * 2, state["max_backoff"])
        
        # Add small random jitter to avoid all clients retrying at the same time
        jitter = random.uniform(0, 0.5)
        backoff_with_jitter = state["backoff_time"] + jitter
        
        return backoff_with_jitter

def reset_rate_limit_state(api_type=None):
    """Reset rate limit state
    
    Args:
        api_type (str, optional): API type to reset. If None, reset all.
    """
    with _rate_limit_lock:
        if api_type is None:
            # Reset all API states
            for api in _rate_limit_state:
                _rate_limit_state[api].update({
                    "last_request_time": 0,
                    "backoff_time": 0.5,
                    "requests_count": 0,
                    "rate_limit_hit": False
                })
        elif api_type in _rate_limit_state:
            # Reset specific API state
            _rate_limit_state[api_type].update({
                "last_request_time": 0,
                "backoff_time": 0.5,
                "requests_count": 0,
                "rate_limit_hit": False
            })

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