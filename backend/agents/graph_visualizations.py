# =============================================================================
# GRAPH VISUALIZATIONS - Mindmaps, Knowledge Graphs, Relationship Diagrams
# =============================================================================
#
# This module generates interactive visualizations from graph data:
# - Mindmaps (Mermaid format for hierarchical views)
# - Knowledge Graphs (Plotly network diagrams)
# - Relationship Diagrams (Entity connections)
#
# All dynamically generated from actual graph data - NO hardcoding!
#

import json
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


def generate_mindmap(
    graph,
    query: str,
    focus_entity: Optional[str] = None,
    max_depth: int = 3,
    max_children: int = 5
) -> Tuple[Optional[Dict], str]:
    """
    🧠 Generate a proper MINDMAP with nodes and branches (tree-style diagram).
    
    Creates a visualization like the reference with:
    - Central root node on the left
    - Branches connecting to child nodes
    - Child nodes positioned to the right
    """
    print(f"[MINDMAP] Starting mindmap generation for query: {query}")
    
    if not graph or graph.number_of_nodes() == 0:
        print("[MINDMAP] ERROR: No graph data")
        return None, "No graph data available for mindmap"
    
    def clean_name(name: str) -> str:
        """Clean entity name for display."""
        name_str = str(name)
        if ':' in name_str:
            name_str = name_str.split(':')[-1].strip()
        return name_str[:20]
    
    # Get all nodes and their degrees
    all_nodes = list(graph.nodes())
    print(f"[MINDMAP] Graph has {len(all_nodes)} nodes")
    
    # Use highest-degree node as root
    degrees = sorted(graph.degree(), key=lambda x: x[1], reverse=True)
    
    if not degrees:
        print("[MINDMAP] ERROR: No node degrees found")
        return None, "No nodes found in graph"
    
    focus_entity = degrees[0][0]
    print(f"[MINDMAP] Root entity: {focus_entity} (degree: {degrees[0][1]})")
    
    # Build tree structure
    node_data = []  # [{name, x, y, size, color}]
    edges = []  # [(x1, y1, x2, y2)]
    
    colors = ['#818cf8', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
    
    # Root node at (0, 0)
    root_name = clean_name(focus_entity)
    node_data.append({'name': root_name, 'x': 0, 'y': 0, 'size': 40, 'color': colors[0]})
    
    visited = {focus_entity}
    current_level = [(focus_entity, 0, 0)]  # (node, x, y)
    
    level_x = 2  # X offset for each level
    
    for depth in range(max_depth):
        next_level = []
        level_color = colors[(depth + 1) % len(colors)]
        
        for parent_node, parent_x, parent_y in current_level:
            try:
                neighbors = [n for n in graph.neighbors(parent_node) if n not in visited]
            except:
                neighbors = []
            
            if not neighbors:
                continue
            
            # Take top N children
            children = neighbors[:max_children]
            child_count = len(children)
            
            # Spread children vertically
            if child_count > 1:
                spacing = 1.5
                start_y = parent_y + (child_count - 1) * spacing / 2
            else:
                start_y = parent_y
            
            for i, child in enumerate(children):
                visited.add(child)
                child_x = parent_x + level_x
                child_y = start_y - i * 1.5 if child_count > 1 else parent_y
                
                # Add node
                child_name = clean_name(child)
                node_data.append({
                    'name': child_name, 
                    'x': child_x, 
                    'y': child_y, 
                    'size': 30 - depth * 4,
                    'color': level_color
                })
                
                # Add edge
                edges.append((parent_x, parent_y, child_x, child_y))
                
                next_level.append((child, child_x, child_y))
        
        current_level = next_level
        if not current_level:
            break
    
    print(f"[MINDMAP] Generated {len(node_data)} nodes, {len(edges)} edges")
    
    if len(node_data) < 2:
        print("[MINDMAP] ERROR: Not enough connected nodes")
        return None, "Not enough connected entities for mindmap"
    
    # Build Plotly traces
    edge_x = []
    edge_y = []
    for x1, y1, x2, y2 in edges:
        edge_x.extend([x1, x2, None])
        edge_y.extend([y1, y2, None])
    
    node_x = [n['x'] for n in node_data]
    node_y = [n['y'] for n in node_data]
    node_text = [n['name'] for n in node_data]
    node_sizes = [n['size'] for n in node_data]
    node_colors = [n['color'] for n in node_data]
    
    chart = {
        "data": [
            {
                "type": "scatter",
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 2, "color": "#94a3b8"},
                "hoverinfo": "none"
            },
            {
                "type": "scatter",
                "x": node_x,
                "y": node_y,
                "mode": "markers+text",
                "marker": {
                    "size": node_sizes,
                    "color": node_colors,
                    "line": {"width": 2, "color": "#ffffff"}
                },
                "text": node_text,
                "textposition": "bottom center",
                "textfont": {"size": 11, "color": "#1e293b", "family": "Arial, sans-serif"},
                "hoverinfo": "text",
                "hovertext": node_text
            }
        ],
        "layout": {
            "title": {"text": f"Mindmap: {root_name}", "font": {"size": 18, "color": "#1e293b"}},
            "showlegend": False,
            "xaxis": {"visible": False, "showgrid": False},
            "yaxis": {"visible": False, "showgrid": False},
            "height": 550,
            "margin": {"l": 80, "r": 150, "t": 80, "b": 80}
        }
    }

    
    print(f"[MINDMAP] ✅ Chart generated successfully")
    
    explanation = f"""**Mindmap: {root_name}**

Shows hierarchical relationships from **{root_name}**:
- **Nodes**: {len(node_data)} entities
- **Connections**: {len(edges)} relationships  
- **Source**: Your business data"""
    
    return chart, explanation




def generate_knowledge_graph(
    graph,
    query: str,
    max_nodes: int = 30,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🕸️ Generate an interactive Plotly network diagram.
    
    Shows entities as nodes and relationships as edges,
    with node size based on importance and edge thickness based on relationship strength.
    
    Returns Plotly JSON specification.
    """
    from core.llm import chat
    
    if not graph or graph.number_of_nodes() == 0:
        return None, "No graph data available"
    
    nodes = list(graph.nodes(data=True))
    edges = list(graph.edges(data=True))
    
    # Limit nodes by degree (importance)
    degrees = sorted(graph.degree(), key=lambda x: x[1], reverse=True)
    top_nodes = [d[0] for d in degrees[:max_nodes]]
    
    # Filter edges to only include top nodes
    filtered_edges = [
        e for e in edges 
        if e[0] in top_nodes and e[1] in top_nodes
    ]
    
    # Create node positions using spring layout
    try:
        import networkx as nx
        pos = nx.spring_layout(graph.subgraph(top_nodes), k=2, iterations=50)
    except:
        # Fallback to circular layout
        import math
        pos = {}
        for i, node in enumerate(top_nodes):
            angle = 2 * math.pi * i / len(top_nodes)
            pos[node] = [math.cos(angle), math.sin(angle)]
    
    # Build node traces
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    # Color map by node type
    color_map = {
        'customer': '#FF6B35',
        'product': '#4ECDC4',
        'category': '#45B7D1',
        'region': '#96CEB4',
        'default': '#FFEAA7'
    }
    
    for node in top_nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Get node data
        node_data = graph.nodes.get(node, {})
        node_type = node_data.get('type', 'default')
        node_value = node_data.get('value', 0)
        
        node_text.append(f"{node}<br>{node_type.title()}")
        node_size.append(max(20, min(50, 20 + graph.degree(node) * 3)))
        node_color.append(color_map.get(node_type, color_map['default']))
    
    # Build edge traces
    edge_x = []
    edge_y = []
    
    for edge in filtered_edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Create Plotly figure
    chart = {
        "data": [
            # Edges
            {
                "type": "scatter",
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 1, "color": "rgba(150,150,150,0.5)"},
                "hoverinfo": "none"
            },
            # Nodes
            {
                "type": "scatter",
                "x": node_x,
                "y": node_y,
                "mode": "markers+text",
                "marker": {
                    "size": node_size,
                    "color": node_color,
                    "line": {"width": 2, "color": "white"}
                },
                "text": [str(n)[:15] for n in top_nodes],
                "textposition": "top center",
                "hovertext": node_text,
                "hoverinfo": "text"
            }
        ],
        "layout": {
            "title": {"text": "Knowledge Graph", "font": {"size": 16}},
            "showlegend": False,
            "hovermode": "closest",
            "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
            "height": 500,
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20}
        }
    }
    
    explanation = f"""**Knowledge Graph Visualization**

This interactive network shows the relationships in your business data:
- **Nodes**: {len(top_nodes)} entities (customers, products, etc.)
- **Edges**: {len(filtered_edges)} relationships
- **Node size**: Based on connection count (importance)
- **Colors**: Different entity types

Hover over nodes to see details."""
    
    return chart, explanation


def generate_relationship_diagram(
    df: pd.DataFrame,
    query: str,
    source_col: str = "customer",
    target_col: str = "product",
    value_col: str = "amount",
    top_n: int = 20,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🔗 Generate a Sankey diagram showing relationships between entities.
    
    Shows flow/connections between two entity types (e.g., customers → products).
    """
    from core.llm import chat
    
    if df is None or df.empty:
        return None, "No data available"
    
    # LLM determines best columns if not obvious
    if source_col not in df.columns or target_col not in df.columns:
        cols = list(df.columns)
        prompt = f"""Query: "{query}"
Available columns: {cols}

For a relationship diagram, pick:
1. SOURCE column (e.g., customer, category)
2. TARGET column (e.g., product, region)
3. VALUE column (e.g., amount, revenue)

Respond in JSON: {{"source": "col", "target": "col", "value": "col"}}"""

        try:
            response = chat(prompt, max_tokens=100)
            spec = json.loads(response.strip())
            source_col = spec.get("source", source_col)
            target_col = spec.get("target", target_col)
            value_col = spec.get("value", value_col)
        except:
            pass
    
    # Aggregate data
    try:
        grouped = df.groupby([source_col, target_col])[value_col].sum().reset_index()
        grouped = grouped.nlargest(top_n, value_col)
    except:
        return None, f"Could not aggregate data with columns: {source_col}, {target_col}, {value_col}"
    
    # Create node list
    sources = grouped[source_col].unique().tolist()
    targets = grouped[target_col].unique().tolist()
    all_nodes = sources + targets
    node_map = {n: i for i, n in enumerate(all_nodes)}
    
    # Build Sankey data
    source_indices = [node_map[s] for s in grouped[source_col]]
    target_indices = [node_map[t] for t in grouped[target_col]]
    values = [float(v) for v in grouped[value_col]]
    
    chart = {
        "data": [{
            "type": "sankey",
            "node": {
                "pad": 15,
                "thickness": 20,
                "label": [str(n)[:20] for n in all_nodes],
                "color": ["#FF6B35"] * len(sources) + ["#4ECDC4"] * len(targets)
            },
            "link": {
                "source": source_indices,
                "target": target_indices,
                "value": values,
                "color": "rgba(255, 107, 53, 0.4)"
            }
        }],
        "layout": {
            "title": {"text": f"{source_col.title()} → {target_col.title()} Relationships", "font": {"size": 16}},
            "height": 500,
            "font": {"size": 12}
        }
    }
    
    total_flow = sum(values)
    explanation = f"""**Relationship Diagram: {source_col.title()} → {target_col.title()}**

This Sankey diagram shows how {source_col}s connect to {target_col}s:
- **Total flow**: {currency_symbol}{total_flow:,.0f}
- **Connections shown**: {len(values)}
- **Source entities**: {len(sources)} {source_col}s
- **Target entities**: {len(targets)} {target_col}s"""
    
    return chart, explanation


def detect_graph_visualization_type(query: str) -> str:
    """
    Detect graph visualization type from query using keywords.
    Returns: 'mindmap', 'knowledge_graph', 'relationship', or 'none'
    """
    q = query.lower()
    
    # Direct keyword matching (most reliable)
    if 'mindmap' in q or 'mind map' in q or 'mind-map' in q:
        print(f"[DETECT] Found mindmap keyword")
        return 'mindmap'
    
    if 'knowledge graph' in q or 'knowledge-graph' in q:
        print(f"[DETECT] Found knowledge graph keyword")
        return 'knowledge_graph'
    
    if 'sankey' in q or 'relationship diagram' in q or 'flow diagram' in q:
        print(f"[DETECT] Found relationship keyword")
        return 'relationship'
    
    if 'network' in q and ('diagram' in q or 'graph' in q or 'visualiz' in q):
        print(f"[DETECT] Found network diagram keyword")
        return 'knowledge_graph'
    
    # No specific graph visualization requested
    return 'none'


def wants_graph_visualization(query: str) -> bool:
    """Check if user wants a graph-based visualization."""
    keywords = [
        'mindmap', 'mind map', 'knowledge graph', 'network',
        'relationship', 'sankey', 'flow diagram', 'entity map',
        'connections', 'relationship diagram', 'graph visualization'
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in keywords)
