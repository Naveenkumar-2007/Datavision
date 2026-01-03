"""
Visual Intelligence - Smart Chart and Visualization Selection
===============================================================

Intelligently selects the best visualization type based on:
1. Query intent
2. Data characteristics
3. Number of data points
"""

import logging
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)


def extract_count_from_query(query: str) -> int:
    """Extract count/limit from query like 'top 5' or 'show 10'"""
    import re
    
    # Patterns for count extraction
    patterns = [
        r'top\s+(\d+)',
        r'bottom\s+(\d+)',
        r'first\s+(\d+)',
        r'last\s+(\d+)',
        r'show\s+(\d+)',
        r'list\s+(\d+)',
        r'(\d+)\s+(?:customers?|products?|items?|orders?)',
    ]
    
    query_lower = query.lower()
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            return int(match.group(1))
    
    # Default limits
    if 'all' in query_lower:
        return 20  # Reasonable limit for "all"
    
    return 10  # Default


def suggest_chart_type(
    query: str,
    data_characteristics: Dict[str, Any] = None
) -> str:
    """
    Suggest the best chart type based on query and data.
    
    Args:
        query: The user's query
        data_characteristics: Dict with data info (num_categories, has_time, etc.)
        
    Returns:
        Chart type: 'bar', 'line', 'pie', 'scatter', 'table'
    """
    query_lower = query.lower()
    
    # Explicit chart type requests
    if 'pie' in query_lower or 'breakdown' in query_lower:
        return 'pie'
    if 'line' in query_lower or 'trend' in query_lower or 'over time' in query_lower:
        return 'line'
    if 'scatter' in query_lower or 'correlation' in query_lower:
        return 'scatter'
    if 'bar' in query_lower:
        return 'bar'
    if 'table' in query_lower or 'list' in query_lower:
        return 'table'
    
    # Infer from query intent
    if any(w in query_lower for w in ['compare', 'vs', 'versus', 'top', 'bottom', 'ranking']):
        return 'bar'
    if any(w in query_lower for w in ['monthly', 'weekly', 'daily', 'yearly', 'growth']):
        return 'line'
    if any(w in query_lower for w in ['distribution', 'percentage', 'share', 'portion']):
        return 'pie'
    
    # Use data characteristics if available
    if data_characteristics:
        num_cats = data_characteristics.get('num_categories', 0)
        has_time = data_characteristics.get('has_time_column', False)
        
        if has_time:
            return 'line'
        if num_cats <= 6:
            return 'pie'
        if num_cats <= 15:
            return 'bar'
    
    # Default
    return 'bar'


def get_chart_config(chart_type: str, title: str = "Analysis") -> Dict:
    """Get default configuration for a chart type"""
    
    base_config = {
        "responsive": True,
        "displayModeBar": True,
    }
    
    configs = {
        "bar": {
            **base_config,
            "type": "bar",
            "layout": {
                "title": title,
                "xaxis": {"title": "Category"},
                "yaxis": {"title": "Value"},
                "barmode": "group"
            }
        },
        "line": {
            **base_config,
            "type": "scatter",
            "mode": "lines+markers",
            "layout": {
                "title": title,
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"}
            }
        },
        "pie": {
            **base_config,
            "type": "pie",
            "layout": {
                "title": title,
            }
        },
        "scatter": {
            **base_config,
            "type": "scatter",
            "mode": "markers",
            "layout": {
                "title": title,
                "xaxis": {"title": "X"},
                "yaxis": {"title": "Y"}
            }
        }
    }
    
    return configs.get(chart_type, configs["bar"])


def analyze_data_for_visualization(df) -> Dict[str, Any]:
    """
    Analyze a DataFrame to determine best visualization approach.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Dict with analysis results
    """
    if df is None or len(df) == 0:
        return {"empty": True}
    
    analysis = {
        "empty": False,
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "numeric_columns": [],
        "categorical_columns": [],
        "date_columns": [],
        "has_time_column": False,
        "num_categories": 0,
        "suggested_chart": "bar"
    }
    
    for col in df.columns:
        if col.startswith('_'):  # Skip internal columns
            continue
            
        dtype = df[col].dtype
        
        if dtype in ['int64', 'float64']:
            analysis["numeric_columns"].append(col)
        elif dtype == 'object':
            analysis["categorical_columns"].append(col)
            # Check if it looks like a date
            if 'date' in col.lower() or 'time' in col.lower():
                analysis["date_columns"].append(col)
                analysis["has_time_column"] = True
    
    # Get unique category count from first categorical column
    if analysis["categorical_columns"]:
        first_cat = analysis["categorical_columns"][0]
        analysis["num_categories"] = df[first_cat].nunique()
    
    # Suggest chart type
    if analysis["has_time_column"]:
        analysis["suggested_chart"] = "line"
    elif analysis["num_categories"] <= 6:
        analysis["suggested_chart"] = "pie"
    elif analysis["num_categories"] <= 15:
        analysis["suggested_chart"] = "bar"
    else:
        analysis["suggested_chart"] = "bar"  # With scrolling for many categories
    
    return analysis


def format_number_for_display(value: float, currency_symbol: str = "$") -> str:
    """Format a number for display with appropriate units"""
    if abs(value) >= 1_000_000_000:
        return f"{currency_symbol}{value/1_000_000_000:.1f}B"
    elif abs(value) >= 1_000_000:
        return f"{currency_symbol}{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{currency_symbol}{value/1_000:.1f}K"
    else:
        return f"{currency_symbol}{value:,.2f}"
