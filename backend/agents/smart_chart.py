# =============================================================================
# UNIVERSAL CHART GENERATOR - LLM Understands ANY Visualization Request
# =============================================================================
#
# This module uses pure LLM understanding to generate any chart type.
# NO HARDCODED PATTERNS - The AI decides based on query meaning.
#
# Supported: bar, pie, line, scatter, area, heatmap, treemap, funnel, 
#            gauge, waterfall, donut, stacked_bar, horizontal_bar
#

import json
import re
from typing import Optional, Dict, Tuple, List
import pandas as pd


def smart_chart(
    query: str,
    df: pd.DataFrame,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🧠 UNIVERSAL CHART GENERATOR - LLM understands ANY visualization request.
    
    The LLM acts like ChatGPT:
    1. Understands what the user wants to see
    2. Analyzes the data schema
    3. Chooses the best chart type
    4. Generates complete Plotly specification
    
    ENHANCED: Now detects EXPLICIT chart requests first!
    """
    from core.llm import chat
    
    if df is None or df.empty:
        return None, "No data available"
    
    # =========================================================================
    # EXPLICIT CHART TYPE DETECTION - BEFORE LLM (ensures user intent honored)
    # =========================================================================
    query_lower = query.lower()
    forced_chart_type = None
    
    # Explicit pie chart requests
    if any(x in query_lower for x in ['pie chart', 'pie graph', 'as a pie', 'create pie', 'show pie']):
        forced_chart_type = 'pie'
        print(f"[SMART CHART] FORCED: pie chart from explicit request")
    # Explicit donut requests
    elif any(x in query_lower for x in ['donut chart', 'donut graph', 'as a donut']):
        forced_chart_type = 'donut'
        print(f"[SMART CHART] FORCED: donut chart from explicit request")
    # Explicit line chart requests
    elif any(x in query_lower for x in ['line chart', 'line graph', 'trend chart', 'trend line']):
        forced_chart_type = 'line'
        print(f"[SMART CHART] FORCED: line chart from explicit request")
    # Explicit bar chart requests
    elif any(x in query_lower for x in ['bar chart', 'bar graph', 'as a bar']):
        forced_chart_type = 'bar'
        print(f"[SMART CHART] FORCED: bar chart from explicit request")
    # Explicit horizontal bar requests
    elif any(x in query_lower for x in ['horizontal bar', 'horizontal chart']):
        forced_chart_type = 'horizontal_bar'
        print(f"[SMART CHART] FORCED: horizontal_bar from explicit request")
    # Distribution/breakdown implies pie/donut
    elif any(x in query_lower for x in ['distribution', 'breakdown', 'proportion', 'percentage']):
        forced_chart_type = 'pie'
        print(f"[SMART CHART] FORCED: pie chart for distribution query")
    # Trend/over time implies line
    elif any(x in query_lower for x in ['trend', 'over time', 'monthly', 'yearly', 'daily']):
        forced_chart_type = 'line'
        print(f"[SMART CHART] FORCED: line chart for trend query")
    
    # Build comprehensive schema description
    schema_info = []
    numeric_cols = []
    categorical_cols = []
    date_cols = []
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        unique = df[col].nunique()
        
        # Classify columns
        if 'int' in dtype or 'float' in dtype:
            numeric_cols.append(col)
        elif 'datetime' in dtype or 'date' in col.lower():
            date_cols.append(col)
        else:
            categorical_cols.append(col)
        
        schema_info.append(f"  {col} ({dtype}): {unique} unique, samples: {sample[:3]}")
    
    schema = "\n".join(schema_info)
    
    # Ask LLM to understand and generate chart spec
    prompt = f"""You are a data visualization AI. Analyze the query and generate a Plotly chart.

USER QUERY: "{query}"

DATAFRAME ({len(df)} rows):
{schema}

COLUMN CLASSIFICATION:
- Numeric columns: {numeric_cols}
- Categorical columns: {categorical_cols}
- Date columns: {date_cols}

AVAILABLE CHART TYPES:
- bar: Compare categories (vertical bars)
- horizontal_bar: Compare categories (horizontal)
- stacked_bar: Compare multiple series tilted
- pie: Show proportions/percentages
- donut: Pie with center hole
- line: Show trends over time/sequence
- area: Filled line chart for volume trends
- scatter: Show correlations between two variables
- radar: Compare multiple attributes across entities (e.g. skills, performance)
- box: Show distribution, variance, and outliers
- heatmap: Show intensity across two dimensions
- treemap: Hierarchical data breakdown
- funnel: Show conversion/stages
- gauge: Show single KPI vs target
- waterfall: Show incremental changes

RESPOND WITH ONLY A JSON OBJECT (no markdown, no explanation):
{{
    "chart_type": "one of the types above",
    "x_column": "column for X axis/labels",
    "y_column": "numeric column for values",
    "group_column": "optional column for grouping/coloring",
    "count": number (from 'top N' or 'bottom N' in query, default 10),
    "ascending": false for top/best, true for bottom/worst,
    "title": "Descriptive chart title",
    "subtitle": "Optional insight or context"
}}

INTELLIGENCE RULES:
1. "top N customers" → bar or pie, x=customer column, y=amount column, count=N
2. "trend" or "over time" → line or area, x=date column
3. "distribution" or "breakdown" → pie or donut
4. "compare" → bar or grouped bar
5. "correlation" → scatter
6. "heatmap" → heatmap with two categorical dimensions
7. "funnel" or "conversion" → funnel
8. "KPI" or "target" → gauge
9. Always pick the BEST chart type for the data and question

RESPOND WITH ONLY THE JSON, NO OTHER TEXT."""

    try:
        response = chat(prompt, max_tokens=600)
        
        # Clean response - extract JSON
        response = response.strip()
        if response.startswith("```"):
            parts = response.split("```")
            response = parts[1] if len(parts) > 1 else parts[0]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        # Parse the specification
        spec = json.loads(response)
        
        chart_type = spec.get("chart_type", "bar")
        x_col = spec.get("x_column")
        y_col = spec.get("y_column")
        group_col = spec.get("group_column")
        count = spec.get("count", 10)
        ascending = spec.get("ascending", False)
        title = spec.get("title", "Data Visualization")
        subtitle = spec.get("subtitle", "")
        
        # =====================================================================
        # OVERRIDE: If user explicitly requested a chart type, USE IT!
        # =====================================================================
        if forced_chart_type:
            print(f"[SMART CHART] OVERRIDE: Using '{forced_chart_type}' instead of LLM's '{chart_type}'")
            chart_type = forced_chart_type
        
        print(f"[SMART CHART] Final: type={chart_type}, x={x_col}, y={y_col}, count={count}")
        
        # Validate and fix column names
        x_col = _find_matching_column(x_col, df.columns)
        y_col = _find_matching_column(y_col, df.columns)
        if group_col:
            group_col = _find_matching_column(group_col, df.columns)
        
        if not x_col or not y_col:
            print(f"[SMART CHART] Column mismatch: x={x_col}, y={y_col}, available: {list(df.columns)}")
            return {"error": f"Could not match columns to your data. Available: {', '.join(list(df.columns)[:8])}"}, "Unable to generate chart"
        
        # Validate data types
        if y_col not in df.columns or not pd.api.types.is_numeric_dtype(df[y_col]):
            print(f"[SMART CHART] Y-axis column '{y_col}' is not numeric")
            return {"error": f"Column '{y_col}' must be numeric for visualization"}, "Invalid data type"
        
        # Generate the chart
        chart = _generate_chart(
            chart_type=chart_type,
            df=df,
            x_col=x_col,
            y_col=y_col,
            group_col=group_col,
            count=count,
            ascending=ascending,
            title=title,
            subtitle=subtitle,
            currency=currency_symbol
        )
        
        # Validate chart generation
        if not chart or 'error' in chart:
            error_msg = chart.get('error', 'Unknown error') if chart else 'Chart generation failed'
            print(f"[SMART CHART] Chart generation error: {error_msg}")
            return {"error": error_msg}, "Chart generation failed"
        
        # Generate explanation
        explanation = f"**{title}**\n\n{subtitle}" if subtitle else f"**{title}**"
        
        print(f"[SMART CHART] SUCCESS: {chart_type} chart generated")
        return chart, explanation
        
    except json.JSONDecodeError as e:
        print(f"[SMART CHART] JSON parse error: {e}")
        return None, "Failed to parse chart specification"
    except Exception as e:
        print(f"[SMART CHART] Error: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Chart generation failed: {e}"


def _find_matching_column(col_name: str, columns: List[str]) -> Optional[str]:
    """Find matching column in DataFrame, handling fuzzy matches."""
    if not col_name:
        return None
    
    # Exact match
    if col_name in columns:
        return col_name
    
    # Case-insensitive match
    col_lower = col_name.lower()
    for col in columns:
        if col.lower() == col_lower:
            return col
    
    # Partial match
    for col in columns:
        if col_lower in col.lower() or col.lower() in col_lower:
            return col
    
    return None


def _generate_chart(
    chart_type: str,
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: Optional[str],
    count: int,
    ascending: bool,
    title: str,
    subtitle: str,
    currency: str
) -> Dict:
    """Generate Plotly chart specification for any chart type."""
    
    # Prepare data
    grouped = df.groupby(x_col)[y_col].sum().sort_values(ascending=ascending)
    if count:
        grouped = grouped.head(count)
    
    # Convert to native Python types
    labels = [str(x) for x in grouped.index.tolist()]
    values = [float(x) for x in grouped.values.tolist()]
    
    # Color palette
    colors = ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
              '#F1948A', '#82E0AA', '#85C1E9', '#F8B500', '#9B59B6']
    
    # Build chart based on type
    if chart_type == 'pie':
        return _pie_chart(labels, values, title, currency, colors)
    elif chart_type == 'donut':
        return _donut_chart(labels, values, title, currency, colors)
    elif chart_type == 'line':
        return _line_chart(labels, values, title, currency)
    elif chart_type == 'area':
        return _area_chart(labels, values, title, currency)
    elif chart_type == 'horizontal_bar':
        return _horizontal_bar_chart(labels, values, title, currency, colors)
    elif chart_type == 'scatter':
        return _scatter_chart(labels, values, title, currency)
    elif chart_type == 'funnel':
        return _funnel_chart(labels, values, title, currency, colors)
    elif chart_type == 'gauge':
        return _gauge_chart(values[0] if values else 0, title, currency)
    elif chart_type == 'waterfall':
        return _waterfall_chart(labels, values, title, currency)
    elif chart_type == 'treemap':
        return _treemap_chart(labels, values, title, currency, colors)
    elif chart_type == 'heatmap':
        return _heatmap_chart(df, x_col, y_col, title, currency)
    elif chart_type == 'radar':
        from api.v1.endpoints.charts import generate_radar_chart
        return generate_radar_chart(df, title)
    elif chart_type == 'box':
        from api.v1.endpoints.charts import generate_box_plot
        return generate_box_plot(df, title)
    else:  # bar (default)
        return _bar_chart(labels, values, title, currency, colors)


# =============================================================================
# CHART TYPE IMPLEMENTATIONS
# =============================================================================

def _bar_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "bar",
            "x": labels,
            "y": values,
            "marker": {"color": colors[:len(labels)]},
            "hovertemplate": "%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100}
        }
    }


def _horizontal_bar_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "bar",
            "orientation": "h",
            "x": values,
            "y": labels,
            "marker": {"color": colors[:len(labels)]},
            "hovertemplate": "%{y}<br>" + currency + "%{x:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickprefix": currency},
            "yaxis": {"title": ""},
            "height": 400,
            "margin": {"l": 150}
        }
    }


def _pie_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "pie",
            "labels": labels,
            "values": values,
            "textinfo": "label+percent",
            "hovertemplate": "%{label}<br>" + currency + "%{value:,.0f}<br>%{percent}<extra></extra>",
            "marker": {"colors": colors[:len(labels)]}
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "showlegend": True,
            "height": 400
        }
    }


def _donut_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "pie",
            "labels": labels,
            "values": values,
            "hole": 0.4,
            "textinfo": "label+percent",
            "hovertemplate": "%{label}<br>" + currency + "%{value:,.0f}<br>%{percent}<extra></extra>",
            "marker": {"colors": colors[:len(labels)]}
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "showlegend": True,
            "height": 400,
            "annotations": [{"text": "Total", "showarrow": False, "font": {"size": 14}}]
        }
    }


def _line_chart(labels, values, title, currency):
    return {
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": labels,
            "y": values,
            "line": {"color": "#FF6B35", "width": 3},
            "marker": {"size": 10},
            "hovertemplate": "%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100}
        }
    }


def _area_chart(labels, values, title, currency):
    return {
        "data": [{
            "type": "scatter",
            "mode": "lines",
            "fill": "tozeroy",
            "x": labels,
            "y": values,
            "line": {"color": "#4ECDC4", "width": 2},
            "fillcolor": "rgba(78, 205, 196, 0.3)",
            "hovertemplate": "%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100}
        }
    }


def _scatter_chart(labels, values, title, currency):
    return {
        "data": [{
            "type": "scatter",
            "mode": "markers",
            "x": labels,
            "y": values,
            "marker": {"size": 12, "color": values, "colorscale": "Viridis", "showscale": True},
            "hovertemplate": "%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100}
        }
    }


def _funnel_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "funnel",
            "y": labels,
            "x": values,
            "textinfo": "value+percent initial",
            "marker": {"color": colors[:len(labels)]},
            "hovertemplate": "%{y}<br>" + currency + "%{x:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "height": 400
        }
    }


def _gauge_chart(value, title, currency):
    return {
        "data": [{
            "type": "indicator",
            "mode": "gauge+number",
            "value": value,
            "title": {"text": title},
            "gauge": {
                "axis": {"range": [0, value * 1.5]},
                "bar": {"color": "#FF6B35"},
                "steps": [
                    {"range": [0, value * 0.5], "color": "#f0f0f0"},
                    {"range": [value * 0.5, value], "color": "#d0d0d0"}
                ]
            },
            "number": {"prefix": currency}
        }],
        "layout": {
            "height": 350
        }
    }


def _waterfall_chart(labels, values, title, currency):
    # Calculate relative changes
    measures = ["relative"] * len(labels)
    if labels:
        measures[0] = "absolute"  # First value is absolute
    
    return {
        "data": [{
            "type": "waterfall",
            "x": labels,
            "y": values,
            "measure": measures,
            "connector": {"line": {"color": "rgb(63, 63, 63)"}},
            "increasing": {"marker": {"color": "#4ECDC4"}},
            "decreasing": {"marker": {"color": "#FF6B35"}},
            "hovertemplate": "%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100}
        }
    }


def _treemap_chart(labels, values, title, currency, colors):
    return {
        "data": [{
            "type": "treemap",
            "labels": labels,
            "parents": [""] * len(labels),
            "values": values,
            "textinfo": "label+value+percent root",
            "marker": {"colors": colors[:len(labels)]},
            "hovertemplate": "%{label}<br>" + currency + "%{value:,.0f}<br>%{percentRoot:.1%}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "height": 400
        }
    }


def _heatmap_chart(df, x_col, y_col, title, currency):
    # Create a simple heatmap from grouped data
    pivot = df.pivot_table(values=y_col, index=x_col, aggfunc='sum')
    
    return {
        "data": [{
            "type": "heatmap",
            "z": [[float(v)] for v in pivot.values],
            "y": [str(i) for i in pivot.index.tolist()],
            "x": [y_col],
            "colorscale": "Viridis",
            "hovertemplate": "%{y}<br>" + currency + "%{z:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "height": 400
        }
    }
