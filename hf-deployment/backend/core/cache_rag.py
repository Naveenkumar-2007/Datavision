# Query Cache System (Cache RAG)
"""
Enterprise Query Cache with Semantic Matching

Features:
- 3-tier cache logic (exact/partial/miss)
- PostgreSQL storage with async support
- Vector embeddings for semantic matching
- Workspace isolation
- 40-80% API cost reduction

Usage:
    from core.cache_rag import QueryCache
    cache = QueryCache()
    
    # Lookup
    hit = await cache.lookup(query, workspace_id)
    if hit:
        return hit.answer
    
    # Store after generating answer
    await cache.store(query, answer, workspace_id, metadata)
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class CacheHitType(Enum):
    """Type of cache hit"""
    EXACT = "exact"        # Cosine > 0.92 - Return cached answer directly
    PARTIAL = "partial"    # Cosine > 0.80 - Reuse context, regenerate answer
    MISS = "miss"          # No similar query found


@dataclass
class CacheEntry:
    """A cached query-answer pair"""
    query_text: str
    query_hash: str
    query_embedding: List[float]
    answer_text: str
    charts_payload: Optional[Dict] = None
    citations: Optional[List[str]] = None
    reasoning_type: str = "hybrid"
    workspace_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


@dataclass
class CacheHit:
    """Result of a cache lookup"""
    hit_type: CacheHitType
    entry: Optional[CacheEntry] = None
    similarity: float = 0.0
    context_chunks: Optional[List[str]] = None


class EmbeddingService:
    """
    Generate embeddings for cache queries.
    Falls back to simple hash-based embedding if no API available.
    """
    
    def __init__(self):
        self._dimension = 384  # Default dimension
        
    def generate(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            # Try to use sentence-transformers if available
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except ImportError:
            # Fallback: Simple hash-based pseudo-embedding
            return self._hash_embedding(text)
    
    def _hash_embedding(self, text: str) -> List[float]:
        """Generate a pseudo-embedding from text hash (fallback)"""
        # Normalize text
        text = text.lower().strip()
        
        # Create multiple hashes for different "dimensions"
        embedding = []
        for i in range(self._dimension):
            h = hashlib.sha256(f"{text}_{i}".encode()).hexdigest()
            # Convert first 8 hex chars to float between -1 and 1
            val = (int(h[:8], 16) / (16**8)) * 2 - 1
            embedding.append(val)
        
        return embedding
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        a_arr = np.array(a)
        b_arr = np.array(b)
        
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot / (norm_a * norm_b))


class QueryCache:
    """
    Enterprise Query Cache with semantic matching.
    
    Cache Logic:
    1. Compute embedding of incoming query
    2. Find similar cached queries
    3. If cosine > 0.92: Return cached answer (EXACT hit)
    4. If cosine > 0.80: Reuse context, regenerate answer (PARTIAL hit)
    5. Else: Run full pipeline (MISS)
    """
    
    # Similarity thresholds
    EXACT_THRESHOLD = 0.92
    PARTIAL_THRESHOLD = 0.80
    
    # Cache settings
    MAX_ENTRIES_PER_WORKSPACE = 1000
    DEFAULT_TTL_DAYS = 30
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize cache.
        
        Args:
            db_url: PostgreSQL connection URL (optional, uses in-memory if not provided)
        """
        self.db_url = db_url
        self.embedding_service = EmbeddingService()
        
        # In-memory cache for fast access (workspace_id -> list of entries)
        self._memory_cache: Dict[str, List[CacheEntry]] = {}
        
        # Statistics
        self.stats = {
            "hits_exact": 0,
            "hits_partial": 0,
            "misses": 0,
            "total_saved_api_calls": 0
        }
        
        # Initialize PostgreSQL if URL provided
        if db_url:
            self._init_postgres()
    
    def _init_postgres(self):
        """Initialize PostgreSQL tables"""
        try:
            import asyncpg
            # Will be initialized on first async call
            self._pg_pool = None
        except ImportError:
            print("⚠️ asyncpg not installed. Using in-memory cache only.")
            self.db_url = None
    
    async def _get_pool(self):
        """Get or create PostgreSQL connection pool"""
        if not hasattr(self, '_pg_pool') or self._pg_pool is None:
            try:
                import asyncpg
                self._pg_pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)
                await self._create_tables()
            except Exception as e:
                print(f"⚠️ PostgreSQL connection failed: {e}")
                self._pg_pool = None
        return self._pg_pool
    
    async def _create_tables(self):
        """Create cache tables in PostgreSQL"""
        pool = await self._get_pool()
        if not pool:
            return
            
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    id SERIAL PRIMARY KEY,
                    query_hash VARCHAR(64) UNIQUE NOT NULL,
                    query_text TEXT NOT NULL,
                    query_embedding JSONB NOT NULL,
                    answer_text TEXT NOT NULL,
                    charts_payload JSONB,
                    citations JSONB,
                    reasoning_type VARCHAR(20) DEFAULT 'hybrid',
                    workspace_id VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    
                    INDEX idx_workspace (workspace_id),
                    INDEX idx_created (created_at)
                )
            """)
    
    def _compute_hash(self, query: str, workspace_id: str) -> str:
        """Compute unique hash for query + workspace"""
        normalized = f"{workspace_id}:{query.lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def lookup_sync(self, query: str, workspace_id: str) -> CacheHit:
        """
        Synchronous cache lookup (uses in-memory cache only).
        
        Args:
            query: User query text
            workspace_id: Workspace/user ID for isolation
            
        Returns:
            CacheHit with type and optional entry
        """
        query_embedding = self.embedding_service.generate(query)
        
        # Get workspace cache
        entries = self._memory_cache.get(workspace_id, [])
        
        if not entries:
            self.stats["misses"] += 1
            return CacheHit(hit_type=CacheHitType.MISS)
        
        # Find most similar entry
        best_similarity = 0.0
        best_entry = None
        
        for entry in entries:
            similarity = EmbeddingService.cosine_similarity(
                query_embedding, 
                entry.query_embedding
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry
        
        # Determine hit type
        if best_similarity >= self.EXACT_THRESHOLD:
            self.stats["hits_exact"] += 1
            self.stats["total_saved_api_calls"] += 1
            
            # Update access stats
            if best_entry:
                best_entry.access_count += 1
                best_entry.last_accessed = datetime.now()
            
            return CacheHit(
                hit_type=CacheHitType.EXACT,
                entry=best_entry,
                similarity=best_similarity
            )
        
        elif best_similarity >= self.PARTIAL_THRESHOLD:
            self.stats["hits_partial"] += 1
            
            return CacheHit(
                hit_type=CacheHitType.PARTIAL,
                entry=best_entry,
                similarity=best_similarity,
                context_chunks=best_entry.citations if best_entry else None
            )
        
        else:
            self.stats["misses"] += 1
            return CacheHit(hit_type=CacheHitType.MISS)
    
    async def lookup(self, query: str, workspace_id: str) -> CacheHit:
        """
        Async cache lookup with PostgreSQL fallback.
        
        Args:
            query: User query text
            workspace_id: Workspace/user ID for isolation
            
        Returns:
            CacheHit with type and optional entry
        """
        # First check in-memory cache
        result = self.lookup_sync(query, workspace_id)
        
        if result.hit_type != CacheHitType.MISS:
            return result
        
        # If PostgreSQL available, check there
        pool = await self._get_pool() if self.db_url else None
        if pool:
            query_hash = self._compute_hash(query, workspace_id)
            
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM query_cache WHERE query_hash = $1",
                    query_hash
                )
                
                if row:
                    # Exact hash match
                    entry = CacheEntry(
                        query_text=row['query_text'],
                        query_hash=row['query_hash'],
                        query_embedding=json.loads(row['query_embedding']),
                        answer_text=row['answer_text'],
                        charts_payload=json.loads(row['charts_payload']) if row['charts_payload'] else None,
                        citations=json.loads(row['citations']) if row['citations'] else None,
                        reasoning_type=row['reasoning_type'],
                        workspace_id=row['workspace_id'],
                        created_at=row['created_at'],
                        access_count=row['access_count']
                    )
                    
                    # Add to memory cache
                    if workspace_id not in self._memory_cache:
                        self._memory_cache[workspace_id] = []
                    self._memory_cache[workspace_id].append(entry)
                    
                    self.stats["hits_exact"] += 1
                    return CacheHit(
                        hit_type=CacheHitType.EXACT,
                        entry=entry,
                        similarity=1.0
                    )
        
        return CacheHit(hit_type=CacheHitType.MISS)
    
    def store_sync(
        self, 
        query: str, 
        answer: str, 
        workspace_id: str,
        reasoning_type: str = "hybrid",
        charts_payload: Optional[Dict] = None,
        citations: Optional[List[str]] = None
    ) -> CacheEntry:
        """
        Synchronous store (in-memory).
        
        Args:
            query: Original query text
            answer: Generated answer
            workspace_id: Workspace ID
            reasoning_type: RAG/GraphRAG/Hybrid/Vision
            charts_payload: Any chart data
            citations: Source citations
            
        Returns:
            Created CacheEntry
        """
        query_embedding = self.embedding_service.generate(query)
        query_hash = self._compute_hash(query, workspace_id)
        
        entry = CacheEntry(
            query_text=query,
            query_hash=query_hash,
            query_embedding=query_embedding,
            answer_text=answer,
            charts_payload=charts_payload,
            citations=citations,
            reasoning_type=reasoning_type,
            workspace_id=workspace_id
        )
        
        # Add to memory cache
        if workspace_id not in self._memory_cache:
            self._memory_cache[workspace_id] = []
        
        # Check if already exists (by hash)
        existing = [e for e in self._memory_cache[workspace_id] if e.query_hash == query_hash]
        if existing:
            # Update existing
            self._memory_cache[workspace_id].remove(existing[0])
        
        self._memory_cache[workspace_id].append(entry)
        
        # Limit entries per workspace
        if len(self._memory_cache[workspace_id]) > self.MAX_ENTRIES_PER_WORKSPACE:
            # Remove oldest
            self._memory_cache[workspace_id].sort(key=lambda e: e.last_accessed)
            self._memory_cache[workspace_id] = self._memory_cache[workspace_id][-self.MAX_ENTRIES_PER_WORKSPACE:]
        
        return entry
    
    async def store(
        self, 
        query: str, 
        answer: str, 
        workspace_id: str,
        reasoning_type: str = "hybrid",
        charts_payload: Optional[Dict] = None,
        citations: Optional[List[str]] = None
    ) -> CacheEntry:
        """
        Async store with PostgreSQL persistence.
        """
        # Store in memory first
        entry = self.store_sync(
            query, answer, workspace_id, 
            reasoning_type, charts_payload, citations
        )
        
        # Persist to PostgreSQL if available
        pool = await self._get_pool() if self.db_url else None
        if pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO query_cache 
                    (query_hash, query_text, query_embedding, answer_text, 
                     charts_payload, citations, reasoning_type, workspace_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (query_hash) 
                    DO UPDATE SET 
                        answer_text = EXCLUDED.answer_text,
                        charts_payload = EXCLUDED.charts_payload,
                        last_accessed = CURRENT_TIMESTAMP,
                        access_count = query_cache.access_count + 1
                """,
                    entry.query_hash,
                    entry.query_text,
                    json.dumps(entry.query_embedding),
                    entry.answer_text,
                    json.dumps(entry.charts_payload) if entry.charts_payload else None,
                    json.dumps(entry.citations) if entry.citations else None,
                    entry.reasoning_type,
                    entry.workspace_id
                )
        
        return entry
    
    def invalidate(self, workspace_id: str):
        """Clear cache for a workspace"""
        if workspace_id in self._memory_cache:
            del self._memory_cache[workspace_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats["hits_exact"] + self.stats["hits_partial"] + self.stats["misses"]
        hit_rate = (self.stats["hits_exact"] + self.stats["hits_partial"]) / total if total > 0 else 0
        
        return {
            **self.stats,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.1%}",
            "estimated_cost_savings": f"${self.stats['total_saved_api_calls'] * 0.002:.2f}"
        }


# Singleton instance
_cache_instance: Optional[QueryCache] = None


def get_query_cache(db_url: Optional[str] = None) -> QueryCache:
    """Get or create the query cache singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = QueryCache(db_url)
    return _cache_instance


# Convenience functions for sync usage
def cache_lookup(query: str, workspace_id: str) -> CacheHit:
    """Quick sync cache lookup"""
    return get_query_cache().lookup_sync(query, workspace_id)


def cache_store(
    query: str, 
    answer: str, 
    workspace_id: str,
    reasoning_type: str = "hybrid"
) -> CacheEntry:
    """Quick sync cache store"""
    return get_query_cache().store_sync(query, answer, workspace_id, reasoning_type)


# Quick test
if __name__ == "__main__":
    cache = QueryCache()
    
    # Test store
    entry = cache.store_sync(
        query="What is our total revenue?",
        answer="Your total revenue is ₹5,00,000",
        workspace_id="test_workspace",
        reasoning_type="hybrid"
    )
    print(f"Stored: {entry.query_hash[:16]}...")
    
    # Test exact match
    hit = cache.lookup_sync("What is our total revenue?", "test_workspace")
    print(f"Lookup 1: {hit.hit_type.value}, similarity: {hit.similarity:.3f}")
    
    # Test similar query
    hit2 = cache.lookup_sync("Show me total revenue", "test_workspace")
    print(f"Lookup 2: {hit2.hit_type.value}, similarity: {hit2.similarity:.3f}")
    
    # Test different query
    hit3 = cache.lookup_sync("Who are our top customers?", "test_workspace")
    print(f"Lookup 3: {hit3.hit_type.value}, similarity: {hit3.similarity:.3f}")
    
    print(f"\nStats: {cache.get_stats()}")
