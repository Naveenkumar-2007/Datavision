"""
🎨 INTELLIGENT VISUALIZER - Claude-Style Advanced Visualization System
======================================================================

A comprehensive visualization engine that generates beautiful, interactive
visualizations from user data including:

- 📊 Standard Charts (bar, line, pie, scatter, area, etc.)
- 🧠 Knowledge Graphs (entity relationships)
- 🗺️ Mind Maps (hierarchical concepts)
- 🌐 Network Graphs (connections)
- 🌳 Treemaps & Sunbursts (hierarchical data)
- 📈 Advanced Analytics (funnel, gauge, waterfall)

Architecture:
1. Data Analyzer: Understand data structure and relationships
2. Visualization Selector: Choose best viz type for query
3. Graph Generators: Create knowledge graphs, mind maps
4. Chart Renderer: Generate Plotly/Chart.js output
5. Style Engine: Beautiful, professional styling
"""

import logging
import json
import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# LLM for intelligent decisions
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def llm_chat(*args, **kwargs):
        return ""


# =============================================================================
# VISUALIZATION TYPES
# =============================================================================

class VizType(Enum):
    """All supported visualization types."""
    # Standard Charts
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    AREA = "area"
    
    # Statistical
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    
    # Advanced
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    WATERFALL = "waterfall"
    RADAR = "radar"
    BUBBLE = "bubble"
    
    # Knowledge/Relationship
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MIND_MAP = "mind_map"
    NETWORK_GRAPH = "network_graph"
    SANKEY = "sankey"
    
    # Time Series
    TIMELINE = "timeline"
    CANDLESTICK = "candlestick"


@dataclass
class VisualizationResult:
    """Result from visualization generation."""
    viz_type: VizType
    title: str
    data: Dict[str, Any]  # Plotly/Chart.js compatible data
    layout: Dict[str, Any]  # Layout configuration
    insights: List[str]  # Key insights from the visualization
    html: str = ""  # Optional HTML embed code


# =============================================================================
# DATA ANALYZER
# =============================================================================

class DataAnalyzer:
    """
    Analyzes data structure to understand relationships and best visualization.
    """
    
    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze dataframe structure."""
        if df is None or df.empty:
            return {"error": "No data"}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Detect date columns from object types
        for col in categorical_cols[:]:
            try:
                pd.to_datetime(df[col].head(10), errors='raise')
                datetime_cols.append(col)
                categorical_cols.remove(col)
            except:
                pass
        
        # Find relationships
        relationships = []
        for cat_col in categorical_cols[:5]:
            for num_col in numeric_cols[:5]:
                relationships.append({
                    "category": cat_col,
                    "measure": num_col,
                    "type": "category_measure"
                })
        
        # Detect hierarchies (columns with parent-child like names)
        hierarchies = []
        for i, col1 in enumerate(categorical_cols):
            for col2 in categorical_cols[i+1:]:
                if df.groupby(col1)[col2].nunique().mean() > 1:
                    hierarchies.append({"parent": col1, "child": col2})
        
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_cols": numeric_cols,
            "categorical_cols": categorical_cols,
            "datetime_cols": datetime_cols,
            "relationships": relationships[:10],
            "hierarchies": hierarchies[:5],
            "has_time_series": len(datetime_cols) > 0,
            "has_categories": len(categorical_cols) > 0,
            "has_numerics": len(numeric_cols) > 0
        }
    
    @staticmethod
    def detect_entities(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect entities and their relationships for knowledge graphs."""
        entities = []
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in categorical_cols[:5]:
            unique_vals = df[col].dropna().unique()[:20]  # Top 20 unique values
            for val in unique_vals:
                entities.append({
                    "id": f"{col}_{val}",
                    "label": str(val),
                    "type": col,
                    "count": int(df[df[col] == val].shape[0])
                })
        
        return entities
    
    @staticmethod
    def detect_relationships(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect relationships between entities for network/knowledge graphs."""
        relationships = []
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Find co-occurrences
        for i, col1 in enumerate(categorical_cols[:4]):
            for col2 in categorical_cols[i+1:4]:
                # Group and count co-occurrences
                grouped = df.groupby([col1, col2]).size().reset_index(name='weight')
                grouped = grouped.nlargest(10, 'weight')  # Top 10 relationships
                
                for _, row in grouped.iterrows():
                    relationships.append({
                        "source": f"{col1}_{row[col1]}",
                        "target": f"{col2}_{row[col2]}",
                        "weight": int(row['weight']),
                        "label": f"appears with"
                    })
        
        return relationships


# =============================================================================
# VISUALIZATION SELECTOR
# =============================================================================

class VisualizationSelector:
    """
    Intelligently selects the best visualization type based on query and data.
    """
    
    # Query keyword mappings
    KEYWORD_MAP = {
        VizType.KNOWLEDGE_GRAPH: ['knowledge graph', 'entity', 'relationship', 'connection', 'network of'],
        VizType.MIND_MAP: ['mind map', 'concept map', 'hierarchy', 'breakdown', 'structure'],
        VizType.NETWORK_GRAPH: ['network', 'connections', 'links', 'graph of', 'relationships between'],
        VizType.TREEMAP: ['treemap', 'proportion', 'nested', 'hierarchical breakdown'],
        VizType.SUNBURST: ['sunburst', 'drill down', 'hierarchical', 'multi-level pie'],
        VizType.SANKEY: ['sankey', 'flow', 'journey', 'path', 'conversion'],
        VizType.PIE: ['pie', 'share', 'percentage', 'portion', 'composition'],
        VizType.DONUT: ['donut', 'ring chart'],
        VizType.LINE: ['trend', 'over time', 'time series', 'progression', 'history'],
        VizType.BAR: ['bar', 'compare', 'top', 'ranking', 'comparison'],
        VizType.SCATTER: ['scatter', 'correlation', 'relationship between', 'x vs y'],
        VizType.HEATMAP: ['heatmap', 'matrix', 'cross-tab', 'intensity'],
        VizType.FUNNEL: ['funnel', 'conversion', 'stages', 'pipeline'],
        VizType.GAUGE: ['gauge', 'meter', 'progress', 'kpi', 'performance indicator'],
        VizType.WATERFALL: ['waterfall', 'contribution', 'breakdown of change'],
        VizType.RADAR: ['radar', 'spider', 'profile', 'multi-dimension'],
        VizType.BOX_PLOT: ['box plot', 'distribution', 'quartile', 'outliers'],
        VizType.HISTOGRAM: ['histogram', 'distribution', 'frequency'],
        VizType.BUBBLE: ['bubble', 'three variable', '3d scatter'],
        VizType.AREA: ['area', 'stacked area', 'cumulative'],
    }
    
    @classmethod
    def select(cls, query: str, data_analysis: Dict[str, Any]) -> Tuple[VizType, float]:
        """
        Select best visualization type.
        
        Returns: (VizType, confidence)
        """
        q_lower = query.lower()
        
        # Check for explicit keywords
        for viz_type, keywords in cls.KEYWORD_MAP.items():
            for kw in keywords:
                if kw in q_lower:
                    return viz_type, 0.9
        
        # Infer from data structure
        has_time = data_analysis.get('has_time_series', False)
        has_cats = data_analysis.get('has_categories', False)
        has_nums = data_analysis.get('has_numerics', False)
        hierarchies = data_analysis.get('hierarchies', [])
        
        # Time series → Line chart
        if has_time and ('trend' in q_lower or 'over time' in q_lower):
            return VizType.LINE, 0.85
        
        # Hierarchical data → Treemap or Sunburst
        if hierarchies and ('breakdown' in q_lower or 'structure' in q_lower):
            return VizType.TREEMAP, 0.8
        
        # Category + Numeric → Bar chart
        if has_cats and has_nums:
            if 'top' in q_lower or 'best' in q_lower or 'worst' in q_lower:
                return VizType.BAR, 0.85
            if 'share' in q_lower or 'percentage' in q_lower:
                return VizType.PIE, 0.8
            return VizType.BAR, 0.7
        
        # Default
        return VizType.BAR, 0.5


# =============================================================================
# KNOWLEDGE GRAPH GENERATOR
# =============================================================================

class KnowledgeGraphGenerator:
    """
    Generates knowledge graphs showing entity relationships in data.
    
    Creates interactive node-link diagrams.
    """
    
    # Professional color palette
    COLORS = [
        '#14b8a6',  # Teal
        '#f59e0b',  # Amber
        '#8b5cf6',  # Purple
        '#ef4444',  # Red
        '#22c55e',  # Green
        '#3b82f6',  # Blue
        '#ec4899',  # Pink
        '#06b6d4',  # Cyan
    ]
    
    def generate(self, df: pd.DataFrame, query: str = "", 
                 max_nodes: int = 30) -> VisualizationResult:
        """Generate knowledge graph from data."""
        
        # Get entities and relationships
        entities = DataAnalyzer.detect_entities(df)[:max_nodes]
        relationships = DataAnalyzer.detect_relationships(df)
        
        # Create node types color mapping
        node_types = list(set(e['type'] for e in entities))
        color_map = {t: self.COLORS[i % len(self.COLORS)] for i, t in enumerate(node_types)}
        
        # Build nodes
        nodes = []
        for entity in entities:
            nodes.append({
                "id": entity['id'],
                "label": entity['label'],
                "group": entity['type'],
                "size": min(30, 10 + entity['count'] * 2),
                "color": color_map.get(entity['type'], self.COLORS[0])
            })
        
        # Build edges
        edges = []
        node_ids = {n['id'] for n in nodes}
        for rel in relationships:
            if rel['source'] in node_ids and rel['target'] in node_ids:
                edges.append({
                    "source": rel['source'],
                    "target": rel['target'],
                    "weight": rel['weight'],
                    "label": rel.get('label', '')
                })
        
        # Create visualization data
        data = {
            "nodes": nodes,
            "edges": edges,
            "type": "knowledge_graph"
        }
        
        layout = {
            "title": f"Knowledge Graph: {query}" if query else "Data Knowledge Graph",
            "physics": {
                "enabled": True,
                "stabilization": True
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 200
            }
        }
        
        insights = [
            f"Found {len(nodes)} entities across {len(node_types)} categories",
            f"Detected {len(edges)} relationships",
            f"Entity types: {', '.join(node_types)}"
        ]
        
        return VisualizationResult(
            viz_type=VizType.KNOWLEDGE_GRAPH,
            title=layout['title'],
            data=data,
            layout=layout,
            insights=insights
        )


# =============================================================================
# MIND MAP GENERATOR
# =============================================================================

class MindMapGenerator:
    """
    Generates mind maps for hierarchical data exploration.
    
    Creates radial tree layouts showing data structure.
    """
    
    COLORS = ['#14b8a6', '#f59e0b', '#8b5cf6', '#ef4444', '#22c55e', '#3b82f6']
    
    def generate(self, df: pd.DataFrame, query: str = "",
                 center_topic: str = None) -> VisualizationResult:
        """Generate mind map from data."""
        
        # Determine central topic
        if not center_topic:
            center_topic = query if query else "Data Analysis"
        
        # Build hierarchical structure
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()[:4]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:3]
        
        # Create mind map structure
        mind_map = {
            "id": "root",
            "label": center_topic,
            "children": []
        }
        
        # Add category branches
        for i, col in enumerate(categorical_cols):
            branch = {
                "id": f"cat_{col}",
                "label": col.replace('_', ' ').title(),
                "color": self.COLORS[i % len(self.COLORS)],
                "children": []
            }
            
            # Add top values as children
            top_values = df[col].value_counts().head(5)
            for val, count in top_values.items():
                branch["children"].append({
                    "id": f"cat_{col}_{val}",
                    "label": f"{val} ({count})",
                    "size": count
                })
            
            mind_map["children"].append(branch)
        
        # Add metric branches
        if numeric_cols:
            metrics_branch = {
                "id": "metrics",
                "label": "📊 Key Metrics",
                "color": self.COLORS[-1],
                "children": []
            }
            
            for col in numeric_cols:
                metrics_branch["children"].append({
                    "id": f"metric_{col}",
                    "label": f"{col}: {df[col].sum():,.0f}",
                    "size": df[col].sum()
                })
            
            mind_map["children"].append(metrics_branch)
        
        data = {
            "tree": mind_map,
            "type": "mind_map"
        }
        
        layout = {
            "title": f"Mind Map: {center_topic}",
            "type": "radial",
            "nodeSpacing": 60,
            "levelSpacing": 120
        }
        
        insights = [
            f"Central topic: {center_topic}",
            f"{len(categorical_cols)} category dimensions analyzed",
            f"{len(numeric_cols)} numeric metrics included"
        ]
        
        return VisualizationResult(
            viz_type=VizType.MIND_MAP,
            title=layout['title'],
            data=data,
            layout=layout,
            insights=insights
        )


# =============================================================================
# NETWORK GRAPH GENERATOR
# =============================================================================

class NetworkGraphGenerator:
    """
    Generates network graphs showing connections and communities.
    """
    
    def generate(self, df: pd.DataFrame, source_col: str = None, 
                 target_col: str = None, query: str = "") -> VisualizationResult:
        """Generate network graph."""
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Auto-detect source/target if not provided
        if not source_col and len(categorical_cols) >= 1:
            source_col = categorical_cols[0]
        if not target_col and len(categorical_cols) >= 2:
            target_col = categorical_cols[1]
        
        if not source_col or not target_col:
            return VisualizationResult(
                viz_type=VizType.NETWORK_GRAPH,
                title="Network Graph",
                data={"error": "Need at least 2 categorical columns"},
                layout={},
                insights=["Insufficient data for network graph"]
            )
        
        # Build network
        edge_data = df.groupby([source_col, target_col]).size().reset_index(name='weight')
        edge_data = edge_data.nlargest(50, 'weight')  # Top 50 edges
        
        nodes = set()
        edges = []
        
        for _, row in edge_data.iterrows():
            source = str(row[source_col])
            target = str(row[target_col])
            nodes.add(source)
            nodes.add(target)
            edges.append({
                "source": source,
                "target": target,
                "weight": int(row['weight'])
            })
        
        node_list = [{"id": n, "label": n, "size": 20} for n in nodes]
        
        data = {
            "nodes": node_list,
            "edges": edges,
            "type": "network_graph"
        }
        
        layout = {
            "title": f"Network: {source_col} → {target_col}",
            "physics": True
        }
        
        insights = [
            f"Network has {len(node_list)} nodes and {len(edges)} connections",
            f"Source: {source_col}, Target: {target_col}",
            f"Strongest connection: {edges[0]['weight']} occurrences" if edges else "No connections"
        ]
        
        return VisualizationResult(
            viz_type=VizType.NETWORK_GRAPH,
            title=layout['title'],
            data=data,
            layout=layout,
            insights=insights
        )


# =============================================================================
# CHART GENERATOR (Plotly-compatible)
# =============================================================================

class ChartGenerator:
    """
    Generates standard charts in Plotly format.
    """
    
    # Beautiful color palette
    COLORS = [
        '#14b8a6', '#f59e0b', '#8b5cf6', '#ef4444', '#22c55e',
        '#3b82f6', '#ec4899', '#06b6d4', '#84cc16', '#f97316'
    ]
    
    def generate(self, df: pd.DataFrame, viz_type: VizType, 
                 query: str = "", x_col: str = None, 
                 y_col: str = None) -> VisualizationResult:
        """Generate a chart based on type."""
        
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Auto-detect columns
        if not x_col and categorical_cols:
            x_col = categorical_cols[0]
        if not y_col and numeric_cols:
            y_col = numeric_cols[0]
        
        # Generate based on type
        if viz_type == VizType.BAR:
            return self._generate_bar(df, x_col, y_col, query)
        elif viz_type == VizType.LINE:
            return self._generate_line(df, x_col, y_col, query)
        elif viz_type in [VizType.PIE, VizType.DONUT]:
            return self._generate_pie(df, x_col, y_col, query, viz_type == VizType.DONUT)
        elif viz_type == VizType.SCATTER:
            return self._generate_scatter(df, numeric_cols, query)
        elif viz_type == VizType.TREEMAP:
            return self._generate_treemap(df, categorical_cols, y_col, query)
        elif viz_type == VizType.SUNBURST:
            return self._generate_sunburst(df, categorical_cols, y_col, query)
        elif viz_type == VizType.HEATMAP:
            return self._generate_heatmap(df, query)
        elif viz_type == VizType.FUNNEL:
            return self._generate_funnel(df, x_col, y_col, query)
        elif viz_type == VizType.GAUGE:
            return self._generate_gauge(df, y_col, query)
        elif viz_type == VizType.RADAR:
            return self._generate_radar(df, categorical_cols, numeric_cols, query)
        else:
            return self._generate_bar(df, x_col, y_col, query)
    
    def _generate_bar(self, df, x_col, y_col, query) -> VisualizationResult:
        """Generate bar chart."""
        if not x_col or not y_col:
            return self._empty_result(VizType.BAR, "Need categorical and numeric columns")
        
        grouped = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(10)
        
        data = {
            "data": [{
                "type": "bar",
                "x": grouped.index.tolist(),
                "y": grouped.values.tolist(),
                "marker": {"color": self.COLORS[:len(grouped)]}
            }],
            "layout": {
                "title": query if query else f"{y_col} by {x_col}",
                "xaxis": {"title": x_col},
                "yaxis": {"title": y_col},
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.BAR,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[
                f"Top {x_col}: {grouped.index[0]} ({grouped.values[0]:,.0f})",
                f"Total: {grouped.sum():,.0f}"
            ]
        )
    
    def _generate_line(self, df, x_col, y_col, query) -> VisualizationResult:
        """Generate line chart."""
        if x_col:
            grouped = df.groupby(x_col)[y_col].sum().reset_index()
            x_vals = grouped[x_col].tolist()
            y_vals = grouped[y_col].tolist()
        else:
            x_vals = list(range(len(df)))
            y_vals = df[y_col].tolist() if y_col else []
        
        data = {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": x_vals,
                "y": y_vals,
                "line": {"color": self.COLORS[0], "width": 2},
                "marker": {"size": 6}
            }],
            "layout": {
                "title": query if query else f"{y_col} Trend",
                "xaxis": {"title": x_col or "Index"},
                "yaxis": {"title": y_col},
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.LINE,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Data points: {len(x_vals)}", f"Peak: {max(y_vals) if y_vals else 'N/A'}"]
        )
    
    def _generate_pie(self, df, x_col, y_col, query, donut=False) -> VisualizationResult:
        """Generate pie/donut chart."""
        if not x_col or not y_col:
            return self._empty_result(VizType.PIE, "Need categorical and numeric columns")
        
        grouped = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(8)
        
        data = {
            "data": [{
                "type": "pie",
                "labels": grouped.index.tolist(),
                "values": grouped.values.tolist(),
                "hole": 0.4 if donut else 0,
                "marker": {"colors": self.COLORS[:len(grouped)]}
            }],
            "layout": {
                "title": query if query else f"{y_col} Distribution",
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.DONUT if donut else VizType.PIE,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Largest segment: {grouped.index[0]} ({grouped.values[0]/grouped.sum()*100:.1f}%)"]
        )
    
    def _generate_scatter(self, df, numeric_cols, query) -> VisualizationResult:
        """Generate scatter plot."""
        if len(numeric_cols) < 2:
            return self._empty_result(VizType.SCATTER, "Need at least 2 numeric columns")
        
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        
        data = {
            "data": [{
                "type": "scatter",
                "mode": "markers",
                "x": df[x_col].tolist()[:1000],
                "y": df[y_col].tolist()[:1000],
                "marker": {"color": self.COLORS[0], "size": 8, "opacity": 0.6}
            }],
            "layout": {
                "title": query if query else f"{x_col} vs {y_col}",
                "xaxis": {"title": x_col},
                "yaxis": {"title": y_col},
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.SCATTER,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Points: {min(len(df), 1000)}", f"Correlation: {df[x_col].corr(df[y_col]):.2f}"]
        )
    
    def _generate_treemap(self, df, cat_cols, val_col, query) -> VisualizationResult:
        """Generate treemap."""
        if not cat_cols or not val_col:
            return self._empty_result(VizType.TREEMAP, "Need categorical and value columns")
        
        cat_col = cat_cols[0]
        grouped = df.groupby(cat_col)[val_col].sum().sort_values(ascending=False).head(15)
        
        data = {
            "data": [{
                "type": "treemap",
                "labels": grouped.index.tolist(),
                "parents": [""] * len(grouped),
                "values": grouped.values.tolist(),
                "textinfo": "label+value+percent parent",
                "marker": {"colors": self.COLORS[:len(grouped)]}
            }],
            "layout": {
                "title": query if query else f"{val_col} Treemap by {cat_col}",
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.TREEMAP,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Categories: {len(grouped)}", f"Largest: {grouped.index[0]}"]
        )
    
    def _generate_sunburst(self, df, cat_cols, val_col, query) -> VisualizationResult:
        """Generate sunburst chart."""
        if len(cat_cols) < 2 or not val_col:
            return self._empty_result(VizType.SUNBURST, "Need 2+ categorical columns and value")
        
        grouped = df.groupby(cat_cols[:2])[val_col].sum().reset_index()
        
        labels = [grouped.iloc[:, 0].tolist(), grouped.iloc[:, 1].tolist()]
        parents = [[""] * len(grouped), grouped.iloc[:, 0].tolist()]
        values = grouped[val_col].tolist()
        
        data = {
            "data": [{
                "type": "sunburst",
                "labels": labels[0] + labels[1],
                "parents": parents[0] + parents[1],
                "values": values + values
            }],
            "layout": {"title": query if query else "Sunburst Chart"}
        }
        
        return VisualizationResult(
            viz_type=VizType.SUNBURST,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=["Hierarchical breakdown created"]
        )
    
    def _generate_heatmap(self, df, query) -> VisualizationResult:
        """Generate correlation heatmap."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return self._empty_result(VizType.HEATMAP, "Need numeric columns")
        
        corr = numeric_df.corr()
        
        data = {
            "data": [{
                "type": "heatmap",
                "z": corr.values.tolist(),
                "x": corr.columns.tolist(),
                "y": corr.columns.tolist(),
                "colorscale": "Teal"
            }],
            "layout": {
                "title": query if query else "Correlation Heatmap",
                "template": "plotly_white"
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.HEATMAP,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Analyzed {len(corr.columns)} variables"]
        )
    
    def _generate_funnel(self, df, x_col, y_col, query) -> VisualizationResult:
        """Generate funnel chart."""
        if not x_col or not y_col:
            return self._empty_result(VizType.FUNNEL, "Need categorical and numeric columns")
        
        grouped = df.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(6)
        
        data = {
            "data": [{
                "type": "funnel",
                "y": grouped.index.tolist(),
                "x": grouped.values.tolist(),
                "marker": {"color": self.COLORS[:len(grouped)]}
            }],
            "layout": {"title": query if query else "Funnel Chart"}
        }
        
        return VisualizationResult(
            viz_type=VizType.FUNNEL,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Stages: {len(grouped)}"]
        )
    
    def _generate_gauge(self, df, val_col, query) -> VisualizationResult:
        """Generate gauge chart."""
        if not val_col:
            return self._empty_result(VizType.GAUGE, "Need numeric column")
        
        value = df[val_col].mean()
        max_val = df[val_col].max()
        
        data = {
            "data": [{
                "type": "indicator",
                "mode": "gauge+number",
                "value": value,
                "gauge": {
                    "axis": {"range": [0, max_val]},
                    "bar": {"color": self.COLORS[0]},
                    "steps": [
                        {"range": [0, max_val/3], "color": "#fee2e2"},
                        {"range": [max_val/3, 2*max_val/3], "color": "#fef3c7"},
                        {"range": [2*max_val/3, max_val], "color": "#d1fae5"}
                    ]
                }
            }],
            "layout": {"title": query if query else f"Average {val_col}"}
        }
        
        return VisualizationResult(
            viz_type=VizType.GAUGE,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Current: {value:,.2f}", f"Max: {max_val:,.2f}"]
        )
    
    def _generate_radar(self, df, cat_cols, num_cols, query) -> VisualizationResult:
        """Generate radar chart with optional custom color from query."""
        if not num_cols:
            return self._empty_result(VizType.RADAR, "Need numeric columns")
        
        # Extract custom color from query
        color_map = {
            'pink': '#ec4899',
            'red': '#ef4444',
            'blue': '#3b82f6',
            'green': '#22c55e',
            'purple': '#8b5cf6',
            'orange': '#f97316',
            'teal': '#14b8a6',
            'cyan': '#06b6d4',
            'amber': '#f59e0b',
            'yellow': '#eab308',
            'indigo': '#6366f1',
            'rose': '#f43f5e',
            'lime': '#84cc16',
        }
        
        # Find color in query
        q_lower = query.lower()
        chart_color = self.COLORS[0]  # Default
        for color_name, hex_val in color_map.items():
            if color_name in q_lower:
                chart_color = hex_val
                break
        
        # Normalize values
        values = []
        for col in num_cols[:6]:
            val = df[col].mean()
            max_val = df[col].max()
            values.append(val / max_val if max_val > 0 else 0)
        
        values.append(values[0])  # Close the polygon
        labels = num_cols[:6] + [num_cols[0]]
        
        data = {
            "data": [{
                "type": "scatterpolar",
                "r": values,
                "theta": labels,
                "fill": "toself",
                "fillcolor": f"{chart_color}40",  # 25% opacity
                "line": {"color": chart_color, "width": 2},
                "marker": {"color": chart_color, "size": 8}
            }],
            "layout": {
                "title": query if query else "Radar Chart",
                "polar": {
                    "radialaxis": {"visible": True, "range": [0, 1]},
                    "bgcolor": "rgba(0,0,0,0)"
                },
                "template": "plotly_white",
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "showlegend": False
            }
        }
        
        return VisualizationResult(
            viz_type=VizType.RADAR,
            title=data["layout"]["title"],
            data=data,
            layout=data["layout"],
            insights=[f"Dimensions: {len(num_cols[:6])}", f"Custom color: {chart_color}"]
        )
    
    def _empty_result(self, viz_type: VizType, message: str) -> VisualizationResult:
        """Return empty result with error message."""
        return VisualizationResult(
            viz_type=viz_type,
            title="Visualization Error",
            data={"error": message},
            layout={},
            insights=[message]
        )


# =============================================================================
# INTELLIGENT VISUALIZER (MAIN INTERFACE)
# =============================================================================

class IntelligentVisualizer:
    """
    🎨 INTELLIGENT VISUALIZER - Main Interface
    
    Auto-generates the best visualization for any query/data combination.
    Supports knowledge graphs, mind maps, and 20+ chart types.
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.data_analyzer = DataAnalyzer()
        self.viz_selector = VisualizationSelector()
        self.chart_gen = ChartGenerator()
        self.kg_gen = KnowledgeGraphGenerator()
        self.mm_gen = MindMapGenerator()
        self.network_gen = NetworkGraphGenerator()
    
    def visualize(self, df: pd.DataFrame, query: str = "",
                  viz_type: VizType = None) -> VisualizationResult:
        """
        Generate visualization automatically or with specified type.
        
        Args:
            df: DataFrame to visualize
            query: User's query for context
            viz_type: Optional specific type, or auto-detect
            
        Returns:
            VisualizationResult with data ready for frontend
        """
        if df is None or df.empty:
            return VisualizationResult(
                viz_type=VizType.BAR,
                title="No Data",
                data={"error": "No data available"},
                layout={},
                insights=["Please upload data first"]
            )
        
        # Analyze data
        analysis = self.data_analyzer.analyze(df)
        
        # Select visualization type if not specified
        if not viz_type:
            viz_type, confidence = self.viz_selector.select(query, analysis)
        
        # Generate appropriate visualization
        if viz_type == VizType.KNOWLEDGE_GRAPH:
            return self.kg_gen.generate(df, query)
        elif viz_type == VizType.MIND_MAP:
            return self.mm_gen.generate(df, query)
        elif viz_type == VizType.NETWORK_GRAPH:
            return self.network_gen.generate(df, query=query)
        else:
            return self.chart_gen.generate(df, viz_type, query)
    
    def to_json(self, result: VisualizationResult) -> str:
        """Convert result to JSON for frontend."""
        return json.dumps({
            "type": result.viz_type.value,
            "title": result.title,
            "data": result.data,
            "layout": result.layout,
            "insights": result.insights
        }, default=str)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def smart_visualize(user_id: str, query: str, df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Quick function for intelligent visualization.
    
    CLAUDE-STYLE: Uses LLM to understand ANY chart request dynamically.
    Falls back to rule-based if LLM fails.
    """
    if df is None:
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(user_id)
        except:
            return {"error": "No data available"}
    
    # TRY LLM-DRIVEN VISUALIZATION FIRST (Claude-style)
    try:
        from core.llm_visualizer import llm_visualize
        result = llm_visualize(df, query, user_id)
        if result.get("success"):
            return {
                "success": True,
                "type": result.get("chart_type", "auto"),
                "visualization_type": result.get("visualization_type", "auto"),
                "chart": result.get("chart"),
                "data": result.get("chart", {}).get("data", []),
                "layout": result.get("chart", {}).get("layout", {}),
                "insights": result.get("chart", {}).get("insights", [])
            }
    except Exception as e:
        logger.warning(f"LLM visualizer failed, falling back: {e}")
    
    # FALLBACK: Rule-based visualization
    visualizer = IntelligentVisualizer(user_id)
    result = visualizer.visualize(df, query)
    
    return {
        "success": True,
        "type": result.viz_type.value,
        "visualization_type": result.viz_type.value,
        "title": result.title,
        "chart": result.data,
        "data": result.data,
        "layout": result.layout,
        "insights": result.insights
    }


def generate_knowledge_graph(user_id: str, df: pd.DataFrame = None, query: str = "") -> Dict:
    """Generate knowledge graph from user data."""
    if df is None:
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(user_id)
        except:
            return {"error": "No data available"}
    
    gen = KnowledgeGraphGenerator()
    result = gen.generate(df, query)
    return {"type": "knowledge_graph", "data": result.data, "insights": result.insights}


def generate_mind_map(user_id: str, df: pd.DataFrame = None, topic: str = "") -> Dict:
    """Generate mind map from user data."""
    if df is None:
        try:
            from api.v1.endpoints.charts import get_user_data
            df = get_user_data(user_id)
        except:
            return {"error": "No data available"}
    
    gen = MindMapGenerator()
    result = gen.generate(df, topic)
    return {"type": "mind_map", "data": result.data, "insights": result.insights}


# Module exports
__all__ = [
    'VizType',
    'VisualizationResult',
    'IntelligentVisualizer',
    'ChartGenerator',
    'KnowledgeGraphGenerator',
    'MindMapGenerator',
    'NetworkGraphGenerator',
    'DataAnalyzer',
    'VisualizationSelector',
    'smart_visualize',
    'generate_knowledge_graph',
    'generate_mind_map'
]
