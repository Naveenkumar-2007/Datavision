"""
PURE LLM-DRIVEN VISUALIZATION - ZERO HARDCODING
=================================================

This is the ULTIMATE autonomous chart system.
The LLM generates the COMPLETE Plotly configuration.

NO predefined chart types.
NO hardcoded generators.
LLM decides EVERYTHING based on:
1. User's query
2. User's actual data
3. What makes sense for the visualization

Just like ChatGPT - pure intelligence, pure autonomy.
"""

import json
import logging
from typing import Optional
import pandas as pd

from core.llm import chat

logger = logging.getLogger(__name__)


def generate_visualization_pure_llm(query: str, df: pd.DataFrame) -> Optional[str]:
    """
    100% LLM-DRIVEN VISUALIZATION.
    
    The LLM decides:
    - IF a chart should be generated
    - WHAT type of chart
    - WHICH columns to use
    - HOW to structure the data
    - ALL styling and configuration
    
    Returns complete Plotly JSON - no hardcoding!
    """
    if df is None or df.empty:
        return None
    
    try:
        # Prepare data context for LLM
        columns = list(df.columns)
        dtypes = {col: str(df[col].dtype) for col in columns}
        sample_data = df.head(10).to_dict(orient='records')
        row_count = len(df)
        
        # For numeric columns, get basic stats
        numeric_summary = {}
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            numeric_summary[col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "sum": float(df[col].sum()),
                "mean": float(df[col].mean())
            }
        
        # For categorical columns, get value counts
        categorical_summary = {}
        for col in df.select_dtypes(include=['object']).columns[:5]:
            categorical_summary[col] = df[col].value_counts().head(10).to_dict()
        
        # THE MASTER PROMPT - LLM does EVERYTHING
        prompt = f"""You are an expert data visualization AI. Generate a Plotly chart configuration.

USER REQUEST: "{query}"

DATA AVAILABLE:
- Columns: {columns}
- Data Types: {dtypes}
- Total Rows: {row_count}
- Sample Data: {json.dumps(sample_data[:5], default=str)[:1000]}

NUMERIC DATA SUMMARY:
{json.dumps(numeric_summary, indent=2)[:800]}

CATEGORICAL DATA SUMMARY:
{json.dumps(categorical_summary, default=str, indent=2)[:800]}

YOUR TASK:
1. Analyze what the user is asking for
2. Decide the BEST visualization (or no chart if not needed)
3. Generate a COMPLETE Plotly chart configuration using the ACTUAL data values above

IMPORTANT RULES:
- Use ONLY the actual data values shown above
- Choose the visualization that best answers the user's question
- Include proper titles, labels, and styling
- Use dark theme colors (paper_bgcolor: "rgba(0,0,0,0)", font color: "#9ca3af")
- Accent colors: teal (#14b8a6), indigo (#6366f1), amber (#f59e0b)
- For pie/donut charts, use "labels" and "values" (NEVER "x" and "y") in the data array.

Return your response in this EXACT format:
{{
    "should_generate": true or false,
    "visualization_type": "what you chose and why",
    "plotly_chart": {{COMPLETE PLOTLY JSON HERE}}
}}

If no chart is needed, return:
{{"should_generate": false, "reason": "why no chart needed"}}

Generate the visualization:"""

        response = chat(prompt, temperature=0.2, max_tokens=2000)
        
        # Parse the response
        response = response.strip()
        
        # Find JSON in response
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        
        # Find the JSON object
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            response = response[start:end]
        
        result = json.loads(response)
        
        # Check if we should generate
        if not result.get("should_generate", True):
            logger.info(f"LLM decided not to generate chart: {result.get('reason', 'No reason')}")
            return None
        
        # Get the Plotly chart configuration
        plotly_config = result.get("plotly_chart", {})
        
        if not plotly_config or "data" not in plotly_config:
            logger.warning("LLM returned invalid Plotly config")
            return None
        
        # Ensure dark theme styling
        if "layout" not in plotly_config:
            plotly_config["layout"] = {}
        
        plotly_config["layout"]["paper_bgcolor"] = "rgba(0,0,0,0)"
        plotly_config["layout"]["plot_bgcolor"] = "rgba(0,0,0,0)"
        plotly_config["layout"]["font"] = {"color": "#9ca3af"}
        
        if "title" in plotly_config["layout"]:
            if isinstance(plotly_config["layout"]["title"], str):
                plotly_config["layout"]["title"] = {
                    "text": plotly_config["layout"]["title"],
                    "font": {"color": "#fff"}
                }
            elif isinstance(plotly_config["layout"]["title"], dict):
                plotly_config["layout"]["title"]["font"] = {"color": "#fff"}
        
        logger.info(f"LLM generated {result.get('visualization_type', 'chart')}")
        
        return f"\n\n```plotly_chart\n{json.dumps(plotly_config)}\n```"
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Pure LLM visualization error: {e}")
        return None


def should_visualize(query: str) -> bool:
    """
    Quick check if query likely needs visualization.
    This is just a hint - LLM makes final decision.
    """
    viz_hints = [
        'chart', 'graph', 'plot', 'visualize', 'show', 'display',
        'pie', 'bar', 'line', 'scatter', 'distribution',
        'top', 'bottom', 'compare', 'trend', 'breakdown',
        'heatmap', 'histogram', 'funnel', 'gauge', 'mindmap',
        'how many', 'what is the total', 'percentage',
        'img', 'image', 'picture', 'dashboard', 'report'
    ]
    
    query_lower = query.lower()
    return any(hint in query_lower for hint in viz_hints)


def generate_smart_chart(query: str, df: pd.DataFrame) -> Optional[str]:
    """
    Main entry point for smart chart generation.
    
    This is 100% autonomous:
    1. Checks if visualization might be needed
    2. Calls LLM to generate complete chart
    3. Returns Plotly JSON or None
    """
    # Quick check for visualization hints
    if not should_visualize(query):
        # Still let LLM decide - it might choose to visualize anyway
        pass
    
    return generate_visualization_pure_llm(query, df)


# Backwards compatibility aliases
def smart_chart(query: str, df: pd.DataFrame) -> Optional[str]:
    """Alias for generate_smart_chart for backwards compatibility"""
    return generate_smart_chart(query, df)


def get_color_palette_from_query(query: str) -> list:
    """Get color palette - returns default teal/indigo theme"""
    return ["#14b8a6", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]
