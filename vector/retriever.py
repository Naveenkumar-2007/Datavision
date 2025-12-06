# Vector retriever module
"""
Retrieval module with support for:
1. Basic FAISS semantic search
2. Hybrid search (BM25 + FAISS) for better accuracy

Default: Hybrid search for business queries
"""
from typing import List, Dict, Any, Optional
from core.llm import embed_text
from vector.store_faiss import FaissStore


def retrieve(
    query: str,
    k: int = 5,
    user_id: str = "user_001",
    use_hybrid: bool = True,
    alpha: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant documents for a query
    
    Args:
        query: Search query string
        k: Number of results to return (default: 5)
        user_id: User ID for per-user FAISS index (default: "user_001")
        use_hybrid: Use hybrid search if available (default: True)
        alpha: Semantic weight for hybrid search (0-1, default: 0.6)
    
    Returns:
        List of documents with text and metadata
    """
    # Try hybrid search first (better accuracy)
    if use_hybrid:
        try:
            from vector.hybrid_search import hybrid_retrieve
            results = hybrid_retrieve(query, k=k, user_id=user_id, alpha=alpha)
            if results:
                return results
        except ImportError:
            print("⚠️ Hybrid search not available, using basic FAISS")
        except Exception as e:
            print(f"⚠️ Hybrid search error: {e}, falling back to FAISS")
    
    # Fallback to basic FAISS search
    store = FaissStore.load_or_create(user_id=user_id)
    emb = embed_text(query)
    return store.search(emb, k=k)


def retrieve_with_rerank(
    query: str,
    k: int = 5,
    user_id: str = "user_001",
    rerank_top: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve with reranking for better precision
    
    Retrieves more documents, then reranks by relevance.
    
    Args:
        query: Search query
        k: Final number of results
        user_id: User identifier
        rerank_top: Number to retrieve before reranking
        
    Returns:
        Reranked list of documents
    """
    # Get more results than needed
    candidates = retrieve(query, k=rerank_top, user_id=user_id, use_hybrid=True)
    
    if len(candidates) <= k:
        return candidates
    
    # Simple relevance reranking using query term overlap
    query_terms = set(query.lower().split())
    
    for doc in candidates:
        text = doc.get("text", "").lower()
        doc_terms = set(text.split())
        
        # Calculate overlap score
        overlap = len(query_terms & doc_terms)
        doc["rerank_score"] = overlap + doc.get("hybrid_score", 0)
    
    # Sort by combined score
    candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    
    return candidates[:k]

