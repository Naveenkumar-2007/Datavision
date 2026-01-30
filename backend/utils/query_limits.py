"""
Query-Aware Limits - NO MORE HARDCODING!
==========================================

This module provides DYNAMIC limits based on user queries.
All hardcoded numbers like [:5], head(10), top_k=5 should be replaced
with calls to this module.

Usage:
    from utils.query_limits import get_limit_from_query, get_dynamic_colors

    # Instead of hardcoded head(5):
    limit = get_limit_from_query(query)  # Detects "top 10" etc.
    df.head(limit)

    # Instead of hardcoded color lists:
    colors = get_dynamic_colors(num_items)
"""

import re
from typing import List, Optional, Dict, Tuple


# ============================================================================
# EXPANDED COLOR PALETTE - 50 colors for any chart
# ============================================================================

ENTERPRISE_COLORS = [
    # Primary vibrant colors
    "#f97316", "#3b82f6", "#22c55e", "#a855f7", "#ef4444",
    "#06b6d4", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6",
    # Secondary colors
    "#84cc16", "#6366f1", "#f43f5e", "#0ea5e9", "#d946ef",
    "#eab308", "#10b981", "#6b7280", "#78716c", "#0284c7",
    # Extended palette
    "#dc2626", "#059669", "#7c3aed", "#db2777", "#2563eb",
    "#16a34a", "#9333ea", "#e11d48", "#0891b2", "#ca8a04",
    # Additional colors
    "#4f46e5", "#c026d3", "#0d9488", "#ea580c", "#7e22ce",
    "#15803d", "#be185d", "#1d4ed8", "#047857", "#9a3412",
    # Final colors for large datasets
    "#4338ca", "#a21caf", "#0f766e", "#c2410c", "#6d28d9",
    "#166534", "#9d174d", "#1e40af", "#065f46", "#7c2d12",
]


def get_limit_from_query(query: str, default: int = 10, max_limit: int = 100) -> int:
    """
    Extract limit from query.
    
    Detects patterns like:
    - "top 5 customers"
    - "show 10 products"
    - "first 3 items"
    - "15 best sellers"
    
    Args:
        query: User's query string
        default: Default limit if not specified (10)
        max_limit: Maximum allowed limit (100)
        
    Returns:
        Detected limit or default
    """
    q_lower = query.lower()
    
    # Comprehensive patterns
    patterns = [
        r'(?:top|best|bottom|worst|first|last|show|display|get|give)\s+(\d+)',
        r'(\d+)\s+(?:customers?|products?|items?|entries|records|rows)',
        r'only\s+(\d+)',
        r'limit\s+(?:to\s+)?(\d+)',
        r'(\d+)\s+(?:top|best|bottom|worst)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, q_lower)
        if match:
            limit = int(match.group(1))
            # Apply reasonable bounds
            if 1 <= limit <= max_limit:
                return limit
    
    return default


def get_chart_type_from_query(query: str) -> str:
    """
    Detect chart type from query.
    
    Returns: 'pie', 'bar', 'line', 'area', 'scatter', 'forecast', 'table', 'auto'
    """
    q_lower = query.lower()
    
    # Explicit chart requests
    chart_map = {
        'pie': ['pie chart', 'pie graph', 'donut'],
        'bar': ['bar chart', 'bar graph', 'histogram', 'column chart'],
        'line': ['line chart', 'line graph', 'trend line'],
        'area': ['area chart', 'area graph'],
        'scatter': ['scatter plot', 'scatter chart', 'correlation'],
        'forecast': ['forecast', 'prediction', 'predict', 'future'],
        'table': ['table', 'list all', 'show all details'],
    }
    
    for chart_type, keywords in chart_map.items():
        if any(kw in q_lower for kw in keywords):
            return chart_type
    
    # Detect implicit chart type from intent
    if any(w in q_lower for w in ['trend', 'over time', 'monthly', 'yearly']):
        return 'line'
    elif any(w in q_lower for w in ['compare', 'comparison', 'versus', 'vs']):
        return 'bar'
    elif any(w in q_lower for w in ['breakdown', 'distribution', 'proportion', 'share']):
        return 'pie'
    elif any(w in q_lower for w in ['ranking', 'top', 'best', 'worst']):
        return 'bar'
    
    return 'auto'


def get_prediction_periods_from_query(query: str) -> Tuple[int, str]:
    """
    Extract prediction periods and unit from query.
    
    Returns: (periods, unit) e.g., (3, "months"), (12, "weeks")
    """
    q_lower = query.lower()
    
    # Period patterns
    patterns = {
        'days': [r'next\s+(\d+)\s+days?', r'(\d+)\s+days?\s+ahead'],
        'weeks': [r'next\s+(\d+)\s+weeks?', r'(\d+)\s+weeks?\s+ahead'],
        'months': [r'next\s+(\d+)\s+months?', r'(\d+)\s+months?\s+ahead'],
        'quarters': [r'next\s+(\d+)\s+quarters?', r'next\s+quarter'],
        'years': [r'next\s+(\d+)\s+years?', r'(\d+)\s+years?\s+ahead', r'next\s+year'],
    }
    
    for unit, unit_patterns in patterns.items():
        for pattern in unit_patterns:
            match = re.search(pattern, q_lower)
            if match:
                groups = match.groups()
                if groups and groups[0] and groups[0].isdigit():
                    return int(groups[0]), unit
                else:
                    # Default periods per unit
                    defaults = {'days': 7, 'weeks': 4, 'months': 3, 'quarters': 1, 'years': 1}
                    return defaults.get(unit, 3), unit
    
    # Detect unit without number
    if 'month' in q_lower:
        return 3, 'months'
    elif 'quarter' in q_lower:
        return 3, 'months'  # 1 quarter = 3 months
    elif 'year' in q_lower:
        return 12, 'months'  # 1 year = 12 months
    elif 'week' in q_lower:
        return 4, 'weeks'
    
    # Default: 3 months
    return 3, 'months'


def get_dynamic_colors(num_items: int) -> List[str]:
    """
    Get enough colors for the number of items.
    
    Args:
        num_items: Number of data points/items
        
    Returns:
        List of color hex codes
    """
    if num_items <= len(ENTERPRISE_COLORS):
        return ENTERPRISE_COLORS[:num_items]
    
    # If more colors needed, cycle through palette
    colors = []
    for i in range(num_items):
        colors.append(ENTERPRISE_COLORS[i % len(ENTERPRISE_COLORS)])
    return colors


def get_grouping_from_query(query: str) -> Optional[str]:
    """
    Detect what dimension to group by.
    
    Returns: 'customer', 'product', 'date', 'category', etc.
    """
    q_lower = query.lower()
    
    grouping_map = {
        'customer': ['by customer', 'per customer', 'each customer', 'customers'],
        'product': ['by product', 'per product', 'each product', 'products'],
        'date': ['by date', 'daily', 'by day', 'per day'],
        'month': ['by month', 'monthly', 'per month', 'each month'],
        'year': ['by year', 'yearly', 'per year', 'annual'],
        'category': ['by category', 'per category', 'categories'],
        'region': ['by region', 'per region', 'regional'],
    }
    
    for grouping, keywords in grouping_map.items():
        if any(kw in q_lower for kw in keywords):
            return grouping
    
    return None


def get_metric_from_query(query: str) -> str:
    """
    Detect which metric is being asked about.
    
    Returns: 'revenue', 'orders', 'customers', 'quantity', 'profit', etc.
    """
    q_lower = query.lower()
    
    metrics = {
        'revenue': ['revenue', 'sales', 'income', 'earnings', 'money', 'amount', 'total'],
        'orders': ['order', 'transaction', 'invoice', 'purchase', 'sale count'],
        'customers': ['customer', 'client', 'buyer', 'account'],
        'products': ['product', 'item', 'sku', 'goods'],
        'quantity': ['quantity', 'units', 'count', 'volume', 'how many'],
        'profit': ['profit', 'margin', 'net'],
        'average': ['average', 'avg', 'mean', 'per'],
        'growth': ['growth', 'increase', 'change', 'trend'],
    }
    
    for metric, keywords in metrics.items():
        if any(kw in q_lower for kw in keywords):
            return metric
    
    return 'revenue'  # Default to revenue


def get_time_range_from_query(query: str) -> Optional[str]:
    """
    Detect time range from query.
    
    Returns: 'today', 'week', 'month', 'quarter', 'year', 'all', etc.
    """
    q_lower = query.lower()
    
    ranges = {
        'today': ['today', 'this day'],
        'week': ['this week', 'past week', 'last week', 'weekly'],
        'month': ['this month', 'past month', 'last month', 'monthly'],
        'quarter': ['this quarter', 'past quarter', 'last quarter', 'quarterly'],
        'year': ['this year', 'past year', 'last year', 'yearly', 'annual'],
        'all': ['all time', 'total', 'overall', 'entire'],
    }
    
    for range_type, keywords in ranges.items():
        if any(kw in q_lower for kw in keywords):
            return range_type
    
    return None


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def analyze_query_for_data_limits(query: str) -> Dict[str, any]:
    """
    Comprehensive query analysis for data handling.
    
    Returns all detected parameters from query.
    """
    return {
        'limit': get_limit_from_query(query),
        'chart_type': get_chart_type_from_query(query),
        'grouping': get_grouping_from_query(query),
        'metric': get_metric_from_query(query),
        'time_range': get_time_range_from_query(query),
        'prediction': get_prediction_periods_from_query(query),
        'colors': get_dynamic_colors(get_limit_from_query(query)),
    }


# Quick test
if __name__ == "__main__":
    test_queries = [
        "Give me top 10 customers",
        "Show 5 best products by revenue",
        "Forecast next 6 months",
        "Compare customers with pie chart",
        "Monthly trend for this year",
    ]
    
    for q in test_queries:
        result = analyze_query_for_data_limits(q)
        print(f"\nQuery: {q}")
        print(f"  Limit: {result['limit']}")
        print(f"  Chart: {result['chart_type']}")
        print(f"  Grouping: {result['grouping']}")
        print(f"  Metric: {result['metric']}")
