"""
AUTONOMOUS DASHBOARD GENERATOR - Like Power BI but AI-Driven
=============================================================

Generates complete dashboards AUTONOMOUSLY from user data.
NO HARDCODING - LLM decides everything:

- Which KPIs to show
- What charts to generate
- Colors and themes
- Layout and organization
- Insights and recommendations

This is a $50B Silicon Valley feature!
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd

from core.llm import chat

logger = logging.getLogger(__name__)


@dataclass
class DashboardWidget:
    """A single widget in the dashboard"""
    widget_type: str  # kpi, chart, table, insight
    title: str
    data: Dict
    config: Dict
    position: int


@dataclass
class AutonomousDashboard:
    """Complete autonomous dashboard"""
    title: str
    theme: Dict
    kpis: List[Dict]
    charts: List[Dict]
    insights: List[str]
    recommendations: List[str]
    generated_at: str


def analyze_data_for_dashboard(df: pd.DataFrame) -> Dict:
    """
    Analyze data to understand what kind of dashboard to generate.
    """
    analysis = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": [],
        "numeric_summary": {},
        "categorical_summary": {},
        "date_columns": [],
        "suggested_kpis": [],
        "suggested_charts": []
    }
    
    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "unique_count": df[col].nunique(),
            "null_count": df[col].isnull().sum()
        }
        
        if df[col].dtype in ['int64', 'float64']:
            col_info["is_numeric"] = True
            analysis["numeric_summary"][col] = {
                "sum": float(df[col].sum()),
                "mean": float(df[col].mean()),
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
        else:
            col_info["is_numeric"] = False
            if df[col].nunique() < 20:  # Categorical
                analysis["categorical_summary"][col] = df[col].value_counts().head(10).to_dict()
        
        # Detect date columns
        if 'date' in col.lower() or 'time' in col.lower():
            analysis["date_columns"].append(col)
        
        analysis["columns"].append(col_info)
    
    return analysis


def generate_autonomous_dashboard(df: pd.DataFrame, user_id: str) -> Dict:
    """
    Generate a COMPLETE dashboard autonomously using LLM.
    
    The LLM decides:
    - Dashboard title and theme
    - Which KPIs to highlight
    - What charts to generate
    - Layout and colors
    - Insights and recommendations
    """
    if df is None or df.empty:
        return {"error": "No data available. Please upload files first."}
    
    try:
        # Step 1: Analyze data structure
        analysis = analyze_data_for_dashboard(df)
        
        # Step 2: Use LLM to design the dashboard
        prompt = f"""You are an expert dashboard designer like Power BI. Design an AUTONOMOUS dashboard for this data.

DATA ANALYSIS:
- Total Rows: {analysis['row_count']}
- Columns: {[c['name'] for c in analysis['columns']]}
- Numeric Columns: {list(analysis['numeric_summary'].keys())}
- Categorical Columns: {list(analysis['categorical_summary'].keys())}
- Date Columns: {analysis['date_columns']}

NUMERIC DATA SUMMARY:
{json.dumps(analysis['numeric_summary'], indent=2)[:1000]}

CATEGORICAL DATA SUMMARY:
{json.dumps(analysis['categorical_summary'], default=str, indent=2)[:1000]}

SAMPLE DATA:
{df.head(5).to_string()[:800]}

GENERATE A COMPLETE DASHBOARD with this JSON structure:
{{
    "dashboard_title": "Descriptive title based on data",
    "theme": {{
        "primary_color": "#hex",
        "secondary_color": "#hex",
        "accent_color": "#hex",
        "background": "dark or light"
    }},
    "kpis": [
        {{
            "title": "KPI Name",
            "value": actual_number_from_data,
            "format": "currency/number/percentage",
            "trend": "up/down/neutral",
            "comparison": "vs previous period text"
        }}
    ],
    "charts": [
        {{
            "chart_id": "chart_1",
            "title": "Chart Title",
            "type": "bar/line/pie/donut/area",
            "x_column": "column_name",
            "y_column": "column_name",
            "color": "#hex"
        }}
    ],
    "insights": [
        "Key insight 1 with specific numbers",
        "Key insight 2 with specific numbers"
    ],
    "recommendations": [
        "Action recommendation 1",
        "Action recommendation 2"
    ]
}}

Generate 3-5 KPIs, 4-6 charts, 3-5 insights, 2-3 recommendations.
Use REAL values from the data summary above.
Make it look like a professional Power BI dashboard!

DASHBOARD JSON:"""

        dashboard_config = chat(prompt, temperature=0.3, max_tokens=2500)
        
        # Parse the response
        config = dashboard_config.strip()
        if '```json' in config:
            config = config.split('```json')[1].split('```')[0]
        elif '```' in config:
            config = config.split('```')[1].split('```')[0]
        
        start = config.find('{')
        end = config.rfind('}') + 1
        if start >= 0 and end > start:
            config = config[start:end]
        
        dashboard = json.loads(config)
        
        # Step 3: Generate actual Plotly charts for each chart config
        charts_with_data = []
        for chart_config in dashboard.get("charts", []):
            plotly_chart = generate_dashboard_chart(df, chart_config, dashboard.get("theme", {}))
            if plotly_chart:
                charts_with_data.append({
                    **chart_config,
                    "plotly_config": plotly_chart
                })
        
        dashboard["charts"] = charts_with_data
        dashboard["generated_at"] = pd.Timestamp.now().isoformat()
        dashboard["data_source"] = f"{analysis['row_count']} rows, {analysis['column_count']} columns"
        
        logger.info(f"✅ Generated autonomous dashboard: {dashboard.get('dashboard_title', 'Dashboard')}")
        return dashboard
        
    except json.JSONDecodeError as e:
        logger.error(f"Dashboard JSON parse error: {e}")
        return {"error": f"Failed to parse dashboard config: {str(e)}"}
    except Exception as e:
        logger.error(f"Dashboard generation error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def generate_dashboard_chart(df: pd.DataFrame, chart_config: Dict, theme: Dict) -> Optional[Dict]:
    """
    Generate a Plotly chart configuration for a dashboard widget.
    """
    try:
        chart_type = chart_config.get("type", "bar")
        x_col = chart_config.get("x_column")
        y_col = chart_config.get("y_column")
        title = chart_config.get("title", "Chart")
        color = chart_config.get("color", theme.get("primary_color", "#14b8a6"))
        
        # Validate columns
        if x_col not in df.columns:
            x_col = df.columns[0]
        if y_col and y_col not in df.columns:
            y_col = df.select_dtypes(include=['int64', 'float64']).columns[0] if len(df.select_dtypes(include=['int64', 'float64']).columns) > 0 else df.columns[-1]
        
        # Prepare data
        if y_col and df[y_col].dtype in ['int64', 'float64']:
            grouped = df.groupby(x_col)[y_col].sum().head(10)
            labels = [str(l) for l in grouped.index.tolist()]
            values = grouped.values.tolist()
        else:
            counts = df[x_col].value_counts().head(10)
            labels = [str(l) for l in counts.index.tolist()]
            values = counts.values.tolist()
        
        # Base layout with dark theme
        base_layout = {
            "title": {"text": title, "font": {"color": "#fff", "size": 14}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#9ca3af", "size": 11},
            "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
            "xaxis": {"gridcolor": "#374151", "showgrid": True},
            "yaxis": {"gridcolor": "#374151", "showgrid": True}
        }
        
        if chart_type == "pie" or chart_type == "donut":
            return {
                "data": [{
                    "type": "pie",
                    "labels": labels,
                    "values": values,
                    "hole": 0.4 if chart_type == "donut" else 0,
                    "marker": {"colors": ["#14b8a6", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]}
                }],
                "layout": {**base_layout, "showlegend": True, "legend": {"font": {"color": "#9ca3af"}}}
            }
        elif chart_type == "line":
            return {
                "data": [{
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": labels,
                    "y": values,
                    "line": {"color": color, "width": 2},
                    "marker": {"size": 6}
                }],
                "layout": base_layout
            }
        elif chart_type == "area":
            return {
                "data": [{
                    "type": "scatter",
                    "mode": "lines",
                    "x": labels,
                    "y": values,
                    "fill": "tozeroy",
                    "fillcolor": f"{color}40",
                    "line": {"color": color, "width": 2}
                }],
                "layout": base_layout
            }
        else:  # bar
            return {
                "data": [{
                    "type": "bar",
                    "x": labels,
                    "y": values,
                    "marker": {"color": color}
                }],
                "layout": base_layout
            }
            
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        return None


def get_dashboard_summary(df: pd.DataFrame) -> Dict:
    """
    Get a quick summary for dashboard header.
    """
    if df is None or df.empty:
        return {"error": "No data"}
    
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(df.select_dtypes(include=['int64', 'float64']).columns),
        "categorical_columns": len(df.select_dtypes(include=['object']).columns),
        "date_columns": len([c for c in df.columns if 'date' in c.lower()])
    }
    
    # Get top metric
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        top_col = numeric_cols[0]
        summary["top_metric"] = {
            "name": top_col,
            "total": float(df[top_col].sum()),
            "average": float(df[top_col].mean())
        }
    
    return summary
