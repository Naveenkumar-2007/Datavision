# Advanced Chart Generator - Plotly-Based Dynamic Charts
"""
Generates Plotly charts based on VisualizationDecision.

This module takes decisions from visualization_intelligence.py
and creates actual chart payloads for the frontend.

Features:
- Dynamic chart type rendering
- Consistent styling
- Proper axis labels
- Interactive tooltips
- Color schemes per mode
"""

from typing import Dict, List, Optional, Any, Tuple
import json


# Color schemes for different contexts - EXPANDED for 20+ items
COLOR_SCHEMES = {
    "default": [
        "#f97316", "#3b82f6", "#22c55e", "#a855f7", "#ef4444",
        "#06b6d4", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6",
        "#84cc16", "#6366f1", "#f43f5e", "#0ea5e9", "#d946ef",
        "#eab308", "#10b981", "#6b7280", "#78716c", "#0284c7"
    ],
    "executive": ["#1e40af", "#3b82f6", "#60a5fa", "#93c5fd", "#1d4ed8", "#2563eb"],
    "finance": ["#059669", "#10b981", "#34d399", "#6ee7b7", "#047857", "#0d9488"],
    "warning": ["#dc2626", "#ef4444", "#f87171", "#fca5a5", "#b91c1c", "#991b1b"],
    "neutral": ["#6b7280", "#9ca3af", "#d1d5db", "#e5e7eb", "#4b5563", "#374151"],
}


def generate_dynamic_chart(
    df,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str,
    group_col: Optional[str] = None,
    currency_symbol: str = "₹",
    color_scheme: str = "default",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generate a Plotly chart payload based on chart type.
    
    Returns a JSON-serializable dict for frontend rendering.
    """
    if df is None or df.empty:
        return {"error": "No data available"}
    
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["default"])
    
    # Route to specific generator
    generators = {
        "line": _generate_line_chart,
        "bar": _generate_bar_chart,
        "grouped_bar": _generate_grouped_bar_chart,
        "stacked_bar": _generate_stacked_bar_chart,
        "pie": _generate_pie_chart,
        "donut": _generate_donut_chart,
        "area": _generate_area_chart,
        "scatter": _generate_scatter_chart,
        "forecast": _generate_forecast_chart,
        "waterfall": _generate_waterfall_chart,
    }
    
    generator = generators.get(chart_type, _generate_bar_chart)
    
    return generator(
        df=df,
        x_col=x_col,
        y_col=y_col,
        title=title,
        group_col=group_col,
        currency_symbol=currency_symbol,
        colors=colors,
        limit=limit
    )


def _generate_line_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate line chart for trends."""
    
    # Aggregate by x column if needed
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(x_col).tail(limit)
        
        x_values = aggregated[x_col].astype(str).tolist()
        y_values = aggregated[y_col].tolist()
    else:
        x_values = list(range(len(df)))
        y_values = df[y_col].tolist() if y_col in df.columns else []
    
    return {
        "type": "plotly",
        "chart_type": "line",
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": x_values,
            "y": y_values,
            "line": {"color": colors[0], "width": 3},
            "marker": {"size": 8, "color": colors[0]},
            "hovertemplate": f"<b>%{{x}}</b><br>{currency_symbol}%{{y:,.0f}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": x_col, "gridcolor": "rgba(128,128,128,0.2)"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(128,128,128,0.2)"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "showlegend": False
        }
    }


def _generate_bar_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate bar chart for comparisons/rankings."""
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(y_col, ascending=False).head(limit)
        
        x_values = aggregated[x_col].astype(str).tolist()
        y_values = aggregated[y_col].tolist()
    else:
        x_values = []
        y_values = []
    
    # Assign colors per bar
    bar_colors = [colors[i % len(colors)] for i in range(len(x_values))]
    
    return {
        "type": "plotly",
        "chart_type": "bar",
        "data": [{
            "type": "bar",
            "x": x_values,
            "y": y_values,
            "marker": {"color": bar_colors, "line": {"width": 0}},
            "hovertemplate": f"<b>%{{x}}</b><br>{currency_symbol}%{{y:,.0f}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": "", "gridcolor": "rgba(128,128,128,0.2)", "tickangle": -45},
            "yaxis": {"title": y_col, "gridcolor": "rgba(128,128,128,0.2)"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 100},
            "showlegend": False
        }
    }


def _generate_pie_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate pie chart for proportional data."""
    
    print(f"[PIE CHART DEBUG] x_col={x_col}, y_col={y_col}, limit={limit}")
    print(f"[PIE CHART DEBUG] df columns: {list(df.columns)}")
    print(f"[PIE CHART DEBUG] df['{x_col}'] unique values: {df[x_col].nunique() if x_col in df.columns else 'N/A'}")
    if x_col in df.columns:
        print(f"[PIE CHART DEBUG] Sample values: {df[x_col].head(5).tolist()}")
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(y_col, ascending=False).head(limit)
        
        labels = aggregated[x_col].astype(str).tolist()
        values = aggregated[y_col].tolist()
        print(f"[PIE CHART DEBUG] Final labels: {labels}")
    else:
        labels = []
        values = []
    
    pie_colors = [colors[i % len(colors)] for i in range(len(labels))]
    
    return {
        "type": "plotly",
        "chart_type": "pie",
        "data": [{
            "type": "pie",
            "labels": labels,
            "values": values,
            "marker": {"colors": pie_colors},
            "textposition": "auto",
            "textinfo": "label+percent",
            "hovertemplate": f"<b>%{{label}}</b><br>{currency_symbol}%{{value:,.0f}}<br>%{{percent}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "showlegend": True,
            "legend": {"font": {}},
            "margin": {"l": 30, "r": 30, "t": 60, "b": 30}
        }
    }


def _generate_donut_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate donut chart (pie with hole)."""
    pie = _generate_pie_chart(df, x_col, y_col, title, group_col, currency_symbol, colors, limit)
    if pie.get("data"):
        pie["data"][0]["hole"] = 0.4
        pie["chart_type"] = "donut"
    return pie


def _generate_grouped_bar_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate grouped bar chart for multi-category comparison."""
    
    if not group_col or group_col not in df.columns:
        return _generate_bar_chart(df, x_col, y_col, title, None, currency_symbol, colors, limit)
    
    traces = []
    groups = df[group_col].unique()[:5]  # Max 5 groups
    
    for i, group in enumerate(groups):
        group_df = df[df[group_col] == group]
        aggregated = group_df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(y_col, ascending=False).head(limit)
        
        traces.append({
            "type": "bar",
            "name": str(group),
            "x": aggregated[x_col].astype(str).tolist(),
            "y": aggregated[y_col].tolist(),
            "marker": {"color": colors[i % len(colors)]},
            "hovertemplate": f"<b>%{{x}}</b><br>{group}: {currency_symbol}%{{y:,.0f}}<extra></extra>"
        })
    
    return {
        "type": "plotly",
        "chart_type": "grouped_bar",
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "barmode": "group",
            "xaxis": {"title": "", "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "legend": {"font": {"color": "#ffffff"}},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 80}
        }
    }


def _generate_stacked_bar_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate stacked bar chart for composition."""
    
    if not group_col or group_col not in df.columns:
        return _generate_bar_chart(df, x_col, y_col, title, None, currency_symbol, colors, limit)
    
    traces = []
    groups = df[group_col].unique()[:8]  # Max 8 stacks
    
    for i, group in enumerate(groups):
        group_df = df[df[group_col] == group]
        aggregated = group_df.groupby(x_col)[y_col].sum().reset_index()
        
        traces.append({
            "type": "bar",
            "name": str(group),
            "x": aggregated[x_col].astype(str).tolist(),
            "y": aggregated[y_col].tolist(),
            "marker": {"color": colors[i % len(colors)]},
            "hovertemplate": f"<b>%{{x}}</b><br>{group}: {currency_symbol}%{{y:,.0f}}<extra></extra>"
        })
    
    return {
        "type": "plotly",
        "chart_type": "stacked_bar",
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "barmode": "stack",
            "xaxis": {"title": "", "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "legend": {"font": {"color": "#ffffff"}},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 80}
        }
    }


def _generate_pie_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate pie chart for proportions."""
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(y_col, ascending=False).head(8)  # Max 8 slices
        
        labels = aggregated[x_col].astype(str).tolist()
        values = aggregated[y_col].tolist()
    else:
        labels = []
        values = []
    
    return {
        "type": "plotly",
        "chart_type": "pie",
        "data": [{
            "type": "pie",
            "labels": labels,
            "values": values,
            "marker": {"colors": colors[:len(labels)]},
            "textinfo": "label+percent",
            "textposition": "inside",
            "hovertemplate": f"<b>%{{label}}</b><br>{currency_symbol}%{{value:,.0f}}<br>%{{percent}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "showlegend": True,
            "legend": {"font": {"color": "#ffffff"}},
            "margin": {"l": 30, "r": 30, "t": 50, "b": 30}
        }
    }


def _generate_donut_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate donut chart (pie with hole)."""
    
    chart = _generate_pie_chart(df, x_col, y_col, title, group_col, currency_symbol, colors, limit)
    
    if chart.get("data"):
        chart["data"][0]["hole"] = 0.4
        chart["chart_type"] = "donut"
    
    return chart


def _generate_area_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate area chart for cumulative trends."""
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(x_col).tail(limit)
        
        x_values = aggregated[x_col].astype(str).tolist()
        y_values = aggregated[y_col].tolist()
    else:
        x_values = []
        y_values = []
    
    return {
        "type": "plotly",
        "chart_type": "area",
        "data": [{
            "type": "scatter",
            "mode": "lines",
            "x": x_values,
            "y": y_values,
            "fill": "tozeroy",
            "fillcolor": f"rgba(249, 115, 22, 0.3)",
            "line": {"color": colors[0], "width": 2},
            "hovertemplate": f"<b>%{{x}}</b><br>{currency_symbol}%{{y:,.0f}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": x_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50}
        }
    }


def _generate_scatter_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate scatter plot for correlations."""
    
    # For scatter, use first two numeric columns if not specified
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    if len(numeric_cols) >= 2:
        x_col = x_col if x_col in numeric_cols else numeric_cols[0]
        y_col = y_col if y_col in numeric_cols else numeric_cols[1]
        
        x_values = df[x_col].tolist()[:limit*10]
        y_values = df[y_col].tolist()[:limit*10]
    else:
        x_values = []
        y_values = []
    
    return {
        "type": "plotly",
        "chart_type": "scatter",
        "data": [{
            "type": "scatter",
            "mode": "markers",
            "x": x_values,
            "y": y_values,
            "marker": {
                "color": colors[0],
                "size": 10,
                "opacity": 0.7,
                "line": {"width": 1, "color": "#ffffff"}
            },
            "hovertemplate": f"<b>{x_col}</b>: %{{x:,.0f}}<br><b>{y_col}</b>: %{{y:,.0f}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": x_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50}
        }
    }


def _generate_forecast_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate forecast chart with historical + predicted + confidence bands."""
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(x_col)
        
        x_values = aggregated[x_col].astype(str).tolist()
        y_values = aggregated[y_col].tolist()
        
        # Simple linear forecast (3 periods)
        if len(y_values) >= 2:
            last_val = y_values[-1]
            growth_rate = (y_values[-1] - y_values[0]) / len(y_values) if len(y_values) > 1 else 0
            
            forecast_x = [f"Forecast {i+1}" for i in range(3)]
            forecast_y = [last_val + growth_rate * (i + 1) for i in range(3)]
            
            # Confidence bands (±15%)
            upper_band = [v * 1.15 for v in forecast_y]
            lower_band = [v * 0.85 for v in forecast_y]
        else:
            forecast_x = []
            forecast_y = []
            upper_band = []
            lower_band = []
    else:
        x_values = []
        y_values = []
        forecast_x = []
        forecast_y = []
        upper_band = []
        lower_band = []
    
    traces = [
        # Historical line
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Historical",
            "x": x_values,
            "y": y_values,
            "line": {"color": colors[0], "width": 3},
            "marker": {"size": 8},
            "hovertemplate": f"<b>%{{x}}</b><br>{currency_symbol}%{{y:,.0f}}<extra></extra>"
        },
        # Forecast line
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Forecast",
            "x": forecast_x,
            "y": forecast_y,
            "line": {"color": colors[1], "width": 3, "dash": "dash"},
            "marker": {"size": 8},
            "hovertemplate": f"<b>%{{x}}</b><br>Predicted: {currency_symbol}%{{y:,.0f}}<extra></extra>"
        },
        # Upper confidence band
        {
            "type": "scatter",
            "mode": "lines",
            "name": "Upper Band",
            "x": forecast_x,
            "y": upper_band,
            "line": {"width": 0},
            "showlegend": False,
            "hoverinfo": "skip"
        },
        # Lower confidence band (with fill)
        {
            "type": "scatter",
            "mode": "lines",
            "name": "Lower Band",
            "x": forecast_x,
            "y": lower_band,
            "line": {"width": 0},
            "fill": "tonexty",
            "fillcolor": "rgba(59, 130, 246, 0.2)",
            "showlegend": False,
            "hoverinfo": "skip"
        }
    ]
    
    return {
        "type": "plotly",
        "chart_type": "forecast",
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": "", "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "legend": {"font": {"color": "#ffffff"}},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50}
        }
    }


def _generate_waterfall_chart(
    df, x_col: str, y_col: str, title: str,
    group_col: Optional[str], currency_symbol: str,
    colors: List[str], limit: int
) -> Dict:
    """Generate waterfall chart for financial breakdowns."""
    
    if x_col and x_col in df.columns and y_col and y_col in df.columns:
        aggregated = df.groupby(x_col)[y_col].sum().reset_index()
        aggregated = aggregated.sort_values(y_col, ascending=False).head(limit)
        
        labels = aggregated[x_col].astype(str).tolist()
        values = aggregated[y_col].tolist()
        
        # Add total at end
        labels.append("Total")
        values.append(sum(values[:-1]) if len(values) > 1 else values[0] if values else 0)
        
        # Waterfall measure types
        measures = ["relative"] * (len(labels) - 1) + ["total"]
    else:
        labels = []
        values = []
        measures = []
    
    return {
        "type": "plotly",
        "chart_type": "waterfall",
        "data": [{
            "type": "waterfall",
            "orientation": "v",
            "x": labels,
            "y": values,
            "measure": measures,
            "connector": {"line": {"color": "rgba(255,255,255,0.3)"}},
            "increasing": {"marker": {"color": colors[2] if len(colors) > 2 else "#22c55e"}},
            "decreasing": {"marker": {"color": colors[4] if len(colors) > 4 else "#ef4444"}},
            "totals": {"marker": {"color": colors[0]}},
            "hovertemplate": f"<b>%{{x}}</b><br>{currency_symbol}%{{y:,.0f}}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16, "color": "#ffffff"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "xaxis": {"title": "", "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "yaxis": {"title": y_col, "gridcolor": "rgba(255,255,255,0.1)", "color": "#ffffff"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 80}
        }
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def create_chart_from_decision(
    decision,  # VisualizationDecision from visualization_intelligence.py
    df,
    currency_symbol: str = "₹",
    user_role: str = "analyst"
) -> Optional[Dict]:
    """
    Create a chart payload from a VisualizationDecision.
    
    This is the main entry point that bridges the decision layer
    with actual chart generation.
    
    IMPORTANT: Only uses REAL data from the DataFrame - no fabrication!
    """
    if not decision.should_render:
        return None
    
    # STRICT DATA VALIDATION - Ensure we have real data
    if df is None or df.empty:
        return {"error": "No data available - cannot generate chart"}
    
    # Verify columns exist in DataFrame
    if decision.x_column and decision.x_column not in df.columns:
        return {"error": f"Column '{decision.x_column}' not found in uploaded data"}
    if decision.y_column and decision.y_column not in df.columns:
        return {"error": f"Column '{decision.y_column}' not found in uploaded data"}
    
    # Determine color scheme based on role
    color_scheme = "default"
    if user_role:
        role_lower = user_role.lower()
        if role_lower == "executive":
            color_scheme = "executive"
        elif role_lower == "finance":
            color_scheme = "finance"
    
    chart = generate_dynamic_chart(
        df=df,
        chart_type=decision.chart_type.value,
        x_col=decision.x_column,
        y_col=decision.y_column,
        title=decision.title,
        group_col=decision.group_column,
        currency_symbol=currency_symbol,
        color_scheme=color_scheme,
        limit=decision.limit if hasattr(decision, 'limit') else 10  # Use dynamic limit from query
    )
    
    # Add data source metadata to confirm real data usage
    if chart and not chart.get("error"):
        chart["_data_source"] = {
            "type": "uploaded_data",
            "row_count": len(df),
            "columns_used": [c for c in [decision.x_column, decision.y_column, decision.group_column] if c],
            "verified": True
        }
    
    return chart

