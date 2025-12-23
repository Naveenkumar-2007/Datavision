# Chart Gatekeeping - Strict validation before chart generation
"""
Ensures charts are only generated when:
1. Sufficient data exists
2. Chart type matches data
3. Data quality is acceptable
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd


# ============================================================================
# CHART REQUIREMENTS
# ============================================================================

CHART_REQUIREMENTS = {
    "bar": {
        "min_data_points": 2,
        "max_data_points": 50,  # Too many bars = unreadable
        "required_columns": ["name", "value"],
        "description": "Bar chart for comparing categories"
    },
    "line": {
        "min_data_points": 3,  # Need trend
        "max_data_points": 365,
        "required_columns": ["x", "y"],
        "description": "Line chart for trends over time"
    },
    "pie": {
        "min_data_points": 2,
        "max_data_points": 8,  # More than 8 slices = confusing
        "required_columns": ["label", "value"],
        "description": "Pie chart for proportions"
    },
    "scatter": {
        "min_data_points": 5,
        "max_data_points": 1000,
        "required_columns": ["x", "y"],
        "description": "Scatter plot for correlations"
    },
    "prediction": {
        "min_data_points": 5,  # Need history for forecast
        "max_data_points": 365,
        "required_columns": ["date", "value"],
        "description": "Forecast chart with predictions"
    },
}


# ============================================================================
# GATEKEEPING FUNCTIONS
# ============================================================================

def should_render_chart(
    df: Optional[pd.DataFrame],
    chart_type: str,
    query_type: str = None
) -> Tuple[bool, str]:
    """
    Strict gatekeeping: Should we render this chart?
    
    Returns:
        Tuple[bool, str]: (should_render, reason)
    """
    
    # No data = no chart
    if df is None:
        return False, "No data available"
    
    if df.empty:
        return False, "Dataset is empty"
    
    # Get requirements for chart type
    requirements = CHART_REQUIREMENTS.get(chart_type.lower())
    if not requirements:
        return False, f"Unknown chart type: {chart_type}"
    
    # Check minimum data points
    data_points = len(df)
    if data_points < requirements["min_data_points"]:
        return False, f"Insufficient data: {data_points} points (need {requirements['min_data_points']} minimum)"
    
    # Check maximum data points
    if data_points > requirements["max_data_points"]:
        return False, f"Too many data points: {data_points} (max {requirements['max_data_points']} for readability)"
    
    # Check for excessive null values (>30% = unreliable)
    null_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if null_ratio > 0.3:
        return False, f"Data quality issue: {null_ratio:.0%} null values"
    
    return True, "Chart approved"


def validate_chart_data(
    df: pd.DataFrame,
    chart_type: str
) -> Tuple[bool, str, Optional[pd.DataFrame]]:
    """
    Validate and clean data for charting.
    
    Returns:
        Tuple[bool, str, DataFrame]: (is_valid, message, cleaned_df)
    """
    
    if df is None or df.empty:
        return False, "No data to validate", None
    
    # Make a copy to avoid modifying original
    clean_df = df.copy()
    
    # Remove rows with all nulls
    clean_df = clean_df.dropna(how='all')
    
    # Check again after cleaning
    if clean_df.empty:
        return False, "All data rows were empty", None
    
    # For numeric charts, ensure we have numeric data
    numeric_types = ["bar", "line", "pie", "scatter", "prediction"]
    if chart_type.lower() in numeric_types:
        # Find numeric columns
        numeric_cols = clean_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            return False, "No numeric data for chart", None
    
    return True, "Data validated", clean_df


def get_chart_decision(
    df: Optional[pd.DataFrame],
    chart_type: str,
    query_type: str = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Make a chart rendering decision with full reasoning.
    
    Returns:
        Dict with keys: should_render, reason, warnings, chart_type, data_points
    """
    
    decision = {
        "should_render": False,
        "reason": "",
        "warnings": [],
        "chart_type": chart_type,
        "data_points": 0
    }
    
    if df is not None and not df.empty:
        decision["data_points"] = len(df)
    
    # Check gatekeeping
    can_render, reason = should_render_chart(df, chart_type, query_type)
    
    if not can_render and not force:
        decision["reason"] = reason
        return decision
    
    # Validate data
    if df is not None:
        is_valid, message, _ = validate_chart_data(df, chart_type)
        if not is_valid and not force:
            decision["reason"] = message
            return decision
    
    # Approved
    decision["should_render"] = True
    decision["reason"] = "Chart approved"
    
    # Add warnings if applicable
    if decision["data_points"] < 5:
        decision["warnings"].append("Limited data points - interpretation may be less reliable")
    
    return decision


# ============================================================================
# QUERY-BASED CHART SELECTION
# ============================================================================

def suggest_chart_type(query: str, df: Optional[pd.DataFrame]) -> Optional[str]:
    """
    Suggest appropriate chart type based on query and data.
    Returns None if no chart is appropriate.
    """
    query_lower = query.lower()
    
    # Trend/time queries → line chart
    if any(word in query_lower for word in ["trend", "over time", "monthly", "weekly", "daily", "growth"]):
        return "line"
    
    # Comparison queries → bar chart
    if any(word in query_lower for word in ["compare", "top", "bottom", "ranking", "best", "worst"]):
        return "bar"
    
    # Distribution queries → pie chart
    if any(word in query_lower for word in ["breakdown", "distribution", "percentage", "share", "proportion"]):
        if df is not None and len(df) <= 8:  # Pie only for small datasets
            return "pie"
        return "bar"  # Fall back to bar for larger datasets
    
    # Prediction queries → prediction chart
    if any(word in query_lower for word in ["predict", "forecast", "future", "next"]):
        return "prediction"
    
    # Correlation queries → scatter
    if any(word in query_lower for word in ["correlation", "relationship", "vs", "versus"]):
        return "scatter"
    
    # Default: no chart if not clearly needed
    return None
