"""
🎨 VISUAL INTELLIGENCE 2.0 - DataVision Advanced Visualizations
================================================================

Next-level visualization capabilities:
- Knowledge Graph generation
- Interactive network diagrams
- Smart chart layouts
- Animated trend visualizations
- Comparative dashboards

All visualizations are Plotly-compatible for frontend rendering.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from core.llm import chat

logger = logging.getLogger(__name__)


# =============================================================================
# KNOWLEDGE GRAPH ENGINE
# =============================================================================

@dataclass
class GraphNode:
    """A node in the knowledge graph"""
    id: str
    label: str
    type: str  # entity, metric, category, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    size: float = 1.0
    color: Optional[str] = None


@dataclass
class GraphEdge:
    """An edge in the knowledge graph"""
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphEngine:
    """
    🔗 Knowledge Graph Engine
    
    Automatically builds knowledge graphs from data:
    - Entity relationships
    - Data column connections
    - Metric dependencies
    """
    
    def __init__(self):
        self.node_colors = {
            "metric": "#10b981",      # Teal
            "category": "#6366f1",    # Indigo
            "entity": "#f59e0b",      # Amber
            "date": "#ec4899",        # Pink
            "value": "#8b5cf6",       # Purple
        }
    
    async def build_from_dataframe(
        self,
        df: pd.DataFrame,
        max_nodes: int = 50,
        min_relationship_strength: float = 0.3
    ) -> KnowledgeGraph:
        """
        Build a knowledge graph from DataFrame
        
        Args:
            df: Source data
            max_nodes: Maximum number of nodes
            min_relationship_strength: Minimum correlation for edges
            
        Returns:
            Knowledge graph with nodes and edges
        """
        nodes = []
        edges = []
        node_ids = set()
        
        # 1. Add column nodes
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in numeric_cols[:15]:
            node_id = f"col_{col}"
            nodes.append(GraphNode(
                id=node_id,
                label=col,
                type="metric",
                properties={
                    "mean": float(df[col].mean()) if not df[col].isna().all() else 0,
                    "min": float(df[col].min()) if not df[col].isna().all() else 0,
                    "max": float(df[col].max()) if not df[col].isna().all() else 0,
                },
                size=1.5,
                color=self.node_colors["metric"]
            ))
            node_ids.add(node_id)
        
        for col in categorical_cols[:10]:
            node_id = f"col_{col}"
            nodes.append(GraphNode(
                id=node_id,
                label=col,
                type="category",
                properties={"unique_values": int(df[col].nunique())},
                size=1.2,
                color=self.node_colors["category"]
            ))
            node_ids.add(node_id)
        
        # 2. Add correlation edges between numeric columns
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr()
                for i, col1 in enumerate(numeric_cols):
                    for col2 in numeric_cols[i+1:]:
                        corr = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr) and abs(corr) >= min_relationship_strength:
                            edges.append(GraphEdge(
                                source=f"col_{col1}",
                                target=f"col_{col2}",
                                relationship="correlates_with",
                                weight=abs(corr),
                                properties={"correlation": round(float(corr), 3)}
                            ))
            except Exception as e:
                logger.warning(f"Correlation calculation failed: {e}")
        
        # 3. Add category value nodes (top values)
        for col in categorical_cols[:5]:
            top_values = df[col].value_counts().head(5)
            parent_id = f"col_{col}"
            
            for value, count in top_values.items():
                if len(nodes) >= max_nodes:
                    break
                    
                value_id = f"val_{col}_{str(value)[:20]}"
                if value_id not in node_ids:
                    nodes.append(GraphNode(
                        id=value_id,
                        label=str(value)[:30],
                        type="value",
                        properties={"count": int(count)},
                        size=0.8 + (count / top_values.sum()) * 0.7,
                        color=self.node_colors["value"]
                    ))
                    node_ids.add(value_id)
                    
                    edges.append(GraphEdge(
                        source=parent_id,
                        target=value_id,
                        relationship="has_value",
                        weight=count / top_values.sum()
                    ))
        
        # 4. Add categorical-numeric relationships
        for cat_col in categorical_cols[:3]:
            for num_col in numeric_cols[:5]:
                try:
                    grouped = df.groupby(cat_col)[num_col].mean()
                    overall_mean = df[num_col].mean()
                    
                    for value, mean_val in grouped.head(3).items():
                        deviation = abs(mean_val - overall_mean) / overall_mean if overall_mean != 0 else 0
                        if deviation > 0.1:  # Significant deviation
                            value_id = f"val_{cat_col}_{str(value)[:20]}"
                            if value_id in node_ids:
                                edges.append(GraphEdge(
                                    source=value_id,
                                    target=f"col_{num_col}",
                                    relationship="influences",
                                    weight=min(deviation, 1.0),
                                    properties={"mean": round(float(mean_val), 2)}
                                ))
                except Exception:
                    pass
        
        return KnowledgeGraph(
            nodes=nodes[:max_nodes],
            edges=edges,
            metadata={
                "source": "dataframe",
                "rows": len(df),
                "columns": len(df.columns),
                "generated_at": datetime.now().isoformat()
            }
        )
    
    def to_plotly(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Convert knowledge graph to Plotly format for visualization"""
        if not NETWORKX_AVAILABLE:
            return self._simple_plotly_format(graph)
        
        # Build NetworkX graph for layout
        G = nx.Graph()
        
        for node in graph.nodes:
            G.add_node(node.id, label=node.label, type=node.type)
        
        for edge in graph.edges:
            G.add_edge(edge.source, edge.target, weight=edge.weight)
        
        # Calculate layout
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            pos = nx.random_layout(G)
        
        # Build Plotly traces
        edge_x = []
        edge_y = []
        
        for edge in graph.edges:
            if edge.source in pos and edge.target in pos:
                x0, y0 = pos[edge.source]
                x1, y1 = pos[edge.target]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in graph.nodes:
            if node.id in pos:
                x, y = pos[node.id]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node.label)
                node_colors.append(node.color or "#888")
                node_sizes.append(node.size * 20)
        
        return {
            "data": [
                {
                    "type": "scatter",
                    "x": edge_x,
                    "y": edge_y,
                    "mode": "lines",
                    "line": {"width": 1, "color": "#888"},
                    "hoverinfo": "none",
                    "showlegend": False
                },
                {
                    "type": "scatter",
                    "x": node_x,
                    "y": node_y,
                    "mode": "markers+text",
                    "marker": {
                        "size": node_sizes,
                        "color": node_colors,
                        "line": {"width": 2, "color": "white"}
                    },
                    "text": node_text,
                    "textposition": "top center",
                    "hoverinfo": "text",
                    "showlegend": False
                }
            ],
            "layout": {
                "title": "Knowledge Graph",
                "showlegend": False,
                "hovermode": "closest",
                "xaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "yaxis": {"showgrid": False, "zeroline": False, "showticklabels": False},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)"
            }
        }
    
    def _simple_plotly_format(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Simple layout without NetworkX"""
        n = len(graph.nodes)
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        
        node_x = np.cos(angles).tolist()
        node_y = np.sin(angles).tolist()
        
        pos = {node.id: (node_x[i], node_y[i]) for i, node in enumerate(graph.nodes)}
        
        edge_x = []
        edge_y = []
        
        for edge in graph.edges:
            if edge.source in pos and edge.target in pos:
                x0, y0 = pos[edge.source]
                x1, y1 = pos[edge.target]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
        
        return {
            "data": [
                {
                    "type": "scatter",
                    "x": edge_x,
                    "y": edge_y,
                    "mode": "lines",
                    "line": {"width": 1, "color": "#888"},
                    "hoverinfo": "none"
                },
                {
                    "type": "scatter",
                    "x": node_x,
                    "y": node_y,
                    "mode": "markers+text",
                    "marker": {
                        "size": [n.size * 20 for n in graph.nodes],
                        "color": [n.color or "#888" for n in graph.nodes]
                    },
                    "text": [n.label for n in graph.nodes],
                    "textposition": "top center"
                }
            ],
            "layout": {
                "title": "Knowledge Graph",
                "showlegend": False
            }
        }
    
    def to_dict(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type,
                    "properties": n.properties,
                    "size": n.size,
                    "color": n.color
                }
                for n in graph.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "relationship": e.relationship,
                    "weight": e.weight,
                    "properties": e.properties
                }
                for e in graph.edges
            ],
            "metadata": graph.metadata
        }


# =============================================================================
# SMART CHART LAYOUT ENGINE
# =============================================================================

@dataclass
class ChartRecommendation:
    """A chart recommendation"""
    chart_type: str
    title: str
    description: str
    columns: List[str]
    priority: int  # 1 = highest
    config: Dict[str, Any] = field(default_factory=dict)


class SmartLayoutEngine:
    """
    📊 Smart Chart Layout Engine
    
    AI-powered chart selection and layout:
    - Automatically select best chart types
    - Optimal dashboard arrangement
    - Responsive grid layouts
    """
    
    def __init__(self):
        self.chart_priority = {
            "line": 1,      # Time series
            "bar": 2,       # Comparisons
            "scatter": 3,   # Correlations
            "pie": 4,       # Proportions
            "heatmap": 5,   # Patterns
            "histogram": 6, # Distributions
            "box": 7,       # Distributions
            "area": 8,      # Cumulative
            "funnel": 9,    # Processes
            "gauge": 10,    # Single metrics
        }
    
    async def recommend_charts(
        self,
        df: pd.DataFrame,
        max_charts: int = 6
    ) -> List[ChartRecommendation]:
        """
        Recommend best charts for dashboard
        
        Args:
            df: Source data
            max_charts: Maximum number of charts
            
        Returns:
            List of chart recommendations
        """
        recommendations = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        
        # Detect potential date columns
        for col in df.columns:
            if col not in datetime_cols:
                try:
                    pd.to_datetime(df[col].head(10))
                    datetime_cols.append(col)
                except:
                    pass
        
        # 1. Time series charts
        if datetime_cols and numeric_cols:
            dt_col = datetime_cols[0]
            for num_col in numeric_cols[:2]:
                recommendations.append(ChartRecommendation(
                    chart_type="line",
                    title=f"{num_col} Over Time",
                    description=f"Track {num_col} trends over {dt_col}",
                    columns=[dt_col, num_col],
                    priority=1,
                    config={"x": dt_col, "y": num_col}
                ))
        
        # 2. Category comparisons
        if categorical_cols and numeric_cols:
            for cat_col in categorical_cols[:2]:
                if df[cat_col].nunique() <= 15:
                    for num_col in numeric_cols[:2]:
                        recommendations.append(ChartRecommendation(
                            chart_type="bar",
                            title=f"{num_col} by {cat_col}",
                            description=f"Compare {num_col} across {cat_col}",
                            columns=[cat_col, num_col],
                            priority=2,
                            config={"x": cat_col, "y": num_col}
                        ))
        
        # 3. Correlation scatter
        if len(numeric_cols) >= 2:
            try:
                corr_matrix = df[numeric_cols].corr()
                for i, col1 in enumerate(numeric_cols):
                    for col2 in numeric_cols[i+1:]:
                        corr = corr_matrix.loc[col1, col2]
                        if not pd.isna(corr) and abs(corr) > 0.5:
                            recommendations.append(ChartRecommendation(
                                chart_type="scatter",
                                title=f"{col1} vs {col2}",
                                description=f"Correlation: {corr:.2f}",
                                columns=[col1, col2],
                                priority=3,
                                config={"x": col1, "y": col2, "correlation": corr}
                            ))
            except:
                pass
        
        # 4. Distribution charts
        for num_col in numeric_cols[:3]:
            recommendations.append(ChartRecommendation(
                chart_type="histogram",
                title=f"{num_col} Distribution",
                description=f"Distribution of {num_col} values",
                columns=[num_col],
                priority=4,
                config={"x": num_col}
            ))
        
        # 5. Pie charts for small cardinality categories
        for cat_col in categorical_cols:
            if 2 <= df[cat_col].nunique() <= 8:
                recommendations.append(ChartRecommendation(
                    chart_type="pie",
                    title=f"{cat_col} Distribution",
                    description=f"Proportion breakdown of {cat_col}",
                    columns=[cat_col],
                    priority=5,
                    config={"labels": cat_col}
                ))
        
        # 6. Correlation heatmap
        if len(numeric_cols) >= 3:
            recommendations.append(ChartRecommendation(
                chart_type="heatmap",
                title="Correlation Matrix",
                description="Relationships between numeric columns",
                columns=numeric_cols[:10],
                priority=6,
                config={"type": "correlation"}
            ))
        
        # Sort by priority and limit
        recommendations.sort(key=lambda x: x.priority)
        return recommendations[:max_charts]
    
    def generate_grid_layout(
        self,
        charts: List[ChartRecommendation],
        columns: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate responsive grid layout for charts
        
        Args:
            charts: List of chart recommendations
            columns: Number of columns in grid
            
        Returns:
            Grid layout configuration
        """
        layout = []
        
        for i, chart in enumerate(charts):
            row = i // columns
            col = i % columns
            
            # Adjust sizes based on chart type
            col_span = 2 if chart.chart_type in ["heatmap", "line"] else 1
            row_span = 1
            
            layout.append({
                "chart": chart.chart_type,
                "title": chart.title,
                "columns": chart.columns,
                "config": chart.config,
                "grid": {
                    "row": row,
                    "col": col,
                    "colSpan": min(col_span, columns - col),
                    "rowSpan": row_span
                }
            })
        
        return layout


# =============================================================================
# COMPARATIVE DASHBOARD ENGINE
# =============================================================================

class ComparativeDashboard:
    """
    📊 Comparative Dashboard Engine
    
    Generate side-by-side comparisons:
    - Period over period
    - Segment comparisons
    - Benchmark analysis
    """
    
    async def compare_periods(
        self,
        df: pd.DataFrame,
        date_column: str,
        metric_columns: List[str],
        period1_label: str = "Previous",
        period2_label: str = "Current"
    ) -> Dict[str, Any]:
        """
        Compare two time periods
        
        Args:
            df: Data with date column
            date_column: Column with dates
            metric_columns: Columns to compare
            
        Returns:
            Comparison data and visualizations
        """
        try:
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            df = df.dropna(subset=[date_column])
            
            # Split into two periods (simple: first half vs second half)
            mid_date = df[date_column].median()
            
            period1 = df[df[date_column] < mid_date]
            period2 = df[df[date_column] >= mid_date]
            
            comparisons = []
            
            for col in metric_columns:
                if col not in df.columns:
                    continue
                    
                val1 = float(period1[col].mean()) if len(period1) > 0 else 0
                val2 = float(period2[col].mean()) if len(period2) > 0 else 0
                
                change = ((val2 - val1) / val1 * 100) if val1 != 0 else 0
                
                comparisons.append({
                    "metric": col,
                    period1_label: round(val1, 2),
                    period2_label: round(val2, 2),
                    "change_percent": round(change, 1),
                    "trend": "up" if change > 0 else "down" if change < 0 else "flat"
                })
            
            return {
                "type": "period_comparison",
                "period1": {
                    "label": period1_label,
                    "start": str(period1[date_column].min()),
                    "end": str(period1[date_column].max()),
                    "records": len(period1)
                },
                "period2": {
                    "label": period2_label,
                    "start": str(period2[date_column].min()),
                    "end": str(period2[date_column].max()),
                    "records": len(period2)
                },
                "comparisons": comparisons
            }
            
        except Exception as e:
            logger.error(f"Period comparison error: {e}")
            return {"error": str(e)}
    
    async def compare_segments(
        self,
        df: pd.DataFrame,
        segment_column: str,
        metric_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Compare metrics across segments
        
        Args:
            df: Data
            segment_column: Column to segment by
            metric_columns: Metrics to compare
            
        Returns:
            Segment comparison data
        """
        try:
            segments = df[segment_column].unique().tolist()[:10]
            
            comparison_data = []
            
            for segment in segments:
                segment_data = df[df[segment_column] == segment]
                
                metrics = {"segment": str(segment), "count": len(segment_data)}
                
                for col in metric_columns:
                    if col in df.columns:
                        metrics[col] = round(float(segment_data[col].mean()), 2)
                
                comparison_data.append(metrics)
            
            return {
                "type": "segment_comparison",
                "segment_column": segment_column,
                "segments": comparison_data,
                "metrics": metric_columns
            }
            
        except Exception as e:
            logger.error(f"Segment comparison error: {e}")
            return {"error": str(e)}


# =============================================================================
# EXPORTS
# =============================================================================

knowledge_graph_engine = KnowledgeGraphEngine()
smart_layout_engine = SmartLayoutEngine()
comparative_dashboard = ComparativeDashboard()


async def build_knowledge_graph(df: pd.DataFrame) -> Dict[str, Any]:
    """Quick function to build knowledge graph"""
    graph = await knowledge_graph_engine.build_from_dataframe(df)
    return {
        "graph": knowledge_graph_engine.to_dict(graph),
        "plotly": knowledge_graph_engine.to_plotly(graph)
    }


async def get_chart_recommendations(df: pd.DataFrame, max_charts: int = 6) -> List[Dict]:
    """Quick function to get chart recommendations"""
    recs = await smart_layout_engine.recommend_charts(df, max_charts)
    return [
        {
            "type": r.chart_type,
            "title": r.title,
            "description": r.description,
            "columns": r.columns,
            "priority": r.priority
        }
        for r in recs
    ]


async def compare_time_periods(
    df: pd.DataFrame,
    date_column: str,
    metrics: List[str]
) -> Dict[str, Any]:
    """Quick function for period comparison"""
    return await comparative_dashboard.compare_periods(df, date_column, metrics)
