# Enterprise Graph Traversal Module
"""
Advanced graph traversal algorithms for GraphRAG.

Features:
- Multi-hop reasoning with path tracking
- PageRank for node importance
- BFS/DFS traversal strategies
- Causal chain detection
- Path explanation generation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from enum import Enum
import networkx as nx
from collections import defaultdict
import heapq


class TraversalStrategy(Enum):
    """Graph traversal strategies"""
    BFS = "bfs"           # Breadth-first for shortest paths
    DFS = "dfs"           # Depth-first for exhaustive search
    WEIGHTED = "weighted"  # Dijkstra for weighted paths
    PAGERANK = "pagerank"  # Importance-based traversal


@dataclass
class GraphPath:
    """A path through the knowledge graph"""
    nodes: List[str]
    edges: List[str]
    total_weight: float
    hop_count: int
    path_type: str  # "direct", "multi-hop", "causal"
    explanation: str


@dataclass
class TraversalResult:
    """Complete traversal result"""
    paths: List[GraphPath]
    visited_nodes: Set[str]
    node_importance: Dict[str, float]
    total_hops: int
    reasoning_chain: List[str]
    summary: str


@dataclass
class NodeInfo:
    """Information about a graph node"""
    node_id: str
    node_type: str
    label: str
    attributes: Dict[str, Any]
    importance: float
    neighbors: List[str]


class EnterpriseGraphTraversal:
    """
    Enterprise-grade graph traversal for knowledge graph reasoning.
    
    Supports:
    - Multi-hop path finding
    - Importance-weighted traversal
    - Causal chain detection
    - Path explanation generation
    """
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self._pagerank_cache = None
        self._node_types_cache = None
    
    @property
    def pagerank(self) -> Dict[str, float]:
        """Lazy-computed PageRank scores"""
        if self._pagerank_cache is None:
            if self.graph.number_of_nodes() > 0:
                self._pagerank_cache = nx.pagerank(self.graph, weight='weight')
            else:
                self._pagerank_cache = {}
        return self._pagerank_cache
    
    def invalidate_cache(self):
        """Invalidate cached computations"""
        self._pagerank_cache = None
        self._node_types_cache = None
    
    def get_node_info(self, node_id: str) -> Optional[NodeInfo]:
        """Get detailed information about a node"""
        if not self.graph.has_node(node_id):
            return None
        
        attrs = dict(self.graph.nodes[node_id])
        node_type = attrs.get('type', 'unknown')
        label = attrs.get('label', node_id)
        importance = self.pagerank.get(node_id, 0.0)
        neighbors = list(self.graph.neighbors(node_id))
        
        return NodeInfo(
            node_id=node_id,
            node_type=node_type,
            label=label,
            attributes=attrs,
            importance=importance,
            neighbors=neighbors
        )
    
    def find_paths(
        self,
        source_entities: List[str],
        target_entities: Optional[List[str]] = None,
        max_hops: int = 3,
        strategy: TraversalStrategy = TraversalStrategy.BFS,
        max_paths: int = 10
    ) -> TraversalResult:
        """
        Find paths between entities in the graph.
        
        Args:
            source_entities: Starting entity IDs or patterns
            target_entities: Optional target entity IDs
            max_hops: Maximum path length
            strategy: Traversal strategy to use
            max_paths: Maximum number of paths to return
            
        Returns:
            TraversalResult with found paths and metadata
        """
        # Find matching source nodes
        source_nodes = self._find_matching_nodes(source_entities)
        
        if not source_nodes:
            return TraversalResult(
                paths=[],
                visited_nodes=set(),
                node_importance={},
                total_hops=0,
                reasoning_chain=["No matching source nodes found"],
                summary="Could not find relevant entities in the knowledge graph"
            )
        
        # Find matching target nodes if specified
        target_nodes = None
        if target_entities:
            target_nodes = self._find_matching_nodes(target_entities)
        
        # Execute traversal based on strategy
        if strategy == TraversalStrategy.BFS:
            paths, visited = self._bfs_traversal(source_nodes, target_nodes, max_hops, max_paths)
        elif strategy == TraversalStrategy.DFS:
            paths, visited = self._dfs_traversal(source_nodes, target_nodes, max_hops, max_paths)
        elif strategy == TraversalStrategy.WEIGHTED:
            paths, visited = self._weighted_traversal(source_nodes, target_nodes, max_hops, max_paths)
        elif strategy == TraversalStrategy.PAGERANK:
            paths, visited = self._pagerank_traversal(source_nodes, max_hops, max_paths)
        else:
            paths, visited = self._bfs_traversal(source_nodes, target_nodes, max_hops, max_paths)
        
        # Compute node importance for visited nodes
        node_importance = {n: self.pagerank.get(n, 0.0) for n in visited}
        
        # Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(paths)
        
        # Generate summary
        summary = self._generate_summary(paths, visited)
        
        return TraversalResult(
            paths=paths,
            visited_nodes=visited,
            node_importance=node_importance,
            total_hops=max(p.hop_count for p in paths) if paths else 0,
            reasoning_chain=reasoning_chain,
            summary=summary
        )
    
    def _find_matching_nodes(self, patterns: List[str]) -> Set[str]:
        """Find nodes matching given patterns"""
        matches = set()
        
        for pattern in patterns:
            pattern_lower = pattern.lower()
            
            for node in self.graph.nodes():
                node_lower = str(node).lower()
                attrs = self.graph.nodes[node]
                label = str(attrs.get('label', '')).lower()
                
                # Match by ID, label, or type
                if (pattern_lower in node_lower or 
                    pattern_lower in label or
                    pattern_lower == attrs.get('type', '').lower()):
                    matches.add(node)
        
        return matches
    
    def _bfs_traversal(
        self,
        sources: Set[str],
        targets: Optional[Set[str]],
        max_hops: int,
        max_paths: int
    ) -> Tuple[List[GraphPath], Set[str]]:
        """Breadth-first traversal for shortest paths"""
        paths = []
        visited = set()
        
        from collections import deque
        
        for source in sources:
            if len(paths) >= max_paths:
                break
            
            queue = deque([(source, [source], [], 0)])
            local_visited = {source}
            
            while queue and len(paths) < max_paths:
                current, path, edges, hops = queue.popleft()
                visited.add(current)
                
                if hops >= max_hops:
                    continue
                
                for neighbor in self.graph.neighbors(current):
                    if neighbor not in local_visited:
                        local_visited.add(neighbor)
                        
                        edge_data = self.graph.edges[current, neighbor]
                        edge_label = edge_data.get('relation', 'connected')
                        new_path = path + [neighbor]
                        new_edges = edges + [edge_label]
                        
                        # Check if target reached
                        if targets and neighbor in targets:
                            paths.append(self._create_path(
                                new_path, new_edges, hops + 1, "direct"
                            ))
                        elif not targets and hops + 1 <= max_hops:
                            # Explore further for discovery
                            paths.append(self._create_path(
                                new_path, new_edges, hops + 1, "exploration"
                            ))
                        
                        queue.append((neighbor, new_path, new_edges, hops + 1))
        
        return paths[:max_paths], visited
    
    def _dfs_traversal(
        self,
        sources: Set[str],
        targets: Optional[Set[str]],
        max_hops: int,
        max_paths: int
    ) -> Tuple[List[GraphPath], Set[str]]:
        """Depth-first traversal for exhaustive search"""
        paths = []
        visited = set()
        
        def dfs(node: str, path: List[str], edges: List[str], depth: int):
            if len(paths) >= max_paths:
                return
            
            visited.add(node)
            
            if depth >= max_hops:
                return
            
            for neighbor in self.graph.neighbors(node):
                if neighbor not in path:  # Avoid cycles
                    edge_data = self.graph.edges[node, neighbor]
                    edge_label = edge_data.get('relation', 'connected')
                    new_path = path + [neighbor]
                    new_edges = edges + [edge_label]
                    
                    if targets and neighbor in targets:
                        paths.append(self._create_path(
                            new_path, new_edges, depth + 1, "multi-hop"
                        ))
                    
                    dfs(neighbor, new_path, new_edges, depth + 1)
        
        for source in sources:
            if len(paths) >= max_paths:
                break
            dfs(source, [source], [], 0)
        
        return paths[:max_paths], visited
    
    def _weighted_traversal(
        self,
        sources: Set[str],
        targets: Optional[Set[str]],
        max_hops: int,
        max_paths: int
    ) -> Tuple[List[GraphPath], Set[str]]:
        """Weighted path finding using Dijkstra-like approach"""
        paths = []
        visited = set()
        
        for source in sources:
            if len(paths) >= max_paths:
                break
            
            if not targets:
                continue
            
            for target in targets:
                if len(paths) >= max_paths:
                    break
                
                try:
                    path = nx.shortest_path(
                        self.graph, source, target, weight='weight'
                    )
                    
                    if len(path) - 1 <= max_hops:
                        edges = []
                        total_weight = 0
                        
                        for i in range(len(path) - 1):
                            edge_data = self.graph.edges[path[i], path[i+1]]
                            edges.append(edge_data.get('relation', 'connected'))
                            total_weight += edge_data.get('weight', 1.0)
                        
                        gpath = GraphPath(
                            nodes=path,
                            edges=edges,
                            total_weight=total_weight,
                            hop_count=len(path) - 1,
                            path_type="weighted",
                            explanation=self._explain_path(path, edges)
                        )
                        paths.append(gpath)
                        visited.update(path)
                except nx.NetworkXNoPath:
                    pass
        
        return paths, visited
    
    def _pagerank_traversal(
        self,
        sources: Set[str],
        max_hops: int,
        max_paths: int
    ) -> Tuple[List[GraphPath], Set[str]]:
        """Traverse following high-importance nodes"""
        paths = []
        visited = set()
        
        for source in sources:
            if len(paths) >= max_paths:
                break
            
            current = source
            path = [current]
            edges = []
            
            for _ in range(max_hops):
                visited.add(current)
                
                # Get neighbors sorted by PageRank
                neighbors = list(self.graph.neighbors(current))
                if not neighbors:
                    break
                
                # Choose highest PageRank neighbor not in path
                neighbors = [n for n in neighbors if n not in path]
                if not neighbors:
                    break
                
                neighbors.sort(key=lambda n: self.pagerank.get(n, 0), reverse=True)
                next_node = neighbors[0]
                
                edge_data = self.graph.edges[current, next_node]
                edges.append(edge_data.get('relation', 'connected'))
                path.append(next_node)
                current = next_node
            
            if len(path) > 1:
                paths.append(self._create_path(
                    path, edges, len(path) - 1, "importance"
                ))
        
        return paths, visited
    
    def _create_path(
        self,
        nodes: List[str],
        edges: List[str],
        hop_count: int,
        path_type: str
    ) -> GraphPath:
        """Create a GraphPath with explanation"""
        # Calculate weight
        total_weight = 0
        for i in range(len(nodes) - 1):
            if self.graph.has_edge(nodes[i], nodes[i+1]):
                edge_data = self.graph.edges[nodes[i], nodes[i+1]]
                total_weight += edge_data.get('weight', 1.0)
        
        return GraphPath(
            nodes=nodes,
            edges=edges,
            total_weight=total_weight,
            hop_count=hop_count,
            path_type=path_type,
            explanation=self._explain_path(nodes, edges)
        )
    
    def _explain_path(self, nodes: List[str], edges: List[str]) -> str:
        """Generate human-readable explanation of a path"""
        if len(nodes) < 2:
            return f"Single entity: {self._get_node_label(nodes[0])}"
        
        parts = []
        for i in range(len(nodes) - 1):
            src_label = self._get_node_label(nodes[i])
            edge_label = edges[i] if i < len(edges) else "connected to"
            dst_label = self._get_node_label(nodes[i + 1])
            
            parts.append(f"{src_label} → [{edge_label}] → {dst_label}")
        
        return " | ".join(parts)
    
    def _get_node_label(self, node_id: str) -> str:
        """Get human-readable label for node"""
        if self.graph.has_node(node_id):
            attrs = self.graph.nodes[node_id]
            label = attrs.get('label', node_id)
            node_type = attrs.get('type', '')
            if node_type:
                return f"{label} ({node_type})"
            return label
        return node_id
    
    def _generate_reasoning_chain(self, paths: List[GraphPath]) -> List[str]:
        """Generate step-by-step reasoning from paths"""
        if not paths:
            return ["No paths found in knowledge graph"]
        
        chain = []
        for i, path in enumerate(paths[:5]):  # Top 5 paths
            chain.append(f"Path {i+1}: {path.explanation}")
        
        return chain
    
    def _generate_summary(self, paths: List[GraphPath], visited: Set[str]) -> str:
        """Generate summary of traversal results"""
        if not paths:
            return "No relevant paths found in the knowledge graph."
        
        unique_entities = len(visited)
        total_paths = len(paths)
        avg_hops = sum(p.hop_count for p in paths) / len(paths)
        
        return (
            f"Found {total_paths} paths connecting {unique_entities} entities. "
            f"Average path length: {avg_hops:.1f} hops."
        )
    
    def get_entity_neighbors(
        self,
        entity: str,
        max_neighbors: int = 10
    ) -> List[NodeInfo]:
        """Get neighbors of an entity sorted by importance"""
        nodes = self._find_matching_nodes([entity])
        
        if not nodes:
            return []
        
        neighbors = set()
        for node in nodes:
            neighbors.update(self.graph.neighbors(node))
        
        # Sort by PageRank
        neighbor_info = []
        for n in neighbors:
            info = self.get_node_info(n)
            if info:
                neighbor_info.append(info)
        
        neighbor_info.sort(key=lambda x: x.importance, reverse=True)
        return neighbor_info[:max_neighbors]
    
    def detect_causal_chain(
        self,
        effect_entity: str,
        max_causes: int = 5
    ) -> TraversalResult:
        """Detect potential causal relationships leading to an effect"""
        # Find the effect node
        effect_nodes = self._find_matching_nodes([effect_entity])
        
        if not effect_nodes:
            return TraversalResult(
                paths=[],
                visited_nodes=set(),
                node_importance={},
                total_hops=0,
                reasoning_chain=["Effect entity not found"],
                summary="Could not identify the effect entity"
            )
        
        # Traverse backwards to find causes
        causal_paths = []
        visited = set()
        
        for effect in effect_nodes:
            # Use reverse BFS to find predecessors
            # In undirected graph, just find connected high-importance nodes
            neighbors = self.get_entity_neighbors(effect, max_neighbors=max_causes * 2)
            
            for neighbor in neighbors[:max_causes]:
                path = GraphPath(
                    nodes=[neighbor.node_id, effect],
                    edges=["contributes_to"],
                    total_weight=neighbor.importance,
                    hop_count=1,
                    path_type="causal",
                    explanation=f"{neighbor.label} may influence {self._get_node_label(effect)}"
                )
                causal_paths.append(path)
                visited.add(neighbor.node_id)
            
            visited.add(effect)
        
        return TraversalResult(
            paths=causal_paths,
            visited_nodes=visited,
            node_importance={n: self.pagerank.get(n, 0) for n in visited},
            total_hops=1,
            reasoning_chain=[p.explanation for p in causal_paths],
            summary=f"Identified {len(causal_paths)} potential causal factors"
        )


def create_traversal(graph: nx.Graph) -> EnterpriseGraphTraversal:
    """Create a graph traversal instance"""
    return EnterpriseGraphTraversal(graph)
