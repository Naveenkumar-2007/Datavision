# CacheRAG Module - Query Caching for Cost & Speed
"""
Caching layer for RAG queries to:
1. Reduce LLM API costs (no re-processing identical queries)
2. Faster response times for repeated questions
3. Session-aware caching for personalized responses

Cache Strategies:
- Exact match: Same query text
- Semantic match: Similar meaning queries
- Time-based expiry: Stale cache invalidation
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import OrderedDict
import threading


@dataclass
class CacheEntry:
    """Single cache entry"""
    query: str
    query_hash: str
    response: str
    route: str
    sources: List[str]
    timestamp: float
    hit_count: int = 0
    user_id: str = ""
    ttl: int = 3600  # Time to live in seconds (1 hour default)


class QueryCache:
    """
    In-memory + persistent cache for RAG responses
    
    Features:
    - LRU eviction for memory management
    - Semantic similarity matching (optional)
    - Per-user cache isolation
    - TTL-based expiry
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        default_ttl: int = 3600,
        cache_dir: Optional[Path] = None,
        enable_semantic_match: bool = False
    ):
        """
        Args:
            max_entries: Maximum cache entries in memory
            default_ttl: Default time-to-live in seconds
            cache_dir: Directory for persistent cache (None = memory only)
            enable_semantic_match: Use embedding similarity for cache lookup
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cache_dir = cache_dir
        self.enable_semantic_match = enable_semantic_match
        
        # LRU cache (ordered dict)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        
        # Stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "semantic_hits": 0
        }
        
        # Load persistent cache
        if cache_dir:
            self._load_persistent_cache()
    
    def _hash_query(self, query: str, user_id: str = "") -> str:
        """Create consistent hash for query"""
        # Normalize query
        normalized = query.lower().strip()
        key = f"{user_id}:{normalized}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, query: str, user_id: str = "") -> Optional[CacheEntry]:
        """
        Get cached response for query
        
        Args:
            query: User query
            user_id: User identifier for isolation
            
        Returns:
            CacheEntry if found and valid, None otherwise
        """
        query_hash = self._hash_query(query, user_id)
        
        with self._lock:
            # Exact match lookup
            if query_hash in self._cache:
                entry = self._cache[query_hash]
                
                # Check TTL
                if time.time() - entry.timestamp < entry.ttl:
                    # Move to end (LRU update)
                    self._cache.move_to_end(query_hash)
                    entry.hit_count += 1
                    self.stats["hits"] += 1
                    print(f"✅ Cache HIT: {query[:50]}... (hits: {entry.hit_count})")
                    return entry
                else:
                    # Expired - remove
                    del self._cache[query_hash]
            
            # Semantic match (if enabled)
            if self.enable_semantic_match:
                semantic_match = self._semantic_lookup(query, user_id)
                if semantic_match:
                    self.stats["semantic_hits"] += 1
                    return semantic_match
            
            self.stats["misses"] += 1
            return None
    
    def set(
        self,
        query: str,
        response: str,
        route: str,
        sources: List[str],
        user_id: str = "",
        ttl: Optional[int] = None
    ) -> CacheEntry:
        """
        Cache a query response
        
        Args:
            query: User query
            response: Generated response
            route: Route used (rag/graph/hybrid)
            sources: Source documents
            user_id: User identifier
            ttl: Custom TTL (seconds)
            
        Returns:
            Created CacheEntry
        """
        query_hash = self._hash_query(query, user_id)
        
        entry = CacheEntry(
            query=query,
            query_hash=query_hash,
            response=response,
            route=route,
            sources=sources,
            timestamp=time.time(),
            hit_count=0,
            user_id=user_id,
            ttl=ttl or self.default_ttl
        )
        
        with self._lock:
            # Check capacity
            while len(self._cache) >= self.max_entries:
                # Evict oldest (first item)
                evicted_key = next(iter(self._cache))
                del self._cache[evicted_key]
                self.stats["evictions"] += 1
            
            self._cache[query_hash] = entry
        
        # Persist if enabled
        if self.cache_dir:
            self._persist_entry(entry)
        
        print(f"💾 Cache SET: {query[:50]}... (ttl: {entry.ttl}s)")
        return entry
    
    def invalidate(self, user_id: str = "", pattern: str = None):
        """
        Invalidate cache entries
        
        Args:
            user_id: Invalidate all entries for user (empty = all)
            pattern: Invalidate entries matching pattern
        """
        with self._lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                if user_id and entry.user_id != user_id:
                    continue
                if pattern and pattern.lower() not in entry.query.lower():
                    continue
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            print(f"🗑️ Cache invalidated: {len(keys_to_remove)} entries")
    
    def invalidate_on_data_change(self, user_id: str):
        """
        Called when user uploads new data - invalidates their cache
        """
        self.invalidate(user_id=user_id)
        print(f"🔄 User cache invalidated due to data change: {user_id}")
    
    def _semantic_lookup(self, query: str, user_id: str) -> Optional[CacheEntry]:
        """
        Find semantically similar cached query
        Uses embedding similarity with threshold
        """
        if not self._cache:
            return None
        
        try:
            from core.llm import embed_text
            import numpy as np
            
            query_embedding = embed_text(query)
            if query_embedding is None:
                return None
            
            best_match = None
            best_similarity = 0.0
            similarity_threshold = 0.92  # High threshold for cache
            
            for key, entry in self._cache.items():
                # Skip expired or different user
                if time.time() - entry.timestamp >= entry.ttl:
                    continue
                if user_id and entry.user_id != user_id:
                    continue
                
                # Get embedding for cached query
                cached_embedding = embed_text(entry.query)
                if cached_embedding is None:
                    continue
                
                # Cosine similarity
                similarity = np.dot(query_embedding, cached_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
                )
                
                if similarity > similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry
            
            if best_match:
                print(f"🔍 Semantic cache match (sim={best_similarity:.3f}): {best_match.query[:30]}...")
                best_match.hit_count += 1
                return best_match
                
        except Exception as e:
            print(f"⚠️ Semantic lookup error: {e}")
        
        return None
    
    def _load_persistent_cache(self):
        """Load cache from disk"""
        if not self.cache_dir:
            return
        
        cache_file = Path(self.cache_dir) / "query_cache.json"
        if not cache_file.exists():
            return
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            current_time = time.time()
            loaded = 0
            
            for entry_data in data.get("entries", []):
                entry = CacheEntry(**entry_data)
                
                # Skip expired entries
                if current_time - entry.timestamp >= entry.ttl:
                    continue
                
                self._cache[entry.query_hash] = entry
                loaded += 1
            
            print(f"📂 Loaded {loaded} cache entries from disk")
            
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
    
    def _persist_entry(self, entry: CacheEntry):
        """Save cache to disk"""
        if not self.cache_dir:
            return
        
        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "query_cache.json"
        
        try:
            # Load existing
            existing = []
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    existing = json.load(f).get("entries", [])
            
            # Update or add
            updated = False
            for i, e in enumerate(existing):
                if e.get("query_hash") == entry.query_hash:
                    existing[i] = asdict(entry)
                    updated = True
                    break
            
            if not updated:
                existing.append(asdict(entry))
            
            # Save
            with open(cache_file, 'w') as f:
                json.dump({"entries": existing, "updated": time.time()}, f)
                
        except Exception as e:
            print(f"⚠️ Error persisting cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        total = self.stats["hits"] + self.stats["misses"]
        if total > 0:
            hit_rate = self.stats["hits"] / total * 100
        
        return {
            **self.stats,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self._cache),
            "max_entries": self.max_entries
        }


# Global cache instance
_cache_instance: Optional[QueryCache] = None


def get_cache(cache_dir: Optional[Path] = None) -> QueryCache:
    """Get or create global cache instance"""
    global _cache_instance
    
    if _cache_instance is None:
        from config.settings import Settings
        cache_path = cache_dir or Settings.STORAGE / "cache"
        _cache_instance = QueryCache(
            max_entries=1000,
            default_ttl=3600,  # 1 hour
            cache_dir=cache_path,
            enable_semantic_match=False  # Disable for speed
        )
    
    return _cache_instance


def cached_query(
    query: str,
    user_id: str,
    query_fn,
    ttl: int = 3600
) -> Dict[str, Any]:
    """
    Decorator-style cached query execution
    
    Args:
        query: User query
        user_id: User identifier
        query_fn: Function to call on cache miss (returns dict with response, route, sources)
        ttl: Cache TTL in seconds
        
    Returns:
        Query result (from cache or fresh)
    """
    cache = get_cache()
    
    # Check cache
    cached = cache.get(query, user_id)
    if cached:
        return {
            "answer": cached.response,
            "route": cached.route,
            "sources": cached.sources,
            "cached": True,
            "cache_hits": cached.hit_count
        }
    
    # Execute query
    result = query_fn()
    
    # Cache result
    cache.set(
        query=query,
        response=result.get("answer", ""),
        route=result.get("route", "unknown"),
        sources=result.get("sources", []),
        user_id=user_id,
        ttl=ttl
    )
    
    return {**result, "cached": False}
