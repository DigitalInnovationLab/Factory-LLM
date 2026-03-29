import os
import json
import hashlib

# Cache With Json File System
class Cache:
    """
    Cache class to manage the cache for the application.
    """

    def __init__(self, cache_dir: str):
        """
        Initialize the Cache class.

        Args:
            cache_dir (str): Directory where the cache will be stored.
        """
        self.cache_dir = cache_dir
        self.cache = {}

        # Load existing cache from JSON file if it exists
        self.load_cache()

    def load_cache(self):
        """
        Load the cache from a JSON file.
        """
        try:
            with open(os.path.join(self.cache_dir, "cache.json"), "r") as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}
        except json.JSONDecodeError:
            print("Cache file is corrupted. Starting with an empty cache.")
            self.cache = {}
        except Exception as e:
            print(f"An error occurred while loading the cache: {e}")
            self.cache = {}
        finally:
            # Ensure the cache directory exists
            os.makedirs(self.cache_dir, exist_ok=True)
            # Save the cache to a JSON file
            self.save_cache()     

    def save_cache(self):   
        """
        Save the cache to a JSON file.
        """
        try:
            with open(os.path.join(self.cache_dir, "cache.json"), "w") as f:
                json.dump(self.cache, f)
        except Exception as e:
            print(f"An error occurred while saving the cache: {e}")

    def get(self, key: str):
        """
        Get a value from the cache.

        Args:
            key (str): The key to retrieve from the cache.

        Returns:
            The value associated with the key, or None if the key does not exist.
        """
        return self.cache.get(key)
    
        # Return None if the key does not exist
    def set(self, key: str, value):
        """
        Set a value in the cache.
        Args:
            key (str): The key to set in the cache.
            value: The value to associate with the key.
        """
        self.cache[key] = value
        # Save the cache to a JSON file
        self.save_cache()

    def clear(self):
        """
        Clear the cache.
        """
        self.cache = {}
        # Save the cache to a JSON file
        self.save_cache()

    def delete(self, key: str):
        """
        Delete a key from the cache.
        Args:
            key (str): The key to delete from the cache.
        """ 
        if key in self.cache:
            del self.cache[key]
            # Save the cache to a JSON file
            self.save_cache()
        else:
            print(f"Key '{key}' not found in cache.")     

    def create_cache_key(self,model:str,prompt:str):
        """
        Create a cache key based on model and prompt.
        Args:
            model (str): The model name.
            prompt (str): The prompt text.
        Returns:
            str: The generated cache key.
        """
        key = f"{model.strip().lower()}_{prompt.strip().lower()}"
        return hashlib.sha256(key.encode('utf-8')).hexdigest()