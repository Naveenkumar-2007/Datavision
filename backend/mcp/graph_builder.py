# MCP Graph Builder Module
"""
Knowledge graph construction tools for MCP integration.

Features:
- Entity extraction from data
- Relation detection
- Graph JSON generation
- Graph merging
- Schema inference
"""

from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import json


class EntityType(Enum):
    """Common business entity types"""
    CUSTOMER = "customer"
    PRODUCT = "product"
    INVOICE = "invoice"
    DATE = "date"
    AMOUNT = "amount"
    CATEGORY = "category"
    REGION = "region"
    EMPLOYEE = "employee"
    VENDOR = "vendor"
    ORDER = "order"


class RelationType(Enum):
    """Common relation types"""
    PURCHASED = "purchased"
    SOLD_TO = "sold_to"
    CONTAINS = "contains"
    BELONGS_TO = "belongs_to"
    OCCURRED_ON = "occurred_on"
    HAS_AMOUNT = "has_amount"
    MANAGED_BY = "managed_by"
    SUPPLIED_BY = "supplied_by"


@dataclass
class Entity:
    """Extracted entity"""
    id: str
    type: EntityType
    label: str
    attributes: Dict[str, Any]
    source: str


@dataclass
class Relation:
    """Extracted relation"""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float
    attributes: Dict[str, Any]


def extract_entities(
    data: Any,
    entity_types: Optional[List[str]] = None,
    source: str = "unknown"
) -> Dict:
    """
    Extract entities from data.
    
    Args:
        data: DataFrame, dict, or list of records
        entity_types: Types to extract (None = all)
        source: Source identifier
        
    Returns:
        Extracted entities
    """
    try:
        import pandas as pd
        
        # Convert to DataFrame
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, dict):
            df = pd.DataFrame([data]) if not any(isinstance(v, list) for v in data.values()) else pd.DataFrame(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            return {
                "success": False,
                "error": "Unsupported data type",
                "entities": []
            }
        
        entities = []
        entity_types_set = set(entity_types) if entity_types else None
        
        # Detect schema
        column_mapping = _detect_column_types(df.columns)
        
        for idx, row in df.iterrows():
            for col, etype in column_mapping.items():
                if entity_types_set and etype.value not in entity_types_set:
                    continue
                
                value = row[col]
                if pd.isna(value) or str(value).strip() == '':
                    continue
                
                entity_id = f"{etype.value}:{str(value).strip()}"
                
                entity = {
                    "id": entity_id,
                    "type": etype.value,
                    "label": str(value).strip(),
                    "attributes": {"source_column": col, "row_index": idx},
                    "source": source
                }
                
                # Avoid duplicates
                if entity_id not in [e["id"] for e in entities]:
                    entities.append(entity)
        
        return {
            "success": True,
            "entities": entities,
            "count": len(entities),
            "types_found": list(set(e["type"] for e in entities))
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "entities": []
        }


def _detect_column_types(columns: List[str]) -> Dict[str, EntityType]:
    """Detect entity types from column names"""
    mapping = {}
    
    patterns = {
        EntityType.CUSTOMER: ["customer", "client", "buyer", "cust", "customer_name", "customername"],
        EntityType.PRODUCT: ["product", "item", "sku", "service", "product_name", "productname"],
        EntityType.INVOICE: ["invoice", "order_id", "orderid", "order", "transaction", "invoice_no"],
        EntityType.DATE: ["date", "datetime", "timestamp", "created", "order_date", "transaction_date"],
        EntityType.AMOUNT: ["amount", "price", "total", "revenue", "sales", "value", "cost"],
        EntityType.CATEGORY: ["category", "type", "segment", "group", "class"],
        EntityType.REGION: ["region", "country", "state", "city", "location", "area"],
    }
    
    for col in columns:
        col_lower = col.lower().replace('_', '').replace(' ', '')
        
        for etype, keywords in patterns.items():
            if any(kw.replace('_', '') in col_lower for kw in keywords):
                mapping[col] = etype
                break
    
    return mapping


def build_graph_json(
    entities: List[Dict],
    relations: Optional[List[Dict]] = None,
    auto_relations: bool = True
) -> Dict:
    """
    Build graph structure from entities and relations.
    
    Args:
        entities: List of entity dicts
        relations: Optional explicit relations
        auto_relations: Whether to infer relations automatically
        
    Returns:
        Graph in JSON format (nodes + edges)
    """
    try:
        nodes = []
        edges = []
        node_ids = set()
        
        # Add nodes
        for entity in entities:
            node_id = entity.get("id", f"node_{len(nodes)}")
            
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "type": entity.get("type", "unknown"),
                    "label": entity.get("label", node_id),
                    "attributes": entity.get("attributes", {})
                })
                node_ids.add(node_id)
        
        # Add explicit relations
        if relations:
            for rel in relations:
                edges.append({
                    "source": rel.get("source_id"),
                    "target": rel.get("target_id"),
                    "relation": rel.get("relation_type", "related"),
                    "weight": rel.get("weight", 1.0),
                    "attributes": rel.get("attributes", {})
                })
        
        # Auto-infer relations
        if auto_relations:
            inferred = _infer_relations(entities)
            edges.extend(inferred)
        
        return {
            "success": True,
            "graph": {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "graph": None
        }


def _infer_relations(entities: List[Dict]) -> List[Dict]:
    """Infer relations between entities from same source"""
    edges = []
    
    # Group entities by source row
    by_row = {}
    for entity in entities:
        row_idx = entity.get("attributes", {}).get("row_index", -1)
        if row_idx not in by_row:
            by_row[row_idx] = []
        by_row[row_idx].append(entity)
    
    # Create edges between entities from same row
    for row_entities in by_row.values():
        if len(row_entities) < 2:
            continue
        
        # Find key entity types
        invoice = next((e for e in row_entities if e.get("type") == "invoice"), None)
        customer = next((e for e in row_entities if e.get("type") == "customer"), None)
        product = next((e for e in row_entities if e.get("type") == "product"), None)
        amount = next((e for e in row_entities if e.get("type") == "amount"), None)
        date = next((e for e in row_entities if e.get("type") == "date"), None)
        
        # Create relations
        if invoice and customer:
            edges.append({
                "source": invoice["id"],
                "target": customer["id"],
                "relation": "sold_to",
                "weight": 1.0
            })
        
        if invoice and product:
            edges.append({
                "source": invoice["id"],
                "target": product["id"],
                "relation": "contains",
                "weight": 1.0
            })
        
        if customer and product:
            edges.append({
                "source": customer["id"],
                "target": product["id"],
                "relation": "purchased",
                "weight": 1.0
            })
        
        if invoice and amount:
            edges.append({
                "source": invoice["id"],
                "target": amount["id"],
                "relation": "has_amount",
                "weight": 1.0
            })
        
        if invoice and date:
            edges.append({
                "source": invoice["id"],
                "target": date["id"],
                "relation": "occurred_on",
                "weight": 1.0
            })
    
    return edges


def merge_graphs(graphs: List[Dict]) -> Dict:
    """
    Merge multiple graphs into one.
    
    Args:
        graphs: List of graph dicts with nodes and edges
        
    Returns:
        Merged graph
    """
    try:
        merged_nodes = {}
        merged_edges = []
        edge_set = set()
        
        for graph in graphs:
            graph_data = graph.get("graph", graph)
            
            # Merge nodes
            for node in graph_data.get("nodes", []):
                node_id = node.get("id")
                if node_id not in merged_nodes:
                    merged_nodes[node_id] = node
                else:
                    # Merge attributes
                    existing = merged_nodes[node_id]
                    existing["attributes"] = {
                        **existing.get("attributes", {}),
                        **node.get("attributes", {})
                    }
            
            # Merge edges
            for edge in graph_data.get("edges", []):
                edge_key = (edge.get("source"), edge.get("target"), edge.get("relation"))
                
                if edge_key not in edge_set:
                    merged_edges.append(edge)
                    edge_set.add(edge_key)
        
        return {
            "success": True,
            "graph": {
                "nodes": list(merged_nodes.values()),
                "edges": merged_edges,
                "node_count": len(merged_nodes),
                "edge_count": len(merged_edges)
            },
            "merged_from": len(graphs)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "graph": None
        }


def graph_to_networkx(graph_json: Dict) -> Any:
    """
    Convert graph JSON to NetworkX graph.
    
    Args:
        graph_json: Graph in JSON format
        
    Returns:
        NetworkX graph object
    """
    try:
        import networkx as nx
        
        graph_data = graph_json.get("graph", graph_json)
        
        G = nx.Graph()
        
        # Add nodes
        for node in graph_data.get("nodes", []):
            G.add_node(
                node["id"],
                type=node.get("type", "unknown"),
                label=node.get("label", node["id"]),
                **node.get("attributes", {})
            )
        
        # Add edges
        for edge in graph_data.get("edges", []):
            G.add_edge(
                edge["source"],
                edge["target"],
                relation=edge.get("relation", "related"),
                weight=edge.get("weight", 1.0),
                **edge.get("attributes", {})
            )
        
        return G
        
    except Exception as e:
        return None


def networkx_to_json(graph: Any) -> Dict:
    """
    Convert NetworkX graph to JSON format.
    
    Args:
        graph: NetworkX graph object
        
    Returns:
        Graph in JSON format
    """
    try:
        nodes = []
        edges = []
        
        for node_id, attrs in graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": attrs.get("type", "unknown"),
                "label": attrs.get("label", node_id),
                "attributes": {k: v for k, v in attrs.items() if k not in ["type", "label"]}
            })
        
        for source, target, attrs in graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": attrs.get("relation", "connected"),
                "weight": attrs.get("weight", 1.0),
                "attributes": {k: v for k, v in attrs.items() if k not in ["relation", "weight"]}
            })
        
        return {
            "success": True,
            "graph": {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "graph": None
        }


def get_graph_stats(graph_json: Dict) -> Dict:
    """Get statistics about a graph"""
    try:
        graph_data = graph_json.get("graph", graph_json)
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        # Type distribution
        type_counts = {}
        for node in nodes:
            ntype = node.get("type", "unknown")
            type_counts[ntype] = type_counts.get(ntype, 0) + 1
        
        # Relation distribution
        relation_counts = {}
        for edge in edges:
            rel = edge.get("relation", "unknown")
            relation_counts[rel] = relation_counts.get(rel, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": type_counts,
                "relation_types": relation_counts,
                "density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stats": None
        }
