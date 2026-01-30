"""
Cross-Encoder Re-ranker for RAG
================================

Uses a Cross-Encoder model to re-rank retrieved documents for better relevance.
This is more accurate than bi-encoder (FAISS) similarity because it compares
query and document together, not separately.

Model: Uses lightweight cross-encoder for production speed.
"""

import os
from typing import List, Dict, Any, Tuple
from functools import lru_cache


# Lazy load to avoid startup delays
_reranker = None
_reranker_available = False


def _get_reranker():
    """Lazy load the cross-encoder model."""
    global _reranker, _reranker_available
    
    if _reranker is not None:
        return _reranker
    
    try:
        from sentence_transformers import CrossEncoder
        
        # Get model from environment or use default
        model_name = os.getenv(
            "RERANKER_MODEL", 
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        
        print(f"🔄 Loading reranker model: {model_name}")
        _reranker = CrossEncoder(model_name, max_length=512)
        _reranker_available = True
        print(f"✅ Reranker loaded successfully")
        
        return _reranker
        
    except ImportError:
        print("⚠️ sentence-transformers not installed. Re-ranking disabled.")
        print("   Install with: pip install sentence-transformers")
        _reranker_available = False
        return None
    except Exception as e:
        print(f"⚠️ Reranker loading failed: {e}")
        _reranker_available = False
        return None


def is_reranker_available() -> bool:
    """Check if reranker is available."""
    global _reranker_available
    
    # Try to load if not attempted yet
    if _reranker is None:
        _get_reranker()
    
    return _reranker_available


def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5,
    text_key: str = "text",
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Re-rank documents using cross-encoder for better relevance.
    
    Args:
        query: The user's search query
        documents: List of document dicts (must have 'text' or text_key field)
        top_k: Number of top documents to return
        text_key: Key in document dict containing text (default: 'text')
        min_score: Minimum score threshold (0-1)
        
    Returns:
        List of top_k most relevant documents, sorted by relevance
    """
    if not documents:
        return []
    
    if len(documents) <= top_k:
        return documents
    
    reranker = _get_reranker()
    
    if reranker is None:
        # Fallback: return original order
        print("⚠️ Reranker not available, returning original order")
        return documents[:top_k]
    
    try:
        # Prepare query-document pairs
        pairs = []
        valid_indices = []
        
        for i, doc in enumerate(documents):
            text = doc.get(text_key) or doc.get('content', '')
            if text:
                pairs.append([query, text[:1000]])  # Limit text length
                valid_indices.append(i)
        
        if not pairs:
            return documents[:top_k]
        
        # Get relevance scores
        scores = reranker.predict(pairs)
        
        # Pair scores with document indices
        scored_docs = list(zip(valid_indices, scores))
        
        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Build result list
        result = []
        for idx, score in scored_docs[:top_k]:
            if score >= min_score:
                doc = documents[idx].copy()
                doc['rerank_score'] = float(score)
                result.append(doc)
        
        print(f"📊 Reranked {len(documents)} → {len(result)} docs")
        if result:
            print(f"   Top score: {result[0].get('rerank_score', 0):.3f}, "
                  f"Bottom: {result[-1].get('rerank_score', 0):.3f}")
        
        return result
        
    except Exception as e:
        print(f"⚠️ Reranking failed: {e}")
        return documents[:top_k]


def rerank_with_scores(
    query: str,
    documents: List[Dict[str, Any]],
    text_key: str = "text"
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Re-rank and return (document, score) tuples.
    Useful when you need the raw scores for further processing.
    """
    if not documents:
        return []
    
    reranker = _get_reranker()
    
    if reranker is None:
        # Fallback with dummy scores
        return [(doc, 0.5) for doc in documents]
    
    try:
        pairs = []
        for doc in documents:
            text = doc.get(text_key) or doc.get('content', '')
            pairs.append([query, text[:1000]])
        
        scores = reranker.predict(pairs)
        
        # Pair docs with scores and sort
        results = list(zip(documents, scores))
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
        
    except Exception as e:
        print(f"⚠️ Reranking with scores failed: {e}")
        return [(doc, 0.5) for doc in documents]


# Test
if __name__ == "__main__":
    # Test documents
    test_docs = [
        {"text": "The Engineering department has 50 employees."},
        {"text": "Average salary in Engineering is $85,000."},
        {"text": "Engineering uses Python and JavaScript."},
        {"text": "Sales department salary average is $65,000."},
        {"text": "Total salary budget for Engineering is $4.25M."},
    ]
    
    query = "What is the Engineering department salary?"
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    print("\nOriginal order:")
    for i, doc in enumerate(test_docs):
        print(f"  {i+1}. {doc['text'][:50]}...")
    
    print("\nAfter re-ranking:")
    reranked = rerank(query, test_docs, top_k=3)
    for i, doc in enumerate(reranked):
        score = doc.get('rerank_score', 0)
        print(f"  {i+1}. [{score:.3f}] {doc['text'][:50]}...")
