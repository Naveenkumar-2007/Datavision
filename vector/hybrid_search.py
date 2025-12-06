# Hybrid Search Module - BM25 + FAISS Semantic Search
"""
Combines keyword-based BM25 with semantic FAISS search
for best accuracy on business queries.

BM25: Good for exact terms like "invoice #12345", "Q2 2024"
FAISS: Good for semantic meaning like "revenue decline" → "sales dropped"
"""

import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from collections import defaultdict
import re


class HybridSearcher:
    """
    Enterprise Hybrid Search combining BM25 + FAISS
    
    Weight balancing:
    - alpha = 0.5: Equal weight (balanced)
    - alpha = 0.7: More semantic (good for business insights)
    - alpha = 0.3: More keyword (good for exact lookups)
    """
    
    def __init__(self, faiss_store, alpha: float = 0.6):
        """
        Args:
            faiss_store: FaissStore instance with loaded vectors
            alpha: Weight for semantic search (1-alpha for BM25)
        """
        self.faiss_store = faiss_store
        self.alpha = alpha
        self.bm25 = None
        self.tokenized_corpus = []
        self._build_bm25_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        # Remove very short tokens
        tokens = [t for t in tokens if len(t) > 1]
        return tokens
    
    def _build_bm25_index(self):
        """Build BM25 index from FAISS metadata"""
        if not self.faiss_store.meta:
            print("⚠️ No metadata for BM25 index")
            return
        
        self.tokenized_corpus = []
        for meta in self.faiss_store.meta:
            text = meta.get('text', '')
            tokens = self._tokenize(text)
            self.tokenized_corpus.append(tokens)
        
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            print(f"✅ BM25 index built: {len(self.tokenized_corpus)} documents")
    
    def rebuild_index(self):
        """Rebuild BM25 index after new documents added"""
        self._build_bm25_index()
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 and FAISS scores
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of results with combined scores
        """
        if not self.faiss_store.meta:
            print("⚠️ No documents to search")
            return []
        
        # 1. BM25 keyword search
        bm25_scores = self._bm25_search(query, k * 2)
        
        # 2. FAISS semantic search
        faiss_scores = self._faiss_search(query, k * 2)
        
        # 3. Combine scores with reciprocal rank fusion
        combined = self._reciprocal_rank_fusion(bm25_scores, faiss_scores, k)
        
        return combined
    
    def _bm25_search(self, query: str, k: int) -> Dict[int, float]:
        """BM25 keyword search"""
        scores = {}
        
        if not self.bm25:
            return scores
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return scores
        
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Normalize scores to [0, 1]
        max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1
        
        for idx, score in enumerate(bm25_scores):
            if score > 0:
                scores[idx] = score / max_score
        
        return scores
    
    def _faiss_search(self, query: str, k: int) -> Dict[int, float]:
        """FAISS semantic search with scores"""
        scores = {}
        
        from core.llm import embed_text
        query_vector = embed_text(query)
        
        if query_vector is None:
            return scores
        
        query_vector = np.array([query_vector], dtype="float32")
        
        actual_k = min(k, self.faiss_store.index.ntotal)
        if actual_k == 0:
            return scores
        
        distances, ids = self.faiss_store.index.search(query_vector, actual_k)
        
        # Convert L2 distance to similarity score (closer = higher)
        max_dist = max(distances[0]) if max(distances[0]) > 0 else 1
        
        for i, idx in enumerate(ids[0]):
            if idx >= 0 and idx < len(self.faiss_store.meta):
                # Invert distance: higher is better
                similarity = 1 - (distances[0][i] / (max_dist + 1))
                scores[int(idx)] = similarity
        
        return scores
    
    def _reciprocal_rank_fusion(
        self, 
        bm25_scores: Dict[int, float], 
        faiss_scores: Dict[int, float], 
        k: int,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) to combine rankings
        
        RRF score = sum(1 / (k + rank)) for each system
        """
        # Get all unique document IDs
        all_ids = set(bm25_scores.keys()) | set(faiss_scores.keys())
        
        if not all_ids:
            return []
        
        # Calculate RRF scores
        rrf_scores = {}
        
        # Sort BM25 results by score
        bm25_ranked = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_ranked)}
        
        # Sort FAISS results by score
        faiss_ranked = sorted(faiss_scores.items(), key=lambda x: x[1], reverse=True)
        faiss_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(faiss_ranked)}
        
        for doc_id in all_ids:
            rrf_score = 0
            
            # BM25 contribution
            if doc_id in bm25_ranks:
                rrf_score += (1 - self.alpha) * (1 / (rrf_k + bm25_ranks[doc_id]))
            
            # FAISS contribution
            if doc_id in faiss_ranks:
                rrf_score += self.alpha * (1 / (rrf_k + faiss_ranks[doc_id]))
            
            rrf_scores[doc_id] = rrf_score
        
        # Sort by combined score and get top k
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        results = []
        for doc_id, score in sorted_results:
            if 0 <= doc_id < len(self.faiss_store.meta):
                meta = self.faiss_store.meta[doc_id]
                results.append({
                    "text": meta.get("text", ""),
                    "metadata": meta,
                    "hybrid_score": score,
                    "bm25_score": bm25_scores.get(doc_id, 0),
                    "semantic_score": faiss_scores.get(doc_id, 0),
                    "source": meta.get("source", "Unknown")
                })
        
        return results


def hybrid_retrieve(query: str, k: int = 5, user_id: str = "user_001", alpha: float = 0.6) -> List[Dict]:
    """
    Main hybrid retrieval function
    
    Args:
        query: Search query
        k: Number of results
        user_id: User identifier
        alpha: Semantic weight (0-1)
        
    Returns:
        List of search results
    """
    from vector.store_faiss import FaissStore
    
    store = FaissStore.load_or_create(user_id=user_id)
    
    if store.index.ntotal == 0:
        print("⚠️ No vectors in FAISS index for hybrid search")
        return []
    
    searcher = HybridSearcher(store, alpha=alpha)
    results = searcher.search(query, k=k)
    
    print(f"🔍 Hybrid search: {len(results)} results (α={alpha})")
    
    return results
