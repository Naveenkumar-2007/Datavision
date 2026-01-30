"""
MMR (Max Marginal Relevance) Search
====================================

Diversifies retrieval results to reduce redundancy.
λ * similarity(query, doc) - (1-λ) * max_similarity(doc, selected_docs)
"""

import numpy as np
from typing import List, Tuple, Dict, Any


def compute_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors"""
    if vec1 is None or vec2 is None:
        return 0.0
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def mmr_search(
    query_embedding: np.ndarray,
    document_embeddings: List[np.ndarray],
    documents: List[Dict[str, Any]],
    similarity_scores: List[float] = None,
    lambda_param: float = 0.7,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Select diverse documents using Max Marginal Relevance.
    
    Args:
        query_embedding: Embedding vector for the query
        document_embeddings: List of embedding vectors for documents
        documents: List of document dicts with 'text', 'metadata', etc.
        similarity_scores: Pre-computed similarity scores (optional)
        lambda_param: Balance between relevance (1.0) and diversity (0.0)
                      0.7 = slight preference for relevance
        k: Number of documents to select
        
    Returns:
        List of k diverse documents
    """
    if not documents:
        return []
    
    if len(documents) <= k:
        return documents
    
    # Compute similarity scores if not provided
    if similarity_scores is None:
        similarity_scores = [
            compute_similarity(query_embedding, doc_emb)
            for doc_emb in document_embeddings
        ]
    
    # Track selected and remaining indices
    selected_indices = []
    remaining_indices = list(range(len(documents)))
    
    # Convert to numpy for faster computation
    doc_embeddings_array = np.array(document_embeddings) if document_embeddings else None
    
    while len(selected_indices) < k and remaining_indices:
        best_score = float('-inf')
        best_idx = None
        
        for idx in remaining_indices:
            # Relevance to query
            relevance = similarity_scores[idx]
            
            # Compute max similarity to already selected documents
            max_redundancy = 0.0
            if selected_indices and doc_embeddings_array is not None:
                for sel_idx in selected_indices:
                    sim = compute_similarity(
                        doc_embeddings_array[idx],
                        doc_embeddings_array[sel_idx]
                    )
                    max_redundancy = max(max_redundancy, sim)
            
            # MMR score: λ * relevance - (1-λ) * max_redundancy
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_redundancy
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
        
        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
    
    # Return selected documents in order
    return [documents[idx] for idx in selected_indices]


def mmr_rerank(
    results: List[Dict[str, Any]],
    lambda_param: float = 0.7,
    k: int = 5
) -> List[Dict[str, Any]]:
    """
    Simpler MMR that works with pre-retrieved results.
    Uses text similarity (Jaccard) instead of embeddings.
    
    For use when embeddings aren't available.
    """
    if len(results) <= k:
        return results
    
    def text_similarity(text1: str, text2: str) -> float:
        """Simple Jaccard similarity between texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0
    
    selected = []
    remaining = list(results)
    
    # First, take the top result (most relevant)
    if remaining:
        selected.append(remaining.pop(0))
    
    # Then apply MMR for the rest
    while len(selected) < k and remaining:
        best_score = float('-inf')
        best_idx = -1
        
        for i, doc in enumerate(remaining):
            doc_text = doc.get('text', '') or doc.get('content', '')
            
            # Assuming results are ordered by relevance, use position as proxy
            relevance = 1.0 / (i + 2)  # Earlier = more relevant
            
            # Max similarity to selected docs
            max_sim = 0.0
            for sel_doc in selected:
                sel_text = sel_doc.get('text', '') or sel_doc.get('content', '')
                sim = text_similarity(doc_text, sel_text)
                max_sim = max(max_sim, sim)
            
            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
        
        if best_idx >= 0:
            selected.append(remaining.pop(best_idx))
    
    return selected


# Test
if __name__ == "__main__":
    # Test data
    test_docs = [
        {"text": "Revenue in Q1 was $100M", "score": 0.95},
        {"text": "Revenue in Q1 reached $100 million", "score": 0.93},  # Redundant
        {"text": "Customer count grew 20%", "score": 0.85},
        {"text": "Q1 revenue performance was strong at $100M", "score": 0.88},  # Redundant
        {"text": "New products launched in Q1", "score": 0.75},
    ]
    
    print("Original order:", [d["text"][:30] for d in test_docs])
    
    reranked = mmr_rerank(test_docs, lambda_param=0.5, k=3)
    print("After MMR:", [d["text"][:30] for d in reranked])
