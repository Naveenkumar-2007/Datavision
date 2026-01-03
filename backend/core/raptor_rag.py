"""
RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval
======================================================================

RAPTOR builds a tree of summaries from documents:
1. Cluster similar chunks
2. Summarize each cluster
3. Recursively cluster and summarize up to a root
4. Retrieval can happen at any level of the tree

This enables:
- Better long-document understanding
- Multi-hop reasoning
- Hierarchical retrieval (overview → details)

Based on: "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval"
(Sarthi et al., 2024)

Uses FREE APIs only (Groq/Gemini).
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

from core.llm import chat, embed_texts

logger = logging.getLogger(__name__)


@dataclass
class RAPTORNode:
    """A node in the RAPTOR tree"""
    id: str
    text: str
    level: int  # 0 = leaf (original chunks), higher = more abstract
    children: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    

class RAPTORTree:
    """
    Builds and manages a RAPTOR tree for hierarchical retrieval.
    
    The tree has multiple levels:
    - Level 0: Original document chunks
    - Level 1: Summaries of clustered chunks
    - Level 2+: Recursive summaries up to root
    
    Uses FREE APIs (Groq/Gemini).
    """
    
    def __init__(
        self,
        cluster_size: int = 5,
        max_levels: int = 3,
        summary_max_tokens: int = 300
    ):
        self.cluster_size = cluster_size
        self.max_levels = max_levels
        self.summary_max_tokens = summary_max_tokens
        
        self.nodes: Dict[str, RAPTORNode] = {}
        self.levels: Dict[int, List[str]] = defaultdict(list)
        
    def _generate_node_id(self, level: int, index: int) -> str:
        """Generate unique node ID"""
        return f"L{level}_N{index}"
    
    async def _summarize_texts(self, texts: List[str], context: str = "") -> str:
        """Summarize a group of texts into a single summary"""
        
        combined = "\n\n---\n\n".join(texts)
        
        prompt = f"""Summarize the following texts into a single coherent paragraph.
Focus on key facts, numbers, and insights. Be concise but comprehensive.

{f'CONTEXT: {context}' if context else ''}

TEXTS TO SUMMARIZE:
{combined[:4000]}

SUMMARY:"""

        try:
            summary = chat(prompt, temperature=0.2, max_tokens=self.summary_max_tokens)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            return combined[:500]  # Fallback to truncated combo
    
    def _cluster_nodes(
        self, 
        nodes: List[RAPTORNode], 
        embeddings: List[List[float]]
    ) -> List[List[RAPTORNode]]:
        """
        Cluster nodes by embedding similarity.
        Uses simple greedy clustering for efficiency.
        """
        
        if len(nodes) <= self.cluster_size:
            return [nodes]
        
        # Simple greedy clustering
        clusters = []
        remaining = list(range(len(nodes)))
        
        while remaining:
            cluster_indices = [remaining.pop(0)]
            
            while len(cluster_indices) < self.cluster_size and remaining:
                # Find most similar to cluster centroid
                cluster_embs = [embeddings[i] for i in cluster_indices]
                centroid = np.mean(cluster_embs, axis=0)
                
                best_idx = -1
                best_sim = -1
                
                for idx in remaining:
                    emb = embeddings[idx]
                    sim = np.dot(centroid, emb) / (
                        np.linalg.norm(centroid) * np.linalg.norm(emb) + 1e-8
                    )
                    if sim > best_sim:
                        best_sim = sim
                        best_idx = idx
                
                if best_idx >= 0:
                    remaining.remove(best_idx)
                    cluster_indices.append(best_idx)
                else:
                    break
            
            clusters.append([nodes[i] for i in cluster_indices])
        
        return clusters
    
    async def build_tree(
        self,
        chunks: List[str],
        document_name: str = ""
    ) -> Dict[str, Any]:
        """
        Build RAPTOR tree from document chunks.
        
        Args:
            chunks: List of text chunks (level 0)
            document_name: Name of source document
            
        Returns:
            Tree statistics and root node ID
        """
        
        # Clear existing tree
        self.nodes.clear()
        self.levels.clear()
        
        # Create leaf nodes (level 0)
        current_level = 0
        logger.info(f"RAPTOR: Creating {len(chunks)} leaf nodes")
        
        for i, chunk in enumerate(chunks):
            node_id = self._generate_node_id(current_level, i)
            node = RAPTORNode(
                id=node_id,
                text=chunk,
                level=current_level,
                metadata={"document": document_name, "chunk_index": i}
            )
            self.nodes[node_id] = node
            self.levels[current_level].append(node_id)
        
        # Generate embeddings for current level
        current_texts = [self.nodes[nid].text for nid in self.levels[current_level]]
        current_embeddings = embed_texts(current_texts)
        
        for nid, emb in zip(self.levels[current_level], current_embeddings):
            self.nodes[nid].embedding = emb
        
        # Build higher levels recursively
        while len(self.levels[current_level]) > 1 and current_level < self.max_levels:
            current_level += 1
            logger.info(f"RAPTOR: Building level {current_level}")
            
            # Get current level nodes
            prev_nodes = [self.nodes[nid] for nid in self.levels[current_level - 1]]
            prev_embeddings = [node.embedding for node in prev_nodes]
            
            # Cluster nodes
            clusters = self._cluster_nodes(prev_nodes, prev_embeddings)
            logger.info(f"RAPTOR: Created {len(clusters)} clusters at level {current_level}")
            
            # Summarize each cluster
            for i, cluster in enumerate(clusters):
                cluster_texts = [node.text for node in cluster]
                summary = await self._summarize_texts(cluster_texts)
                
                # Create parent node
                node_id = self._generate_node_id(current_level, i)
                node = RAPTORNode(
                    id=node_id,
                    text=summary,
                    level=current_level,
                    children=[n.id for n in cluster],
                    metadata={"cluster_size": len(cluster)}
                )
                
                # Link children to parent
                for child in cluster:
                    child.parent = node_id
                
                self.nodes[node_id] = node
                self.levels[current_level].append(node_id)
            
            # Generate embeddings for new level
            level_texts = [self.nodes[nid].text for nid in self.levels[current_level]]
            level_embeddings = embed_texts(level_texts)
            
            for nid, emb in zip(self.levels[current_level], level_embeddings):
                self.nodes[nid].embedding = emb
        
        # Get root(s)
        root_level = max(self.levels.keys())
        root_ids = self.levels[root_level]
        
        return {
            "num_nodes": len(self.nodes),
            "num_levels": root_level + 1,
            "root_ids": root_ids,
            "level_sizes": {k: len(v) for k, v in self.levels.items()}
        }
    
    def retrieve(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        level: Optional[int] = None
    ) -> List[Tuple[RAPTORNode, float]]:
        """
        Retrieve most relevant nodes.
        
        Args:
            query_embedding: Query vector
            top_k: Number of nodes to retrieve
            level: Specific level to search (None = all levels)
            
        Returns:
            List of (node, similarity_score) tuples
        """
        
        candidates = []
        
        levels_to_search = [level] if level is not None else list(self.levels.keys())
        
        for lvl in levels_to_search:
            for node_id in self.levels[lvl]:
                node = self.nodes[node_id]
                if node.embedding:
                    sim = np.dot(query_embedding, node.embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(node.embedding) + 1e-8
                    )
                    candidates.append((node, float(sim)))
        
        # Sort by similarity
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates[:top_k]
    
    def hierarchical_retrieve(
        self,
        query_embedding: List[float],
        top_k_per_level: int = 2
    ) -> Dict[int, List[Tuple[RAPTORNode, float]]]:
        """
        Retrieve top results from each level.
        Useful for getting both overview (high level) and details (low level).
        """
        
        results = {}
        
        for level in sorted(self.levels.keys(), reverse=True):
            level_results = self.retrieve(
                query_embedding, 
                top_k=top_k_per_level, 
                level=level
            )
            if level_results:
                results[level] = level_results
        
        return results
    
    def get_context_with_hierarchy(
        self,
        query_embedding: List[float],
        max_chunks: int = 5
    ) -> str:
        """
        Get context that includes both high-level summaries and relevant details.
        """
        
        # Get hierarchical results
        hier_results = self.hierarchical_retrieve(query_embedding, top_k_per_level=2)
        
        context_parts = []
        
        # Start with highest level (most abstract)
        for level in sorted(hier_results.keys(), reverse=True):
            level_name = "Overview" if level == max(hier_results.keys()) else f"Level {level}"
            for node, score in hier_results[level][:2]:
                context_parts.append(f"[{level_name} - Relevance: {score:.2f}]\n{node.text}")
        
        return "\n\n---\n\n".join(context_parts[:max_chunks])

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tree to dictionary"""
        return {
            "nodes": {nid: {
                "id": node.id,
                "text": node.text,
                "level": node.level,
                "children": node.children,
                "parent": node.parent,
                "metadata": node.metadata
            } for nid, node in self.nodes.items()},
            "levels": dict(self.levels)
        }


# Convenience function for easy integration
async def build_raptor_tree(
    chunks: List[str],
    document_name: str = ""
) -> RAPTORTree:
    """
    Build a RAPTOR tree from document chunks.
    
    Returns the tree object for retrieval.
    """
    
    tree = RAPTORTree()
    stats = await tree.build_tree(chunks, document_name)
    logger.info(f"RAPTOR tree built: {stats}")
    
    return tree


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test chunks
        chunks = [
            "Q1 revenue was $1.2M, primarily from product sales.",
            "Q2 revenue grew to $1.5M, a 25% increase from Q1.",
            "Q3 saw a slight dip to $1.4M due to market conditions.",
            "Q4 recovered strongly with $2.5M in revenue.",
            "Total annual revenue reached $6.6M.",
            "Customer count grew from 800 to 1,250 over the year.",
            "Churn rate improved from 5% to 3.2%.",
            "NPS score increased from 65 to 72.",
            "Operating expenses remained stable at $1.8M per quarter.",
            "Net profit margin improved to 12% by year end.",
        ]
        
        tree = await build_raptor_tree(chunks, "Annual Report")
        
        print(f"Tree has {len(tree.nodes)} nodes")
        print(f"Levels: {tree.levels.keys()}")
        
        # Test retrieval
        query = "What was the annual revenue?"
        query_emb = embed_texts([query])[0]
        
        results = tree.retrieve(query_emb, top_k=3)
        print(f"\nTop 3 results for '{query}':")
        for node, score in results:
            print(f"  [{node.level}] {score:.2f}: {node.text[:80]}...")
    
    asyncio.run(test())
