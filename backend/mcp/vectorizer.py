# MCP Vectorizer Module
"""
Embedding generation and similarity computation for MCP integration.

Features:
- Text embedding generation
- Batch embedding
- Similarity computation
- Embedding caching
"""

from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from functools import lru_cache


# Embedding cache
_embedding_cache: Dict[str, List[float]] = {}
_cache_max_size = 1000


def generate_embeddings(text: str, use_cache: bool = True) -> Dict:
    """
    Generate embeddings for text.
    
    Args:
        text: Input text to embed
        use_cache: Whether to use cached embeddings
        
    Returns:
        Embedding vector and metadata
    """
    global _embedding_cache
    
    if not text or not text.strip():
        return {
            "success": False,
            "error": "Empty text provided",
            "embedding": None
        }
    
    # Check cache
    cache_key = text[:500]  # Use first 500 chars as key
    
    if use_cache and cache_key in _embedding_cache:
        return {
            "success": True,
            "embedding": _embedding_cache[cache_key],
            "cached": True,
            "dimensions": len(_embedding_cache[cache_key])
        }
    
    try:
        from core.llm import embed_text
        
        embedding = embed_text(text)
        
        if embedding is None:
            return {
                "success": False,
                "error": "Embedding generation failed",
                "embedding": None
            }
        
        # Convert to list if numpy array
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        
        # Cache the result
        if use_cache:
            if len(_embedding_cache) >= _cache_max_size:
                # Remove oldest entries
                oldest = list(_embedding_cache.keys())[:100]
                for k in oldest:
                    del _embedding_cache[k]
            _embedding_cache[cache_key] = embedding
        
        return {
            "success": True,
            "embedding": embedding,
            "cached": False,
            "dimensions": len(embedding)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "embedding": None
        }


def batch_embed(
    texts: List[str],
    batch_size: int = 10,
    use_cache: bool = True
) -> Dict:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch
        use_cache: Whether to use cached embeddings
        
    Returns:
        List of embeddings with metadata
    """
    if not texts:
        return {
            "success": False,
            "error": "No texts provided",
            "embeddings": []
        }
    
    embeddings = []
    errors = []
    cached_count = 0
    
    for i, text in enumerate(texts):
        result = generate_embeddings(text, use_cache=use_cache)
        
        if result["success"]:
            embeddings.append({
                "index": i,
                "text_preview": text[:50],
                "embedding": result["embedding"],
                "cached": result.get("cached", False)
            })
            if result.get("cached"):
                cached_count += 1
        else:
            embeddings.append({
                "index": i,
                "text_preview": text[:50],
                "embedding": None,
                "error": result.get("error")
            })
            errors.append(f"Text {i}: {result.get('error')}")
    
    return {
        "success": len(errors) == 0,
        "embeddings": embeddings,
        "total": len(texts),
        "successful": len(texts) - len(errors),
        "cached_hits": cached_count,
        "errors": errors if errors else None
    }


def compute_similarity(
    embedding1: List[float],
    embedding2: List[float],
    method: str = "cosine"
) -> Dict:
    """
    Compute similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        method: "cosine", "euclidean", "dot"
        
    Returns:
        Similarity score and metadata
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        if len(vec1) != len(vec2):
            return {
                "success": False,
                "error": f"Dimension mismatch: {len(vec1)} vs {len(vec2)}",
                "similarity": None
            }
        
        if method == "cosine":
            # Cosine similarity
            dot = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                similarity = 0.0
            else:
                similarity = dot / (norm1 * norm2)
        
        elif method == "euclidean":
            # Euclidean distance (converted to similarity)
            distance = np.linalg.norm(vec1 - vec2)
            similarity = 1.0 / (1.0 + distance)
        
        elif method == "dot":
            # Dot product
            similarity = float(np.dot(vec1, vec2))
        
        else:
            return {
                "success": False,
                "error": f"Unknown method: {method}",
                "similarity": None
            }
        
        return {
            "success": True,
            "similarity": float(similarity),
            "method": method,
            "dimensions": len(vec1)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "similarity": None
        }


def find_most_similar(
    query_embedding: List[float],
    candidate_embeddings: List[Dict],
    top_k: int = 5,
    threshold: float = 0.0
) -> Dict:
    """
    Find most similar embeddings from candidates.
    
    Args:
        query_embedding: Query vector
        candidate_embeddings: List of {"id": str, "embedding": List[float]}
        top_k: Number of top results
        threshold: Minimum similarity threshold
        
    Returns:
        Top k most similar candidates
    """
    try:
        query_vec = np.array(query_embedding)
        
        similarities = []
        
        for candidate in candidate_embeddings:
            cand_vec = np.array(candidate["embedding"])
            
            # Cosine similarity
            dot = np.dot(query_vec, cand_vec)
            norm_q = np.linalg.norm(query_vec)
            norm_c = np.linalg.norm(cand_vec)
            
            if norm_q > 0 and norm_c > 0:
                sim = dot / (norm_q * norm_c)
            else:
                sim = 0.0
            
            if sim >= threshold:
                similarities.append({
                    "id": candidate.get("id", "unknown"),
                    "similarity": float(sim),
                    "metadata": candidate.get("metadata", {})
                })
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "success": True,
            "results": similarities[:top_k],
            "total_candidates": len(candidate_embeddings),
            "above_threshold": len(similarities)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }


def compute_centroid(embeddings: List[List[float]]) -> Dict:
    """
    Compute centroid of multiple embeddings.
    
    Args:
        embeddings: List of embedding vectors
        
    Returns:
        Centroid vector
    """
    try:
        if not embeddings:
            return {
                "success": False,
                "error": "No embeddings provided",
                "centroid": None
            }
        
        vectors = np.array(embeddings)
        centroid = np.mean(vectors, axis=0)
        
        return {
            "success": True,
            "centroid": centroid.tolist(),
            "num_vectors": len(embeddings),
            "dimensions": len(centroid)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "centroid": None
        }


def clear_embedding_cache() -> Dict:
    """Clear the embedding cache"""
    global _embedding_cache
    count = len(_embedding_cache)
    _embedding_cache = {}
    
    return {
        "success": True,
        "cleared_entries": count
    }


def get_cache_stats() -> Dict:
    """Get embedding cache statistics"""
    global _embedding_cache
    
    return {
        "entries": len(_embedding_cache),
        "max_size": _cache_max_size,
        "utilization": len(_embedding_cache) / _cache_max_size
    }
