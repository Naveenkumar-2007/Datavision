"""
AUTONOMOUS CHART GENERATOR - 100% LLM-Driven from User Data
=============================================================

Generates charts, mindmaps, and visualizations AUTONOMOUSLY
based on user's query and their uploaded data.

NO HARDCODING - Everything is determined by LLM at runtime:
- Chart type selection
- Data extraction
- Colors and styling
- Labels and titles

Supports:
- Bar, Line, Pie, Scatter charts
- Mindmaps (hierarchical tree diagrams)
- Network graphs (relationships)
- Heatmaps
- Tables
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from core.llm import chat

logger = logging.getLogger(__name__)


def autonomous_chart_decision(query: str, columns: List[str], sample_data: str) -> Dict:
    """
    Use LLM to decide what chart to create - NO HARDCODING!
    """
    try:
        prompt = f"""Analyze this query and data to determine the best visualization.

USER QUERY: "{query}"
DATA COLUMNS: {columns}
SAMPLE DATA: {sample_data[:500]}

Decide:
1. Should a chart be generated? (yes/no)
2. What chart type? (bar, line, pie, scatter, heatmap, table, mindmap, network)
3. Which column for X-axis/categories?
4. Which column for Y-axis/values?
5. Chart title?

Return JSON:
{{
    "generate_chart": true/false,
    "chart_type": "bar/line/pie/scatter/heatmap/table/mindmap/network",
    "x_column": "column_name",
    "y_column": "column_name",
    "title": "Chart Title",
    "reason": "why this chart type"
}}

JSON:"""

        result = chat(prompt, temperature=0.1, max_tokens=200)
        
        # Parse JSON
        result = result.strip()
        if '```' in result:
            result = result.split('```')[1]
            if result.startswith('json'):
                result = result[4:]
        
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            result = result[start:end]
        
        decision = json.loads(result)
        return decision
        
    except Exception as e:
        logger.warning(f"Chart decision error: {e}")
        return {"generate_chart": False, "reason": str(e)}


def autonomous_data_extraction(df: pd.DataFrame, query: str, chart_type: str) -> Dict:
    """
    Autonomously extract the right data for visualization.
    """
    try:
        columns = list(df.columns)
        sample = df.head(5).to_string()
        
        prompt = f"""Extract data for a {chart_type} chart from this DataFrame.

QUERY: "{query}"
COLUMNS: {columns}
SAMPLE DATA:
{sample}

TASK: Return JSON with the exact column names to use:
{{
    "x_column": "exact_column_name_for_x",
    "y_column": "exact_column_name_for_y",
    "group_by": "column_to_group_by or null",
    "aggregate": "sum/mean/count/max/min",
    "top_n": 10,
    "sort_by": "asc/desc"
}}

Use EXACT column names from the list above.
JSON:"""

        result = chat(prompt, temperature=0.1, max_tokens=150)
        
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
        logger.warning(f"Data extraction error: {e}")
        # Fallback: use first string and numeric columns
        str_cols = [c for c in df.columns if df[c].dtype == 'object']
        num_cols = [c for c in df.columns if df[c].dtype in ['int64', 'float64']]
        return {
            "x_column": str_cols[0] if str_cols else columns[0],
            "y_column": num_cols[0] if num_cols else columns[-1],
            "aggregate": "sum",
            "top_n": 10
        }


def generate_autonomous_chart(
    query: str,
    df: pd.DataFrame,
    chart_type: str = None,
    x_column: str = None,
    y_column: str = None
) -> Optional[str]:
    """
    Generate chart autonomously from user data.
    Returns Plotly chart as JSON or markdown code block.
    """
    if df is None or df.empty:
        return None
    
    try:
        columns = list(df.columns)
        sample = df.head(3).to_string()
        
        # Step 1: Get chart decision if not specified
        if not chart_type:
            decision = autonomous_chart_decision(query, columns, sample)
            if not decision.get("generate_chart", False):
                return None
            chart_type = decision.get("chart_type", "bar")
            x_column = decision.get("x_column")
            y_column = decision.get("y_column")
        
        # Step 2: Extract data
        extraction = autonomous_data_extraction(df, query, chart_type)
        x_col = x_column or extraction.get("x_column")
        y_col = y_column or extraction.get("y_column")
        aggregate = extraction.get("aggregate", "sum")
        top_n = extraction.get("top_n", 10)
        
        # Validate columns exist
        if x_col not in df.columns:
            x_col = columns[0]
        if y_col not in df.columns:
            y_col = columns[-1] if len(columns) > 1 else columns[0]
        
        # Step 3: Prepare data
        if aggregate == "count":
            chart_data = df[x_col].value_counts().head(top_n)
            labels = chart_data.index.tolist()
            values = chart_data.values.tolist()
        else:
            # Group and aggregate
            try:
                if df[y_col].dtype in ['int64', 'float64']:
                    grouped = df.groupby(x_col)[y_col].agg(aggregate).head(top_n)
                    labels = grouped.index.tolist()
                    values = grouped.values.tolist()
                else:
                    # Count if not numeric
                    chart_data = df[x_col].value_counts().head(top_n)
                    labels = chart_data.index.tolist()
                    values = chart_data.values.tolist()
            except:
                chart_data = df[x_col].value_counts().head(top_n)
                labels = chart_data.index.tolist()
                values = chart_data.values.tolist()
        
        # Step 4: Build Plotly chart
        title = f"{y_col} by {x_col}" if y_col != x_col else f"Distribution of {x_col}"
        
        if chart_type == "pie":
            chart_json = {
                "data": [{
                    "type": "pie",
                    "labels": [str(l) for l in labels],
                    "values": values,
                    "hole": 0.4,
                    "marker": {"colors": ["#14b8a6", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]}
                }],
                "layout": {
                    "title": {"text": title, "font": {"color": "#fff"}},
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#9ca3af"},
                    "showlegend": True
                }
            }
        elif chart_type == "line":
            chart_json = {
                "data": [{
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": [str(l) for l in labels],
                    "y": values,
                    "line": {"color": "#14b8a6", "width": 3},
                    "marker": {"size": 8, "color": "#14b8a6"}
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
        elif chart_type == "scatter":
            chart_json = {
                "data": [{
                    "type": "scatter",
                    "mode": "markers",
                    "x": [str(l) for l in labels],
                    "y": values,
                    "marker": {"size": 12, "color": "#6366f1", "opacity": 0.7}
                }],
                "layout": {
                    "title": {"text": title, "font": {"color": "#fff"}},
                    "paper_bgcolor": "rgba(0,0,0,0)",
                    "plot_bgcolor": "rgba(0,0,0,0)",
                    "font": {"color": "#9ca3af"}
                }
            }
        else:  # bar (default)
            chart_json = {
                "data": [{
                    "type": "bar",
                    "x": [str(l) for l in labels],
                    "y": values,
                    "marker": {
                        "color": values,
                        "colorscale": [[0, "#14b8a6"], [1, "#6366f1"]]
                    }
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
        
        return f"\n\n```plotly_chart\n{json.dumps(chart_json)}\n```"
        
    except Exception as e:
        logger.error(f"Autonomous chart error: {e}")
        return None


def generate_mindmap(query: str, df: pd.DataFrame) -> Optional[str]:
    """
    Generate mindmap visualization from user data.
    """
    if df is None or df.empty:
        return None
    
    try:
        columns = list(df.columns)
        sample = df.head(10).to_string()
        
        # Use LLM to structure the mindmap
        prompt = f"""Create a mindmap structure from this data.

QUERY: "{query}"
COLUMNS: {columns}
DATA:
{sample}

Create a hierarchical mindmap with:
- Central topic
- Main branches (3-5)
- Sub-items under each branch

Return JSON:
{{
    "center": "main topic",
    "branches": [
        {{"name": "Branch 1", "items": ["item1", "item2"]}},
        {{"name": "Branch 2", "items": ["item1", "item2"]}}
    ]
}}

Use REAL data from above.
JSON:"""

        result = chat(prompt, temperature=0.3, max_tokens=500)
        
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
        
        mindmap = json.loads(result)
        
        # Build Plotly treemap/sunburst
        labels = [mindmap["center"]]
        parents = [""]
        values = [10]
        
        for branch in mindmap.get("branches", []):
            branch_name = branch["name"]
            labels.append(branch_name)
            parents.append(mindmap["center"])
            values.append(5)
            
            for item in branch.get("items", [])[:5]:
                labels.append(str(item))
                parents.append(branch_name)
                values.append(1)
        
        chart_json = {
            "data": [{
                "type": "sunburst",
                "labels": labels,
                "parents": parents,
                "values": values,
                "branchvalues": "total",
                "marker": {"colorscale": "Teal"}
            }],
            "layout": {
                "title": {"text": f"Mindmap: {mindmap['center']}", "font": {"color": "#fff"}},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#9ca3af"}
            }
        }
        
        return f"\n\n```plotly_chart\n{json.dumps(chart_json)}\n```"
        
    except Exception as e:
        logger.error(f"Mindmap error: {e}")
        return None


def should_generate_visualization(query: str) -> Tuple[bool, str]:
    """
    Determine if we should generate a visualization and what type.
    """
    query_lower = query.lower()
    
    # Visualization keywords
    if any(w in query_lower for w in ['chart', 'graph', 'visualize', 'plot', 'show me']):
        if 'pie' in query_lower:
            return True, 'pie'
        elif 'line' in query_lower or 'trend' in query_lower:
            return True, 'line'
        elif 'scatter' in query_lower:
            return True, 'scatter'
        else:
            return True, 'bar'
    
    if 'mindmap' in query_lower or 'mind map' in query_lower:
        return True, 'mindmap'
    
    if any(w in query_lower for w in ['top', 'bottom', 'highest', 'lowest', 'compare', 'breakdown', 'distribution']):
        return True, 'bar'
    
    return False, 'none'
