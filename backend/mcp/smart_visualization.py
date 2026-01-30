# Smart Visualization MCP - Dynamic Chart/Graph Generation
"""
🎨 SMART VISUALIZATION ENGINE
==============================

Intelligently generates charts, graphs, mind maps, and knowledge graphs
based on DATA and USER QUERY - no hardcoding.

Features:
- 📊 Smart chart type selection based on data structure
- 🧠 Mind maps for hierarchical data
- 🔗 Knowledge graphs for relationships
- 📈 Automatic visualization recommendations
- 🎯 Query-driven visualization selection

Author: AI Business Analyst Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import re
import json
import logging

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """All supported visualization types"""
    # Standard Charts
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    
    # Statistical
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    
    # Time Series
    TREND_LINE = "trend_line"
    FORECAST_CHART = "forecast_chart"
    SEASONAL_CHART = "seasonal_chart"
    
    # Comparison
    GROUPED_BAR = "grouped_bar"
    STACKED_BAR = "stacked_bar"
    RADAR_CHART = "radar_chart"
    
    # Hierarchical
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    MIND_MAP = "mind_map"
    
    # Relationship
    KNOWLEDGE_GRAPH = "knowledge_graph"
    NETWORK_GRAPH = "network_graph"
    SANKEY = "sankey"
    
    # Advanced
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TABLE = "table"


@dataclass
class VisualizationRecommendation:
    """Recommendation for visualization"""
    viz_type: VisualizationType
    confidence: float
    reason: str
    priority: int
    data_requirements: List[str]


class SmartVisualization:
    """
    🎨 Smart Visualization Engine
    
    Automatically selects and generates the best visualization
    based on data characteristics and user query.
    """
    
    # Keywords for different visualizations
    VIZ_KEYWORDS = {
        VisualizationType.BAR_CHART: ['bar', 'comparison', 'compare', 'versus', 'vs'],
        VisualizationType.LINE_CHART: ['trend', 'over time', 'timeline', 'progress', 'line'],
        VisualizationType.PIE_CHART: ['distribution', 'share', 'percentage', 'proportion', 'pie'],
        VisualizationType.SCATTER_PLOT: ['correlation', 'relationship', 'scatter', 'versus'],
        VisualizationType.HEATMAP: ['heatmap', 'matrix', 'correlation matrix', 'intensity'],
        VisualizationType.HISTOGRAM: ['distribution', 'frequency', 'histogram', 'spread'],
        VisualizationType.BOX_PLOT: ['outlier', 'distribution', 'quartile', 'box'],
        VisualizationType.TREEMAP: ['hierarchy', 'breakdown', 'composition', 'treemap'],
        VisualizationType.MIND_MAP: ['mind map', 'concept', 'structure', 'hierarchy', 'overview'],
        VisualizationType.KNOWLEDGE_GRAPH: ['knowledge graph', 'relationship', 'network', 'connection', 'entities'],
        VisualizationType.NETWORK_GRAPH: ['network', 'connection', 'nodes', 'links', 'graph'],
        VisualizationType.SANKEY: ['flow', 'sankey', 'transition', 'movement'],
        VisualizationType.WATERFALL: ['waterfall', 'contribution', 'breakdown', 'impact'],
        VisualizationType.FUNNEL: ['funnel', 'conversion', 'stages', 'pipeline'],
        VisualizationType.RADAR_CHART: ['radar', 'multi-dimensional', 'comparison', 'profile'],
        VisualizationType.FORECAST_CHART: ['forecast', 'predict', 'future', 'projection'],
        VisualizationType.GAUGE: ['gauge', 'score', 'level', 'indicator', 'meter'],
    }
    
    def __init__(self):
        self.colors = {
            'primary': '#f97316',
            'secondary': '#06b6d4',
            'success': '#22c55e',
            'warning': '#eab308',
            'danger': '#ef4444',
            'info': '#3b82f6',
            'muted': '#6b7280',
        }
    
    def analyze_and_visualize(
        self,
        df: pd.DataFrame,
        query: str,
        prefer_type: Optional[VisualizationType] = None
    ) -> Dict[str, Any]:
        """
        Analyze data and query, generate appropriate visualization.
        
        Args:
            df: DataFrame with data
            query: User's query
            prefer_type: Optional preferred visualization type
            
        Returns:
            Visualization payload for frontend
        """
        if df is None or df.empty:
            return {"error": "No data provided", "chart": None}
        
        # 1. Analyze data characteristics
        data_profile = self._profile_data(df)
        
        # 2. Detect user's visualization intent
        detected_type, confidence = self._detect_viz_intent(query, data_profile)
        
        # 3. Override with preference if provided
        if prefer_type:
            detected_type = prefer_type
            confidence = 1.0
        
        # 4. Generate visualization
        viz = self._generate_visualization(df, detected_type, query, data_profile)
        
        return {
            "success": True,
            "visualization_type": detected_type.value,
            "confidence": confidence,
            "chart": viz,
            "recommendations": self._get_alternative_recommendations(data_profile, query)
        }
    
    def _profile_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Profile the data to understand its structure."""
        profile = {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_cols": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_cols": df.select_dtypes(include=['object', 'category']).columns.tolist(),
            "datetime_cols": [],
            "has_time_series": False,
            "has_hierarchy": False,
            "unique_categories": {},
            "numeric_stats": {}
        }
        
        # Check for datetime columns
        for col in df.columns:
            try:
                if 'date' in col.lower() or 'time' in col.lower():
                    profile["datetime_cols"].append(col)
                    profile["has_time_series"] = True
            except:
                pass
        
        # Check for hierarchy (parent-child relationships)
        id_cols = [c for c in df.columns if 'id' in c.lower() or 'parent' in c.lower()]
        if len(id_cols) >= 2:
            profile["has_hierarchy"] = True
        
        # Unique values for categorical columns
        for col in profile["categorical_cols"][:5]:
            try:
                profile["unique_categories"][col] = df[col].nunique()
            except:
                pass
        
        # Stats for numeric columns
        for col in profile["numeric_cols"][:5]:
            try:
                profile["numeric_stats"][col] = {
                    "mean": float(df[col].mean()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "std": float(df[col].std())
                }
            except:
                pass
        
        return profile
    
    def _detect_viz_intent(
        self,
        query: str,
        data_profile: Dict
    ) -> Tuple[VisualizationType, float]:
        """Detect what visualization the user wants."""
        q_lower = query.lower()
        
        # Score each visualization type based on keywords
        scores = {}
        for viz_type, keywords in self.VIZ_KEYWORDS.items():
            score = sum(2 if kw in q_lower else 0 for kw in keywords)
            if score > 0:
                scores[viz_type] = score
        
        # If no keyword match, infer from data
        if not scores:
            return self._infer_from_data(data_profile)
        
        # Return highest scoring
        best_type = max(scores, key=scores.get)
        confidence = min(1.0, scores[best_type] / 4)
        
        return best_type, confidence
    
    def _infer_from_data(self, profile: Dict) -> Tuple[VisualizationType, float]:
        """Infer best visualization from data structure."""
        # Time series data -> Line chart
        if profile["has_time_series"] and profile["numeric_cols"]:
            return VisualizationType.LINE_CHART, 0.8
        
        # Few categories + numeric -> Bar chart
        cat_cols = profile["categorical_cols"]
        num_cols = profile["numeric_cols"]
        
        if cat_cols and num_cols:
            max_unique = max(profile["unique_categories"].values()) if profile["unique_categories"] else 0
            if max_unique <= 10:
                return VisualizationType.BAR_CHART, 0.7
            elif max_unique <= 20:
                return VisualizationType.TREEMAP, 0.6
        
        # Multiple numeric -> Scatter or heatmap
        if len(num_cols) >= 2:
            if len(num_cols) > 4:
                return VisualizationType.HEATMAP, 0.7
            return VisualizationType.SCATTER_PLOT, 0.7
        
        # Single numeric -> Histogram
        if len(num_cols) == 1:
            return VisualizationType.HISTOGRAM, 0.6
        
        # Default to table
        return VisualizationType.TABLE, 0.5
    
    def _generate_visualization(
        self,
        df: pd.DataFrame,
        viz_type: VisualizationType,
        query: str,
        profile: Dict
    ) -> Dict[str, Any]:
        """Generate the visualization payload."""
        
        generators = {
            VisualizationType.BAR_CHART: self._gen_bar_chart,
            VisualizationType.LINE_CHART: self._gen_line_chart,
            VisualizationType.PIE_CHART: self._gen_pie_chart,
            VisualizationType.SCATTER_PLOT: self._gen_scatter_plot,
            VisualizationType.HEATMAP: self._gen_heatmap,
            VisualizationType.HISTOGRAM: self._gen_histogram,
            VisualizationType.TREEMAP: self._gen_treemap,
            VisualizationType.MIND_MAP: self._gen_mind_map,
            VisualizationType.KNOWLEDGE_GRAPH: self._gen_knowledge_graph,
            VisualizationType.NETWORK_GRAPH: self._gen_network_graph,
            VisualizationType.RADAR_CHART: self._gen_radar_chart,
            VisualizationType.WATERFALL: self._gen_waterfall,
            VisualizationType.GAUGE: self._gen_gauge,
            VisualizationType.TABLE: self._gen_table,
        }
        
        generator = generators.get(viz_type, self._gen_bar_chart)
        return generator(df, profile, query)
    
    # ==========================================================================
    # CHART GENERATORS
    # ==========================================================================
    
    def _gen_bar_chart(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate bar chart from data."""
        cat_col = profile["categorical_cols"][0] if profile["categorical_cols"] else df.columns[0]
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else df.columns[-1]
        
        # Group data
        try:
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(15)
            x_labels = grouped.index.tolist()
            values = grouped.values.tolist()
        except:
            x_labels = df[cat_col].head(15).tolist()
            values = list(range(len(x_labels)))
        
        return {
            "type": "bar",
            "data": {
                "labels": x_labels,
                "datasets": [{
                    "label": num_col,
                    "data": [round(v, 2) if isinstance(v, float) else v for v in values],
                    "backgroundColor": self.colors['primary'],
                    "borderColor": self.colors['primary'],
                    "borderRadius": 6
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"{num_col} by {cat_col}"},
                    "legend": {"display": False}
                },
                "scales": {"y": {"beginAtZero": True}}
            }
        }
    
    def _gen_line_chart(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate line chart for time series."""
        time_col = profile["datetime_cols"][0] if profile["datetime_cols"] else df.columns[0]
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else df.columns[-1]
        
        try:
            df_sorted = df.sort_values(time_col)
            x_labels = df_sorted[time_col].astype(str).tolist()[:100]
            values = df_sorted[num_col].tolist()[:100]
        except:
            x_labels = list(range(min(100, len(df))))
            values = df[num_col].head(100).tolist()
        
        return {
            "type": "line",
            "data": {
                "labels": x_labels,
                "datasets": [{
                    "label": num_col,
                    "data": [round(v, 2) if isinstance(v, (int, float)) else v for v in values],
                    "borderColor": self.colors['primary'],
                    "backgroundColor": f"{self.colors['primary']}20",
                    "fill": True,
                    "tension": 0.4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"{num_col} Over Time"}
                }
            }
        }
    
    def _gen_pie_chart(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate pie chart for distribution."""
        cat_col = profile["categorical_cols"][0] if profile["categorical_cols"] else df.columns[0]
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else None
        
        if num_col:
            grouped = df.groupby(cat_col)[num_col].sum().nlargest(8)
            labels = grouped.index.tolist()
            values = grouped.values.tolist()
        else:
            value_counts = df[cat_col].value_counts().head(8)
            labels = value_counts.index.tolist()
            values = value_counts.values.tolist()
        
        colors = ['#f97316', '#06b6d4', '#22c55e', '#eab308', '#ef4444', '#8b5cf6', '#ec4899', '#6b7280']
        
        return {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": [round(v, 2) for v in values],
                    "backgroundColor": colors[:len(labels)],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"Distribution of {cat_col}"},
                    "legend": {"position": "right"}
                }
            }
        }
    
    def _gen_scatter_plot(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate scatter plot for correlation."""
        num_cols = profile["numeric_cols"][:2]
        if len(num_cols) < 2:
            num_cols = df.select_dtypes(include=[np.number]).columns[:2].tolist()
        
        x_col, y_col = num_cols[0], num_cols[1] if len(num_cols) > 1 else num_cols[0]
        
        data_points = []
        for _, row in df.head(500).iterrows():
            try:
                data_points.append({"x": float(row[x_col]), "y": float(row[y_col])})
            except:
                pass
        
        return {
            "type": "scatter",
            "data": {
                "datasets": [{
                    "label": f"{x_col} vs {y_col}",
                    "data": data_points,
                    "backgroundColor": self.colors['primary'],
                    "pointRadius": 4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"Correlation: {x_col} vs {y_col}"}
                },
                "scales": {
                    "x": {"title": {"display": True, "text": x_col}},
                    "y": {"title": {"display": True, "text": y_col}}
                }
            }
        }
    
    def _gen_heatmap(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate correlation heatmap."""
        num_cols = profile["numeric_cols"][:8]
        if len(num_cols) < 2:
            return self._gen_table(df, profile, query)
        
        corr = df[num_cols].corr()
        
        data = []
        for i, row in enumerate(corr.values):
            for j, val in enumerate(row):
                data.append({
                    "x": num_cols[j],
                    "y": num_cols[i],
                    "value": round(val, 2)
                })
        
        return {
            "type": "heatmap",
            "data": {
                "labels": {"x": num_cols, "y": num_cols},
                "datasets": [{
                    "data": data,
                    "backgroundColor": self._get_heatmap_colors(data)
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Correlation Matrix"}
                }
            }
        }
    
    def _gen_histogram(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate histogram for distribution."""
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else df.columns[0]
        
        values = df[num_col].dropna().values
        hist, bins = np.histogram(values, bins=20)
        
        labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": f"Distribution of {num_col}",
                    "data": hist.tolist(),
                    "backgroundColor": self.colors['secondary'],
                    "borderRadius": 4
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"Distribution of {num_col}"}
                },
                "scales": {"y": {"title": {"display": True, "text": "Frequency"}}}
            }
        }
    
    def _gen_treemap(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate treemap for hierarchical data."""
        cat_col = profile["categorical_cols"][0] if profile["categorical_cols"] else df.columns[0]
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else None
        
        if num_col:
            grouped = df.groupby(cat_col)[num_col].sum().nlargest(20)
        else:
            grouped = df[cat_col].value_counts().head(20)
        
        data = [{"name": str(k), "value": float(v)} for k, v in grouped.items()]
        
        return {
            "type": "treemap",
            "data": {
                "datasets": [{
                    "tree": data,
                    "key": "value",
                    "groups": ["name"],
                    "backgroundColor": self._generate_colors(len(data))
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"Breakdown by {cat_col}"}
                }
            }
        }
    
    def _gen_mind_map(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate mind map structure from data."""
        # Create hierarchical structure from data
        nodes = []
        edges = []
        
        # Root node from query or first column
        root_id = "root"
        root_label = query[:50] if query else "Data Overview"
        nodes.append({"id": root_id, "label": root_label, "level": 0, "type": "root"})
        
        # Add category branches
        for i, col in enumerate(profile["categorical_cols"][:5]):
            cat_id = f"cat_{i}"
            nodes.append({"id": cat_id, "label": col, "level": 1, "type": "category"})
            edges.append({"from": root_id, "to": cat_id})
            
            # Add top values as children
            try:
                top_vals = df[col].value_counts().head(5).index.tolist()
                for j, val in enumerate(top_vals):
                    val_id = f"val_{i}_{j}"
                    nodes.append({"id": val_id, "label": str(val)[:30], "level": 2, "type": "value"})
                    edges.append({"from": cat_id, "to": val_id})
            except:
                pass
        
        # Add numeric branches
        for i, col in enumerate(profile["numeric_cols"][:5]):
            num_id = f"num_{i}"
            stats = profile["numeric_stats"].get(col, {})
            label = f"{col}\nμ={stats.get('mean', 0):.1f}"
            nodes.append({"id": num_id, "label": label, "level": 1, "type": "numeric"})
            edges.append({"from": root_id, "to": num_id})
        
        return {
            "type": "mindmap",
            "data": {
                "nodes": nodes,
                "edges": edges
            },
            "options": {
                "responsive": True,
                "layout": "radial",
                "nodeColors": {
                    "root": self.colors['primary'],
                    "category": self.colors['secondary'],
                    "numeric": self.colors['success'],
                    "value": self.colors['muted']
                }
            }
        }
    
    def _gen_knowledge_graph(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate knowledge graph showing relationships."""
        nodes = []
        edges = []
        node_ids = set()
        
        # Use categorical columns as entity types
        cat_cols = profile["categorical_cols"][:3]
        
        if len(cat_cols) >= 2:
            # Create nodes from first few rows
            for idx, row in df.head(50).iterrows():
                for col in cat_cols:
                    val = str(row[col])[:30]
                    node_id = f"{col}_{val}"
                    if node_id not in node_ids:
                        nodes.append({
                            "id": node_id,
                            "label": val,
                            "group": col,
                            "size": 20
                        })
                        node_ids.add(node_id)
                
                # Create edges between entities in same row
                for i, col1 in enumerate(cat_cols):
                    for col2 in cat_cols[i+1:]:
                        val1, val2 = str(row[col1])[:30], str(row[col2])[:30]
                        edges.append({
                            "from": f"{col1}_{val1}",
                            "to": f"{col2}_{val2}",
                            "relationship": "related"
                        })
        else:
            # Just show column relationships
            for col in df.columns[:10]:
                nodes.append({"id": col, "label": col, "group": "column", "size": 25})
            
            # Add correlation edges for numeric columns
            num_cols = profile["numeric_cols"][:6]
            if len(num_cols) >= 2:
                try:
                    corr = df[num_cols].corr()
                    for i, col1 in enumerate(num_cols):
                        for col2 in num_cols[i+1:]:
                            if abs(corr.loc[col1, col2]) > 0.3:
                                edges.append({
                                    "from": col1,
                                    "to": col2,
                                    "relationship": f"corr: {corr.loc[col1, col2]:.2f}",
                                    "weight": abs(corr.loc[col1, col2])
                                })
                except:
                    pass
        
        return {
            "type": "knowledge_graph",
            "data": {
                "nodes": nodes[:100],  # Limit nodes
                "edges": edges[:200]   # Limit edges
            },
            "options": {
                "responsive": True,
                "physics": {"enabled": True},
                "layout": "force-directed",
                "nodeColors": {col: self._get_color(i) for i, col in enumerate(cat_cols)}
            }
        }
    
    def _gen_network_graph(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate network graph."""
        return self._gen_knowledge_graph(df, profile, query)
    
    def _gen_radar_chart(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate radar chart for multi-dimensional comparison."""
        num_cols = profile["numeric_cols"][:6]
        if len(num_cols) < 3:
            return self._gen_bar_chart(df, profile, query)
        
        # Normalize values
        datasets = []
        cat_col = profile["categorical_cols"][0] if profile["categorical_cols"] else None
        
        if cat_col:
            # Compare top categories
            top_cats = df[cat_col].value_counts().head(3).index.tolist()
            for i, cat in enumerate(top_cats):
                subset = df[df[cat_col] == cat]
                values = []
                for col in num_cols:
                    try:
                        val = subset[col].mean()
                        max_val = df[col].max()
                        values.append(round(val / max_val * 100 if max_val else 0, 2))
                    except:
                        values.append(0)
                
                datasets.append({
                    "label": str(cat),
                    "data": values,
                    "borderColor": self._get_color(i),
                    "backgroundColor": f"{self._get_color(i)}40"
                })
        else:
            # Show overall statistics
            values = [round(df[col].mean(), 2) for col in num_cols]
            datasets.append({
                "label": "Average",
                "data": values,
                "borderColor": self.colors['primary'],
                "backgroundColor": f"{self.colors['primary']}40"
            })
        
        return {
            "type": "radar",
            "data": {
                "labels": num_cols,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Multi-Dimensional Analysis"}}
            }
        }
    
    def _gen_waterfall(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate waterfall chart for contributions."""
        cat_col = profile["categorical_cols"][0] if profile["categorical_cols"] else df.columns[0]
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else df.columns[-1]
        
        try:
            grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
            labels = ['Start'] + grouped.index.tolist() + ['Total']
            
            running = 0
            data = [0]  # Start
            colors = [self.colors['muted']]
            
            for val in grouped.values:
                data.append(float(val))
                colors.append(self.colors['success'] if val >= 0 else self.colors['danger'])
                running += val
            
            data.append(running)  # Total
            colors.append(self.colors['primary'])
            
        except:
            labels = ['Start', 'Change', 'Total']
            data = [0, float(df[num_col].sum()), float(df[num_col].sum())]
            colors = [self.colors['muted'], self.colors['success'], self.colors['primary']]
        
        return {
            "type": "waterfall",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": colors
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": f"{num_col} Breakdown"}}
            }
        }
    
    def _gen_gauge(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate gauge chart for single metric."""
        num_col = profile["numeric_cols"][0] if profile["numeric_cols"] else df.columns[0]
        
        try:
            value = float(df[num_col].mean())
            min_val = float(df[num_col].min())
            max_val = float(df[num_col].max())
            percentage = (value - min_val) / (max_val - min_val) * 100 if max_val != min_val else 50
        except:
            value, min_val, max_val, percentage = 50, 0, 100, 50
        
        return {
            "type": "gauge",
            "data": {
                "value": round(value, 2),
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "percentage": round(percentage, 1)
            },
            "options": {
                "responsive": True,
                "title": f"Average {num_col}",
                "colors": {
                    "low": self.colors['danger'],
                    "medium": self.colors['warning'],
                    "high": self.colors['success']
                }
            }
        }
    
    def _gen_table(self, df: pd.DataFrame, profile: Dict, query: str) -> Dict:
        """Generate data table."""
        return {
            "type": "table",
            "data": {
                "columns": df.columns.tolist(),
                "rows": df.head(100).values.tolist(),
                "summary": {
                    "rows": len(df),
                    "columns": len(df.columns)
                }
            },
            "options": {
                "responsive": True,
                "sortable": True,
                "searchable": True,
                "pagination": True
            }
        }
    
    # ==========================================================================
    # HELPERS
    # ==========================================================================
    
    def _get_alternative_recommendations(
        self,
        profile: Dict,
        query: str
    ) -> List[Dict]:
        """Get alternative visualization recommendations."""
        recommendations = []
        
        # Based on data characteristics
        if profile["has_time_series"]:
            recommendations.append({
                "type": "line_chart",
                "reason": "Time series data detected",
                "confidence": 0.8
            })
        
        if len(profile["numeric_cols"]) >= 2:
            recommendations.append({
                "type": "scatter_plot",
                "reason": "Multiple numeric columns - show correlation",
                "confidence": 0.7
            })
            recommendations.append({
                "type": "heatmap",
                "reason": "Show correlation matrix",
                "confidence": 0.6
            })
        
        if profile["categorical_cols"]:
            recommendations.append({
                "type": "bar_chart",
                "reason": "Categorical data - compare values",
                "confidence": 0.8
            })
            recommendations.append({
                "type": "pie_chart",
                "reason": "Show distribution",
                "confidence": 0.6
            })
        
        if profile["has_hierarchy"]:
            recommendations.append({
                "type": "treemap",
                "reason": "Hierarchical structure detected",
                "confidence": 0.7
            })
        
        return recommendations[:5]
    
    def _generate_colors(self, n: int) -> List[str]:
        """Generate n distinct colors."""
        base_colors = list(self.colors.values())
        if n <= len(base_colors):
            return base_colors[:n]
        
        # Generate additional colors
        import colorsys
        colors = base_colors.copy()
        for i in range(n - len(base_colors)):
            hue = (i * 0.618033988749895) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
            colors.append(hex_color)
        
        return colors
    
    def _get_color(self, index: int) -> str:
        """Get color by index."""
        colors = list(self.colors.values())
        return colors[index % len(colors)]
    
    def _get_heatmap_colors(self, data: List[Dict]) -> List[str]:
        """Get colors for heatmap based on values."""
        colors = []
        for point in data:
            val = point.get('value', 0)
            if val > 0.7:
                colors.append(self.colors['success'])
            elif val > 0.3:
                colors.append(self.colors['warning'])
            elif val > 0:
                colors.append(self.colors['danger'])
            elif val > -0.3:
                colors.append('#fef2f2')
            else:
                colors.append(self.colors['info'])
        return colors


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def smart_visualize(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """Quick visualization based on data and query."""
    engine = SmartVisualization()
    return engine.analyze_and_visualize(df, query)


def generate_chart_from_data(
    df: pd.DataFrame,
    chart_type: str,
    query: str = ""
) -> Dict[str, Any]:
    """Generate specific chart type from data."""
    engine = SmartVisualization()
    try:
        viz_type = VisualizationType(chart_type)
    except:
        viz_type = None
    return engine.analyze_and_visualize(df, query, prefer_type=viz_type)


def get_visualization_recommendations(df: pd.DataFrame) -> List[Dict]:
    """Get recommended visualizations for data."""
    engine = SmartVisualization()
    profile = engine._profile_data(df)
    return engine._get_alternative_recommendations(profile, "")


# Quick test
if __name__ == "__main__":
    # Test data
    test_df = pd.DataFrame({
        'category': ['A', 'B', 'C', 'A', 'B', 'C'] * 10,
        'date': pd.date_range('2024-01-01', periods=60),
        'value': np.random.randint(100, 1000, 60),
        'quantity': np.random.randint(1, 50, 60)
    })
    
    # Test smart visualization
    result = smart_visualize(test_df, "show me a bar chart of value by category")
    print(f"Generated: {result['visualization_type']}")
    print(f"Confidence: {result['confidence']}")
    
    result = smart_visualize(test_df, "create a mind map of the data")
    print(f"Generated: {result['visualization_type']}")
