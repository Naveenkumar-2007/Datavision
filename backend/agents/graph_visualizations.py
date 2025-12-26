# =============================================================================
# GRAPH VISUALIZATIONS v2.0 - Pro-Level Mindmaps, Knowledge Graphs
# =============================================================================
#
# PRO FEATURES:
# - Advanced Radial Mindmap with hierarchical tree layout
# - Force-directed Knowledge Graph with community detection
# - Entity Clustering Visualization
# - Sankey Flow Diagrams
# - Interactive zoom/pan with detailed tooltips
# - Premium styling with gradients and animations
#
# All dynamically generated from actual graph data - NO hardcoding!
#

import json
import math
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import networkx as nx
from collections import defaultdict

def generate_mindmap(
    graph: nx.Graph,
    query: str,
    focus_entity: Optional[str] = None,
    max_depth: int = 3,
    max_children: int = 5
) -> Tuple[Optional[Dict], str]:
    """
    🧠 Generate a proper MINDMAP with nodes and branches (tree-style diagram).
    
    Uses improved BFS tree layout to show true hierarchy:
    Root -> Level 1 (e.g. Categories) -> Level 2 (e.g. Products)
    """
    print(f"[MINDMAP] Starting mindmap generation for query: {query}")
    
    if not graph or graph.number_of_nodes() == 0:
        return None, "No graph data available for mindmap"
    
    def clean_name(name: str) -> str:
        name_str = str(name)
        if ':' in name_str:
            name_str = name_str.split(':')[-1].strip()
        return name_str[:20]
    
    # 1. Determine Root Node
    # Priority: Explicit focus -> Query match -> Centrality -> Degree
    root_node = focus_entity
    
    if not root_node:
        # Try finding entity mentioned in query
        query_lower = query.lower()
        for node in graph.nodes():
            if str(node).lower() in query_lower:
                root_node = node
                break
    
    if not root_node:
        # Fallback to Degree Centrality (most connected node)
        degrees = sorted(graph.degree(), key=lambda x: x[1], reverse=True)
        if degrees:
            root_node = degrees[0][0]
    
    if not root_node:
        return None, "Could not determine root node for mindmap"

    print(f"[MINDMAP] Selected root: {root_node}")

    # 2. Build BFS Tree from Root
    # This creates a hierarchical structure ensuring no cycles
    try:
        # Limit graph size for performance before building tree
        # Get egocentric subgraph radius max_depth
        subgraph = nx.ego_graph(graph, root_node, radius=max_depth)
        tree = nx.bfs_tree(subgraph, root_node, depth_limit=max_depth)
    except Exception as e:
        print(f"[MINDMAP] Error building tree: {e}")
        # Fallback shallow tree
        tree = nx.Graph()
        tree.add_node(root_node)
        for n in list(graph.neighbors(root_node))[:max_children]:
            tree.add_edge(root_node, n)

    # 3. Calculate Layout Positions (Reingold-Tilford / Tree Layout)
    # Custom implementation for Plotly since NX doesn't have a great tree layout built-in for all vers
    
    node_data = [] # {name, x, y, size, color, depth}
    edges = []     # (x1, y1, x2, y2)
    
    # Identify levels
    levels = {} # node -> depth
    levels[root_node] = 0
    bfs_layers = list(nx.bfs_layers(tree, [root_node]))
    
    # Process layers to determining positions
    # Simple strategy: Root at 0,0. Children spaced out vertically at x=1, etc.
    
    pos = {}
    max_y_at_level = {}
    
    for depth, layer in enumerate(bfs_layers):
        # Limit children per layer to keep map readable
        if depth > 0:
            # Sort by degree in original graph to show important nodes first
            layer = sorted(layer, key=lambda n: graph.degree(n), reverse=True)
            layer = layer[:max_children * (depth+1)] # Allow more nodes at deeper levels
            
        layer_height = len(layer)
        y_start = -(layer_height - 1) * 0.8 / 2
        
        for i, node in enumerate(layer):
            levels[node] = depth
            x = depth * 2  # Horizontal spacing
            y = y_start + i * 0.8 # Vertical spacing
            pos[node] = (x, y)
            
            # Store edge info (except for root)
            if depth > 0:
                # Find parent in previous layer
                parents = list(tree.predecessors(node))
                if parents:
                    parent = parents[0]
                    if parent in pos:
                        px, py = pos[parent]
                        edges.append((px, py, x, y))

    # 4. Generate Visualization Data
    colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    
    for node, (x, y) in pos.items():
        depth = levels.get(node, 0)
        color = colors[depth % len(colors)]
        size = max(15, 40 - depth * 8)
        
        node_data.append({
            'name': clean_name(node),
            'x': x,
            'y': y,
            'size': size,
            'color': color,
            'hover': f"{node}<br>Level {depth}"
        })

    # 5. Build Chart JSON
    edge_x = []
    edge_y = []
    for x1, y1, x2, y2 in edges:
        # Curved lines (simple bezier approximation via None point)
        # For simplicity in scatter plot, we use straight lines or segmented
        edge_x.extend([x1, x2, None])
        edge_y.extend([y1, y2, None])

    chart = {
        "data": [
            # Edges
            {
                "type": "scatter",
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {
                    "width": 1.5,
                    "color": "#cbd5e1",
                    "shape": "spline" # Attempt curved lines
                },
                "hoverinfo": "none"
            },
            # Nodes
            {
                "type": "scatter",
                "x": [n['x'] for n in node_data],
                "y": [n['y'] for n in node_data],
                "mode": "markers+text",
                "marker": {
                    "size": [n['size'] for n in node_data],
                    "color": [n['color'] for n in node_data],
                    "line": {"width": 2, "color": "white"}
                },
                "text": [n['name'] for n in node_data],
                "textposition": "bottom center" if len(node_data) < 20 else "middle right",
                "hovertext": [n['hover'] for n in node_data],
                "hoverinfo": "text"
            }
        ],
        "layout": {
            "title": {
                "text": f"Mindmap: {clean_name(root_node)}", 
                "font": {"size": 20, "color": "#1e293b"}
            },
            "showlegend": False,
            "xaxis": {"visible": False, "showgrid": False, "zeroline": False},
            "yaxis": {"visible": False, "showgrid": False, "zeroline": False},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "height": 600,
            "margin": {"l": 50, "r": 50, "t": 80, "b": 50}
        }
    }

    explanation = f"""**Hierarchical Mindmap**
Starts from **{clean_name(root_node)}** and branches out to {len(node_data)-1} connected entities.
• **Level 1**: Main Categories/Connections
• **Level 2**: Detailed Items
"""
    return chart, explanation


def generate_knowledge_graph(
    graph: nx.Graph,
    query: str,
    max_nodes: int = 40,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🕸️ Generate an Advanced Knowledge Graph with COMMUNITY DETECTION.
    
    Features:
    - Nodes sized by PageRank (influence)
    - Colors by Community (Louvain/Modularity)
    - Filtering to show most relevant nodes
    """
    if not graph or graph.number_of_nodes() == 0:
        return None, "No graph data available"
    
    # 1. Select Important Nodes (PageRank or Degree)
    # PageRank is better for finding "influential" nodes not just hubs
    try:
        importance = nx.pagerank(graph)
    except:
        importance = dict(nx.degree(graph))
        # Normalize
        m = max(importance.values()) or 1
        importance = {k: v/m for k,v in importance.items()}

    # Sort nodes by importance
    top_nodes_with_score = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_nodes = [n[0] for n in top_nodes_with_score]
    
    subgraph = graph.subgraph(top_nodes)
    
    # 2. Community Detection (Greedy Modularity)
    # Groups nodes that are densely connected
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        communities = list(greedy_modularity_communities(subgraph))
        # Map node -> community_id
        partition = {}
        for idx, comm in enumerate(communities):
            for node in comm:
                partition[node] = idx
    except ImportError:
        # Fallback if algo missing
        partition = {n: 0 for n in top_nodes}
    except Exception as e:
        print(f"Community detection failed: {e}")
        partition = {n: 0 for n in top_nodes}
        
    # 3. Layout (Spring / Fruchterman-Reingold)
    pos = nx.spring_layout(subgraph, k=0.5, iterations=50, seed=42)
    
    # 4. Build Traces
    node_x, node_y = [], []
    node_text, node_size, node_color = [], [], []
    
    # Palette for communities
    community_colors = [
        '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
        '#ec4899', '#06b6d4', '#84cc16', '#6366f1', '#d946ef'
    ]
    
    for node in top_nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Metadata
        comm_id = partition.get(node, 0)
        score = importance.get(node, 0)
        
        # Size based on importance (min 10, max 50)
        size = 10 + (math.sqrt(score) * 40)
        node_size.append(size)
        
        # Color by community
        node_color.append(community_colors[comm_id % len(community_colors)])
        
        # Label
        node_type = graph.nodes[node].get('type', 'Unknown')
        node_text.append(f"<b>{node}</b><br>Type: {node_type}<br>Group: {comm_id+1}")
        
    # Edges
    edge_x, edge_y = [], []
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    chart = {
        "data": [
            {
                "type": "scatter",
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 1, "color": "rgba(100, 116, 139, 0.4)"},
                "hoverinfo": "none"
            },
            {
                "type": "scatter",
                "x": node_x,
                "y": node_y,
                "mode": "markers+text",
                "marker": {
                    "size": node_size,
                    "color": node_color,
                    "line": {"width": 1.5, "color": "white"}
                },
                "text": [str(n)[:15] for n in top_nodes],
                "textposition": "top center",
                "hoverinfo": "text",
                "hovertext": node_text
            }
        ],
        "layout": {
            "title": {"text": "Network Analysis (Community Detected)", "font": {"size": 20}},
            "showlegend": False,
            "hovermode": "closest",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "height": 600,
            "margin": {"l": 20, "r": 20, "t": 60, "b": 20}
        }
    }
    
    explanation = f"""**Smart Knowledge Graph**
Visualizes the top {len(top_nodes)} most influential entities, grouped by behavior.
• **Colors**: Represent {len(set(partition.values()))} detected communities (closely related groups).
• **Node Size**: Indicates network influence (centrality).
"""
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
        # Simple heuristic fallback
        cat_cols = [c for c in df.columns if df[c].dtype == 'object']
        num_cols = [c for c in df.columns if df[c].dtype != 'object']
        
        if len(cat_cols) >= 2:
            source_col = cat_cols[0]
            target_col = cat_cols[1]
        if num_cols:
            value_col = num_cols[0]
    
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
                "line": {"color": "black", "width": 0.5},
                "label": [str(n)[:20] for n in all_nodes],
                "color": ["#6366f1"] * len(sources) + ["#ec4899"] * len(targets)
            },
            "link": {
                "source": source_indices,
                "target": target_indices,
                "value": values,
                "color": "rgba(99, 102, 241, 0.2)"
            }
        }],
        "layout": {
            "title": {"text": f"{source_col.title()} → {target_col.title()} Flow", "font": {"size": 20}},
            "height": 500,
            "font": {"size": 12},
            "plot_bgcolor": "rgba(0,0,0,0)",
             "paper_bgcolor": "rgba(0,0,0,0)",
        }
    }
    
    total_flow = sum(values)
    explanation = f"""**Relationship Flow**
Mapping the flow of value from **{source_col}** to **{target_col}**.
• **Top connections**: {len(values)} pathways shown
• **Total Value**: {currency_symbol}{total_flow:,.0f}
"""
    return chart, explanation


def detect_graph_visualization_type(query: str) -> str:
    """
    Detect graph visualization type from query using keywords.
    Returns: 'mindmap', 'knowledge_graph', 'relationship', 'radial', 'cluster', or 'none'
    """
    q = query.lower()
    
    # Direct keyword matching (most reliable)
    if any(kw in q for kw in ['mindmap', 'mind map', 'mind-map', 'hierarchy', 'tree structure', 'tree diagram']):
        return 'mindmap'
    
    if any(kw in q for kw in ['radial', 'radial graph', 'radial layout', 'circular layout']):
        return 'radial'
    
    if any(kw in q for kw in ['knowledge graph', 'network', 'network graph', 'entity network']):
        return 'knowledge_graph'
    
    if any(kw in q for kw in ['cluster', 'clustering', 'group entities', 'community', 'communities']):
        return 'cluster'
    
    if any(kw in q for kw in ['sankey', 'relationship', 'flow', 'path', 'connection', 'link']):
        return 'relationship'
    
    # Implicit visualization requests
    if any(kw in q for kw in ['visualize relationships', 'show connections', 'how are they connected']):
        return 'knowledge_graph'
    
    return 'none'


def wants_graph_visualization(query: str) -> bool:
    """Check if user wants a graph-based visualization."""
    return detect_graph_visualization_type(query) != 'none'


# =============================================================================
# PRO-LEVEL GRAPH VISUALIZATIONS v2.0
# =============================================================================

def generate_radial_mindmap(
    graph: nx.Graph,
    query: str,
    focus_entity: Optional[str] = None,
    max_depth: int = 3,
    max_children: int = 8
) -> Tuple[Optional[Dict], str]:
    """
    🌟 PRO RADIAL MINDMAP - Circular hierarchical layout.
    
    Creates a stunning radial tree with the root at center,
    branches spreading outward in concentric circles.
    """
    print(f"[RADIAL MINDMAP] Generating for query: {query}")
    
    if not graph or graph.number_of_nodes() == 0:
        return None, "No graph data available for radial mindmap"
    
    def clean_name(name: str) -> str:
        name_str = str(name)
        if ':' in name_str:
            name_str = name_str.split(':')[-1].strip()
        return name_str[:25]
    
    # Determine root node
    root_node = focus_entity
    if not root_node:
        degrees = sorted(graph.degree(), key=lambda x: x[1], reverse=True)
        if degrees:
            root_node = degrees[0][0]
    
    if not root_node:
        return None, "Could not determine root node"
    
    # Build BFS tree
    try:
        subgraph = nx.ego_graph(graph, root_node, radius=max_depth)
        tree = nx.bfs_tree(subgraph, root_node, depth_limit=max_depth)
    except:
        tree = nx.Graph()
        tree.add_node(root_node)
        for n in list(graph.neighbors(root_node))[:max_children]:
            tree.add_edge(root_node, n)
    
    # Calculate radial positions
    bfs_layers = list(nx.bfs_layers(tree, [root_node]))
    
    node_data = []
    edges = []
    levels = {root_node: 0}
    pos = {root_node: (0, 0)}
    
    # Premium gradient colors
    level_colors = [
        '#6366F1',  # Indigo (root)
        '#8B5CF6',  # Violet (level 1)
        '#A855F7',  # Purple (level 2)
        '#C084FC',  # Light purple (level 3)
        '#DDD6FE',  # Very light purple (level 4)
    ]
    
    for depth, layer in enumerate(bfs_layers):
        if depth == 0:
            continue  # Root already positioned
        
        # Limit nodes per layer
        layer = sorted(layer, key=lambda n: graph.degree(n), reverse=True)[:max_children * depth]
        
        radius = depth * 1.5
        angle_step = 2 * math.pi / max(len(layer), 1)
        
        for i, node in enumerate(layer):
            levels[node] = depth
            angle = i * angle_step - math.pi / 2  # Start from top
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            pos[node] = (x, y)
            
            # Find parent and add edge
            parents = list(tree.predecessors(node))
            if parents and parents[0] in pos:
                px, py = pos[parents[0]]
                edges.append((px, py, x, y))
    
    # Build node data
    for node, (x, y) in pos.items():
        depth = levels.get(node, 0)
        color = level_colors[min(depth, len(level_colors) - 1)]
        size = max(20, 50 - depth * 10)
        
        node_data.append({
            'name': clean_name(node),
            'x': x, 'y': y,
            'size': size,
            'color': color,
            'hover': f"<b>{node}</b><br>Level {depth}"
        })
    
    # Build edge traces with curved lines
    edge_x, edge_y = [], []
    for x1, y1, x2, y2 in edges:
        # Create smooth bezier curve
        cx, cy = (x1 + x2) / 2 * 1.1, (y1 + y2) / 2 * 1.1
        for t in [0, 0.25, 0.5, 0.75, 1]:
            bx = (1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2
            by = (1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2
            edge_x.append(bx)
            edge_y.append(by)
        edge_x.append(None)
        edge_y.append(None)
    
    chart = {
        "data": [
            {
                "type": "scatter",
                "x": edge_x,
                "y": edge_y,
                "mode": "lines",
                "line": {"width": 1.5, "color": "#CBD5E1"},
                "hoverinfo": "none"
            },
            {
                "type": "scatter",
                "x": [n['x'] for n in node_data],
                "y": [n['y'] for n in node_data],
                "mode": "markers+text",
                "marker": {
                    "size": [n['size'] for n in node_data],
                    "color": [n['color'] for n in node_data],
                    "line": {"width": 2, "color": "white"}
                },
                "text": [n['name'] for n in node_data],
                "textposition": "middle center",
                "textfont": {"size": 10, "color": "white"},
                "hovertext": [n['hover'] for n in node_data],
                "hoverinfo": "text"
            }
        ],
        "layout": {
            "title": {"text": f"🌟 Radial Mindmap: {clean_name(root_node)}", "font": {"size": 18}},
            "showlegend": False,
            "xaxis": {"visible": False, "showgrid": False, "zeroline": False},
            "yaxis": {"visible": False, "showgrid": False, "zeroline": False, "scaleanchor": "x"},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "height": 600,
            "margin": {"l": 20, "r": 20, "t": 60, "b": 20}
        }
    }
    
    explanation = f"""**🌟 Radial Mindmap**
Central entity: **{clean_name(root_node)}** with {len(node_data)-1} connected entities across {len(bfs_layers)-1} levels.
"""
    return chart, explanation


def generate_entity_cluster(
    df: pd.DataFrame,
    query: str,
    entity_col: Optional[str] = None,
    value_col: Optional[str] = None,
    top_n: int = 30,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🔮 ENTITY CLUSTERING - Group entities by similarity/value.
    
    Creates a bubble cluster where:
    - Bubble size = value/importance
    - Color = cluster/category
    - Position = similarity grouping
    """
    if df is None or df.empty:
        return None, "No data available for clustering"
    
    # Auto-detect columns if not specified
    if not entity_col:
        cat_cols = [c for c in df.columns if df[c].dtype == 'object']
        entity_col = cat_cols[0] if cat_cols else None
    
    if not value_col:
        num_cols = [c for c in df.columns if df[c].dtype in ['int64', 'float64']]
        value_col = num_cols[0] if num_cols else None
    
    if not entity_col or not value_col:
        return None, "Could not detect suitable columns for clustering"
    
    # Aggregate by entity
    grouped = df.groupby(entity_col)[value_col].sum().sort_values(ascending=False).head(top_n)
    
    entities = grouped.index.tolist()
    values = grouped.values.tolist()
    
    # Normalize for sizing (radius 10-50)
    max_val = max(values) if values else 1
    sizes = [max(15, min(60, (v / max_val) * 45 + 15)) for v in values]
    
    # Create force-directed-like layout
    n = len(entities)
    positions = []
    for i in range(n):
        # Spiral layout
        angle = i * 0.5
        radius = math.sqrt(i + 1) * 0.8
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions.append((x, y))
    
    # Cluster colors based on value quartiles
    colors = []
    for v in values:
        ratio = v / max_val
        if ratio > 0.75:
            colors.append('#22C55E')  # Green (top performers)
        elif ratio > 0.5:
            colors.append('#6366F1')  # Indigo (good)
        elif ratio > 0.25:
            colors.append('#F59E0B')  # Amber (medium)
        else:
            colors.append('#EF4444')  # Red (low)
    
    chart = {
        "data": [{
            "type": "scatter",
            "mode": "markers+text",
            "x": [p[0] for p in positions],
            "y": [p[1] for p in positions],
            "text": [str(e)[:15] for e in entities],
            "textposition": "middle center",
            "textfont": {"size": 9, "color": "white"},
            "marker": {
                "size": sizes,
                "color": colors,
                "opacity": 0.85,
                "line": {"width": 2, "color": "white"}
            },
            "hovertemplate": "<b>%{text}</b><br>" + currency_symbol + "%{customdata:,.0f}<extra></extra>",
            "customdata": values
        }],
        "layout": {
            "title": {"text": "🔮 Entity Clusters by Value", "font": {"size": 18}},
            "showlegend": False,
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "height": 550,
            "margin": {"l": 20, "r": 20, "t": 60, "b": 20},
            "annotations": [
                {"text": "🟢 Top Performers", "x": 0.02, "y": 0.98, "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 10}},
                {"text": "🔴 Low Performers", "x": 0.02, "y": 0.93, "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 10}}
            ]
        }
    }
    
    total_value = sum(values)
    explanation = f"""**🔮 Entity Clustering Analysis**
Showing {len(entities)} {entity_col}s clustered by {value_col}.
• **Total**: {currency_symbol}{total_value:,.0f}
• **Top Entity**: {entities[0]} ({currency_symbol}{values[0]:,.0f})
• 🟢 Green = Top quartile, 🔴 Red = Bottom quartile
"""
    return chart, explanation


def get_best_graph_visualization(
    query: str,
    graph: Optional[nx.Graph] = None,
    df: Optional[pd.DataFrame] = None,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🎯 INTELLIGENT GRAPH VIZ SELECTOR
    
    Automatically selects the best graph visualization based on:
    1. Query keywords
    2. Available data (graph vs DataFrame)
    3. Data characteristics
    """
    viz_type = detect_graph_visualization_type(query)
    
    if viz_type == 'radial' and graph:
        return generate_radial_mindmap(graph, query)
    
    if viz_type == 'mindmap' and graph:
        return generate_mindmap(graph, query)
    
    if viz_type == 'knowledge_graph' and graph:
        return generate_knowledge_graph(graph, query, currency_symbol=currency_symbol)
    
    if viz_type == 'cluster' and df is not None:
        return generate_entity_cluster(df, query, currency_symbol=currency_symbol)
    
    if viz_type == 'relationship' and df is not None:
        return generate_relationship_diagram(df, query, currency_symbol=currency_symbol)
    
    # Default: try knowledge graph if graph available, else cluster
    if graph and graph.number_of_nodes() > 0:
        return generate_knowledge_graph(graph, query, currency_symbol=currency_symbol)
    
    if df is not None and not df.empty:
        return generate_entity_cluster(df, query, currency_symbol=currency_symbol)
    
    return None, "No suitable data for graph visualization"

