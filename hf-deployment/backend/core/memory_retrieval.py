# Memory Retrieval Pipeline
"""
Enterprise Memory Retrieval Pipeline

Orchestrates retrieval from all memory layers + cache
for every query to provide maximum context to the LLM.

Pipeline:
1. Check Query Cache (exact/partial hit)
2. Pull insights from Mid-Term Memory
3. Pull entities from Long-Term Memory
4. Pull chunks from Document Memory (RAG)
5. Merge all context
6. Return unified context for LLM
7. After LLM response, store to memory + cache

Usage:
    from core.memory_retrieval import MemoryPipeline
    pipeline = MemoryPipeline()
    
    # Before LLM call
    context = pipeline.retrieve(query, workspace_id, session_id)
    
    # After LLM response
    pipeline.store_response(query, answer, workspace_id)
"""

import time
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass

from core.cache_rag import QueryCache, CacheHit, CacheHitType, get_query_cache, cache_lookup, cache_store
from core.memory_engine import MemoryEngine, MemoryLayer, get_memory_engine


@dataclass
class RetrievalResult:
    """Result from memory retrieval pipeline"""
    # Cache
    cache_hit: bool
    cache_hit_type: Optional[CacheHitType] = None
    cached_answer: Optional[str] = None
    
    # Memory context
    memory_context: str = ""
    session_context: str = ""
    insights_context: str = ""
    entities_context: str = ""
    documents_context: str = ""
    
    # Chunks for partial cache hit
    reusable_chunks: Optional[List[str]] = None
    
    # Performance
    retrieval_time_ms: float = 0
    sources: List[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []


class MemoryPipeline:
    """
    Unified Memory Retrieval Pipeline.
    
    Integrates:
    - Query Cache (Cache RAG)
    - 4-Layer Memory Engine
    
    For every query:
    1. Check cache first (fast path)
    2. Retrieve from all memory layers
    3. Merge into unified context
    4. Store response after LLM generates
    """
    
    def __init__(self, db_url: Optional[str] = None):
        self.cache = get_query_cache(db_url)
        self.memory = get_memory_engine(db_url)
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_partial": 0,
            "full_retrievals": 0,
            "avg_retrieval_ms": 0
        }
    
    def retrieve(
        self,
        query: str,
        workspace_id: str,
        session_id: Optional[str] = None,
        include_cache: bool = True,
        include_memory: bool = True
    ) -> RetrievalResult:
        """
        Main retrieval method.
        
        Args:
            query: User query text
            workspace_id: Workspace ID for isolation
            session_id: Optional session ID for short-term memory
            include_cache: Whether to check cache
            include_memory: Whether to retrieve from memory layers
            
        Returns:
            RetrievalResult with all context
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        result = RetrievalResult(cache_hit=False)
        
        # =====================================================================
        # STEP 1: Check Query Cache
        # =====================================================================
        if include_cache:
            cache_hit = self.cache.lookup_sync(query, workspace_id)
            
            if cache_hit.hit_type == CacheHitType.EXACT:
                # Fast path - return cached answer directly
                self.stats["cache_hits"] += 1
                
                result.cache_hit = True
                result.cache_hit_type = CacheHitType.EXACT
                result.cached_answer = cache_hit.entry.answer_text if cache_hit.entry else None
                result.retrieval_time_ms = (time.time() - start_time) * 1000
                
                return result
            
            elif cache_hit.hit_type == CacheHitType.PARTIAL:
                # Partial hit - reuse context but regenerate answer
                self.stats["cache_partial"] += 1
                
                result.cache_hit_type = CacheHitType.PARTIAL
                result.reusable_chunks = cache_hit.context_chunks
        
        # =====================================================================
        # STEP 2: Retrieve from Memory Layers
        # =====================================================================
        if include_memory:
            self.stats["full_retrievals"] += 1
            
            # Short-term (session)
            if session_id:
                result.session_context = self.memory.short_term.get_context(session_id)
                if result.session_context:
                    result.sources.append("session_memory")
            
            # Mid-term (insights)
            result.insights_context = self.memory.mid_term.get_context(workspace_id)
            if result.insights_context:
                result.sources.append("insights_memory")
            
            # Long-term (entities)
            result.entities_context = self.memory.long_term.get_context(workspace_id)
            if result.entities_context:
                result.sources.append("company_brain")
            
            # Document (RAG)
            result.documents_context = self.memory.document.get_context(workspace_id)
            if result.documents_context:
                result.sources.append("document_store")
            
            # Merge all context
            result.memory_context = self._merge_context(result)
        
        result.retrieval_time_ms = (time.time() - start_time) * 1000
        self._update_stats(result.retrieval_time_ms)
        
        return result
    
    def _merge_context(self, result: RetrievalResult) -> str:
        """Merge all memory context into unified string"""
        parts = []
        
        if result.session_context:
            parts.append(f"## Session Context\n{result.session_context}")
        
        if result.insights_context:
            parts.append(f"## Recent Insights\n{result.insights_context}")
        
        if result.entities_context:
            parts.append(f"## Company Knowledge\n{result.entities_context}")
        
        if result.documents_context:
            parts.append(f"## Documents\n{result.documents_context}")
        
        if result.reusable_chunks:
            chunks_str = "\n".join(result.reusable_chunks[:3])
            parts.append(f"## Previous Context\n{chunks_str}")
        
        return "\n\n".join(parts)
    
    def store_response(
        self,
        query: str,
        answer: str,
        workspace_id: str,
        session_id: Optional[str] = None,
        reasoning_type: str = "hybrid",
        charts_payload: Optional[Dict] = None,
        citations: Optional[List[str]] = None,
        insights: Optional[List[Dict]] = None,
        entities: Optional[List[Dict]] = None
    ):
        """
        Store response to cache and memory.
        
        Args:
            query: Original query
            answer: Generated answer
            workspace_id: Workspace ID
            session_id: Optional session ID
            reasoning_type: RAG/GraphRAG/Hybrid/Vision
            charts_payload: Any chart data
            citations: Source citations
            insights: Extracted insights to store
            entities: Extracted entities to store
        """
        # Store to cache
        self.cache.store_sync(
            query=query,
            answer=answer,
            workspace_id=workspace_id,
            reasoning_type=reasoning_type,
            charts_payload=charts_payload,
            citations=citations
        )
        
        # Store to session memory
        if session_id:
            self.memory.store_message(workspace_id, session_id, "user", query)
            self.memory.store_message(workspace_id, session_id, "assistant", answer[:500])
        
        # Store extracted insights
        if insights:
            for insight in insights:
                self.memory.store_insight(
                    workspace_id=workspace_id,
                    insight_type=insight.get("type", "insight"),
                    data=insight
                )
        
        # Store extracted entities
        if entities:
            for entity in entities:
                self.memory.store_entity(
                    workspace_id=workspace_id,
                    entity_type=entity.get("type", "unknown"),
                    entity_id=entity.get("id", ""),
                    properties=entity
                )
    
    def _update_stats(self, retrieval_ms: float):
        """Update performance statistics"""
        total = self.stats["total_queries"]
        current_avg = self.stats["avg_retrieval_ms"]
        
        # Running average
        self.stats["avg_retrieval_ms"] = (current_avg * (total - 1) + retrieval_ms) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        total = self.stats["total_queries"]
        
        return {
            **self.stats,
            "cache_stats": self.cache.get_stats(),
            "memory_stats": {
                "short_term_sessions": len(self.memory.short_term._sessions)
            },
            "hit_rate": f"{(self.stats['cache_hits'] / total * 100):.1f}%" if total > 0 else "0%"
        }
    
    def invalidate_cache(self, workspace_id: str):
        """Invalidate cache for a workspace"""
        self.cache.invalidate(workspace_id)
    
    def clear_session(self, session_id: str):
        """Clear session memory"""
        self.memory.clear_session(session_id)


# Singleton instance
_pipeline_instance: Optional[MemoryPipeline] = None


def get_memory_pipeline(db_url: Optional[str] = None) -> MemoryPipeline:
    """Get or create the memory pipeline singleton"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MemoryPipeline(db_url)
    return _pipeline_instance


# Convenience functions for direct use in nodes.py
def memory_retrieve(query: str, workspace_id: str, session_id: Optional[str] = None) -> RetrievalResult:
    """Quick retrieval from memory pipeline"""
    return get_memory_pipeline().retrieve(query, workspace_id, session_id)


def memory_store(
    query: str,
    answer: str,
    workspace_id: str,
    session_id: Optional[str] = None,
    reasoning_type: str = "hybrid"
):
    """Quick store to memory pipeline"""
    get_memory_pipeline().store_response(query, answer, workspace_id, session_id, reasoning_type)


# Quick test
if __name__ == "__main__":
    pipeline = MemoryPipeline()
    
    # Test retrieval (cache miss)
    result1 = pipeline.retrieve("What is our total revenue?", "workspace1", "session1")
    print(f"Result 1: cache_hit={result1.cache_hit}, time={result1.retrieval_time_ms:.1f}ms")
    
    # Store a response
    pipeline.store_response(
        query="What is our total revenue?",
        answer="Your total revenue is ₹5,00,000",
        workspace_id="workspace1",
        session_id="session1",
        reasoning_type="hybrid",
        insights=[{"type": "kpi", "summary": "Revenue is ₹5,00,000"}]
    )
    
    # Test retrieval (cache hit)
    result2 = pipeline.retrieve("What is our total revenue?", "workspace1", "session1")
    print(f"Result 2: cache_hit={result2.cache_hit}, time={result2.retrieval_time_ms:.1f}ms")
    print(f"Cached answer: {result2.cached_answer[:50]}...")
    
    # Test similar query (partial hit)
    result3 = pipeline.retrieve("Show me total revenue", "workspace1", "session1")
    print(f"Result 3: cache_hit={result3.cache_hit}, type={result3.cache_hit_type}")
    
    print(f"\nStats: {pipeline.get_stats()}")
