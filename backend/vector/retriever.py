"""
Vector retrieval module - REAL implementation using FAISS
Retrieves relevant documents from user's vector store
"""

from vector.store_faiss import FaissStore
from core.llm import embed_text
import numpy as np


def retrieve(query: str, k: int = 5, user_id: str = None):
    """
    Retrieve relevant documents from FAISS vector store.
    
    Args:
        query: Search query string
        k: Number of results to return
        user_id: User identifier for per-user store
        
    Returns:
        List of document dicts with text, source, and score
    """
    if not user_id:
        print("⚠️ No user_id provided to retrieve()")
        return []
    
    try:
        # Load user's FAISS store
        store = FaissStore.load_or_create(user_id=user_id, fresh=False)
        
        if store.index.ntotal == 0:
            print(f"⚠️ FAISS store for {user_id} is empty (0 vectors)")
            return []
        
        print(f"📚 Searching FAISS store with {store.index.ntotal} vectors for user {user_id}")
        
        # Embed the query
        query_embedding = embed_text(query)
        query_vector = np.array([query_embedding], dtype="float32")
        
        # Search FAISS index
        distances, indices = store.index.search(query_vector, min(k, store.index.ntotal))
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(store.meta):
                continue
            
            meta = store.meta[idx]
            
            # Calculate similarity score (convert L2 distance to similarity)
            # Lower distance = higher similarity
            score = 1 / (1 + dist)  # Normalize to 0-1 range
            
            result = {
                "text": meta.get("text", ""),
                "source": meta.get("source", "Unknown"),
                "score": float(score),
                "chunk": meta.get("chunk", i),
                "metadata": meta
            }
            results.append(result)
        
        print(f"✅ Retrieved {len(results)} documents from FAISS")
        return results
        
    except Exception as e:
        print(f"⚠️ Error in retrieve(): {e}")
        import traceback
        traceback.print_exc()
        return []


def hybrid_retrieve(query: str, k: int = 5, user_id: str = None):
    """
    Hybrid retrieval combining FAISS vector search with keyword matching.
    Falls back to standard retrieve if hybrid index not available.
    
    Args:
        query: Search query string
        k: Number of results to return
        user_id: User identifier
        
    Returns:
        List of document dicts
    """
    # For now, use standard FAISS retrieval
    # TODO: Implement BM25 keyword matching + score fusion
    return retrieve(query, k=k, user_id=user_id)
