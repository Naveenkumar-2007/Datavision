"""
COMPREHENSIVE CHART SYSTEM - ALL 15+ Chart Types
==================================================

DataVision supports ALL major visualization types!
Everything autonomous - LLM picks the right chart for the query.

CHART TYPES SUPPORTED:
1. Bar Chart (vertical)
2. Horizontal Bar Chart
3. Stacked Bar Chart
4. Line Chart
5. Area Chart
6. Scatter Plot
7. Pie Chart
8. Donut Chart
9. Sunburst (Hierarchical)
10. Treemap
11. Heatmap
12. Radar/Spider Chart
13. Gauge Chart
14. Waterfall Chart
15. Funnel Chart
16. Box Plot
17. Histogram
18. Candlestick (Financial)

All generated from USER'S DATA - never hardcoded!
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from core.llm import chat

logger = logging.getLogger(__name__)


# ============================================================================
# QUERY-BASED DYNAMIC COLOR SYSTEM
# Colors are selected based on what the user is asking about
# ============================================================================

# Color palettes organized by query intent
QUERY_COLOR_PALETTES = {
    # Money/Revenue related - Greens (money = green)
    "sales": ['#10b981', '#059669', '#34d399', '#6ee7b7', '#a7f3d0', '#22c55e', '#4ade80', '#86efac'],
    "revenue": ['#10b981', '#059669', '#34d399', '#6ee7b7', '#a7f3d0', '#22c55e', '#4ade80', '#86efac'],
    "income": ['#10b981', '#059669', '#34d399', '#6ee7b7', '#a7f3d0', '#22c55e', '#4ade80', '#86efac'],
    
    # Profit/Growth - Teal (positive trends)
    "profit": ['#14b8a6', '#0d9488', '#2dd4bf', '#5eead4', '#99f6e4', '#0f766e', '#0891b2', '#06b6d4'],
    "growth": ['#14b8a6', '#0d9488', '#2dd4bf', '#5eead4', '#99f6e4', '#0f766e', '#0891b2', '#06b6d4'],
    "margin": ['#14b8a6', '#0d9488', '#2dd4bf', '#5eead4', '#99f6e4', '#0f766e', '#0891b2', '#06b6d4'],
    
    # Loss/Decline - Reds (warning)
    "loss": ['#ef4444', '#dc2626', '#f87171', '#fca5a5', '#fecaca', '#b91c1c', '#f43f5e', '#fb7185'],
    "decline": ['#ef4444', '#dc2626', '#f87171', '#fca5a5', '#fecaca', '#b91c1c', '#f43f5e', '#fb7185'],
    "risk": ['#ef4444', '#dc2626', '#f87171', '#fca5a5', '#fecaca', '#b91c1c', '#f43f5e', '#fb7185'],
    "cost": ['#ef4444', '#dc2626', '#f87171', '#fca5a5', '#fecaca', '#b91c1c', '#f43f5e', '#fb7185'],
    
    # Performance/Rating - Purple (premium feel)
    "rating": ['#8b5cf6', '#7c3aed', '#a78bfa', '#c4b5fd', '#ddd6fe', '#6d28d9', '#a855f7', '#c084fc'],
    "performance": ['#8b5cf6', '#7c3aed', '#a78bfa', '#c4b5fd', '#ddd6fe', '#6d28d9', '#a855f7', '#c084fc'],
    "quality": ['#8b5cf6', '#7c3aed', '#a78bfa', '#c4b5fd', '#ddd6fe', '#6d28d9', '#a855f7', '#c084fc'],
    
    # Time/Trend - Blue (timeline feel)
    "time": ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8', '#6366f1', '#818cf8'],
    "trend": ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8', '#6366f1', '#818cf8'],
    "month": ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8', '#6366f1', '#818cf8'],
    "year": ['#3b82f6', '#2563eb', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8', '#6366f1', '#818cf8'],
    
    # Categories/Segments - Orange (variety)
    "category": ['#f97316', '#ea580c', '#fb923c', '#fdba74', '#fed7aa', '#c2410c', '#f59e0b', '#fbbf24'],
    "segment": ['#f97316', '#ea580c', '#fb923c', '#fdba74', '#fed7aa', '#c2410c', '#f59e0b', '#fbbf24'],
    "product": ['#f97316', '#ea580c', '#fb923c', '#fdba74', '#fed7aa', '#c2410c', '#f59e0b', '#fbbf24'],
    "region": ['#f97316', '#ea580c', '#fb923c', '#fdba74', '#fed7aa', '#c2410c', '#f59e0b', '#fbbf24'],
    
    # Customers - Pink (people/relationship)
    "customer": ['#ec4899', '#db2777', '#f472b6', '#f9a8d4', '#fbcfe8', '#be185d', '#d946ef', '#e879f9'],
    "user": ['#ec4899', '#db2777', '#f472b6', '#f9a8d4', '#fbcfe8', '#be185d', '#d946ef', '#e879f9'],
    "client": ['#ec4899', '#db2777', '#f472b6', '#f9a8d4', '#fbcfe8', '#be185d', '#d946ef', '#e879f9'],
    
    # Quantity/Volume - Cyan
    "quantity": ['#06b6d4', '#0891b2', '#22d3ee', '#67e8f9', '#a5f3fc', '#0e7490', '#14b8a6', '#2dd4bf'],
    "volume": ['#06b6d4', '#0891b2', '#22d3ee', '#67e8f9', '#a5f3fc', '#0e7490', '#14b8a6', '#2dd4bf'],
    "count": ['#06b6d4', '#0891b2', '#22d3ee', '#67e8f9', '#a5f3fc', '#0e7490', '#14b8a6', '#2dd4bf'],
}

# Default palette (teal theme)
DEFAULT_COLORS = ['#14b8a6', '#0d9488', '#0f766e', '#06b6d4', '#0891b2', '#22d3ee', '#10b981', '#22c55e']

# Current query context for color selection
_current_query = ""

def set_query_context(query: str):
    """Set the current query for color selection"""
    global _current_query
    _current_query = query.lower()

def get_colors_for_query(query: str = None) -> List[str]:
    """Get colors based on query intent"""
    q = (query or _current_query).lower()
    
    # Check each keyword in the query
    for keyword, colors in QUERY_COLOR_PALETTES.items():
        if keyword in q:
            return colors
    
    # Default to teal theme
    return DEFAULT_COLORS

def get_current_colors() -> List[str]:
    """Get current color palette based on query context"""
    return get_colors_for_query(_current_query)


# ============================================================================
# ALL CHART GENERATORS - Enhanced with Interactivity
# ============================================================================

# Common interactive layout settings
INTERACTIVE_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#9ca3af", "family": "Inter, system-ui, sans-serif"},
    "hoverlabel": {
        "bgcolor": "#1f2937",
        "bordercolor": "#374151",
        "font": {"color": "#fff", "size": 13}
    },
    "dragmode": "zoom",
    "hovermode": "closest"
}

def generate_bar_chart(labels: List, values: List, title: str, horizontal: bool = False) -> Dict:
    """Generate interactive bar chart with animations and hover effects"""
    colors = get_current_colors()
    
    # Create gradient colors for each bar
    num_bars = len(labels)
    bar_colors = colors[:num_bars] if num_bars <= len(colors) else (colors * ((num_bars // len(colors)) + 1))[:num_bars]
    
    # Calculate percentage of max for context
    max_val = max(values) if values else 1
    
    if horizontal:
        return {
            "data": [{
                "type": "bar",
                "y": [str(l) for l in labels],
                "x": values,
                "orientation": "h",
                "marker": {
                    "color": bar_colors,
                    "line": {"color": "rgba(255,255,255,0.2)", "width": 1}
                },
                "text": [f"{v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in values],
                "textposition": "outside",
                "textfont": {"color": "#9ca3af"},
                "hovertemplate": "<b>%{y}</b><br>Value: %{x:,.0f}<br>%{customdata:.1f}% of max<extra></extra>",
                "customdata": [v/max_val*100 for v in values]
            }],
            "layout": {
                **INTERACTIVE_LAYOUT,
                "title": {"text": f"📊 {title}", "font": {"color": "#fff", "size": 18}},
                "xaxis": {"gridcolor": "#374151", "tickformat": ",.0f", "zeroline": False},
                "yaxis": {"gridcolor": "#374151", "automargin": True},
                "margin": {"l": 120, "r": 60, "t": 70, "b": 50},
                "bargap": 0.3
            }
        }
    else:
        return {
            "data": [{
                "type": "bar",
                "x": [str(l) for l in labels],
                "y": values,
                "marker": {
                    "color": bar_colors,
                    "line": {"color": "rgba(255,255,255,0.2)", "width": 1}
                },
                "text": [f"{v:,.0f}" if isinstance(v, (int, float)) else str(v) for v in values],
                "textposition": "outside",
                "textfont": {"color": "#9ca3af"},
                "hovertemplate": "<b>%{x}</b><br>Value: %{y:,.0f}<br>%{customdata:.1f}% of max<extra></extra>",
                "customdata": [v/max_val*100 for v in values]
            }],
            "layout": {
                **INTERACTIVE_LAYOUT,
                "title": {"text": f"📊 {title}", "font": {"color": "#fff", "size": 18}},
                "xaxis": {"gridcolor": "#374151", "tickangle": -45, "automargin": True},
                "yaxis": {"gridcolor": "#374151", "tickformat": ",.0f", "zeroline": False},
                "margin": {"l": 70, "r": 40, "t": 70, "b": 100},
                "bargap": 0.25
            }
        }


def generate_stacked_bar(df: pd.DataFrame, x_col: str, y_col: str, stack_col: str, title: str) -> Dict:
    """Generate stacked bar chart"""
    traces = []
    colors = ["#14b8a6", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
    
    for i, category in enumerate(df[stack_col].unique()[:6]):
        subset = df[df[stack_col] == category]
        grouped = subset.groupby(x_col)[y_col].sum()
        traces.append({
            "type": "bar",
            "name": str(category),
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
            "marker": {"color": colors[i % len(colors)]}
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "barmode": "stack",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_line_chart(labels: List, values: List, title: str, fill: bool = False) -> Dict:
    """Generate interactive line chart with animations and hover effects"""
    colors = get_current_colors()
    line_color = colors[0]
    
    # Calculate stats for hover
    avg_val = sum(values) / len(values) if values else 0
    
    return {
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": [str(l) for l in labels],
            "y": values,
            "line": {"color": line_color, "width": 3, "shape": "spline"},
            "marker": {"size": 10, "color": line_color, "line": {"color": "#fff", "width": 2}},
            "fill": "tozeroy" if fill else None,
            "fillcolor": f"rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.2)" if fill else None,
            "hovertemplate": "<b>%{x}</b><br>Value: %{y:,.0f}<br>Avg: " + f"{avg_val:,.0f}" + "<extra></extra>"
        }],
        "layout": {
            **INTERACTIVE_LAYOUT,
            "title": {"text": f"📈 {title}", "font": {"color": "#fff", "size": 18}},
            "xaxis": {"gridcolor": "#374151", "tickangle": -45, "showgrid": True},
            "yaxis": {"gridcolor": "#374151", "tickformat": ",.0f", "zeroline": False},
            "margin": {"l": 70, "r": 40, "t": 70, "b": 100}
        }
    }


def generate_scatter_chart(x_values: List, y_values: List, title: str, labels: List = None) -> Dict:
    """Generate interactive scatter plot with size scaling and gradient"""
    colors = get_current_colors()
    
    return {
        "data": [{
            "type": "scatter",
            "mode": "markers",
            "x": x_values,
            "y": y_values,
            "text": labels if labels else [f"({x}, {y})" for x, y in zip(x_values, y_values)],
            "marker": {
                "size": 14,
                "color": y_values,
                "colorscale": [[0, colors[0]], [0.5, colors[2]], [1, colors[4]]],
                "showscale": True,
                "colorbar": {"title": "Value", "tickfont": {"color": "#9ca3af"}},
                "line": {"color": "#fff", "width": 1}
            },
            "hovertemplate": "<b>%{text}</b><br>X: %{x:,.0f}<br>Y: %{y:,.0f}<extra></extra>"
        }],
        "layout": {
            **INTERACTIVE_LAYOUT,
            "title": {"text": f"🔵 {title}", "font": {"color": "#fff", "size": 18}},
            "xaxis": {"gridcolor": "#374151", "tickformat": ",.0f", "zeroline": False},
            "yaxis": {"gridcolor": "#374151", "tickformat": ",.0f", "zeroline": False},
            "margin": {"l": 70, "r": 100, "t": 70, "b": 60}
        }
    }


def generate_pie_chart(labels: List, values: List, title: str, donut: bool = False) -> Dict:
    """Generate pie chart (or donut if donut=True) with dynamic colors"""
    colors = get_current_colors()
    
    return {
        "data": [{
            "type": "pie",
            "labels": [str(l) for l in labels],
            "values": values,
            "hole": 0.4 if donut else 0,
            "marker": {"colors": colors},
            "textinfo": "label+percent",
            "textfont": {"color": "#fff"},
            "hovertemplate": "%{label}: %{value:,.0f}<br>%{percent}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff", "size": 16}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"},
            "showlegend": True,
            "legend": {"font": {"color": "#9ca3af"}}
        }
    }


def generate_sunburst(labels: List, parents: List, values: List, title: str) -> Dict:
    """Generate sunburst/hierarchical chart"""
    return {
        "data": [{
            "type": "sunburst",
            "labels": labels,
            "parents": parents,
            "values": values,
            "branchvalues": "total",
            "marker": {"colorscale": "Teal"}
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_treemap(labels: List, parents: List, values: List, title: str) -> Dict:
    """Generate treemap chart"""
    return {
        "data": [{
            "type": "treemap",
            "labels": labels,
            "parents": parents,
            "values": values,
            "marker": {"colorscale": "Teal"},
            "textinfo": "label+value"
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_heatmap(z_values: List, x_labels: List, y_labels: List, title: str) -> Dict:
    """Generate heatmap"""
    return {
        "data": [{
            "type": "heatmap",
            "z": z_values,
            "x": x_labels,
            "y": y_labels,
            "colorscale": "Viridis"
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_radar_chart(categories: List, values: List, title: str) -> Dict:
    """Generate radar/spider chart"""
    return {
        "data": [{
            "type": "scatterpolar",
            "r": values + [values[0]],  # Close the shape
            "theta": categories + [categories[0]],
            "fill": "toself",
            "line": {"color": "#14b8a6"},
            "fillcolor": "rgba(20, 184, 166, 0.3)"
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"},
            "polar": {"bgcolor": "rgba(0,0,0,0)"}
        }
    }


def generate_gauge_chart(value: float, max_value: float, title: str) -> Dict:
    """Generate gauge/meter chart"""
    return {
        "data": [{
            "type": "indicator",
            "mode": "gauge+number+delta",
            "value": value,
            "title": {"text": title, "font": {"color": "#fff"}},
            "gauge": {
                "axis": {"range": [0, max_value]},
                "bar": {"color": "#14b8a6"},
                "steps": [
                    {"range": [0, max_value*0.5], "color": "#374151"},
                    {"range": [max_value*0.5, max_value*0.75], "color": "#4b5563"},
                    {"range": [max_value*0.75, max_value], "color": "#6b7280"}
                ],
                "threshold": {"value": value, "thickness": 0.75, "line": {"color": "#14b8a6", "width": 4}}
            }
        }],
        "layout": {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_waterfall_chart(labels: List, values: List, title: str) -> Dict:
    """Generate waterfall chart"""
    return {
        "data": [{
            "type": "waterfall",
            "x": labels,
            "y": values,
            "connector": {"line": {"color": "#6b7280"}},
            "increasing": {"marker": {"color": "#10b981"}},
            "decreasing": {"marker": {"color": "#ef4444"}},
            "totals": {"marker": {"color": "#6366f1"}}
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_funnel_chart(labels: List, values: List, title: str) -> Dict:
    """Generate funnel chart"""
    return {
        "data": [{
            "type": "funnel",
            "y": labels,
            "x": values,
            "textinfo": "value+percent initial",
            "marker": {"color": ["#14b8a6", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6"]}
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_box_plot(df: pd.DataFrame, column: str, title: str) -> Dict:
    """Generate box plot for distribution"""
    return {
        "data": [{
            "type": "box",
            "y": df[column].dropna().tolist(),
            "name": column,
            "marker": {"color": "#14b8a6"},
            "boxpoints": "outliers"
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"}
        }
    }


def generate_histogram(values: List, title: str, bins: int = 20) -> Dict:
    """Generate histogram"""
    return {
        "data": [{
            "type": "histogram",
            "x": values,
            "nbinsx": bins,
            "marker": {"color": "#14b8a6"}
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"},
            "xaxis": {"gridcolor": "#374151"},
            "yaxis": {"gridcolor": "#374151"}
        }
    }


def generate_candlestick(df: pd.DataFrame, date_col: str, open_col: str, high_col: str, low_col: str, close_col: str, title: str) -> Dict:
    """Generate candlestick chart for financial data"""
    return {
        "data": [{
            "type": "candlestick",
            "x": df[date_col].tolist(),
            "open": df[open_col].tolist(),
            "high": df[high_col].tolist(),
            "low": df[low_col].tolist(),
            "close": df[close_col].tolist(),
            "increasing": {"line": {"color": "#10b981"}},
            "decreasing": {"line": {"color": "#ef4444"}}
        }],
        "layout": {
            "title": {"text": title, "font": {"color": "#fff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af"},
            "xaxis": {"rangeslider": {"visible": False}}
        }
    }


# ============================================================================
# AUTONOMOUS CHART SELECTION - LLM decides everything
# ============================================================================

def get_chart_type_from_query(query: str, columns: List[str], sample_data: str = "") -> Dict:
    """
    Use chart intent detection FIRST, then LLM as fallback.
    This ensures user gets exactly what they ask for.
    """
    try:
        # STEP 1: Check for explicit user intent first (faster, no LLM call)
        from core.chart_selector import ChartSelector
        selector = ChartSelector()
        detected_charts = selector.detect_chart_intent(query)
        
        if detected_charts:
            # User explicitly asked for a specific chart type
            preferred_chart = detected_charts[0]  # First match is most specific
            x_col = columns[0] if columns else "category"
            y_col = columns[-1] if len(columns) > 1 else columns[0] if columns else "value"
            
            return {
                "chart_type": preferred_chart,
                "x_column": x_col,
                "y_column": y_col,
                "title": f"{y_col} by {x_col}".replace("_", " ").title(),
                "reason": f"User explicitly requested {preferred_chart} visualization"
            }
        
        # STEP 2: LLM fallback for ambiguous queries
        prompt = f"""Analyze this query and data to recommend the BEST visualization.

QUERY: "{query}"
COLUMNS: {columns}
SAMPLE: {sample_data[:400]}

AVAILABLE CHART TYPES:
1. bar - Comparing categories
2. horizontal_bar - Long category names
3. stacked_bar - Multiple series comparison
4. line - Trends over time
5. area - Volume/cumulative trends
6. scatter - Correlation/relationship
7. pie - Part of whole (few categories)
8. donut - Part of whole (with center)
9. sunburst - Hierarchical data
10. treemap - Hierarchical with sizes
11. heatmap - Two-dimensional correlation
12. radar - Multi-variable comparison
13. gauge - Single KPI value
14. waterfall - Incremental changes
15. funnel - Stage progression
16. box - Distribution/outliers
17. histogram - Value distribution
18. candlestick - Financial OHLC

Return JSON:
{{"chart_type": "best_type", "x_column": "col", "y_column": "col", "title": "title", "reason": "why"}}

JSON:"""

        result = chat(prompt, temperature=0.1, max_tokens=200)
        
        # Parse
        result = result.strip()
        if '```' in result:
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        return json.loads(result)
        
    except Exception as e:
        return {"chart_type": "bar", "reason": str(e)}


def generate_autonomous_visualization(query: str, df: pd.DataFrame) -> Optional[str]:
    """Generate ANY chart type autonomously from user data with query-based colors"""
    if df is None or df.empty:
        return None
    
    try:
        # Set query context for dynamic color selection
        set_query_context(query)
        
        columns = list(df.columns)
        sample = df.head(5).to_string()
        
        # Get LLM recommendation
        recommendation = get_chart_type_from_query(query, columns, sample)
        chart_type = recommendation.get("chart_type", "bar")
        x_col = recommendation.get("x_column", columns[0])
        y_col = recommendation.get("y_column", columns[-1] if len(columns) > 1 else columns[0])
        title = recommendation.get("title", f"{y_col} by {x_col}")
        
        # Validate columns
        if x_col not in columns:
            x_col = columns[0]
        if y_col not in columns:
            y_col = columns[-1] if len(columns) > 1 else columns[0]
        
        # Prepare data
        if df[y_col].dtype in ['int64', 'float64']:
            grouped = df.groupby(x_col)[y_col].sum().head(15)
            labels = grouped.index.tolist()
            values = grouped.values.tolist()
        else:
            counts = df[x_col].value_counts().head(15)
            labels = counts.index.tolist()
            values = counts.values.tolist()
        
        # Generate chart based on type
        if chart_type == "horizontal_bar":
            chart_json = generate_bar_chart(labels, values, title, horizontal=True)
        elif chart_type == "line":
            chart_json = generate_line_chart(labels, values, title)
        elif chart_type == "area":
            chart_json = generate_line_chart(labels, values, title, fill=True)
        elif chart_type == "scatter":
            chart_json = generate_scatter_chart(labels, values, title)
        elif chart_type == "pie":
            chart_json = generate_pie_chart(labels[:8], values[:8], title)
        elif chart_type == "donut":
            chart_json = generate_pie_chart(labels[:8], values[:8], title, donut=True)
        elif chart_type == "funnel":
            chart_json = generate_funnel_chart(labels[:5], values[:5], title)
        elif chart_type == "radar":
            chart_json = generate_radar_chart(labels[:8], values[:8], title)
        elif chart_type == "histogram":
            if df[y_col].dtype in ['int64', 'float64']:
                chart_json = generate_histogram(df[y_col].dropna().tolist(), title)
            else:
                chart_json = generate_bar_chart(labels, values, title)
        elif chart_type == "box":
            if df[y_col].dtype in ['int64', 'float64']:
                chart_json = generate_box_plot(df, y_col, title)
            else:
                chart_json = generate_bar_chart(labels, values, title)
        elif chart_type == "gauge":
            total = sum(values)
            chart_json = generate_gauge_chart(total, total * 1.5, title)
        elif chart_type == "waterfall":
            chart_json = generate_waterfall_chart(labels[:10], values[:10], title)
        else:  # Default to bar
            chart_json = generate_bar_chart(labels, values, title)
        
        return f"\n\n```plotly_chart\n{json.dumps(chart_json)}\n```"
        
    except Exception as e:
        logger.error(f"Autonomous visualization error: {e}")
        return None


# ============================================================================
# CHART TYPES REGISTRY
# ============================================================================

SUPPORTED_CHART_TYPES = {
    "bar": "📊 Bar Chart - Compare categories",
    "horizontal_bar": "📊 Horizontal Bar - Long category names",
    "stacked_bar": "📊 Stacked Bar - Multiple series",
    "line": "📈 Line Chart - Trends over time",
    "area": "📈 Area Chart - Volume trends",
    "scatter": "🔵 Scatter Plot - Correlations",
    "pie": "🥧 Pie Chart - Part of whole",
    "donut": "🍩 Donut Chart - Part of whole",
    "sunburst": "☀️ Sunburst - Hierarchical data",
    "treemap": "🗺️ Treemap - Hierarchical sizes",
    "heatmap": "🔥 Heatmap - 2D correlation",
    "radar": "🕸️ Radar Chart - Multi-variable",
    "gauge": "⏱️ Gauge Chart - Single KPI",
    "waterfall": "💧 Waterfall - Incremental changes",
    "funnel": "🔻 Funnel Chart - Stage progression",
    "box": "📦 Box Plot - Distribution",
    "histogram": "📊 Histogram - Value distribution",
    "candlestick": "📈 Candlestick - Financial OHLC"
}


def get_supported_charts() -> List[str]:
    """Return list of all supported chart types"""
    return list(SUPPORTED_CHART_TYPES.keys())
