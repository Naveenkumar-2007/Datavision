"""
Mind Map Renderer - Mermaid Format
===================================

Converts mind map data to Mermaid mindmap syntax
for rendering in frontend.

Supports:
- Hierarchical mind maps
- Relationship graphs (flowchart)
- Entity diagrams
"""

from typing import Dict, List, Any


def render_mind_map_to_mermaid(mind_map_data: Dict[str, Any]) -> str:
    """
    Convert mind map structure to Mermaid mindmap syntax.
    
    Example output:
    ```mermaid
    mindmap
      root((Business Overview))
        Revenue
          By Product
            Product A: ₹50,000
            Product B: ₹30,000
          By Category
            Digital: ₹45,000
            Physical: ₹35,000
        Customers
          Top Customers
            Customer_33
            Customer_42
        Products
          Best Sellers
    ```
    """
    if not mind_map_data or "root" not in mind_map_data.get("mind_map", {}):
        return "mindmap\n  root((No Data))"
    
    root = mind_map_data.get("mind_map", {}).get("root", {})
    
    lines = ["mindmap"]
    lines.append(f"  root(({root.get('label', 'Business')}))")
    
    def render_children(children: List[Dict], indent: int = 2):
        result = []
        for child in children:
            label = child.get("label", "Item")
            icon = child.get("icon", "")
            if icon:
                label = f"{icon} {label}"
            
            result.append("  " * indent + label)
            
            if child.get("children"):
                result.extend(render_children(child["children"], indent + 1))
        
        return result
    
    if root.get("children"):
        lines.extend(render_children(root["children"]))
    
    return "\n".join(lines)


def render_relationship_graph_to_mermaid(graph_data: Dict[str, Any]) -> str:
    """
    Convert relationship graph to Mermaid flowchart syntax.
    
    Example output:
    ```mermaid
    flowchart TD
        subgraph Customers
            C1[Customer_33]
            C2[Customer_42]
        end
        subgraph Products
            P1[Product A]
            P2[Product B]
        end
        subgraph Revenue
            R[₹548,765]
        end
        C1 -->|₹50,000| R
        C2 -->|₹30,000| R
        P1 -->|₹45,000| R
        P2 -->|₹35,000| R
    ```
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    if not nodes:
        return "flowchart TD\n    N[No Data Available]"
    
    lines = ["flowchart TD"]
    
    # Group nodes by type
    customers = [n for n in nodes if n.get("type") == "customer"]
    products = [n for n in nodes if n.get("type") == "product"]
    metrics = [n for n in nodes if n.get("type") == "metric"]
    
    # Customer subgraph
    if customers:
        lines.append("    subgraph Customers")
        for i, c in enumerate(customers):
            label = c.get("label", f"Customer_{i}")
            lines.append(f"        {c.get('id', f'c{i}')}[{label}]")
        lines.append("    end")
    
    # Product subgraph
    if products:
        lines.append("    subgraph Products")
        for i, p in enumerate(products):
            label = p.get("label", f"Product_{i}")
            lines.append(f"        {p.get('id', f'p{i}')}[{label}]")
        lines.append("    end")
    
    # Metric nodes (central)
    for m in metrics:
        label = m.get("label", "Revenue")
        lines.append(f"    {m.get('id', 'revenue')}(({label}))")
    
    # Edges
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        label = edge.get("label", edge.get("relationship", ""))
        
        if label:
            lines.append(f"    {source} -->|{label}| {target}")
        else:
            lines.append(f"    {source} --> {target}")
    
    return "\n".join(lines)


def render_sankey_to_mermaid(data: Dict[str, Any]) -> str:
    """
    Render Sankey diagram in Mermaid syntax.
    
    Example:
    ```mermaid
    sankey-beta
    Customer_33, Product_A, 50000
    Customer_33, Product_B, 30000
    Product_A, Revenue, 45000
    ```
    """
    flows = data.get("flows", [])
    
    if not flows:
        return "sankey-beta\n  No Data, Available, 1"
    
    lines = ["sankey-beta"]
    for flow in flows:
        source = flow.get("source", "Source")
        target = flow.get("target", "Target")
        value = flow.get("value", 1)
        lines.append(f"  {source}, {target}, {value}")
    
    return "\n".join(lines)


def render_tree_to_mermaid(data: Dict[str, Any]) -> str:
    """
    Render tree diagram in Mermaid syntax.
    
    Example:
    ```mermaid
    graph TD
        A[Revenue] --> B[Products]
        A --> C[Customers]
        B --> D[Product A]
        B --> E[Product B]
    ```
    """
    root = data.get("root", {})
    
    if not root:
        return "graph TD\n    A[No Data]"
    
    lines = ["graph TD"]
    node_counter = [0]
    
    def get_node_id():
        node_counter[0] += 1
        return f"N{node_counter[0]}"
    
    def render_node(node: Dict, parent_id: str = None) -> List[str]:
        result = []
        node_id = get_node_id()
        label = node.get("label", "Node")
        
        result.append(f"    {node_id}[{label}]")
        
        if parent_id:
            result.append(f"    {parent_id} --> {node_id}")
        
        for child in node.get("children", []):
            result.extend(render_node(child, node_id))
        
        return result
    
    lines.extend(render_node(root))
    return "\n".join(lines)


def generate_mermaid_visual(
    visual_type: str,
    data: Dict[str, Any]
) -> str:
    """
    Generate Mermaid diagram based on visual type.
    
    Args:
        visual_type: 'mind_map', 'relationship_graph', 'sankey', 'tree'
        data: Visual data structure
        
    Returns:
        Mermaid syntax string
    """
    renderers = {
        "mind_map": render_mind_map_to_mermaid,
        "relationship_graph": render_relationship_graph_to_mermaid,
        "sankey": render_sankey_to_mermaid,
        "tree": render_tree_to_mermaid,
    }
    
    renderer = renderers.get(visual_type, render_mind_map_to_mermaid)
    return renderer(data)


def create_mermaid_response(
    visual_data: Dict[str, Any],
    include_insight: bool = True
) -> str:
    """
    Create complete Mermaid response with diagram and insights.
    
    Returns markdown with embedded Mermaid diagram.
    """
    visual_type = visual_data.get("visual_type", "mind_map")
    mermaid_code = generate_mermaid_visual(visual_type, visual_data)
    
    title = visual_data.get("title", "Business Visualization")
    insight = visual_data.get("insight", "")
    recommendation = visual_data.get("recommendation", "")
    
    response = f"""## 📊 {title}

```mermaid
{mermaid_code}
```

"""
    if include_insight and insight:
        response += f"""### 💡 Insight
{insight}

"""
    
    if include_insight and recommendation:
        response += f"""### 💼 Recommendation
{recommendation}
"""
    
    return response


def render_ascii_mind_map(mind_map_data: Dict[str, Any]) -> str:
    """
    Render mind map as ASCII/Unicode tree that works EVERYWHERE.
    
    Example:
    📊 Business Overview
    ├── 💰 Revenue: ₹548,765
    │   ├── By Product
    │   │   ├── Digital Product: ₹422,757
    │   │   └── Service: ₹126,007
    │   └── By Customer
    │       ├── Customer_33: ₹29,752
    │       └── Customer_25: ₹26,807
    ├── 👥 Customers: 50
    │   └── Top Customers
    │       ├── Customer_33
    │       └── Customer_25
    └── 📦 Products: 2
    """
    if not mind_map_data or "root" not in mind_map_data.get("mind_map", {}):
        return "📊 No Data Available"
    
    root = mind_map_data.get("mind_map", {}).get("root", {})
    
    lines = [f"📊 **{root.get('label', 'Business')}**"]
    
    def render_children(children: List[Dict], prefix: str = "", is_last: bool = False):
        result = []
        for i, child in enumerate(children):
            is_child_last = i == len(children) - 1
            
            # Choose connector
            connector = "└── " if is_child_last else "├── "
            
            # Build label
            label = child.get("label", "Item")
            icon = child.get("icon", "")
            if icon:
                label = f"{icon} {label}"
            
            result.append(f"{prefix}{connector}{label}")
            
            # Process sub-children
            if child.get("children"):
                # Choose continuation prefix
                new_prefix = prefix + ("    " if is_child_last else "│   ")
                result.extend(render_children(child["children"], new_prefix))
        
        return result
    
    if root.get("children"):
        lines.extend(render_children(root["children"]))
    
    return "\n".join(lines)


def render_ascii_relationship_graph(graph_data: Dict[str, Any]) -> str:
    """
    Render relationship graph as ASCII format.
    
    Example:
    🔗 Business Relationship Map
    
    👥 CUSTOMERS          📦 PRODUCTS          💰 REVENUE
    ───────────          ──────────          ─────────
    Customer_33 ──┐                          
    Customer_25 ──┤──→ Digital Product ──→  ₹422,757
    Customer_39 ──┤
    Customer_45 ──┘──→ Service ─────────→  ₹126,007
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    if not nodes:
        return "🔗 No Relationship Data Available"
    
    customers = [n for n in nodes if n.get("type") == "customer"]
    products = [n for n in nodes if n.get("type") == "product"]
    
    lines = ["🔗 **Business Relationship Map**", ""]
    
    # Show customers
    if customers:
        lines.append("**👥 Customers:**")
        for c in customers[:5]:
            value = c.get("value", 0)
            lines.append(f"  • {c.get('label', 'Customer')} → ₹{value:,.0f}")
    
    lines.append("")
    
    # Show products
    if products:
        lines.append("**📦 Products:**")
        for p in products[:5]:
            value = p.get("value", 0)
            lines.append(f"  • {p.get('label', 'Product')} → ₹{value:,.0f}")
    
    lines.append("")
    
    # Show connections summary
    lines.append(f"**🔗 Connections:** {len(edges)} relationships")
    
    return "\n".join(lines)


def create_visual_response(
    visual_data: Dict[str, Any],
    use_ascii: bool = True
) -> str:
    """
    Create visual response - uses ASCII format for universal compatibility.
    
    Args:
        visual_data: Data from visual_intelligence.py
        use_ascii: If True, use ASCII tree format (works everywhere)
        
    Returns:
        Markdown-formatted response with visual tree
    """
    visual_type = visual_data.get("visual_type", "mind_map")
    title = visual_data.get("title", "Business Visualization")
    insight = visual_data.get("insight", "")
    recommendation = visual_data.get("recommendation", "")
    
    # Generate ASCII visual
    if visual_type == "mind_map":
        visual = render_ascii_mind_map(visual_data)
    elif visual_type == "relationship_graph":
        visual = render_ascii_relationship_graph(visual_data)
    else:
        visual = render_ascii_mind_map(visual_data)  # Default to mind map
    
    response = f"""## 📊 {title}

```
{visual}
```

"""
    if insight:
        response += f"""💡 **Insight:** {insight}

"""
    
    if recommendation:
        response += f"""💼 **Recommendation:** {recommendation}
"""
    
    return response

