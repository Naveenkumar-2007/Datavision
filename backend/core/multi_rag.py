"""
Multi-RAG System
================

Multi-RAG uses multiple retrieval sources simultaneously:
- Vector Store (semantic search)
- Knowledge Graph (relationship queries)
- SQL Database (structured queries)
- Full-text Search (keyword matching)

Then FUSES results using Reciprocal Rank Fusion (RRF).
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio


class RetrievalSource(Enum):
    """Types of retrieval sources"""
    VECTOR = "vector"           # Vector/semantic search
    GRAPH = "graph"             # Knowledge graph
    SQL = "sql"                 # SQL database
    FULLTEXT = "fulltext"       # Full-text/keyword search
    WEB = "web"                 # Web search fallback


@dataclass
class RetrievalResult:
    """Result from a single retrieval source"""
    source: RetrievalSource
    documents: List[Dict[str, Any]]
    scores: List[float]
    metadata: Dict[str, Any] = None


class MultiRAG:
    """
    Multi-RAG System - Retrieves from multiple sources and fuses results.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.sources: Dict[RetrievalSource, callable] = {}
        self.weights = {
            RetrievalSource.VECTOR: 1.0,
            RetrievalSource.GRAPH: 0.8,
            RetrievalSource.SQL: 1.2,  # Higher weight for structured data
            RetrievalSource.FULLTEXT: 0.6,
            RetrievalSource.WEB: 0.4,
        }
    
    def register_source(self, source_type: RetrievalSource, retrieval_func):
        """Register a retrieval source"""
        self.sources[source_type] = retrieval_func
        
    def set_weight(self, source_type: RetrievalSource, weight: float):
        """Set weight for a source in fusion"""
        self.weights[source_type] = weight
    
    async def retrieve_from_source(
        self, 
        source: RetrievalSource, 
        query: str, 
        k: int = 5
    ) -> RetrievalResult:
        """Retrieve from a single source"""
        if source not in self.sources:
            return RetrievalResult(
                source=source,
                documents=[],
                scores=[],
                metadata={"error": "Source not registered"}
            )
        
        try:
            retrieval_func = self.sources[source]
            docs, scores = await retrieval_func(self.user_id, query, k)
            return RetrievalResult(
                source=source,
                documents=docs,
                scores=scores,
                metadata={"success": True}
            )
        except Exception as e:
            return RetrievalResult(
                source=source,
                documents=[],
                scores=[],
                metadata={"error": str(e)}
            )
    
    async def retrieve_parallel(
        self, 
        query: str, 
        sources: List[RetrievalSource] = None,
        k: int = 5
    ) -> List[RetrievalResult]:
        """Retrieve from multiple sources in parallel"""
        if sources is None:
            sources = list(self.sources.keys())
        
        tasks = [
            self.retrieve_from_source(source, query, k)
            for source in sources
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    def reciprocal_rank_fusion(
        self, 
        results: List[RetrievalResult],
        k_constant: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Fuse results using Reciprocal Rank Fusion (RRF).
        
        RRF score = Σ (1 / (k + rank_i)) * weight_i
        
        This gives higher scores to documents that appear highly ranked
        across multiple sources.
        """
        doc_scores: Dict[str, float] = {}
        doc_data: Dict[str, Dict[str, Any]] = {}
        
        for result in results:
            weight = self.weights.get(result.source, 1.0)
            
            for rank, doc in enumerate(result.documents):
                # Create unique document ID
                doc_id = doc.get('id') or doc.get('text', '')[:100]
                
                # Calculate RRF score
                rrf_score = weight * (1.0 / (k_constant + rank + 1))
                
                if doc_id in doc_scores:
                    doc_scores[doc_id] += rrf_score
                else:
                    doc_scores[doc_id] = rrf_score
                    doc_data[doc_id] = doc
                    
                # Track which sources found this doc
                if 'sources' not in doc_data[doc_id]:
                    doc_data[doc_id]['sources'] = []
                doc_data[doc_id]['sources'].append(result.source.value)
        
        # Sort by fused score
        sorted_docs = sorted(
            [(doc_id, score) for doc_id, score in doc_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return documents with fused scores
        fused_results = []
        for doc_id, score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc['rrf_score'] = score
            fused_results.append(doc)
        
        return fused_results
    
    async def retrieve_and_fuse(
        self, 
        query: str, 
        sources: List[RetrievalSource] = None,
        k: int = 5,
        top_n: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Main entry point - retrieve from all sources and fuse.
        
        Returns:
            (fused_documents, metadata)
        """
        # Retrieve from all sources in parallel
        results = await self.retrieve_parallel(query, sources, k)
        
        # Log what we got from each source
        metadata = {
            "sources_used": [],
            "docs_per_source": {}
        }
        
        for result in results:
            source_name = result.source.value
            doc_count = len(result.documents)
            metadata["sources_used"].append(source_name)
            metadata["docs_per_source"][source_name] = doc_count
            print(f"📚 {source_name}: {doc_count} docs")
        
        # Fuse results
        fused = self.reciprocal_rank_fusion(results)
        
        # Return top N
        metadata["total_fused"] = len(fused)
        print(f"🔀 RRF Fusion: {len(fused)} unique docs → top {top_n}")
        
        return fused[:top_n], metadata


def detect_best_sources(query: str) -> List[RetrievalSource]:
    """
    Intelligently detect which sources to use based on query.
    """
    query_lower = query.lower()
    sources = []
    
    # Always use vector search
    sources.append(RetrievalSource.VECTOR)
    
    # Use SQL for aggregations
    if any(kw in query_lower for kw in ['total', 'sum', 'count', 'average', 'max', 'min', 'how many']):
        sources.append(RetrievalSource.SQL)
    
    # Use graph for relationships
    if any(kw in query_lower for kw in ['who', 'reports to', 'works with', 'related', 'connected', 'relationship']):
        sources.append(RetrievalSource.GRAPH)
    
    # Use fulltext for exact matches
    if '"' in query or any(kw in query_lower for kw in ['exact', 'specific', 'named']):
        sources.append(RetrievalSource.FULLTEXT)
    
    return sources


def format_multi_rag_context(
    fused_docs: List[Dict[str, Any]], 
    metadata: Dict[str, Any]
) -> str:
    """Format fused results into context for LLM"""
    context = f"## Retrieved from {len(metadata['sources_used'])} sources:\n"
    context += f"Sources: {', '.join(metadata['sources_used'])}\n\n"
    
    for i, doc in enumerate(fused_docs[:10]):
        text = doc.get('text', '') or doc.get('content', '')
        sources = doc.get('sources', ['unknown'])
        score = doc.get('rrf_score', 0)
        
        context += f"### Document {i+1} (RRF: {score:.3f}, from: {', '.join(sources)})\n"
        context += f"{text[:500]}\n\n"
    
    return context


# Test
if __name__ == "__main__":
    import asyncio
    
    async def mock_vector_search(user_id, query, k):
        return [{"text": "Vector result 1", "id": "v1"}, {"text": "Vector result 2", "id": "v2"}], [0.9, 0.7]
    
    async def mock_sql_search(user_id, query, k):
        return [{"text": "SQL result 1", "id": "s1"}, {"text": "Vector result 1", "id": "v1"}], [0.95, 0.8]
    
    async def test():
        multi = MultiRAG(user_id="test")
        multi.register_source(RetrievalSource.VECTOR, mock_vector_search)
        multi.register_source(RetrievalSource.SQL, mock_sql_search)
        
        fused, meta = await multi.retrieve_and_fuse("What is total salary?")
        
        print("\nFused Results:")
        for doc in fused:
            print(f"  {doc['id']}: RRF={doc['rrf_score']:.3f}, sources={doc['sources']}")
    
    asyncio.run(test())
