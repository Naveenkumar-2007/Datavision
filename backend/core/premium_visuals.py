"""
ANSWER-DRIVEN VISUAL GRAPHS
===========================

CORE PRINCIPLE:
Graph is built from the SAME DATA the LLM used to generate its answer.
NOT from query parsing. NOT hardcoded.

The graph shows EXACTLY the entities in vi_data:
- top_customers: what the LLM knows as top customers
- lowest_customers: what the LLM knows as lowest customers
- top_products: what the LLM knows as products

This ensures graph ALWAYS matches the LLM answer.
"""

import math
import re
from typing import Dict, List, Any, Optional


# ============================================================================
# COLORS
# ============================================================================

COLORS = {
    "customer": "#10b981",      # Emerald green
    "product": "#3b82f6",       # Blue
    "revenue": "#f97316",       # Orange
    "center": "#8b5cf6",        # Purple
    "edge": "#9ca3af",          # Gray
    "top": "#22c55e",           # Green (top performers)
    "low": "#ef4444",           # Red (low performers)
    "border": "#ffffff",
}


# ============================================================================
# DETECT WHAT QUERY IS ASKING FOR
# ============================================================================

def detect_query_intent(query: str) -> Dict[str, Any]:
    """
    Simple intent detection - what type of visualization?
    """
    q = query.lower()
    
    return {
        "is_comparison": any(w in q for w in ['vs', 'versus', 'compare', 'against', 'compared']),
        "wants_top": any(w in q for w in ['top', 'best', 'highest', 'leading']),
        "wants_low": any(w in q for w in ['lowest', 'bottom', 'worst', 'least', 'lowest-revenue']),
        "focus_customer": 'customer' in q,
        "focus_product": 'product' in q,
    }


# ============================================================================
# KNOWLEDGE GRAPH - Built from actual data
# ============================================================================

def generate_knowledge_graph_plotly(
    data: Dict[str, Any],
    currency_symbol: str = "₹",
    query: str = ""
) -> Dict[str, Any]:
    """
    Generate knowledge graph from the ACTUAL DATA in vi_data.
    
    Handles BOTH customer and product queries:
    - "top customer vs lowest" → shows customers
    - "top product vs lowest" → shows products
    """
    # Get ALL available data
    top_customers = data.get("top_customers", [])
    lowest_customers = data.get("lowest_customers", [])
    top_products = data.get("top_products", [])
    lowest_products = data.get("lowest_products", [])
    total_revenue = data.get("total_revenue", 0)
    
    # Detect intent
    intent = detect_query_intent(query)
    
    # Determine if query is about products or customers
    is_product_query = intent["focus_product"] and not intent["focus_customer"]
    
    # Build entity list based on query
    # Data is ALREADY limited based on query at source (vi_data preparation)
    entities_to_show = []
    entity_label = "Customer"
    
    # Extract limit from query (e.g., "top 6" → 6, default 10)
    import re
    limit_match = re.search(r'top\s*(\d+)', query.lower())
    query_limit = int(limit_match.group(1)) if limit_match else len(top_customers) or 6
    
    if is_product_query:
        # PRODUCT focused query
        entity_label = "Product"
        if intent["is_comparison"] and intent["wants_top"] and intent["wants_low"]:
            if top_products:
                entities_to_show.append({**top_products[0], "_type": "top"})
            for p in lowest_products[:3]:
                entities_to_show.append({**p, "_type": "low"})
        elif intent["wants_low"]:
            for p in lowest_products[:query_limit]:
                entities_to_show.append({**p, "_type": "low"})
        elif intent["wants_top"]:
            # Use ALL top_products (already limited by query at source)
            for p in top_products[:query_limit]:
                entities_to_show.append({**p, "_type": "top"})
        else:
            for p in top_products[:query_limit]:
                entities_to_show.append({**p, "_type": "normal"})
    else:
        # CUSTOMER focused query (default)
        entity_label = "Customer"
        if intent["is_comparison"] and intent["wants_top"] and intent["wants_low"]:
            if top_customers:
                entities_to_show.append({**top_customers[0], "_type": "top"})
            for c in lowest_customers[:3]:
                entities_to_show.append({**c, "_type": "low"})
        elif intent["wants_low"]:
            for c in lowest_customers[:query_limit]:
                entities_to_show.append({**c, "_type": "low"})
        elif intent["wants_top"]:
            # Use query_limit (e.g., "top 6" shows 6)
            for c in top_customers[:query_limit]:
                entities_to_show.append({**c, "_type": "top"})
        else:
            for c in top_customers[:query_limit]:
                entities_to_show.append({**c, "_type": "normal"})
    
    # Build graph
    nodes_x = []
    nodes_y = []
    node_colors = []
    node_sizes = []
    node_hovers = []
    edge_x = []
    edge_y = []
    annotations = []
    
    # CENTER NODE
    nodes_x.append(0)
    nodes_y.append(0)
    node_colors.append(COLORS["revenue"])
    node_sizes.append(55)
    node_hovers.append(f"Revenue: {currency_symbol}{total_revenue:,.0f}")
    
    annotations.append({
        "x": 0, "y": -0.5,
        "text": f"Revenue<br>{currency_symbol}{total_revenue:,.0f}",
        "showarrow": False,
        "font": {"size": 10, "color": "#374151"}
    })
    
    # ENTITY NODES (customers or products based on query)
    num_entities = len(entities_to_show)
    
    for i, entity in enumerate(entities_to_show):
        # Dynamic positioning
        if num_entities <= 2:
            y = (i - 0.5) * 1.5
        else:
            y = (i - (num_entities - 1) / 2) * (2.8 / max(num_entities - 1, 1))
        
        name = entity.get("name", entity_label)
        revenue = entity.get("revenue", 0)
        entity_type = entity.get("_type", "normal")
        
        # Color based on type
        if entity_type == "top":
            color = COLORS["top"]
            size = 40
        elif entity_type == "low":
            color = COLORS["low"]
            size = 30
        else:
            color = COLORS["customer"] if not is_product_query else COLORS["product"]
            size = 35
        
        x_pos = -3
        nodes_x.append(x_pos)
        nodes_y.append(y)
        node_colors.append(color)
        node_sizes.append(size)
        node_hovers.append(f"{name}: {currency_symbol}{revenue:,.0f}")
        
        edge_x.extend([x_pos, 0, None])
        edge_y.extend([y, 0, None])
        
        annotations.append({
            "x": x_pos - 0.4, "y": y,
            "text": name,
            "showarrow": False,
            "font": {"size": 9, "color": "#374151"},
            "xanchor": "right"
        })
    
    # PRODUCT NODES (only show if NOT product-focused query - to avoid duplication)
    if not is_product_query:
        products_to_show = top_products[:min(len(top_products), 3)]
        num_prod = len(products_to_show)
        
        for i, prod in enumerate(products_to_show):
            if num_prod == 1:
                y = 0
            else:
                y = (i - (num_prod - 1) / 2) * 1.0
            
            name = prod.get("name", "Product")
            revenue = prod.get("revenue", 0)
            
            nodes_x.append(3)
            nodes_y.append(y)
            node_colors.append(COLORS["product"])
            node_sizes.append(40)
            node_hovers.append(f"{name}: {currency_symbol}{revenue:,.0f}")
            
            edge_x.extend([3, 0, None])
            edge_y.extend([y, 0, None])
            
            annotations.append({
                "x": 3.4, "y": y,
                "text": name,
                "showarrow": False,
                "font": {"size": 10, "color": "#374151"},
                "xanchor": "left"
            })
    
    # FOOTER
    top_count = sum(1 for e in entities_to_show if e.get("_type") == "top")
    low_count = sum(1 for e in entities_to_show if e.get("_type") == "low")
    
    # Calculate counts from entities shown
    num_entities = len(entities_to_show)
    
    entity_name = "products" if is_product_query else "customers"
    if top_count > 0 and low_count > 0:
        footer = f"{top_count} top (green) + {low_count} lowest (red) {entity_name}"
    elif top_count > 0:
        footer = f"{top_count} top {entity_name} (green)"
    elif low_count > 0:
        footer = f"{low_count} lowest customers (red)"
    else:
        footer = f"{num_entities} {entity_name} shown"
    
    annotations.append({
        "x": 0.5, "y": -0.08, "xref": "paper", "yref": "paper",
        "text": footer,
        "showarrow": False,
        "font": {"size": 11, "color": "#6b7280"}
    })
    
    chart = {
        "data": [
            {
                "type": "scatter",
                "x": edge_x, "y": edge_y,
                "mode": "lines",
                "line": {"width": 1.5, "color": COLORS["edge"]},
                "hoverinfo": "none",
                "showlegend": False
            },
            {
                "type": "scatter",
                "x": nodes_x, "y": nodes_y,
                "mode": "markers",
                "marker": {
                    "size": node_sizes,
                    "color": node_colors,
                    "line": {"width": 2, "color": COLORS["border"]}
                },
                "hovertext": node_hovers,
                "hoverinfo": "text",
                "showlegend": False
            }
        ],
        "layout": {
            "title": {"text": "Knowledge Graph", "font": {"size": 18}},
            "showlegend": False,
            "hovermode": "closest",
            "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-5, 5]},
            "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-2.5, 2.5]},
            "margin": {"l": 70, "r": 70, "t": 50, "b": 40},
            "height": 400,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "annotations": annotations
        }
    }
    
    return chart


# ============================================================================
# MIND MAP - Built from actual data
# ============================================================================

def generate_mind_map_plotly(
    data: Dict[str, Any],
    currency_symbol: str = "₹",
    query: str = ""
) -> Dict[str, Any]:
    """
    Mind map showing actual business structure from data.
    """
    total_revenue = data.get("total_revenue", 0)
    customer_count = data.get("customer_count", 0)
    product_count = data.get("product_count", 0)
    top_customers = data.get("top_customers", [])
    top_products = data.get("top_products", [])
    
    nodes_x = []
    nodes_y = []
    node_colors = []
    node_sizes = []
    node_hovers = []
    edge_x = []
    edge_y = []
    annotations = []
    
    # CENTER
    nodes_x.append(0)
    nodes_y.append(0)
    node_colors.append(COLORS["center"])
    node_sizes.append(55)
    node_hovers.append(f"Total: {currency_symbol}{total_revenue:,.0f}")
    
    annotations.append({
        "x": 0, "y": 0.1,
        "text": "Business",
        "showarrow": False,
        "font": {"size": 10, "color": "#374151"}
    })
    
    # REVENUE (right)
    nodes_x.append(2)
    nodes_y.append(0)
    node_colors.append(COLORS["revenue"])
    node_sizes.append(42)
    node_hovers.append(f"Revenue: {currency_symbol}{total_revenue:,.0f}")
    edge_x.extend([0, 2, None])
    edge_y.extend([0, 0, None])
    
    annotations.append({
        "x": 2.5, "y": 0,
        "text": f"Revenue: {currency_symbol}{total_revenue:,.0f}",
        "showarrow": False,
        "font": {"size": 9, "color": "#374151"},
        "xanchor": "left"
    })
    
    # CUSTOMERS (top-left)
    nodes_x.append(-1.3)
    nodes_y.append(1.5)
    node_colors.append(COLORS["customer"])
    node_sizes.append(38)
    node_hovers.append(f"{customer_count} customers")
    edge_x.extend([0, -1.3, None])
    edge_y.extend([0, 1.5, None])
    
    annotations.append({
        "x": -1.3, "y": 1.9,
        "text": f"Customers: {customer_count}",
        "showarrow": False,
        "font": {"size": 9, "color": "#374151"}
    })
    
    # Customer leaves (from actual data)
    for i, cust in enumerate(top_customers[:4]):
        lx = -2.2 + (i * 0.4)
        ly = 2.3 + (i % 2) * 0.25
        
        nodes_x.append(lx)
        nodes_y.append(ly)
        node_colors.append("#86efac")
        node_sizes.append(18)
        
        name = cust.get("name", "C")
        revenue = cust.get("revenue", 0)
        node_hovers.append(f"{name}: {currency_symbol}{revenue:,.0f}")
        
        edge_x.extend([-1.3, lx, None])
        edge_y.extend([1.5, ly, None])
        
        annotations.append({
            "x": lx, "y": ly + 0.25,
            "text": name,
            "showarrow": False,
            "font": {"size": 7, "color": "#6b7280"}
        })
    
    # PRODUCTS (bottom-left)
    nodes_x.append(-1.3)
    nodes_y.append(-1.5)
    node_colors.append(COLORS["product"])
    node_sizes.append(38)
    node_hovers.append(f"{product_count} products")
    edge_x.extend([0, -1.3, None])
    edge_y.extend([0, -1.5, None])
    
    annotations.append({
        "x": -1.3, "y": -1.9,
        "text": f"Products: {product_count}",
        "showarrow": False,
        "font": {"size": 9, "color": "#374151"}
    })
    
    # Product leaves (from actual data)
    for i, prod in enumerate(top_products[:3]):
        lx = -2 + (i * 0.4)
        ly = -2.2 - (i % 2) * 0.2
        
        nodes_x.append(lx)
        nodes_y.append(ly)
        node_colors.append("#93c5fd")
        node_sizes.append(18)
        
        name = prod.get("name", "P")
        revenue = prod.get("revenue", 0)
        node_hovers.append(f"{name}: {currency_symbol}{revenue:,.0f}")
        
        edge_x.extend([-1.3, lx, None])
        edge_y.extend([-1.5, ly, None])
        
        annotations.append({
            "x": lx, "y": ly - 0.25,
            "text": name,
            "showarrow": False,
            "font": {"size": 7, "color": "#6b7280"}
        })
    
    chart = {
        "data": [
            {"type": "scatter", "x": edge_x, "y": edge_y, "mode": "lines",
             "line": {"width": 2, "color": COLORS["edge"]}, "hoverinfo": "none", "showlegend": False},
            {"type": "scatter", "x": nodes_x, "y": nodes_y, "mode": "markers",
             "marker": {"size": node_sizes, "color": node_colors, "line": {"width": 2, "color": COLORS["border"]}},
             "hovertext": node_hovers, "hoverinfo": "text", "showlegend": False}
        ],
        "layout": {
            "title": {"text": "Mind Map", "font": {"size": 18}},
            "showlegend": False,
            "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-3.5, 3.5]},
            "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False, "range": [-3, 3]},
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "height": 380,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "annotations": annotations
        }
    }
    
    return chart


# ============================================================================
# KPI DASHBOARD - From actual data
# ============================================================================

def generate_kpi_dashboard_plotly(
    data: Dict[str, Any],
    currency_symbol: str = "₹",
    query: str = ""
) -> Dict[str, Any]:
    """KPI Dashboard from actual data metrics."""
    total_revenue = data.get("total_revenue", 0)
    customer_count = data.get("customer_count", 0)
    order_count = data.get("order_count", 0)
    
    avg_order = total_revenue / order_count if order_count > 0 else 0
    avg_customer = total_revenue / customer_count if customer_count > 0 else 0
    
    chart = {
        "data": [
            {"type": "indicator", "mode": "number", "value": total_revenue,
             "number": {"prefix": currency_symbol, "font": {"size": 40, "color": COLORS["revenue"]}},
             "title": {"text": "Revenue", "font": {"size": 13}},
             "domain": {"x": [0, 0.33], "y": [0.55, 1]}},
            {"type": "indicator", "mode": "number", "value": customer_count,
             "number": {"font": {"size": 40, "color": COLORS["customer"]}},
             "title": {"text": "Customers", "font": {"size": 13}},
             "domain": {"x": [0.33, 0.66], "y": [0.55, 1]}},
            {"type": "indicator", "mode": "number", "value": order_count,
             "number": {"font": {"size": 40, "color": COLORS["product"]}},
             "title": {"text": "Orders", "font": {"size": 13}},
             "domain": {"x": [0.66, 1], "y": [0.55, 1]}},
            {"type": "indicator", "mode": "number", "value": avg_order,
             "number": {"prefix": currency_symbol, "font": {"size": 34, "color": COLORS["center"]}},
             "title": {"text": "Avg Order", "font": {"size": 11}},
             "domain": {"x": [0.15, 0.5], "y": [0, 0.45]}},
            {"type": "indicator", "mode": "number", "value": avg_customer,
             "number": {"prefix": currency_symbol, "font": {"size": 34, "color": "#06b6d4"}},
             "title": {"text": "Avg Customer", "font": {"size": 11}},
             "domain": {"x": [0.5, 0.85], "y": [0, 0.45]}}
        ],
        "layout": {
            "title": {"text": "KPI Dashboard", "font": {"size": 18}},
            "margin": {"l": 15, "r": 15, "t": 50, "b": 15},
            "height": 350,
            "paper_bgcolor": "rgba(0,0,0,0)"
        }
    }
    
    return chart


# ============================================================================
# MAIN
# ============================================================================

def generate_premium_visual(
    query: str,
    data: Dict[str, Any],
    currency_symbol: str = "₹"
) -> Optional[Dict[str, Any]]:
    """
    Generate visualization based on query type.
    The graph uses the SAME data the LLM used.
    """
    q = query.lower()
    
    if any(w in q for w in ['mind map', 'overview', 'summary', 'structure']):
        return generate_mind_map_plotly(data, currency_symbol, query)
    elif any(w in q for w in ['knowledge', 'relationship', 'network', 'graph', 'vs', 'versus', 'compare']):
        return generate_knowledge_graph_plotly(data, currency_symbol, query)
    elif any(w in q for w in ['kpi', 'dashboard', 'metrics', 'performance']):
        return generate_kpi_dashboard_plotly(data, currency_symbol, query)
    
    return None
