"""
⚡ RESPONSE CACHE - Fast Response Caching System
================================================

Simple LRU cache for LLM responses to speed up repeated queries.

Features:
- In-memory LRU cache
- TTL-based expiration
- Query normalization for better hits
- Statistics tracking
"""

import hashlib
import time
import logging
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from functools import wraps

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    LRU cache for LLM responses with TTL expiration.
    """
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of cached responses
            ttl_seconds: Time-to-live for cached entries (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for better cache hits."""
        # Lowercase, strip, remove extra spaces
        normalized = ' '.join(query.lower().strip().split())
        return normalized
    
    def _make_key(self, query: str, mode: str = "", user_id: str = "") -> str:
        """Create cache key from query parameters."""
        normalized = self._normalize_query(query)
        key_string = f"{user_id}:{mode}:{normalized}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, mode: str = "", user_id: str = "") -> Optional[Any]:
        """
        Get cached response if available and not expired.
        
        Returns:
            Cached value or None if not found/expired
        """
        key = self._make_key(query, mode, user_id)
        
        if key in self._cache:
            value, timestamp = self._cache[key]
            
            # Check TTL
            if time.time() - timestamp < self.ttl_seconds:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug(f"⚡ Cache HIT for query: {query[:50]}...")
                return value
            else:
                # Expired - remove
                del self._cache[key]
        
        self._misses += 1
        return None
    
    def set(self, query: str, value: Any, mode: str = "", user_id: str = ""):
        """Store response in cache."""
        key = self._make_key(query, mode, user_id)
        
        # Remove oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = (value, time.time())
        logger.debug(f"⚡ Cached response for query: {query[:50]}...")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }


# Global cache instance
_global_cache = ResponseCache(max_size=500, ttl_seconds=3600)


def get_cache() -> ResponseCache:
    """Get the global cache instance."""
    return _global_cache


def cached_llm_call(mode: str = ""):
    """
    Decorator for caching LLM responses.
    
    Usage:
        @cached_llm_call(mode="analyst")
        def my_llm_function(query, user_id):
            return llm_chat(query)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(query: str, user_id: str = "", *args, **kwargs):
            cache = get_cache()
            
            # Try cache first
            cached = cache.get(query, mode, user_id)
            if cached is not None:
                return cached
            
            # Call function
            result = func(query, user_id, *args, **kwargs)
            
            # Cache result
            if result:
                cache.set(query, result, mode, user_id)
            
            return result
        return wrapper
    return decorator


# Quick functions
def cache_get(query: str, mode: str = "", user_id: str = "") -> Optional[Any]:
    """Get from global cache."""
    return _global_cache.get(query, mode, user_id)


def cache_set(query: str, value: Any, mode: str = "", user_id: str = ""):
    """Set in global cache."""
    _global_cache.set(query, value, mode, user_id)


def cache_stats() -> Dict[str, Any]:
    """Get global cache stats."""
    return _global_cache.stats()


# Module exports
__all__ = [
    'ResponseCache',
    'get_cache',
    'cached_llm_call',
    'cache_get',
    'cache_set',
    'cache_stats'
]
