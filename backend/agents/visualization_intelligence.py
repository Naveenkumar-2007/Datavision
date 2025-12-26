# Visualization Intelligence Layer - ChatGPT-Level Chart Selection
"""
Intelligent visualization system that:
1. Understands query intent
2. Selects appropriate chart type based on data
3. Validates data before rendering
4. Adapts to user role/mode

This is the DECISION LAYER - it decides WHAT to visualize and HOW,
before any chart is generated.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import re


class ChartType(Enum):
    """All supported chart types - Universal Visualization v2.0"""
    # Standard charts
    LINE = "line"                    # Trends, time-series
    BAR = "bar"                      # Comparisons
    HORIZONTAL_BAR = "horizontal_bar"  # Horizontal comparisons
    GROUPED_BAR = "grouped_bar"      # Multi-category comparisons
    STACKED_BAR = "stacked_bar"      # Composition over categories
    # Proportion charts
    PIE = "pie"                      # Proportions (dynamic limit from query)
    DONUT = "donut"                  # Proportions with center metric (dynamic)
    SUNBURST = "sunburst"            # Hierarchical proportions
    TREEMAP = "treemap"              # Space-filling hierarchies
    # Trend/Area charts
    AREA = "area"                    # Cumulative trends
    # Statistical charts
    SCATTER = "scatter"              # Correlations
    BUBBLE = "bubble"                # Multi-dimensional data
    BOX = "box"                      # Statistical distribution
    HISTOGRAM = "histogram"          # Frequency distribution
    RADAR = "radar"                  # Multi-variable comparison
    HEATMAP = "heatmap"              # Intensity matrices
    # Financial/Process charts
    WATERFALL = "waterfall"          # Financial breakdowns
    FUNNEL = "funnel"                # Conversion analysis
    GAUGE = "gauge"                  # Single metric display
    # Prediction
    FORECAST = "forecast"            # Predictions with confidence bands
    # No chart
    NONE = "none"                    # No visualization appropriate


class VisualizationIntent(Enum):
    """User's visualization intent from query"""
    TREND = "trend"                  # "over time", "trend", "growth"
    COMPARISON = "comparison"        # "compare", "vs", "between"
    DISTRIBUTION = "distribution"    # "distribution", "spread", "histogram"
    PROPORTION = "proportion"        # "share", "percentage", "breakdown"
    CORRELATION = "correlation"      # "relationship", "correlation"
    RANKING = "ranking"              # "top", "bottom", "best", "worst"
    FORECAST = "forecast"            # "predict", "forecast", "next"
    BREAKDOWN = "breakdown"          # "breakdown", "composition"
    NONE = "none"                    # No visualization intent


@dataclass
class VisualizationDecision:
    """Result of visualization decision process"""
    should_render: bool
    chart_type: ChartType
    intent: VisualizationIntent
    x_column: Optional[str]
    y_column: Optional[str]
    group_column: Optional[str]
    title: str
    reason: str
    data_points: int
    confidence: float  # 0-1 confidence in this decision
    limit: int = 10  # Default 10, but extracted from query like "top 3"


@dataclass
class DataProfile:
    """Profile of the dataset for visualization decisions"""
    has_date_column: bool
    date_column: Optional[str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    row_count: int
    has_customer: bool
    has_product: bool
    has_amount: bool
    has_time_series: bool
    unique_categories: Dict[str, int]


# ============================================================================
# INTENT DETECTION - Understanding what user wants to visualize
# ============================================================================

INTENT_PATTERNS = {
    VisualizationIntent.TREND: [
        r'\b(trend|over time|monthly|weekly|daily|yearly|growth|timeline)\b',
        r'\b(how has|how did).*(change|grow|evolve)\b',
        r'\b(show|display).*(trend|progress|evolution)\b',
    ],
    VisualizationIntent.COMPARISON: [
        r'\b(compare|comparison|vs|versus|between|against)\b',
        r'\b(which is (better|worse|higher|lower))\b',
        r'\b(difference between)\b',
    ],
    VisualizationIntent.DISTRIBUTION: [
        r'\b(distribution|spread|histogram|frequency|range)\b',
        r'\b(how (are|is).*(distributed|spread))\b',
    ],
    VisualizationIntent.PROPORTION: [
        r'\b(proportion|percentage|share|breakdown|composition)\b',
        r'\b(pie|donut)\s*(chart)?\b',
        r'\b(what percent|what %)\b',
    ],
    VisualizationIntent.CORRELATION: [
        r'\b(correlation|relationship|correlate|related)\b',
        r'\b(scatter|x vs y)\b',
        r'\b(does .* affect)\b',
    ],
    VisualizationIntent.RANKING: [
        r'\b(top|bottom|best|worst|highest|lowest|rank|ranking)\b',
        r'\b(leader|leaderboard)\b',
    ],
    VisualizationIntent.FORECAST: [
        r'\b(predict|forecast|projection|future|next month|next year)\b',
        r'\b(will|expected|anticipated)\b',
        r'\b(what will be)\b',
    ],
    VisualizationIntent.BREAKDOWN: [
        r'\b(breakdown|break down|split by|by category)\b',
        r'\b(composition|make up|consist)\b',
    ],
}


def extract_count_from_query(query: str) -> int:
    """
    Extract count from query like 'top 3', 'best 5 customers', 'show 10 products'.
    
    Returns extracted count or default of 10.
    """
    import re
    query_lower = query.lower()
    
    # Patterns to extract numbers from queries
    patterns = [
        r'(?:top|best|bottom|worst|first|last|show|display)\s+(\d+)',  # "top 3", "show 5"
        r'(\d+)\s+(?:customers?|products?|items?|entries)',  # "3 customers"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            count = int(match.group(1))
            # Reasonable limits
            if 1 <= count <= 50:
                return count
    
    return 10  # Default


def extract_chart_type_from_query(query: str) -> str:
    """
    Extract chart type from query like 'as a pie chart', 'show bar chart', 'display line graph'.
    
    Returns: 'pie', 'bar', 'line', 'area', 'scatter', or 'auto' (let system decide)
    """
    query_lower = query.lower()
    
    # Explicit chart type requests
    if 'pie' in query_lower or 'donut' in query_lower:
        return 'pie'
    elif 'line' in query_lower and ('chart' in query_lower or 'graph' in query_lower):
        return 'line'
    elif 'bar' in query_lower:
        return 'bar'
    elif 'area' in query_lower:
        return 'area'
    elif 'scatter' in query_lower:
        return 'scatter'
    elif 'trend' in query_lower or 'over time' in query_lower or 'monthly' in query_lower:
        return 'line'  # Trends imply line chart
    elif 'distribution' in query_lower or 'breakdown' in query_lower:
        return 'pie'  # Distribution implies pie chart
    
    return 'auto'  # Let the system decide based on data


def detect_visualization_intent(query: str) -> Tuple[VisualizationIntent, float]:
    """
    Detect what type of visualization the user wants.
    
    Returns: (intent, confidence)
    """
    query_lower = query.lower()
    
    # ==========================================================================
    # CRITICAL: Skip visualization for EXPLANATION queries
    # ==========================================================================
    # Queries like "Explain this chart" should NOT generate a new chart!
    explanation_patterns = [
        'explain this', 'explain the chart', 'what does this chart show',
        'explain what', 'describe the chart', 'interpret this',
        'what does the chart', 'explain above', 'shows in one',
        'in one line', 'in one sentence', 'tell me about this chart',
        'what does it show', 'what is shown', 'about this chart',
        'summarize this', 'describe this'
    ]
    if any(p in query_lower for p in explanation_patterns):
        return VisualizationIntent.NONE, 0.0  # Skip visualization!
    
    # FIRST: Check for explicit chart/visualization requests
    # These ALWAYS trigger visualization regardless of other patterns
    explicit_viz_keywords = ['chart', 'graph', 'plot', 'visualize', 'visualization', 'visual']
    has_explicit_viz = any(kw in query_lower for kw in explicit_viz_keywords)
    
    # If explicit chart request, determine type based on context
    if has_explicit_viz:
        # Check what type of chart is requested
        if any(kw in query_lower for kw in ['customer', 'top customer', 'best customer']):
            return VisualizationIntent.RANKING, 0.9
        if any(kw in query_lower for kw in ['product', 'top product']):
            return VisualizationIntent.RANKING, 0.9
        if any(kw in query_lower for kw in ['revenue', 'sales', 'amount']):
            return VisualizationIntent.RANKING, 0.85
        if any(kw in query_lower for kw in ['pie', 'distribution', 'breakdown']):
            return VisualizationIntent.PROPORTION, 0.9
        if any(kw in query_lower for kw in ['trend', 'over time', 'monthly', 'line']):
            return VisualizationIntent.TREND, 0.9
        if any(kw in query_lower for kw in ['compare', 'vs', 'versus']):
            return VisualizationIntent.COMPARISON, 0.9
        if any(kw in query_lower for kw in ['predict', 'forecast', 'future']):
            return VisualizationIntent.FORECAST, 0.9
        # Default for generic chart request
        return VisualizationIntent.RANKING, 0.8
    
    best_intent = VisualizationIntent.NONE
    best_score = 0
    
    for intent, patterns in INTENT_PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, query_lower):
                matches += 1
        
        if matches > 0:
            # Score based on number of matches
            score = min(matches / len(patterns) + 0.3, 1.0)
            if score > best_score:
                best_score = score
                best_intent = intent
    
    # Check for explicit chart type patterns
    explicit_chart_patterns = [
        (r'\b(line\s*(chart|graph))\b', VisualizationIntent.TREND),
        (r'\b(bar\s*(chart|graph))\b', VisualizationIntent.COMPARISON),
        (r'\b(pie\s*(chart|graph))\b', VisualizationIntent.PROPORTION),
        (r'\b(scatter\s*(plot|chart))\b', VisualizationIntent.CORRELATION),
    ]
    
    for pattern, intent in explicit_chart_patterns:
        if re.search(pattern, query_lower):
            return intent, 0.9
    
    return best_intent, best_score


def detect_visualization_subject(query: str) -> Tuple[str, str]:
    """
    Detect what entities the user wants to visualize.
    
    ENHANCED: Now extracts ANY entity from query, not just hardcoded ones.
    This makes it work like real ChatGPT with any data schema.
    
    Returns: (x_axis_hint, y_axis_hint)
    """
    query_lower = query.lower()
    
    x_hint = None
    y_hint = None
    
    # Time-based X axis
    if any(kw in query_lower for kw in ['over time', 'monthly', 'weekly', 'daily', 'trend', 'timeline']):
        x_hint = 'date'
    
    # =========================================================================
    # ENHANCED: Extract ANY entity from query patterns
    # =========================================================================
    # Pattern: "top N <entity>", "show <entity>", "by <entity>"
    import re
    
    entity_patterns = [
        r'top\s+\d*\s*(\w+)',           # "top 5 vendors", "top customers"
        r'best\s+\d*\s*(\w+)',          # "best 10 stores"
        r'show\s+(\w+)',                 # "show regions"
        r'by\s+(\w+)',                   # "by category"
        r'(\w+)\s+chart',                # "vendors chart"
        r'(\w+)\s+pie',                  # "regions pie"
        r'(\w+)\s+bar',                  # "products bar"
        r'compare\s+(\w+)',              # "compare stores"
    ]
    
    for pattern in entity_patterns:
        match = re.search(pattern, query_lower)
        if match:
            entity = match.group(1)
            # Skip common non-entity words
            skip_words = ['the', 'a', 'an', 'my', 'your', 'our', 'this', 'that', 
                         'chart', 'graph', 'pie', 'bar', 'line', 'data', 'me',
                         'revenue', 'sales', 'amount', 'total', 'all', 'and', 'vs']
            if entity not in skip_words and len(entity) > 2:
                # Remove trailing 's' to normalize (customers -> customer)
                if entity.endswith('s') and len(entity) > 3:
                    x_hint = entity[:-1]
                else:
                    x_hint = entity
                break
    
    # Fallback to known patterns if nothing extracted
    if not x_hint:
        if 'customer' in query_lower:
            x_hint = 'customer'
        elif 'product' in query_lower:
            x_hint = 'product'
        elif 'category' in query_lower:
            x_hint = 'category'
    
    # Metric-based Y axis
    if 'revenue' in query_lower or 'sales' in query_lower or 'amount' in query_lower:
        y_hint = 'revenue'
    if 'orders' in query_lower or 'count' in query_lower or 'quantity' in query_lower:
        y_hint = 'count'
    if 'profit' in query_lower or 'margin' in query_lower:
        y_hint = 'profit'
    
    return x_hint or 'auto', y_hint or 'auto'



def llm_match_column(query: str, columns: list, column_context: str = "") -> Optional[str]:
    """
    🧠 LLM-BASED COLUMN MATCHING - Like Real ChatGPT!
    
    Uses the LLM to dynamically determine which column best matches 
    the user's query, regardless of column naming conventions.
    
    Args:
        query: User's query (e.g., "show top 5 vendors by revenue")
        columns: List of available column names in the DataFrame
        column_context: Optional sample data or column descriptions
        
    Returns:
        The best matching column name, or None if no good match
    """
    if not columns:
        return None
    
    # If only one column, return it
    if len(columns) == 1:
        return columns[0]
    
    try:
        from core.llm import chat
        
        prompt = f"""You are a data analyst matching user queries to DataFrame columns.

USER QUERY: "{query}"

AVAILABLE COLUMNS: {columns}
{f"SAMPLE DATA: {column_context}" if column_context else ""}

TASK: Which column should be used for the X-axis (categories/entities) in a chart for this query?

RULES:
1. Match based on MEANING, not exact names
2. "customers" could match "Account", "Client", "Buyer", "Company Name", etc.
3. "products" could match "Item", "SKU", "Service", "Goods", etc.
4. "region" could match "Area", "Territory", "Zone", "Location", etc.
5. If the query mentions a specific entity, find the column that represents it

RESPOND WITH ONLY THE EXACT COLUMN NAME FROM THE LIST ABOVE. 
NO EXPLANATION, JUST THE COLUMN NAME."""

        response = chat(prompt, max_tokens=50)
        
        # Clean the response to get just the column name
        matched = response.strip().strip('"').strip("'")
        
        # Verify the match exists in columns (case-insensitive)
        for col in columns:
            if col.lower() == matched.lower():
                print(f"[LLM MATCH] Query '{query[:30]}...' -> Column '{col}'")
                return col
        
        # Fallback: Check if response contains any column name
        for col in columns:
            if col.lower() in matched.lower():
                print(f"[LLM MATCH] Extracted '{col}' from LLM response")
                return col
        
        print(f"[LLM MATCH] No valid match found, LLM said: {matched}")
        return None
        
    except Exception as e:
        print(f"[LLM MATCH] Error: {e}")
        return None


def smart_select_column(
    query: str, 
    categorical_columns: list, 
    fallback_patterns: list = None,
    column_samples: dict = None
) -> Optional[str]:
    """
    Smart column selection with LLM fallback.
    
    1. First tries fast pattern matching (for common cases)
    2. Falls back to LLM for complex/unknown schemas
    
    Args:
        query: User's query
        categorical_columns: Available categorical columns
        fallback_patterns: Optional list of pattern tuples [(pattern, column_type), ...]
        column_samples: Optional dict of column_name -> sample_values
    """
    if not categorical_columns:
        return None
    
    query_lower = query.lower()
    
    # Fast path: Direct column name mention in query
    for col in categorical_columns:
        if col.lower() in query_lower:
            return col
    
    # Try pattern matching first (fast)
    if fallback_patterns:
        for col in categorical_columns:
            col_lower = col.lower()
            for pattern in fallback_patterns:
                if pattern in col_lower:
                    return col
    
    # Slow path: Use LLM for complex matching
    context = ""
    if column_samples:
        sample_strs = [f"{k}: {v[:3]}" for k, v in column_samples.items() if k in categorical_columns]
        context = str(sample_strs[:5])
    
    return llm_match_column(query, categorical_columns, context)



# ============================================================================
# DATA PROFILING - Understanding what we can visualize
# ============================================================================

def profile_dataframe(df: pd.DataFrame) -> DataProfile:
    """
    Profile a dataframe to understand visualization possibilities.
    Uses CONTENT-BASED detection via schema_detector (no hardcoded column names).
    """
    if df is None or df.empty:
        return DataProfile(
            has_date_column=False,
            date_column=None,
            numeric_columns=[],
            categorical_columns=[],
            row_count=0,
            has_customer=False,
            has_product=False,
            has_amount=False,
            has_time_series=False,
            unique_categories={}
        )
    
    # =========================================================================
    # TRY UNIVERSAL SCHEMA DETECTOR FIRST (CONTENT-BASED, NOT NAME-BASED)
    # =========================================================================
    try:
        from core.schema_detector import detect_schema, ColumnType, ColumnRole
        schema = detect_schema(df, "profile_analysis")
        
        # Metadata columns to EXCLUDE from visualization
        METADATA_COLUMNS = {
            'source_file', 'file_path', 'file_name', 'filename', 'source', 'file',
            'row_index', 'index', 'id', '_id', 'uuid', 'created_at', 'updated_at',
            'timestamp', 'metadata', '__source__'
        }
        
        # Extract column classifications from schema, excluding metadata
        numeric_cols = [col for col, info in schema.columns.items() 
                       if info.detected_type == ColumnType.NUMERIC]
        categorical_cols = [col for col, info in schema.columns.items() 
                          if info.detected_type == ColumnType.CATEGORICAL
                          and col.lower() not in METADATA_COLUMNS
                          and not col.startswith('_')]

        
        date_column = schema.best_date_col
        has_time_series = date_column is not None
        
        # Check for entity columns
        has_customer = any(info.detected_role == ColumnRole.ENTITY 
                          for info in schema.columns.values())
        has_product = len(schema.best_entity_cols) > 1
        has_amount = schema.best_amount_col is not None
        
        # Build unique categories dict
        unique_categories = {col: info.unique_count 
                           for col, info in schema.columns.items() 
                           if info.detected_type == ColumnType.CATEGORICAL}
        
        return DataProfile(
            has_date_column=has_time_series,
            date_column=date_column,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            row_count=len(df),
            has_customer=has_customer,
            has_product=has_product,
            has_amount=has_amount,
            has_time_series=has_time_series,
            unique_categories=unique_categories
        )
    except ImportError:
        pass  # Fall back to legacy detection
    
    # =========================================================================
    # FALLBACK: Legacy detection (for compatibility)
    # =========================================================================
    
    # Metadata columns to EXCLUDE from visualization (these are system columns, not data)
    METADATA_COLUMNS = {
        'source_file', 'file_path', 'file_name', 'filename', 'source', 'file',
        'row_index', 'index', 'id', '_id', 'uuid', 'created_at', 'updated_at',
        'timestamp', 'metadata', '__source__'
    }
    
    numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    
    # Exclude metadata columns from categorical columns
    categorical_cols = [
        col for col in df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
        if col.lower() not in METADATA_COLUMNS and not col.startswith('_')
    ]

    
    # Detect date column - Strategy 1: Check explicit datetime types
    date_column = None
    has_time_series = False
    
    datetime_cols = df.select_dtypes(include=['datetime', 'datetimetz']).columns.tolist()
    if datetime_cols:
        date_column = datetime_cols[0]
        has_time_series = True
    
    # Strategy 2: Content-based detection on object columns
    if not date_column:
        for col in df.select_dtypes(include=['object', 'string']).columns:
            try:
                sample = df[col].dropna().head(20)
                if not sample.empty:
                    parsed = pd.to_datetime(sample, errors='coerce')
                    if parsed.notna().sum() >= len(sample) * 0.7:  # 70% success
                        date_column = col
                        has_time_series = True
                        break
            except:
                continue
    
    # Content-based business column detection
    has_customer = False
    has_product = False
    has_amount = len(numeric_cols) > 0
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        if 10 < unique_count < 500:  # Likely entities
            has_customer = True
            has_product = True
            break
    
    unique_categories = {}
    for col in categorical_cols:
        try:
            unique_categories[col] = df[col].nunique()
        except:
            pass
    
    return DataProfile(
        has_date_column=date_column is not None,
        date_column=date_column,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        row_count=len(df),
        has_customer=has_customer,
        has_product=has_product,
        has_amount=has_amount,
        has_time_series=has_time_series,
        unique_categories=unique_categories
    )


# ============================================================================
# CHART TYPE SELECTION - Mapping intent + data to chart type
# ============================================================================

def select_chart_type(
    intent: VisualizationIntent,
    profile: DataProfile,
    user_role: str = "analyst"
) -> ChartType:
    """
    Select the best chart type based on intent and data profile.
    """
    # No data = no chart
    if profile.row_count == 0:
        return ChartType.NONE
    
    # No numeric columns = limited options
    if not profile.numeric_columns:
        return ChartType.NONE
    
    # Intent-based selection with data validation
    
    if intent == VisualizationIntent.TREND:
        if profile.has_time_series:
            return ChartType.LINE
        elif profile.row_count >= 3:
            return ChartType.LINE  # Can still show trend with order
        return ChartType.BAR  # Fallback
    
    if intent == VisualizationIntent.FORECAST:
        if profile.has_time_series:
            return ChartType.FORECAST
        return ChartType.BAR  # Can't forecast without time
    
    if intent == VisualizationIntent.COMPARISON:
        if profile.row_count <= 10:
            return ChartType.BAR
        elif profile.row_count <= 20:
            return ChartType.GROUPED_BAR if len(profile.categorical_columns) > 1 else ChartType.BAR
        return ChartType.BAR  # Too many = bar with top N
    
    if intent == VisualizationIntent.RANKING:
        return ChartType.BAR  # Always bar for rankings
    
    if intent == VisualizationIntent.PROPORTION:
        # Pie for small categories, bar for many
        max_categories = max(profile.unique_categories.values()) if profile.unique_categories else 0
        if max_categories <= 8:
            return ChartType.PIE
        return ChartType.BAR  # Too many slices = bar
    
    if intent == VisualizationIntent.DISTRIBUTION:
        if profile.row_count >= 10:
            return ChartType.BAR  # Histogram-style bar
        return ChartType.BAR
    
    if intent == VisualizationIntent.CORRELATION:
        if len(profile.numeric_columns) >= 2 and profile.row_count >= 10:
            return ChartType.SCATTER
        return ChartType.BAR  # Fallback
    
    if intent == VisualizationIntent.BREAKDOWN:
        if profile.has_time_series:
            return ChartType.STACKED_BAR
        return ChartType.PIE if len(profile.categorical_columns) == 1 else ChartType.BAR
    
    # Default based on data characteristics
    if profile.has_time_series:
        return ChartType.LINE
    elif profile.has_customer or profile.has_product:
        return ChartType.BAR
    
    return ChartType.BAR  # Safe default


# ============================================================================
# VALIDATION - Ensuring chart is appropriate
# ============================================================================

def validate_visualization(
    df: pd.DataFrame,
    chart_type: ChartType,
    x_col: Optional[str],
    y_col: Optional[str]
) -> Tuple[bool, str]:
    """
    Validate that the proposed visualization is appropriate.
    STRICT validation to ensure only REAL data is used.
    
    Returns: (is_valid, reason)
    """
    if df is None or df.empty:
        return False, "No data available for visualization"
    
    if chart_type == ChartType.NONE:
        return False, "No appropriate chart type for this data"
    
    # =========================================================================
    # STRICT DATA SOURCE VALIDATION - Prevent fake/hallucinated charts
    # =========================================================================
    
    # Verify X column exists and has data
    if x_col:
        if x_col not in df.columns:
            return False, f"X-axis column '{x_col}' not found in uploaded data"
        if df[x_col].isna().all():
            return False, f"X-axis column '{x_col}' contains only null values"
        if df[x_col].nunique() == 0:
            return False, f"X-axis column '{x_col}' has no unique values"
    
    # Verify Y column exists and has REAL numeric data
    if y_col:
        if y_col not in df.columns:
            return False, f"Y-axis column '{y_col}' not found in uploaded data"
        if df[y_col].isna().all():
            return False, f"Y-axis column '{y_col}' contains only null values"
        # For numeric y-axis, verify there are actual numbers
        if df[y_col].dtype in ['int64', 'float64', 'int32', 'float32']:
            non_null_count = df[y_col].notna().sum()
            if non_null_count == 0:
                return False, f"Y-axis column '{y_col}' has no numeric values"
    
    # =========================================================================
    # MINIMUM DATA POINTS
    # =========================================================================
    MIN_POINTS = {
        ChartType.LINE: 2,
        ChartType.BAR: 1,
        ChartType.PIE: 2,
        ChartType.SCATTER: 5,
        ChartType.FORECAST: 3,
        ChartType.HEATMAP: 4,
    }
    
    min_required = MIN_POINTS.get(chart_type, 2)
    if len(df) < min_required:
        return False, f"Insufficient data points (need at least {min_required}, have {len(df)})"
    
    # =========================================================================
    # CHART-SPECIFIC VALIDATION
    # =========================================================================
    
    # Pie chart slice limit
    if chart_type == ChartType.PIE:
        if x_col and x_col in df.columns:
            unique_count = df[x_col].nunique()
            if unique_count > 10:
                return False, f"Too many categories for pie chart ({unique_count}). Consider bar chart."
    
    # Scatter needs two numeric columns
    if chart_type == ChartType.SCATTER:
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if len(numeric_cols) < 2:
            return False, "Scatter plot requires at least 2 numeric columns"
    
    # Forecast needs time-series data
    if chart_type == ChartType.FORECAST:
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
        if not date_cols and x_col not in df.columns:
            return False, "Forecast chart requires time-series data with date column"
    
    return True, "Validation passed - data verified from uploaded source"


# ============================================================================
# COLUMN SELECTION - Finding the right columns for X and Y
# ============================================================================

def select_columns(
    df: pd.DataFrame,
    profile: DataProfile,
    intent: VisualizationIntent,
    x_hint: str = "auto",
    y_hint: str = "auto"
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Select appropriate columns for X, Y, and grouping.
    
    Returns: (x_column, y_column, group_column)
    """
    x_col = None
    y_col = None
    group_col = None
    
    # Y-axis: always a numeric column (metric)
    if y_hint == 'auto':
        # Priority: amount > total > revenue > first numeric
        for candidate in ['amount', 'total_amount', 'revenue', 'total', 'sales', 'value']:
            matching = [c for c in profile.numeric_columns if candidate in c.lower()]
            if matching:
                y_col = matching[0]
                break
        if not y_col and profile.numeric_columns:
            y_col = profile.numeric_columns[0]
    else:
        matching = [c for c in profile.numeric_columns if y_hint.lower() in c.lower()]
        y_col = matching[0] if matching else (profile.numeric_columns[0] if profile.numeric_columns else None)
    
    # X-axis: depends on intent
    if intent in [VisualizationIntent.TREND, VisualizationIntent.FORECAST]:
        x_col = profile.date_column
    elif intent == VisualizationIntent.RANKING:
        # PRIORITY: Match x_hint from query first, then fallback to defaults
        if x_hint == 'customer':
            # Flexible customer matching - check many variations
            customer_patterns = ['customer', 'account', 'client', 'company', 'name', 'buyer']
            for pattern in customer_patterns:
                matching = [c for c in profile.categorical_columns if pattern in c.lower()]
                if matching:
                    x_col = matching[0]
                    break
        elif x_hint == 'product':
            # Flexible product matching
            product_patterns = ['product', 'item', 'service', 'sku', 'goods']
            for pattern in product_patterns:
                matching = [c for c in profile.categorical_columns if pattern in c.lower()]
                if matching:
                    x_col = matching[0]
                    break
        
        # If x_hint didn't match with patterns, try LLM-based matching
        if not x_col and x_hint not in ['auto', 'date'] and profile.categorical_columns:
            # Use LLM to find the best matching column for the user's intent
            # Build a pseudo-query from the hint
            pseudo_query = f"show {x_hint}s" if x_hint else ""
            llm_matched = llm_match_column(pseudo_query, profile.categorical_columns)
            if llm_matched:
                x_col = llm_matched
                print(f"[VIZ] LLM matched x_hint '{x_hint}' to column '{x_col}'")
        
        # Final fallback: try default patterns
        if not x_col:
            for col, unique in profile.unique_categories.items():
                if 'customer' in col.lower() or 'product' in col.lower():
                    x_col = col
                    break
        if not x_col and profile.categorical_columns:
            x_col = profile.categorical_columns[0]
    else:
        # Match hint or use first categorical
        if x_hint == 'customer':
            customer_patterns = ['customer', 'account', 'client', 'company', 'name', 'buyer']
            for pattern in customer_patterns:
                matching = [c for c in profile.categorical_columns if pattern in c.lower()]
                if matching:
                    x_col = matching[0]
                    break
        elif x_hint == 'product':
            product_patterns = ['product', 'item', 'service', 'sku', 'goods']
            for pattern in product_patterns:
                matching = [c for c in profile.categorical_columns if pattern in c.lower()]
                if matching:
                    x_col = matching[0]
                    break
        elif x_hint == 'date':
            x_col = profile.date_column
        
        # LLM fallback for non-standard x_hint values
        if not x_col and x_hint not in ['auto', 'date', 'customer', 'product'] and profile.categorical_columns:
            pseudo_query = f"show {x_hint}s"
            llm_matched = llm_match_column(pseudo_query, profile.categorical_columns)
            if llm_matched:
                x_col = llm_matched
        
        if not x_col and profile.categorical_columns:
            x_col = profile.categorical_columns[0]
    
    # Group column for grouped/stacked charts
    if len(profile.categorical_columns) > 1:
        remaining = [c for c in profile.categorical_columns if c != x_col]
        if remaining:
            group_col = remaining[0]
    
    return x_col, y_col, group_col




# ============================================================================
# MAIN DECISION FUNCTION - The entry point
# ============================================================================

def decide_visualization(
    query: str,
    df: pd.DataFrame,
    user_role: str = "analyst"
) -> VisualizationDecision:
    """
    Main decision function for visualization.
    
    This is the single entry point that:
    1. Detects intent
    2. Profiles data
    3. Selects chart type
    4. Validates appropriateness
    5. Returns a complete decision
    """
    # Step 1: Detect intent
    intent, intent_confidence = detect_visualization_intent(query)
    
    # No visualization intent detected
    if intent == VisualizationIntent.NONE and intent_confidence < 0.3:
        return VisualizationDecision(
            should_render=False,
            chart_type=ChartType.NONE,
            intent=intent,
            x_column=None,
            y_column=None,
            group_column=None,
            title="",
            reason="No visualization intent detected in query",
            data_points=0,
            confidence=0
        )
    
    # Step 2: Profile data
    profile = profile_dataframe(df)
    
    if profile.row_count == 0:
        return VisualizationDecision(
            should_render=False,
            chart_type=ChartType.NONE,
            intent=intent,
            x_column=None,
            y_column=None,
            group_column=None,
            title="",
            reason="No data available for visualization",
            data_points=0,
            confidence=0
        )
    
    # Step 3: Get axis hints from query
    x_hint, y_hint = detect_visualization_subject(query)
    
    # Step 4: Check for EXPLICIT chart type in query first (user override)
    explicit_chart = extract_chart_type_from_query(query)
    
    if explicit_chart != 'auto':
        # User explicitly requested a chart type (e.g., "pie chart", "bar chart")
        chart_type_map = {
            'pie': ChartType.PIE,
            'bar': ChartType.BAR,
            'line': ChartType.LINE,
            'area': ChartType.AREA,
            'scatter': ChartType.SCATTER,
            'donut': ChartType.DONUT if hasattr(ChartType, 'DONUT') else ChartType.PIE,
        }
        chart_type = chart_type_map.get(explicit_chart, ChartType.BAR)
    else:
        # No explicit request - use intelligent selection based on intent
        chart_type = select_chart_type(intent, profile, user_role)
    
    # Step 5: Select columns
    x_col, y_col, group_col = select_columns(df, profile, intent, x_hint, y_hint)
    
    # Step 6: Validate
    is_valid, validation_reason = validate_visualization(df, chart_type, x_col, y_col)
    
    if not is_valid:
        return VisualizationDecision(
            should_render=False,
            chart_type=ChartType.NONE,
            intent=intent,
            x_column=x_col,
            y_column=y_col,
            group_column=group_col,
            title="",
            reason=validation_reason,
            data_points=profile.row_count,
            confidence=0
        )
    
    # Step 7: Generate title
    title = generate_chart_title(intent, chart_type, x_col, y_col, profile)
    
    # Calculate overall confidence
    overall_confidence = min(intent_confidence + 0.2, 1.0) if is_valid else 0
    
    return VisualizationDecision(
        should_render=True,
        chart_type=chart_type,
        intent=intent,
        x_column=x_col,
        y_column=y_col,
        group_column=group_col,
        title=title,
        reason="Visualization appropriate for query and data",
        data_points=profile.row_count,
        confidence=overall_confidence
    )


def generate_chart_title(
    intent: VisualizationIntent,
    chart_type: ChartType,
    x_col: Optional[str],
    y_col: Optional[str],
    profile: DataProfile
) -> str:
    """Generate a descriptive chart title."""
    
    y_name = y_col.replace('_', ' ').title() if y_col else "Value"
    x_name = x_col.replace('_', ' ').title() if x_col else ""
    
    if intent == VisualizationIntent.TREND:
        return f"📈 {y_name} Trend Over Time"
    elif intent == VisualizationIntent.COMPARISON:
        return f"📊 {y_name} Comparison by {x_name}"
    elif intent == VisualizationIntent.RANKING:
        return f"🏆 Top {x_name}s by {y_name}"
    elif intent == VisualizationIntent.PROPORTION:
        return f"📊 {y_name} Distribution"
    elif intent == VisualizationIntent.FORECAST:
        return f"🔮 {y_name} Forecast"
    elif intent == VisualizationIntent.CORRELATION:
        return f"📈 Correlation Analysis"
    elif intent == VisualizationIntent.BREAKDOWN:
        return f"📊 {y_name} Breakdown by {x_name}"
    else:
        return f"📊 {y_name} Analysis"


# ============================================================================
# ROLE-BASED CHART COMPLEXITY
# ============================================================================

def adjust_for_role(
    decision: VisualizationDecision,
    user_role: str,
    df: pd.DataFrame
) -> VisualizationDecision:
    """
    Adjust visualization decision based on user role.
    
    Executive → Simpler, high-level
    Analyst → Detailed, comparative
    Finance → Financial-focused
    """
    if not decision.should_render:
        return decision
    
    role_lower = user_role.lower() if user_role else "analyst"
    
    if role_lower == "executive":
        # Executives prefer simple charts
        if decision.chart_type == ChartType.GROUPED_BAR:
            decision.chart_type = ChartType.BAR
        if decision.chart_type == ChartType.STACKED_BAR:
            decision.chart_type = ChartType.BAR
        # Limit data points for clarity
        decision.reason += " (Simplified for executive view)"
    
    elif role_lower == "finance":
        # Finance prefers waterfall for breakdowns
        if decision.intent == VisualizationIntent.BREAKDOWN:
            decision.chart_type = ChartType.WATERFALL
            decision.title = decision.title.replace("Breakdown", "Financial Breakdown")
    
    return decision


# ============================================================================
# QUICK HELPERS
# ============================================================================

def should_show_chart(query: str, df: pd.DataFrame) -> bool:
    """Quick check if a chart should be shown for this query."""
    decision = decide_visualization(query, df)
    return decision.should_render


def get_chart_type_for_query(query: str, df: pd.DataFrame) -> str:
    """Get recommended chart type as string."""
    decision = decide_visualization(query, df)
    return decision.chart_type.value if decision.should_render else "none"


# ============================================================================
# LLM-POWERED VISUALIZATION DECISION - $5M Enterprise Quality
# ============================================================================

def llm_decide_visualization(query: str, data_summary: str) -> dict:
    """
    Use LLM to decide visualization when pattern matching is uncertain.
    
    This is the ChatGPT-quality fallback for complex visualization queries.
    
    Args:
        query: User's natural language query
        data_summary: Brief summary of available data columns
        
    Returns:
        dict with visualization decision
    """
    try:
        from core.llm import chat
        
        system_prompt = """You are a visualization expert for a Business Intelligence system.
Given a user query and available data, decide if and what type of chart to show.

Available chart types:
- bar: Comparisons, rankings, categories
- line: Trends over time, temporal patterns
- pie: Proportions, percentages (max 8 slices)
- scatter: Correlations between two metrics
- area: Cumulative trends
- none: No visualization needed (text answer only)

Respond with JSON only:
{
    "should_visualize": true/false,
    "chart_type": "bar|line|pie|scatter|area|none",
    "x_axis": "column name or 'auto'",
    "y_axis": "column name or 'auto'",
    "title": "suggested chart title",
    "reason": "why this visualization"
}"""

        user_prompt = f"""Query: "{query}"

Available data columns: {data_summary}

What visualization (if any) should I show?"""

        response = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.1,
            max_tokens=300
        )
        
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception as e:
        print(f"[VIZ] LLM decision failed: {e}")
    
    return {"should_visualize": False, "chart_type": "none", "reason": "LLM fallback failed"}


def create_chart_from_decision(
    decision: VisualizationDecision,
    df: pd.DataFrame,
    currency_symbol: str = "₹",
    user_role: str = "analyst"
) -> dict:
    """
    Generate a Plotly chart payload from a VisualizationDecision.
    
    This bridges the decision layer with the chart generation layer.
    """
    if not decision.should_render:
        return {"error": decision.reason}
    
    try:
        # Import chart generator
        from agents.advanced_charts import (
            generate_revenue_bar_chart,
            generate_pie_chart,
            generate_trend_chart,
            generate_prediction_chart
        )
        
        chart_type = decision.chart_type
        x_col = decision.x_column
        y_col = decision.y_column
        title = decision.title
        
        # CRITICAL: Extract limit from query if available
        query_limit = None
        if hasattr(decision, 'query') and decision.query:
            import re
            count_patterns = [
                r'top\s+(\d+)', r'bottom\s+(\d+)', r'best\s+(\d+)',
                r'worst\s+(\d+)', r'(\d+)\s+customers?', r'(\d+)\s+products?'
            ]
            for pattern in count_patterns:
                match = re.search(pattern, decision.query.lower())
                if match:
                    query_limit = int(match.group(1))
                    break
        
        # Use query limit, then decision limit, then default 10
        limit = query_limit or (decision.limit if hasattr(decision, 'limit') else 10)
        print(f"[CHART LIMIT] Query limit: {query_limit}, Using: {limit}")

        
        # Apply limit to data
        if decision.intent == VisualizationIntent.RANKING and limit:
            if x_col and y_col:
                # Sort and take top N
                df_sorted = df.copy()
                if y_col in df_sorted.columns:
                    grouped = df_sorted.groupby(x_col)[y_col].sum().sort_values(ascending=False).head(limit)
                    df = pd.DataFrame({x_col: grouped.index, y_col: grouped.values})
        
        if chart_type == ChartType.BAR:
            return generate_revenue_bar_chart(
                df, x_col, y_col, 
                title=title,
                currency_symbol=currency_symbol,
                limit=limit
            )
        elif chart_type == ChartType.PIE:
            return generate_pie_chart(
                df, x_col, y_col,
                title=title,
                currency_symbol=currency_symbol,
                limit=limit  # CRITICAL: Pass limit to ensure correct count
            )

        elif chart_type == ChartType.LINE:
            return generate_trend_chart(
                df, x_col, y_col,
                title=title,
                currency_symbol=currency_symbol
            )
        elif chart_type == ChartType.FORECAST:
            return generate_prediction_chart(
                df, x_col, y_col,
                title=title,
                currency_symbol=currency_symbol
            )
        else:
            # Default to bar chart
            return generate_revenue_bar_chart(
                df, x_col, y_col,
                title=title,
                currency_symbol=currency_symbol,
                limit=limit
            )
            
    except Exception as e:
        print(f"[VIZ] Chart generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


def generate_dynamic_chart(
    query: str,
    df: pd.DataFrame,
    currency_symbol: str = "₹",
    user_role: str = "analyst"
) -> tuple:
    """
    High-level function to generate a chart dynamically based on query intent.
    
    This is the main entry point for the visualization system.
    
    Returns:
        (chart_payload, info_string)
    """
    if df is None or df.empty:
        return None, "No data available for visualization"
    
    # Get visualization decision
    decision = decide_visualization(query, df, user_role)
    
    if not decision.should_render:
        return None, decision.reason
    
    # Apply role adjustments
    decision = adjust_for_role(decision, user_role, df)
    
    # Generate chart
    chart_payload = create_chart_from_decision(
        decision, df, currency_symbol, user_role
    )
    
    if chart_payload and not chart_payload.get("error"):
        return chart_payload, f"Generated {decision.chart_type.value} chart: {decision.title}"
    
    return None, chart_payload.get("error", "Chart generation failed")
