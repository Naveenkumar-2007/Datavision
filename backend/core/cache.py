"""Core cache module - stub for deployment"""

class QueryCache:
    """Simple query cache that accepts various parameter names"""
    def __init__(self, max_entries=1000, ttl_seconds=3600, default_ttl=3600, **kwargs):
        self.cache = {}
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds or default_ttl
        # Accept any other kwargs for compatibility
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key, user_id=None):
        """Get value from cache"""
        cache_key = f"{user_id}:{key}" if user_id else key
        return self.cache.get(cache_key)
    
    def set(self, query, response, route=None, sources=None, user_id=None, ttl=None):
        """Set value in cache with all parameters"""
        cache_key = f"{user_id}:{query}" if user_id else query  
        # Store as object with attributes
        class CacheEntry:
            pass
        entry = CacheEntry()
        entry.response = response
        entry.route = route
        entry.sources = sources
        self.cache[cache_key] = entry
    
    def clear_all(self):
        """Clear entire cache"""
        self.cache = {}
    
    def invalidate(self, user_id=None):
        """Clear cache"""
        if user_id:
            # Clear user-specific cache
            keys_to_remove = [k for k in self.cache.keys() if str(user_id) in str(k)]
            for k in keys_to_remove:
                del self.cache[k]
        else:
            self.cache = {}

def get_cache():
    """Get global cache instance"""
    global _cache
    if '_cache' not in globals():
        _cache = QueryCache()
    return _cache
