"""
🎨 LLM-DRIVEN VISUALIZER - Claude-Style Dynamic Chart Generation
================================================================

Uses LLM to understand ANY visualization request and generate charts dynamically.
No hardcoded patterns - fully intelligent interpretation.

Features:
- 🧠 LLM understands natural language chart requests
- 🎨 Dynamic color extraction (any color, not hardcoded)
- 📊 Any chart type generation
- 🔄 Works with user's actual data
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import LLM
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM not available for visualizer")


class LLMVisualizer:
    """
    🎨 LLM-DRIVEN VISUALIZER
    
    Uses AI to understand ANY visualization request and generate appropriate charts.
    This is Claude-style: interpret the request, don't match patterns.
    """
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
    
    def generate(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Generate visualization based on natural language request.
        
        Args:
            df: User's DataFrame
            query: Natural language request like "radar chart with pink color"
            
        Returns:
            Plotly chart specification
        """
        if df is None or df.empty:
            return {"error": "No data available"}
        
        # PERFORMANCE: Sample large datasets to prevent hanging
        MAX_ROWS_FOR_VIZ = 1000
        if len(df) > MAX_ROWS_FOR_VIZ:
            logger.info(f"Sampling data from {len(df)} to {MAX_ROWS_FOR_VIZ} rows for visualization")
            # Smart sampling - stratified if possible
            df = df.sample(n=MAX_ROWS_FOR_VIZ, random_state=42)
        
        if not LLM_AVAILABLE:
            return self._fallback_chart(df, query)
        
        # Get data summary for LLM
        data_summary = self._get_data_summary(df)
        
        # Ask LLM to interpret the request and generate chart spec
        chart_spec = self._llm_generate_chart(query, data_summary, df)
        
        return chart_spec
    
    def _get_data_summary(self, df: pd.DataFrame) -> str:
        """Get compact data summary for LLM."""
        summary = f"Dataset: {len(df)} rows, {len(df.columns)} columns\n\n"
        
        summary += "Columns:\n"
        for col in df.columns:
            dtype = str(df[col].dtype)
            if pd.api.types.is_numeric_dtype(df[col]):
                summary += f"- {col} (numeric): min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}\n"
            else:
                unique = df[col].nunique()
                summary += f"- {col} (categorical): {unique} unique values\n"
        
        return summary
    
    def _llm_generate_chart(self, query: str, data_summary: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Use LLM to generate Plotly chart specification."""
        
        # Get actual column names and sample data
        columns = list(df.columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Prepare sample values for LLM
        sample_data = {}
        for col in numeric_cols[:5]:
            sample_data[col] = {
                "mean": float(df[col].mean()),
                "values": df[col].head(10).tolist()
            }
        
        prompt = f"""You are a data visualization expert. Generate a Plotly chart specification based on the user's request.

USER REQUEST: {query}

AVAILABLE DATA:
{data_summary}

Numeric columns: {numeric_cols}
Categorical columns: {categorical_cols}

Sample numeric data:
{json.dumps(sample_data, default=str)}

INSTRUCTIONS:
1. Understand what chart type the user wants (bar, line, pie, radar, scatter, heatmap, etc.)
2. Extract any color preferences from the request
3. Select appropriate columns from the available data
4. Generate a valid Plotly chart specification

Respond with ONLY a valid JSON object in this exact format:
{{
    "chart_type": "the chart type",
    "data": [
        {{
            "type": "plotly trace type (bar, scatter, pie, scatterpolar, etc.)",
            "x": [array of x values or labels],
            "y": [array of y values],
            ... other trace properties based on chart type
        }}
    ],
    "layout": {{
        "title": "chart title",
        ... other layout properties
    }},
    "insights": ["insight 1", "insight 2"]
}}

For radar/spider charts, use "scatterpolar" type with r and theta.
For colors, convert color names to hex codes (pink=#ec4899, blue=#3b82f6, etc.).
Use actual values from the sample data provided."""

        try:
            response = llm_chat(prompt, temperature=0.3, max_tokens=1500)
            
            # Extract JSON from response
            chart_spec = self._parse_chart_response(response, df, query)
            
            if chart_spec:
                return {
                    "success": True,
                    "chart": chart_spec,
                    "chart_type": chart_spec.get("chart_type", "auto"),
                    "visualization_type": chart_spec.get("chart_type", "auto")
                }
            else:
                return self._fallback_chart(df, query)
                
        except Exception as e:
            logger.error(f"LLM chart generation failed: {e}")
            return self._fallback_chart(df, query)
    
    def _parse_chart_response(self, response: str, df: pd.DataFrame, query: str) -> Optional[Dict]:
        """Parse LLM response to extract chart specification."""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                chart_spec = json.loads(json_match.group())
                
                # Validate and fill in missing data if needed
                chart_spec = self._validate_and_complete(chart_spec, df, query)
                
                return chart_spec
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse chart JSON: {e}")
        except Exception as e:
            logger.warning(f"Chart parsing error: {e}")
        
        return None
    
    def _validate_and_complete(self, spec: Dict, df: pd.DataFrame, query: str) -> Dict:
        """Validate chart spec and complete with real data if needed."""
        
        # Ensure data array exists
        if "data" not in spec or not spec["data"]:
            spec["data"] = [{}]
        
        # Ensure layout exists
        if "layout" not in spec:
            spec["layout"] = {"title": query}
        
        # For each trace, ensure it has valid data
        for trace in spec["data"]:
            trace_type = trace.get("type", "bar")
            
            # If values are empty or placeholders, fill with real data
            if trace_type == "scatterpolar":
                # Radar chart - ensure r and theta are populated
                if not trace.get("r") or len(trace.get("r", [])) == 0:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:6]
                    values = [df[col].mean() / df[col].max() if df[col].max() > 0 else 0 for col in numeric_cols]
                    values.append(values[0])  # Close polygon
                    trace["r"] = values
                    trace["theta"] = numeric_cols + [numeric_cols[0]]
                    trace["fill"] = "toself"
            
            elif trace_type in ["bar", "scatter", "line"]:
                # Ensure x and y have data
                if not trace.get("x") or not trace.get("y"):
                    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    
                    if cat_cols and num_cols:
                        grouped = df.groupby(cat_cols[0])[num_cols[0]].sum().head(10)
                        trace["x"] = grouped.index.tolist()
                        trace["y"] = grouped.values.tolist()
            
            elif trace_type == "pie":
                if not trace.get("values") or not trace.get("labels"):
                    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    
                    if cat_cols and num_cols:
                        grouped = df.groupby(cat_cols[0])[num_cols[0]].sum().head(8)
                        trace["labels"] = grouped.index.tolist()
                        trace["values"] = grouped.values.tolist()
        
        return spec
    
    def _fallback_chart(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Fallback chart generation without LLM."""
        q_lower = query.lower()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Detect color from query
        color = self._extract_color(query)
        
        # Detect chart type from query
        if "radar" in q_lower or "spider" in q_lower:
            return self._generate_radar_fallback(df, numeric_cols, query, color)
        elif "pie" in q_lower:
            return self._generate_pie_fallback(df, categorical_cols, numeric_cols, query, color)
        elif "line" in q_lower or "trend" in q_lower:
            return self._generate_line_fallback(df, numeric_cols, query, color)
        else:
            return self._generate_bar_fallback(df, categorical_cols, numeric_cols, query, color)
    
    def _extract_color(self, query: str) -> str:
        """Extract color from query using common color names."""
        q_lower = query.lower()
        
        # Common colors with their hex values
        colors = {
            'pink': '#ec4899', 'red': '#ef4444', 'blue': '#3b82f6',
            'green': '#22c55e', 'purple': '#8b5cf6', 'orange': '#f97316',
            'teal': '#14b8a6', 'cyan': '#06b6d4', 'amber': '#f59e0b',
            'yellow': '#eab308', 'indigo': '#6366f1', 'rose': '#f43f5e',
            'lime': '#84cc16', 'emerald': '#10b981', 'violet': '#8b5cf6',
            'fuchsia': '#d946ef', 'sky': '#0ea5e9', 'slate': '#64748b',
        }
        
        for name, hex_val in colors.items():
            if name in q_lower:
                return hex_val
        
        return '#14b8a6'  # Default teal
    
    def _generate_radar_fallback(self, df, numeric_cols, query, color):
        """Generate radar chart without LLM."""
        cols = numeric_cols[:6]
        values = [df[col].mean() / df[col].max() if df[col].max() > 0 else 0 for col in cols]
        values.append(values[0])
        
        return {
            "success": True,
            "chart_type": "radar",
            "visualization_type": "radar",
            "chart": {
                "data": [{
                    "type": "scatterpolar",
                    "r": values,
                    "theta": cols + [cols[0]],
                    "fill": "toself",
                    "fillcolor": f"{color}40",
                    "line": {"color": color, "width": 2},
                    "marker": {"color": color}
                }],
                "layout": {
                    "title": query,
                    "polar": {"radialaxis": {"visible": True, "range": [0, 1]}},
                    "template": "plotly_white"
                }
            }
        }
    
    def _generate_pie_fallback(self, df, cat_cols, num_cols, query, color):
        """Generate pie chart without LLM."""
        if not cat_cols or not num_cols:
            return {"error": "Need categorical and numeric columns"}
        
        grouped = df.groupby(cat_cols[0])[num_cols[0]].sum().head(8)
        
        return {
            "success": True,
            "chart_type": "pie",
            "visualization_type": "pie",
            "chart": {
                "data": [{
                    "type": "pie",
                    "labels": grouped.index.tolist(),
                    "values": grouped.values.tolist()
                }],
                "layout": {"title": query, "template": "plotly_white"}
            }
        }
    
    def _generate_line_fallback(self, df, num_cols, query, color):
        """Generate line chart without LLM."""
        if not num_cols:
            return {"error": "Need numeric columns"}
        
        col = num_cols[0]
        y_vals = df[col].head(50).tolist()
        
        return {
            "success": True,
            "chart_type": "line",
            "visualization_type": "line",
            "chart": {
                "data": [{
                    "type": "scatter",
                    "mode": "lines+markers",
                    "y": y_vals,
                    "line": {"color": color}
                }],
                "layout": {"title": query, "template": "plotly_white"}
            }
        }
    
    def _generate_bar_fallback(self, df, cat_cols, num_cols, query, color):
        """Generate bar chart without LLM."""
        if not cat_cols or not num_cols:
            # Use numeric column as bar values
            if num_cols:
                col = num_cols[0]
                grouped = df[col].head(10)
                return {
                    "success": True,
                    "chart_type": "bar",
                    "visualization_type": "bar",
                    "chart": {
                        "data": [{
                            "type": "bar",
                            "y": grouped.tolist(),
                            "marker": {"color": color}
                        }],
                        "layout": {"title": query, "template": "plotly_white"}
                    }
                }
            return {"error": "Need columns for chart"}
        
        grouped = df.groupby(cat_cols[0])[num_cols[0]].sum().head(10)
        
        return {
            "success": True,
            "chart_type": "bar",
            "visualization_type": "bar",
            "chart": {
                "data": [{
                    "type": "bar",
                    "x": grouped.index.tolist(),
                    "y": grouped.values.tolist(),
                    "marker": {"color": color}
                }],
                "layout": {"title": query, "template": "plotly_white"}
            }
        }


# Convenience function
def llm_visualize(df: pd.DataFrame, query: str, user_id: str = None) -> Dict[str, Any]:
    """Quick function for LLM-driven visualization."""
    visualizer = LLMVisualizer(user_id)
    return visualizer.generate(df, query)


__all__ = ['LLMVisualizer', 'llm_visualize']
