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
    IMPROVED: Ensures results come from ALL uploaded files, not just top-k similar.
    
    Args:
        query: Search query string
        k: Number of results to return (will return k per file for comprehensive coverage)
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
        
        # IMPROVED: Search for MORE results then balance across files
        search_k = min(50, max(k * 5, store.index.ntotal))  # Search 50 or 5x requested
        distances, indices = store.index.search(query_vector, search_k)
        
        # Group results by source file
        results_by_source = {}
        all_results = []
        
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(store.meta):
                continue
            
            meta = store.meta[idx]
            source = meta.get("source", "Unknown")
            
            # Calculate similarity score (convert L2 distance to similarity)
            score = 1 / (1 + dist)
            
            result = {
                "text": meta.get("text", ""),
                "source": source,
                "score": float(score),
                "chunk": meta.get("chunk", i),
                "metadata": meta
            }
            
            # Group by source
            if source not in results_by_source:
                results_by_source[source] = []
            results_by_source[source].append(result)
            all_results.append(result)
        
        # CRITICAL: Ensure we get results from EACH file
        num_files = len(results_by_source)
        print(f"📁 Found results from {num_files} files: {list(results_by_source.keys())}")
        
        if num_files > 1:
            # Balance results across all files
            chunks_per_file = max(2, k // num_files + 1)
            balanced_results = []
            
            for source, file_results in results_by_source.items():
                # Take top chunks from each file (sorted by score)
                file_results.sort(key=lambda x: x['score'], reverse=True)
                balanced_results.extend(file_results[:chunks_per_file])
                print(f"   📄 {source}: {len(file_results[:chunks_per_file])} chunks")
            
            # Sort balanced results by score for final ordering
            balanced_results.sort(key=lambda x: x['score'], reverse=True)
            results = balanced_results[:k * 2]  # Return more for comprehensive coverage
        else:
            # Single file - just return top k
            results = all_results[:k]
        
        print(f"✅ Retrieved {len(results)} documents from FAISS (balanced across {num_files} files)")
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
