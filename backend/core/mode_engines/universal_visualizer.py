"""
UNIVERSAL DYNAMIC VISUALIZER
=============================

Production-level dynamic chart generation for ALL mode engines.
NO HARDCODING - All charts generated from actual DataFrame data.

Usage:
    from core.mode_engines.universal_visualizer import UniversalVisualizer
    chart = UniversalVisualizer.auto_chart(df, query)
"""

import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class UniversalVisualizer:
    """
    🎨 UNIVERSAL DYNAMIC VISUALIZER
    
    Generates production-quality Plotly charts from any DataFrame.
    Automatically detects the best chart type based on query and data.
    
    Features:
    - Auto column detection (date, numeric, category)
    - Query-based chart selection
    - Clean Plotly JSON output
    - No hardcoded values - all from data
    """
    
    # Color palette for consistent styling
    COLORS = {
        'primary': '#3b82f6',
        'secondary': '#8b5cf6',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'info': '#06b6d4',
        'gradient': ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#22c55e', '#06b6d4']
    }
    
    LAYOUT_BASE = {
        'paper_bgcolor': '#f8fafc',
        'plot_bgcolor': '#ffffff',
        'font': {'color': '#1f2937', 'family': 'Inter, -apple-system, sans-serif'},
        'margin': {'l': 60, 'r': 40, 't': 50, 'b': 60}
    }
    
    @staticmethod
    def detect_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
        """Auto-detect column types from DataFrame"""
        result = {
            'date': [],
            'numeric': [],
            'category': [],
            'id': [],
            'text': []
        }
        
        for col in df.columns:
            if col.startswith('_'):  # Skip internal columns
                continue
            
            col_lower = col.lower()
            
            # Date detection
            if any(x in col_lower for x in ['date', 'time', 'created', 'updated', 'year', 'month']):
                result['date'].append(col)
            # ID detection
            elif any(x in col_lower for x in ['id', 'code', 'key', 'number']) and df[col].dtype == 'object':
                result['id'].append(col)
            # Numeric detection
            elif df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                result['numeric'].append(col)
            # Category detection (low cardinality strings)
            elif df[col].dtype == 'object' and df[col].nunique() < 50:
                result['category'].append(col)
            else:
                result['text'].append(col)
        
        return result
    
    @staticmethod
    def detect_chart_type(query: str, col_types: Dict) -> str:
        """Detect best chart type from query"""
        q = query.lower()
        
        # Trend/Time analysis
        if any(x in q for x in ['trend', 'over time', 'monthly', 'yearly', 'timeline', 'growth']):
            return 'line'
        
        # Distribution
        if any(x in q for x in ['distribution', 'histogram', 'spread', 'range']):
            return 'histogram'
        
        # Comparison
        if any(x in q for x in ['compare', 'versus', 'vs', 'difference']):
            return 'grouped_bar'
        
        # Ranking
        if any(x in q for x in ['top', 'best', 'worst', 'highest', 'lowest', 'ranking']):
            return 'horizontal_bar'
        
        # Proportion
        if any(x in q for x in ['percentage', 'proportion', 'share', 'breakdown', 'split']):
            return 'pie'
        
        # Correlation
        if any(x in q for x in ['correlation', 'relationship', 'scatterplot']):
            return 'scatter'
        
        # Aggregation
        if any(x in q for x in ['total', 'sum', 'average', 'count', 'group by']):
            return 'bar'
        
        # Default based on data
        if col_types.get('date'):
            return 'line'
        elif len(col_types.get('category', [])) > 0:
            return 'bar'
        else:
            return 'bar'
    
    @classmethod
    def auto_chart(cls, df: pd.DataFrame, query: str) -> Optional[Dict]:
        """
        Auto-generate the most relevant chart based on query and data.
        
        Returns Plotly JSON dict ready for frontend rendering.
        """
        if df is None or df.empty:
            return None
        
        try:
            col_types = cls.detect_columns(df)
            chart_type = cls.detect_chart_type(query, col_types)
            
            logger.info(f"🎨 Auto-chart: type={chart_type}, cols={col_types}")
            
            if chart_type == 'line':
                return cls.trend_chart(df, query, col_types)
            elif chart_type == 'histogram':
                return cls.distribution_chart(df, col_types)
            elif chart_type == 'grouped_bar':
                return cls.comparison_chart(df, query, col_types)
            elif chart_type == 'horizontal_bar':
                return cls.ranking_chart(df, query, col_types)
            elif chart_type == 'pie':
                return cls.proportion_chart(df, query, col_types)
            elif chart_type == 'scatter':
                return cls.correlation_chart(df, col_types)
            else:
                return cls.aggregation_chart(df, query, col_types)
                
        except Exception as e:
            logger.error(f"Auto-chart error: {e}")
            return None
    
    @classmethod
    def trend_chart(cls, df: pd.DataFrame, query: str, col_types: Dict) -> Optional[Dict]:
        """Generate trend/line chart from data"""
        date_cols = col_types.get('date', [])
        numeric_cols = col_types.get('numeric', [])
        
        if not date_cols or not numeric_cols:
            return cls.aggregation_chart(df, query, col_types)
        
        date_col = date_cols[0]
        value_col = numeric_cols[0]  # Use first numeric column
        
        # Find best value column from query
        for col in numeric_cols:
            if col.lower() in query.lower():
                value_col = col
                break
        
        # Group by date and sum
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            grouped = df.groupby(df[date_col].dt.to_period('M'))[value_col].sum().reset_index()
            grouped[date_col] = grouped[date_col].astype(str)
        except:
            grouped = df.groupby(date_col)[value_col].sum().reset_index()
        
        chart = {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": grouped[date_col].tolist(),
                "y": grouped[value_col].tolist(),
                "line": {"color": cls.COLORS['primary'], "width": 3},
                "marker": {"size": 8},
                "name": value_col.replace('_', ' ').title()
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📈 {value_col.replace('_', ' ').title()} Trend", "font": {"size": 16}},
                "xaxis": {"title": date_col.replace('_', ' ').title()},
                "yaxis": {"title": value_col.replace('_', ' ').title()},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def distribution_chart(cls, df: pd.DataFrame, col_types: Dict) -> Optional[Dict]:
        """Generate histogram/distribution chart"""
        numeric_cols = col_types.get('numeric', [])
        
        if not numeric_cols:
            return None
        
        col = numeric_cols[0]
        values = df[col].dropna()
        
        chart = {
            "data": [{
                "type": "histogram",
                "x": values.tolist(),
                "nbinsx": 30,
                "marker": {"color": cls.COLORS['secondary'], "line": {"color": "#6d28d9", "width": 1}},
                "name": col.replace('_', ' ').title()
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📊 Distribution of {col.replace('_', ' ').title()}", "font": {"size": 16}},
                "xaxis": {"title": col.replace('_', ' ').title()},
                "yaxis": {"title": "Frequency"},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def comparison_chart(cls, df: pd.DataFrame, query: str, col_types: Dict) -> Optional[Dict]:
        """Generate grouped bar comparison chart"""
        category_cols = col_types.get('category', [])
        numeric_cols = col_types.get('numeric', [])
        
        if not category_cols or len(numeric_cols) < 2:
            return cls.aggregation_chart(df, query, col_types)
        
        cat_col = category_cols[0]
        val_cols = numeric_cols[:2]
        
        grouped = df.groupby(cat_col)[val_cols].sum().head(10).reset_index()
        
        data = []
        for i, col in enumerate(val_cols):
            data.append({
                "type": "bar",
                "name": col.replace('_', ' ').title(),
                "x": grouped[cat_col].tolist(),
                "y": grouped[col].tolist(),
                "marker": {"color": cls.COLORS['gradient'][i]}
            })
        
        chart = {
            "data": data,
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "⚖️ Comparison", "font": {"size": 16}},
                "barmode": "group",
                "xaxis": {"tickangle": -45},
                "height": 400,
                "showlegend": True
            }
        }
        return chart
    
    @classmethod
    def ranking_chart(cls, df: pd.DataFrame, query: str, col_types: Dict, n: int = 10) -> Optional[Dict]:
        """Generate horizontal bar ranking chart"""
        category_cols = col_types.get('category', [])
        numeric_cols = col_types.get('numeric', [])
        
        if not category_cols or not numeric_cols:
            return None
        
        cat_col = category_cols[0]
        val_col = numeric_cols[0]
        
        # Find columns mentioned in query
        for col in category_cols:
            if col.lower() in query.lower():
                cat_col = col
                break
        for col in numeric_cols:
            if col.lower() in query.lower():
                val_col = col
                break
        
        # Determine if top or bottom
        is_bottom = any(x in query.lower() for x in ['worst', 'lowest', 'bottom', 'least'])
        
        grouped = df.groupby(cat_col)[val_col].sum().reset_index()
        grouped = grouped.sort_values(val_col, ascending=is_bottom).head(n)
        
        # Reverse for horizontal bar display
        grouped = grouped.iloc[::-1]
        
        chart = {
            "data": [{
                "type": "bar",
                "orientation": "h",
                "y": grouped[cat_col].tolist(),
                "x": grouped[val_col].tolist(),
                "marker": {"color": cls.COLORS['primary']},
                "text": [f"{v:,.0f}" for v in grouped[val_col]],
                "textposition": "outside"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🏆 {'Bottom' if is_bottom else 'Top'} {n} by {val_col.replace('_', ' ').title()}", "font": {"size": 16}},
                "xaxis": {"title": val_col.replace('_', ' ').title()},
                "margin": {"l": 150, "r": 80, "t": 50, "b": 50},
                "height": max(300, n * 40)
            }
        }
        return chart
    
    @classmethod
    def proportion_chart(cls, df: pd.DataFrame, query: str, col_types: Dict) -> Optional[Dict]:
        """Generate pie/donut chart for proportions"""
        category_cols = col_types.get('category', [])
        numeric_cols = col_types.get('numeric', [])
        
        if not category_cols:
            return None
        
        cat_col = category_cols[0]
        
        if numeric_cols:
            val_col = numeric_cols[0]
            grouped = df.groupby(cat_col)[val_col].sum().reset_index()
        else:
            grouped = df[cat_col].value_counts().reset_index()
            grouped.columns = [cat_col, 'count']
            val_col = 'count'
        
        # Limit to top 8 for readability
        grouped = grouped.nlargest(8, val_col)
        
        chart = {
            "data": [{
                "type": "pie",
                "labels": grouped[cat_col].tolist(),
                "values": grouped[val_col].tolist(),
                "hole": 0.4,
                "marker": {"colors": cls.COLORS['gradient']},
                "textposition": "outside",
                "textinfo": "label+percent"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📊 {cat_col.replace('_', ' ').title()} Distribution", "font": {"size": 16}},
                "showlegend": False,
                "height": 450
            }
        }
        return chart
    
    @classmethod
    def correlation_chart(cls, df: pd.DataFrame, col_types: Dict) -> Optional[Dict]:
        """Generate scatter plot for correlation"""
        numeric_cols = col_types.get('numeric', [])
        
        if len(numeric_cols) < 2:
            return None
        
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        # Sample if too large
        sample_df = df.sample(min(len(df), 500)) if len(df) > 500 else df
        
        chart = {
            "data": [{
                "type": "scatter",
                "mode": "markers",
                "x": sample_df[x_col].dropna().tolist(),
                "y": sample_df[y_col].dropna().tolist(),
                "marker": {"color": cls.COLORS['primary'], "opacity": 0.6, "size": 8},
                "name": "Data Points"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"🔗 {x_col} vs {y_col}", "font": {"size": 16}},
                "xaxis": {"title": x_col.replace('_', ' ').title()},
                "yaxis": {"title": y_col.replace('_', ' ').title()},
                "height": 450
            }
        }
        return chart
    
    @classmethod
    def aggregation_chart(cls, df: pd.DataFrame, query: str, col_types: Dict) -> Optional[Dict]:
        """Generate aggregation bar chart (default)"""
        category_cols = col_types.get('category', [])
        numeric_cols = col_types.get('numeric', [])
        
        if not category_cols or not numeric_cols:
            # Fallback: show numeric column sums
            if numeric_cols:
                sums = {col: df[col].sum() for col in numeric_cols[:6]}
                chart = {
                    "data": [{
                        "type": "bar",
                        "x": list(sums.keys()),
                        "y": list(sums.values()),
                        "marker": {"color": cls.COLORS['gradient'][:len(sums)]},
                        "text": [f"{v:,.0f}" for v in sums.values()],
                        "textposition": "outside"
                    }],
                    "layout": {
                        **cls.LAYOUT_BASE,
                        "title": {"text": "📊 Data Summary", "font": {"size": 16}},
                        "xaxis": {"tickangle": -45},
                        "height": 400
                    }
                }
                return chart
            return None
        
        cat_col = category_cols[0]
        val_col = numeric_cols[0]
        
        grouped = df.groupby(cat_col)[val_col].sum().nlargest(10).reset_index()
        
        chart = {
            "data": [{
                "type": "bar",
                "x": grouped[cat_col].tolist(),
                "y": grouped[val_col].tolist(),
                "marker": {"color": cls.COLORS['primary']},
                "text": [f"{v:,.0f}" for v in grouped[val_col]],
                "textposition": "outside"
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": f"📊 {val_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}", "font": {"size": 16}},
                "xaxis": {"tickangle": -45},
                "height": 400
            }
        }
        return chart
    
    @classmethod
    def correlation_heatmap(cls, df: pd.DataFrame) -> Optional[Dict]:
        """Generate correlation heatmap for numeric columns"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return None
        
        # Limit columns
        cols = numeric_df.columns[:10]
        corr = numeric_df[cols].corr()
        
        chart = {
            "data": [{
                "type": "heatmap",
                "z": corr.values.tolist(),
                "x": [c[:15] for c in corr.columns],
                "y": [c[:15] for c in corr.index],
                "colorscale": "RdBu",
                "zmin": -1,
                "zmax": 1,
                "text": [[f"{v:.2f}" for v in row] for row in corr.values],
                "texttemplate": "%{text}",
                "colorbar": {"title": "Correlation"}
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "🔗 Correlation Matrix", "font": {"size": 16}},
                "height": max(400, len(cols) * 35),
                "xaxis": {"tickangle": -45}
            }
        }
        return chart
    
    @classmethod
    def data_overview_chart(cls, df: pd.DataFrame) -> Optional[Dict]:
        """Generate overview chart showing key metrics"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns[:6]
        
        if len(numeric_cols) == 0:
            return None
        
        # Calculate key stats
        stats = []
        for col in numeric_cols:
            stats.append({
                'name': col[:15],
                'total': df[col].sum(),
                'avg': df[col].mean()
            })
        
        chart = {
            "data": [{
                "type": "bar",
                "name": "Total",
                "x": [s['name'] for s in stats],
                "y": [s['total'] for s in stats],
                "marker": {"color": cls.COLORS['primary']}
            }],
            "layout": {
                **cls.LAYOUT_BASE,
                "title": {"text": "📊 Data Overview", "font": {"size": 16}},
                "xaxis": {"tickangle": -45},
                "height": 400
            }
        }
        return chart


# Convenience functions for quick access
def auto_visualize(df: pd.DataFrame, query: str) -> Optional[Dict]:
    """Quick function to auto-generate chart"""
    return UniversalVisualizer.auto_chart(df, query)


def get_chart_for_intent(df: pd.DataFrame, intent: str) -> Optional[Dict]:
    """Generate chart based on detected intent"""
    col_types = UniversalVisualizer.detect_columns(df)
    
    intent_map = {
        'trend': lambda: UniversalVisualizer.trend_chart(df, intent, col_types),
        'distribution': lambda: UniversalVisualizer.distribution_chart(df, col_types),
        'comparison': lambda: UniversalVisualizer.comparison_chart(df, intent, col_types),
        'ranking': lambda: UniversalVisualizer.ranking_chart(df, intent, col_types),
        'proportion': lambda: UniversalVisualizer.proportion_chart(df, intent, col_types),
        'correlation': lambda: UniversalVisualizer.correlation_chart(df, col_types),
        'aggregation': lambda: UniversalVisualizer.aggregation_chart(df, intent, col_types),
    }
    
    generator = intent_map.get(intent, lambda: UniversalVisualizer.auto_chart(df, intent))
    return generator()
