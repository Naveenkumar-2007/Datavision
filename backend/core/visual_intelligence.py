"""
$500K GRAPH MODE - Visual Intelligence Engine
==============================================

PALANTIR-LEVEL VISUAL REASONING SYSTEM

Features:
1. Smart Chart Selection (Auto)
2. Mind Map Generator (AI-driven)
3. Relationship Graphs (Knowledge Graph style)
4. Insight-First Visualizations
5. Decision Recommendations

PHILOSOPHY: Not just charts - VISUAL REASONING.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


# ============================================================================
# VISUAL TYPES - What we can generate
# ============================================================================

class VisualType(Enum):
    """All supported visual types"""
    # Standard Charts
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    HEATMAP = "heatmap"
    SCATTER = "scatter"
    
    # Advanced Intelligence
    MIND_MAP = "mind_map"
    RELATIONSHIP_GRAPH = "relationship_graph"
    SANKEY = "sankey"
    TREE = "tree"
    NETWORK = "network"
    
    # Decision
    KPI_DASHBOARD = "kpi_dashboard"
    COMPARISON = "comparison"
    FORECAST = "forecast"


@dataclass
class VisualArtifact:
    """A complete visual artifact with explanation"""
    visual_type: VisualType
    title: str
    data: Dict[str, Any]
    insight: str
    recommendation: str
    explanation: str
    sources: List[str] = field(default_factory=list)


@dataclass
class MindMapNode:
    """Node in a mind map"""
    id: str
    label: str
    value: Optional[float] = None
    children: List['MindMapNode'] = field(default_factory=list)
    color: str = "#667eea"
    icon: str = ""


@dataclass
class RelationshipEdge:
    """Edge in relationship graph"""
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    color: str = "#667eea"


@dataclass
class GraphNode:
    """Node in knowledge graph"""
    id: str
    label: str
    node_type: str  # customer, product, category, metric
    value: Optional[float] = None
    color: str = "#667eea"
    size: int = 20


# ============================================================================
# VISUAL INTELLIGENCE ENGINE - Core System
# ============================================================================

class VisualIntelligenceEngine:
    """
    $500K Visual Intelligence Engine
    
    Converts business data into:
    - Decision-ready visualizations
    - AI-generated mind maps
    - Knowledge graphs
    - Insight-first outputs
    """
    
    # Color palette for different entity types
    ENTITY_COLORS = {
        "customer": "#22c55e",   # Green
        "product": "#3b82f6",    # Blue
        "revenue": "#f97316",    # Orange
        "category": "#a855f7",   # Purple
        "date": "#06b6d4",       # Cyan
        "metric": "#ef4444",     # Red
        "region": "#eab308",     # Yellow
    }
    
    def __init__(self, currency_symbol: str = "₹"):
        self.currency = currency_symbol
        self.entities_extracted = []
        self.relationships_found = []
    
    # ========================================================================
    # MIND MAP GENERATION - AI-Driven
    # ========================================================================
    
    def generate_mind_map(
        self,
        data: Dict[str, Any],
        title: str = "Business Overview"
    ) -> Dict[str, Any]:
        """
        Generate AI-driven mind map from business data.
        
        Creates hierarchical structure:
        Company Performance
         ├── Revenue
         │    ├── By Product
         │    ├── By Customer
         │    └── Trend
         ├── Customers
         │    ├── Top Customers
         │    └── Distribution
         └── Products
              ├── Best Sellers
              └── Categories
        """
        # Extract metrics from data
        total_revenue = data.get("total_revenue", 0)
        customer_count = data.get("customer_count", 0)
        product_count = data.get("product_count", 0)
        top_customers = data.get("top_customers", [])
        top_products = data.get("top_products", [])
        categories = data.get("categories", [])
        
        # Build mind map structure
        mind_map = {
            "type": "mind_map",
            "title": title,
            "root": {
                "id": "root",
                "label": title,
                "color": "#667eea",
                "children": []
            }
        }
        
        # Revenue Branch
        revenue_branch = {
            "id": "revenue",
            "label": f"Revenue: {self.currency}{total_revenue:,.0f}",
            "color": self.ENTITY_COLORS["revenue"],
            "icon": "💰",
            "children": []
        }
        
        # Add top products to revenue
        if top_products:
            product_children = []
            for i, prod in enumerate(top_products[:5]):
                name = prod.get("name", prod.get("product", f"Product {i+1}"))
                value = prod.get("revenue", prod.get("value", 0))
                product_children.append({
                    "id": f"product_{i}",
                    "label": f"{name}: {self.currency}{value:,.0f}",
                    "color": self.ENTITY_COLORS["product"],
                    "value": value
                })
            revenue_branch["children"].append({
                "id": "by_product",
                "label": "By Product",
                "color": self.ENTITY_COLORS["product"],
                "children": product_children
            })
        
        # Add categories if available
        if categories:
            cat_children = []
            for i, cat in enumerate(categories[:5]):
                name = cat.get("name", cat.get("category", f"Category {i+1}"))
                value = cat.get("revenue", cat.get("value", 0))
                cat_children.append({
                    "id": f"category_{i}",
                    "label": f"{name}: {self.currency}{value:,.0f}",
                    "color": self.ENTITY_COLORS["category"],
                    "value": value
                })
            revenue_branch["children"].append({
                "id": "by_category",
                "label": "By Category",
                "color": self.ENTITY_COLORS["category"],
                "children": cat_children
            })
        
        mind_map["root"]["children"].append(revenue_branch)
        
        # Customers Branch
        customer_branch = {
            "id": "customers",
            "label": f"Customers: {customer_count}",
            "color": self.ENTITY_COLORS["customer"],
            "icon": "👥",
            "children": []
        }
        
        if top_customers:
            cust_children = []
            for i, cust in enumerate(top_customers[:5]):
                name = cust.get("name", cust.get("customer", f"Customer {i+1}"))
                value = cust.get("revenue", cust.get("value", 0))
                cust_children.append({
                    "id": f"customer_{i}",
                    "label": f"{name}: {self.currency}{value:,.0f}",
                    "color": self.ENTITY_COLORS["customer"],
                    "value": value
                })
            customer_branch["children"].append({
                "id": "top_customers",
                "label": "Top Customers",
                "icon": "⭐",
                "children": cust_children
            })
        
        mind_map["root"]["children"].append(customer_branch)
        
        # Products Branch
        product_branch = {
            "id": "products",
            "label": f"Products: {product_count}",
            "color": self.ENTITY_COLORS["product"],
            "icon": "📦",
            "children": []
        }
        
        mind_map["root"]["children"].append(product_branch)
        
        # Generate insight
        insight = self._generate_mind_map_insight(data)
        
        return {
            "visual_type": "mind_map",
            "title": title,
            "mind_map": mind_map,
            "insight": insight,
            "recommendation": self._generate_recommendation(data),
            "format": "mermaid"  # Can be rendered as Mermaid diagram
        }
    
    # ========================================================================
    # RELATIONSHIP GRAPH - Knowledge Graph Style
    # ========================================================================
    
    def generate_relationship_graph(
        self,
        data: Dict[str, Any],
        focus: str = "all"  # customer, product, revenue, all
    ) -> Dict[str, Any]:
        """
        Generate knowledge graph style relationship visualization.
        
        Shows connections:
        Customer → Product → Revenue
        Product → Category → Total
        Customer → Region → Performance
        """
        nodes = []
        edges = []
        
        # Extract entities
        customers = data.get("customers", data.get("top_customers", []))
        products = data.get("products", data.get("top_products", []))
        
        # Create nodes for customers
        for i, cust in enumerate(customers[:10]):
            name = cust.get("name", cust.get("customer", f"Customer_{i}"))
            value = cust.get("revenue", cust.get("value", 0))
            nodes.append({
                "id": f"cust_{i}",
                "label": name,
                "type": "customer",
                "value": value,
                "color": self.ENTITY_COLORS["customer"],
                "size": max(15, min(40, value / 1000))  # Size based on value
            })
        
        # Create nodes for products
        for i, prod in enumerate(products[:10]):
            name = prod.get("name", prod.get("product", f"Product_{i}"))
            value = prod.get("revenue", prod.get("value", 0))
            nodes.append({
                "id": f"prod_{i}",
                "label": name,
                "type": "product",
                "value": value,
                "color": self.ENTITY_COLORS["product"],
                "size": max(15, min(40, value / 1000))
            })
        
        # Create central revenue node
        total_revenue = data.get("total_revenue", 0)
        nodes.append({
            "id": "revenue_center",
            "label": f"Revenue\n{self.currency}{total_revenue:,.0f}",
            "type": "metric",
            "value": total_revenue,
            "color": self.ENTITY_COLORS["revenue"],
            "size": 50
        })
        
        # Create edges - Customer to Revenue
        for i, cust in enumerate(customers[:10]):
            value = cust.get("revenue", cust.get("value", 0))
            edges.append({
                "source": f"cust_{i}",
                "target": "revenue_center",
                "relationship": "contributes",
                "value": value,
                "label": f"{self.currency}{value:,.0f}",
                "color": self.ENTITY_COLORS["customer"]
            })
        
        # Create edges - Product to Revenue
        for i, prod in enumerate(products[:10]):
            value = prod.get("revenue", prod.get("value", 0))
            edges.append({
                "source": f"prod_{i}",
                "target": "revenue_center",
                "relationship": "generates",
                "value": value,
                "label": f"{self.currency}{value:,.0f}",
                "color": self.ENTITY_COLORS["product"]
            })
        
        # If we have customer-product relationships, add those
        customer_products = data.get("customer_products", [])
        for rel in customer_products[:20]:
            edges.append({
                "source": f"cust_{rel.get('customer_id', 0)}",
                "target": f"prod_{rel.get('product_id', 0)}",
                "relationship": "purchases",
                "value": rel.get("amount", 0),
                "color": "#9ca3af"
            })
        
        return {
            "visual_type": "relationship_graph",
            "title": "Business Relationship Map",
            "nodes": nodes,
            "edges": edges,
            "insight": self._generate_graph_insight(nodes, edges, data),
            "recommendation": self._generate_recommendation(data),
            "legend": [
                {"type": "customer", "color": self.ENTITY_COLORS["customer"], "label": "Customer"},
                {"type": "product", "color": self.ENTITY_COLORS["product"], "label": "Product"},
                {"type": "revenue", "color": self.ENTITY_COLORS["revenue"], "label": "Revenue"},
            ]
        }
    
    # ========================================================================
    # SMART VISUALIZATION SELECTOR
    # ========================================================================
    
    def auto_select_visualization(
        self,
        query: str,
        data: Dict[str, Any]
    ) -> VisualType:
        """
        Automatically select best visualization based on query and data.
        
        User NEVER chooses chart type - system decides.
        """
        q_lower = query.lower()
        
        # Mind map triggers
        if any(w in q_lower for w in [
            'overview', 'summary', 'business structure', 'organization',
            'mind map', 'breakdown', 'hierarchy'
        ]):
            return VisualType.MIND_MAP
        
        # Relationship graph triggers
        if any(w in q_lower for w in [
            'relationship', 'connection', 'who buys', 'which customer',
            'network', 'knowledge graph', 'dependencies', 'linked'
        ]):
            return VisualType.RELATIONSHIP_GRAPH
        
        # Sankey diagram triggers
        if any(w in q_lower for w in [
            'flow', 'sankey', 'from to', 'distribution flow'
        ]):
            return VisualType.SANKEY
        
        # Tree triggers
        if any(w in q_lower for w in [
            'drill down', 'tree', 'hierarchy detail'
        ]):
            return VisualType.TREE
        
        # KPI Dashboard triggers
        if any(w in q_lower for w in [
            'kpi', 'dashboard', 'metrics', 'performance'
        ]):
            return VisualType.KPI_DASHBOARD
        
        # Trend triggers → Line
        if any(w in q_lower for w in [
            'trend', 'over time', 'monthly', 'weekly', 'daily', 'growth'
        ]):
            return VisualType.LINE
        
        # Comparison triggers → Bar
        if any(w in q_lower for w in [
            'compare', 'top', 'best', 'worst', 'ranking', 'versus'
        ]):
            return VisualType.BAR
        
        # Distribution triggers → Pie
        if any(w in q_lower for w in [
            'share', 'proportion', 'percentage', 'breakdown by'
        ]):
            return VisualType.PIE
        
        # Correlation triggers → Scatter
        if any(w in q_lower for w in [
            'correlation', 'relationship between', 'scatter'
        ]):
            return VisualType.SCATTER
        
        # Forecast triggers
        if any(w in q_lower for w in [
            'predict', 'forecast', 'future', 'next'
        ]):
            return VisualType.FORECAST
        
        # Default based on data structure
        if data.get("has_time_series"):
            return VisualType.LINE
        elif data.get("has_categories"):
            return VisualType.BAR
        else:
            return VisualType.RELATIONSHIP_GRAPH  # Default to relationship view
    
    # ========================================================================
    # KPI DASHBOARD GENERATOR
    # ========================================================================
    
    def generate_kpi_dashboard(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate KPI dashboard with key metrics.
        """
        total_revenue = data.get("total_revenue", 0)
        customer_count = data.get("customer_count", 0)
        product_count = data.get("product_count", 0)
        order_count = data.get("order_count", 0)
        
        avg_order = total_revenue / order_count if order_count else 0
        avg_customer_value = total_revenue / customer_count if customer_count else 0
        
        kpis = [
            {
                "label": "Total Revenue",
                "value": total_revenue,
                "formatted": f"{self.currency}{total_revenue:,.0f}",
                "icon": "💰",
                "color": self.ENTITY_COLORS["revenue"],
                "trend": data.get("revenue_trend", "stable")
            },
            {
                "label": "Customers",
                "value": customer_count,
                "formatted": f"{customer_count:,}",
                "icon": "👥",
                "color": self.ENTITY_COLORS["customer"],
                "trend": data.get("customer_trend", "stable")
            },
            {
                "label": "Products",
                "value": product_count,
                "formatted": f"{product_count:,}",
                "icon": "📦",
                "color": self.ENTITY_COLORS["product"],
                "trend": "stable"
            },
            {
                "label": "Avg Order Value",
                "value": avg_order,
                "formatted": f"{self.currency}{avg_order:,.0f}",
                "icon": "🛒",
                "color": "#6366f1",
                "trend": data.get("aov_trend", "stable")
            },
            {
                "label": "Customer Value",
                "value": avg_customer_value,
                "formatted": f"{self.currency}{avg_customer_value:,.0f}",
                "icon": "⭐",
                "color": "#f43f5e",
                "trend": "stable"
            }
        ]
        
        return {
            "visual_type": "kpi_dashboard",
            "title": "Business Performance Dashboard",
            "kpis": kpis,
            "insight": self._generate_dashboard_insight(kpis, data),
            "recommendation": self._generate_recommendation(data)
        }
    
    # ========================================================================
    # COMPLETE VISUAL ANALYSIS - Entry Point
    # ========================================================================
    
    def analyze(
        self,
        query: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main entry point - analyze query and data, generate best visual.
        
        Returns complete visual artifact with:
        - Visualization data
        - AI insight
        - Recommendation
        - Explanation
        """
        # Auto-select best visualization
        visual_type = self.auto_select_visualization(query, data)
        print(f"[VISUAL-AI] Selected: {visual_type.value} for query: {query[:50]}...")
        
        # Generate appropriate visualization
        if visual_type == VisualType.MIND_MAP:
            return self.generate_mind_map(data)
        elif visual_type == VisualType.RELATIONSHIP_GRAPH:
            return self.generate_relationship_graph(data)
        elif visual_type == VisualType.KPI_DASHBOARD:
            return self.generate_kpi_dashboard(data)
        else:
            # For standard charts, return chart config
            return self._generate_standard_chart(visual_type, data)
    
    # ========================================================================
    # INSIGHT GENERATORS
    # ========================================================================
    
    def _generate_mind_map_insight(self, data: Dict) -> str:
        """Generate insight for mind map"""
        total_revenue = data.get("total_revenue", 0)
        customer_count = data.get("customer_count", 0)
        top_customers = data.get("top_customers", [])
        
        if top_customers:
            top_name = top_customers[0].get("name", "Top Customer")
            top_value = top_customers[0].get("revenue", 0)
            concentration = (top_value / total_revenue * 100) if total_revenue else 0
            return f"Your business generates {self.currency}{total_revenue:,.0f} from {customer_count} customers. {top_name} contributes {concentration:.1f}% of revenue."
        
        return f"Your business overview shows {self.currency}{total_revenue:,.0f} total revenue across {customer_count} customers."
    
    def _generate_graph_insight(self, nodes: List, edges: List, data: Dict) -> str:
        """Generate insight for relationship graph"""
        customer_nodes = len([n for n in nodes if n.get("type") == "customer"])
        product_nodes = len([n for n in nodes if n.get("type") == "product"])
        total_connections = len(edges)
        
        return f"Your business network shows {customer_nodes} customers connected to {product_nodes} products through {total_connections} relationships."
    
    def _generate_dashboard_insight(self, kpis: List, data: Dict) -> str:
        """Generate insight for KPI dashboard"""
        revenue = data.get("total_revenue", 0)
        customers = data.get("customer_count", 0)
        avg_value = revenue / customers if customers else 0
        
        return f"Key metrics: {self.currency}{revenue:,.0f} revenue from {customers} customers. Average customer value: {self.currency}{avg_value:,.0f}."
    
    def _generate_recommendation(self, data: Dict) -> str:
        """Generate actionable recommendation"""
        total_revenue = data.get("total_revenue", 0)
        customer_count = data.get("customer_count", 0)
        top_customers = data.get("top_customers", [])
        
        recommendations = []
        
        # Check customer concentration
        if top_customers and total_revenue:
            top_revenue = sum(c.get("revenue", 0) for c in top_customers[:3])
            concentration = top_revenue / total_revenue * 100
            if concentration > 50:
                recommendations.append(f"High concentration risk: Top 3 customers = {concentration:.0f}% of revenue. Diversify customer base.")
        
        # Check average order value
        order_count = data.get("order_count", 0)
        if order_count and total_revenue:
            avg_order = total_revenue / order_count
            if avg_order < 1000:
                recommendations.append(f"Increase average order value from {self.currency}{avg_order:,.0f} through upselling.")
        
        if not recommendations:
            recommendations.append("Business is performing steadily. Focus on growth opportunities.")
        
        return " | ".join(recommendations)
    
    def _generate_standard_chart(self, visual_type: VisualType, data: Dict) -> Dict:
        """Generate standard chart configuration"""
        return {
            "visual_type": visual_type.value,
            "title": f"{visual_type.value.replace('_', ' ').title()} Chart",
            "data": data,
            "insight": "Standard chart visualization.",
            "recommendation": self._generate_recommendation(data)
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def generate_visual_intelligence(
    query: str,
    data: Dict[str, Any],
    currency: str = "₹"
) -> Dict[str, Any]:
    """
    Generate visual intelligence artifact from query and data.
    
    Usage:
        result = generate_visual_intelligence(
            query="Show business overview",
            data={"total_revenue": 548765, "customer_count": 50}
        )
    """
    engine = VisualIntelligenceEngine(currency)
    return engine.analyze(query, data)


def generate_mind_map(data: Dict[str, Any], currency: str = "₹") -> Dict[str, Any]:
    """Generate mind map from business data"""
    engine = VisualIntelligenceEngine(currency)
    return engine.generate_mind_map(data)


def generate_knowledge_graph(data: Dict[str, Any], currency: str = "₹") -> Dict[str, Any]:
    """Generate knowledge graph from business data"""
    engine = VisualIntelligenceEngine(currency)
    return engine.generate_relationship_graph(data)


def generate_kpi_dashboard(data: Dict[str, Any], currency: str = "₹") -> Dict[str, Any]:
    """Generate KPI dashboard from business data"""
    engine = VisualIntelligenceEngine(currency)
    return engine.generate_kpi_dashboard(data)
