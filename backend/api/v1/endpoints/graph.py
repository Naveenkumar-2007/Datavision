"""
Graph visualization endpoints for $50,000 AI Business Analyst
Exports knowledge graph data for frontend visualization
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from graph.query import load_graph, get_graph_stats

router = APIRouter()


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    metadata: Optional[Dict] = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class GraphVisualization(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: Dict


@router.get("/graph/{user_id}/visualization", response_model=GraphVisualization)
async def get_graph_visualization(user_id: str, max_nodes: int = 100):
    """
    Export knowledge graph for visualization
    Returns nodes and edges in format suitable for D3.js, Cytoscape, etc.
    """
    try:
        # Load user's knowledge graph
        G = load_graph(user_id)
        
        if not G or G.number_of_nodes() == 0:
            raise HTTPException(
                status_code=404,
                detail="No knowledge graph available. Upload files to build graph."
            )
        
        # Get graph statistics
        stats = get_graph_stats(user_id)
        
        # Extract nodes (limit to max_nodes for performance)
        nodes = []
        node_list = list(G.nodes(data=True))[:max_nodes]
        
        for node_id, data in node_list:
            nodes.append(GraphNode(
                id=str(node_id),
                label=data.get("label", str(node_id)),
                type=data.get("type", "unknown"),
                metadata={
                    "amount": data.get("amount"),
                    "date": data.get("date"),
                    "kind": data.get("kind")
                }
            ))
        
        # Extract edges
        edges = []
        node_ids = set(n.id for n in nodes)
        
        for source, target, data in G.edges(data=True):
            # Only include edges where both nodes are in our node list
            if str(source) in node_ids and str(target) in node_ids:
                edges.append(GraphEdge(
                    source=str(source),
                    target=str(target),
                    relation=data.get("relation", "related_to")
                ))
        
        return GraphVisualization(
            nodes=nodes,
            edges=edges,
            stats={
                **stats,
                "displayed_nodes": len(nodes),
                "displayed_edges": len(edges),
                "total_nodes": G.number_of_nodes(),
                "total_edges": G.number_of_edges()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/{user_id}/stats")
async def get_graph_statistics(user_id: str):
    """
    Get knowledge graph statistics
    """
    try:
        stats = get_graph_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
