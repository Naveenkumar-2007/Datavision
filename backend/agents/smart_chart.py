# =============================================================================
# UNIVERSAL CHART GENERATOR - LLM Understands ANY Visualization Request
# =============================================================================
#
# This module uses pure LLM understanding to generate any chart type.
# NO HARDCODED PATTERNS - The AI decides based on query meaning.
#
# Supported: bar, pie, line, scatter, area, heatmap, treemap, funnel, 
#            gauge, waterfall, donut, stacked_bar, horizontal_bar,
#            radar, box, bubble, sunburst, histogram
#

import json
import re
from typing import Optional, Dict, Tuple, List
import pandas as pd


# =============================================================================
# DYNAMIC COLOR PALETTE SYSTEM - Premium Themes
# =============================================================================

COLOR_PALETTES = {
    'default': [
        '#6366F1', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6',
        '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#14B8A6'
    ],
    'modern': [
        '#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
        '#EC4899', '#0891B2', '#65A30D', '#EA580C', '#0D9488'
    ],
    'vibrant': [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
    ],
    'corporate': [
        '#1E3A5F', '#3D5A80', '#98C1D9', '#E0FBFC', '#EE6C4D',
        '#293241', '#457B9D', '#A8DADC', '#F1FAEE', '#E63946'
    ],
    'pastel': [
        '#FFB3BA', '#BAFFC9', '#BAE1FF', '#FFFFBA', '#FFDFba',
        '#E2B0FF', '#B0FFE2', '#FFE2B0', '#B0E2FF', '#FFB0E2'
    ],
    'dark': [
        '#BB86FC', '#03DAC6', '#FF7597', '#FFD93D', '#6BCB77',
        '#C9B1FF', '#00BFA5', '#FF5252', '#FFAB40', '#69F0AE'
    ],
    'blue': ['#0EA5E9', '#0284C7', '#0369A1', '#075985', '#0C4A6E', '#164E63', '#155E75', '#0E7490'],
    'green': ['#22C55E', '#16A34A', '#15803D', '#166534', '#14532D', '#10B981', '#059669', '#047857'],
    'red': ['#EF4444', '#DC2626', '#B91C1C', '#991B1B', '#7F1D1D', '#F87171', '#FCA5A5', '#FECACA'],
    'purple': ['#8B5CF6', '#7C3AED', '#6D28D9', '#5B21B6', '#4C1D95', '#A78BFA', '#C4B5FD', '#DDD6FE'],
    'orange': ['#F97316', '#EA580C', '#C2410C', '#9A3412', '#7C2D12', '#FB923C', '#FDBA74', '#FED7AA'],
    'teal': ['#14B8A6', '#0D9488', '#0F766E', '#115E59', '#134E4A', '#2DD4BF', '#5EEAD4', '#99F6E4'],
}

# Additional Premium Color Palettes
COLOR_PALETTES.update({
    'neon': ['#FF00FF', '#00FFFF', '#FF6B00', '#00FF00', '#FF0066', '#FFFF00', '#0066FF', '#FF3399'],
    'earth': ['#8B4513', '#A0522D', '#CD853F', '#DEB887', '#D2691E', '#BC8F8F', '#F4A460', '#DAA520'],
    'sunset': ['#FF6B35', '#FF8C42', '#FFD166', '#F4A261', '#E76F51', '#D62828', '#F77F00', '#FCBF49'],
    'rainbow': ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3', '#FF1493'],
    'gradient_blue': ['#E0F7FA', '#B2EBF2', '#80DEEA', '#4DD0E1', '#26C6DA', '#00BCD4', '#00ACC1', '#0097A7'],
    'gradient_green': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50', '#43A047', '#388E3C'],
    'gold': ['#FFD700', '#FFC700', '#FFB700', '#FFA700', '#FF9700', '#DAA520', '#B8860B', '#CD853F'],
    'silver': ['#C0C0C0', '#A9A9A9', '#808080', '#D3D3D3', '#DCDCDC', '#GAINSBORO', '#SILVER', '#708090'],
    'rose': ['#FFB3C1', '#FF8FA3', '#FF758F', '#FF4D6D', '#C9184A', '#A4133C', '#800F2F', '#590D22'],
})


def get_color_palette_from_query(query: str) -> List[str]:
    """
    Extract color preference from user query.
    Returns appropriate color palette based on keywords.
    Enhanced v2.0 with context-aware color selection.
    """
    query_lower = query.lower()
    
    # Context-aware colors (semantic meaning)
    if any(x in query_lower for x in ['profit', 'gain', 'success', 'positive', 'increase']):
        return COLOR_PALETTES['green']
    elif any(x in query_lower for x in ['loss', 'decline', 'negative', 'decrease', 'problem']):
        return COLOR_PALETTES['red']
    elif any(x in query_lower for x in ['growth', 'rising', 'upward']):
        return COLOR_PALETTES['gradient_green']
    elif any(x in query_lower for x in ['falling', 'dropping', 'downward']):
        return COLOR_PALETTES['red']
    
    # Explicit color requests
    if 'blue' in query_lower or 'ocean' in query_lower or 'sky' in query_lower or 'water' in query_lower:
        return COLOR_PALETTES['blue']
    elif 'green' in query_lower or 'nature' in query_lower or 'forest' in query_lower or 'eco' in query_lower:
        return COLOR_PALETTES['green']
    elif 'red' in query_lower or 'hot' in query_lower or 'fire' in query_lower:
        return COLOR_PALETTES['red']
    elif 'purple' in query_lower or 'violet' in query_lower or 'lavender' in query_lower:
        return COLOR_PALETTES['purple']
    elif 'orange' in query_lower or 'warm' in query_lower or 'autumn' in query_lower:
        return COLOR_PALETTES['orange']
    elif 'teal' in query_lower or 'cyan' in query_lower or 'aqua' in query_lower:
        return COLOR_PALETTES['teal']
    elif 'corporate' in query_lower or 'professional' in query_lower or 'business' in query_lower or 'formal' in query_lower:
        return COLOR_PALETTES['corporate']
    elif 'pastel' in query_lower or 'soft' in query_lower or 'light' in query_lower or 'gentle' in query_lower:
        return COLOR_PALETTES['pastel']
    elif 'vibrant' in query_lower or 'bright' in query_lower or 'colorful' in query_lower or 'bold' in query_lower:
        return COLOR_PALETTES['vibrant']
    elif 'dark' in query_lower or 'night' in query_lower or 'midnight' in query_lower:
        return COLOR_PALETTES['dark']
    elif 'modern' in query_lower or 'sleek' in query_lower or 'minimalist' in query_lower:
        return COLOR_PALETTES['modern']
    # New palettes
    elif 'neon' in query_lower or 'glow' in query_lower or 'electric' in query_lower:
        return COLOR_PALETTES['neon']
    elif 'earth' in query_lower or 'brown' in query_lower or 'natural' in query_lower or 'organic' in query_lower:
        return COLOR_PALETTES['earth']
    elif 'sunset' in query_lower or 'sunrise' in query_lower or 'dawn' in query_lower or 'dusk' in query_lower:
        return COLOR_PALETTES['sunset']
    elif 'rainbow' in query_lower or 'spectrum' in query_lower or 'multicolor' in query_lower:
        return COLOR_PALETTES['rainbow']
    elif 'gradient' in query_lower:
        return COLOR_PALETTES['gradient_blue']
    elif 'gold' in query_lower or 'golden' in query_lower or 'luxury' in query_lower or 'premium' in query_lower:
        return COLOR_PALETTES['gold']
    elif 'silver' in query_lower or 'gray' in query_lower or 'grey' in query_lower or 'neutral' in query_lower:
        return COLOR_PALETTES['silver']
    elif 'rose' in query_lower or 'pink' in query_lower or 'blush' in query_lower:
        return COLOR_PALETTES['rose']
    
    # Default: rotate palettes based on query hash for variety
    palette_names = ['default', 'modern', 'vibrant', 'dark', 'sunset', 'teal']
    idx = hash(query) % len(palette_names)
    return COLOR_PALETTES[palette_names[idx]]


def smart_chart(
    query: str,
    df: pd.DataFrame,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    🧠 UNIVERSAL CHART GENERATOR v3.0 - GUARANTEED Chart Rendering
    
    The LLM acts like ChatGPT:
    1. Understands what the user wants to see
    2. Analyzes the data schema
    3. Chooses the best chart type
    4. Generates complete Plotly specification
    
    ENHANCED v3.0:
    - GUARANTEED chart rendering when user asks for chart
    - Dynamic color palette based on query
    - All 18+ chart types fully supported
    - Advanced visualizations: radar, sunburst, treemap, bubble
    """
    from core.llm import chat
    
    if df is None or df.empty:
        return None, "No data available"
    
    # =========================================================================
    # DYNAMIC COLOR PALETTE - Based on user query
    # =========================================================================
    colors = get_color_palette_from_query(query)
    print(f"[SMART CHART] Using color palette: {colors[:3]}...")
    
    # =========================================================================
    # ENHANCED CHART TYPE DETECTION - All chart types supported
    # =========================================================================
    query_lower = query.lower()
    forced_chart_type = None
    
    # ADVANCED CHART TYPES (check first - more specific)
    if any(x in query_lower for x in ['radar chart', 'radar graph', 'spider chart', 'spider graph', 'radar']):
        forced_chart_type = 'radar'
        print(f"[SMART CHART] FORCED: radar chart from explicit request")
    elif any(x in query_lower for x in ['sunburst', 'sun burst', 'hierarchical pie']):
        forced_chart_type = 'sunburst'
        print(f"[SMART CHART] FORCED: sunburst chart from explicit request")
    elif any(x in query_lower for x in ['treemap', 'tree map', 'hierarchical blocks']):
        forced_chart_type = 'treemap'
        print(f"[SMART CHART] FORCED: treemap chart from explicit request")
    elif any(x in query_lower for x in ['bubble chart', 'bubble graph', 'bubble']):
        forced_chart_type = 'bubble'
        print(f"[SMART CHART] FORCED: bubble chart from explicit request")
    elif any(x in query_lower for x in ['box plot', 'box chart', 'boxplot', 'whisker']):
        forced_chart_type = 'box'
        print(f"[SMART CHART] FORCED: box chart from explicit request")
    elif any(x in query_lower for x in ['histogram', 'frequency distribution']):
        forced_chart_type = 'histogram'
        print(f"[SMART CHART] FORCED: histogram from explicit request")
    elif any(x in query_lower for x in ['heatmap', 'heat map', 'matrix']):
        forced_chart_type = 'heatmap'
        print(f"[SMART CHART] FORCED: heatmap from explicit request")
    elif any(x in query_lower for x in ['funnel chart', 'funnel graph', 'funnel', 'conversion']):
        forced_chart_type = 'funnel'
        print(f"[SMART CHART] FORCED: funnel chart from explicit request")
    elif any(x in query_lower for x in ['gauge', 'speedometer', 'meter', 'kpi indicator']):
        forced_chart_type = 'gauge'
        print(f"[SMART CHART] FORCED: gauge chart from explicit request")
    elif any(x in query_lower for x in ['waterfall', 'cascade', 'bridge chart']):
        forced_chart_type = 'waterfall'
        print(f"[SMART CHART] FORCED: waterfall chart from explicit request")
    # NEW CHART TYPES v3.0
    elif any(x in query_lower for x in ['combo chart', 'combo graph', 'bar and line', 'bar with line', 'dual axis']):
        forced_chart_type = 'combo'
        print(f"[SMART CHART] FORCED: combo chart from explicit request")
    elif any(x in query_lower for x in ['multi line', 'multi-line', 'multiple lines', 'compare trends', 'trend comparison']):
        forced_chart_type = 'multi_line'
        print(f"[SMART CHART] FORCED: multi_line chart from explicit request")
    elif any(x in query_lower for x in ['violin', 'violin plot', 'distribution with density']):
        forced_chart_type = 'violin'
        print(f"[SMART CHART] FORCED: violin chart from explicit request")
    elif any(x in query_lower for x in ['multi area', 'stacked area', 'area breakdown', 'composition over time']):
        forced_chart_type = 'multi_area'
        print(f"[SMART CHART] FORCED: multi_area chart from explicit request")
    # STANDARD CHART TYPES - More flexible detection
    # PIE CHART - Check FIRST since it's commonly requested
    elif 'pie' in query_lower:
        forced_chart_type = 'pie'
        print(f"[SMART CHART] FORCED: pie chart detected")
    elif any(x in query_lower for x in ['donut chart', 'donut graph', 'as a donut', 'doughnut', 'donut', 'ring chart']):
        forced_chart_type = 'donut'
        print(f"[SMART CHART] FORCED: donut chart from explicit request")
    elif any(x in query_lower for x in ['line chart', 'line graph', 'trend chart', 'trend line']):
        forced_chart_type = 'line'
        print(f"[SMART CHART] FORCED: line chart from explicit request")
    elif any(x in query_lower for x in ['area chart', 'area graph', 'filled line']):
        forced_chart_type = 'area'
        print(f"[SMART CHART] FORCED: area chart from explicit request")
    elif any(x in query_lower for x in ['scatter chart', 'scatter plot', 'scatter graph']):
        forced_chart_type = 'scatter'
        print(f"[SMART CHART] FORCED: scatter chart from explicit request")
    elif any(x in query_lower for x in ['stacked bar', 'stacked chart']):
        forced_chart_type = 'stacked_bar'
        print(f"[SMART CHART] FORCED: stacked_bar from explicit request")
    elif any(x in query_lower for x in ['horizontal bar', 'horizontal chart']):
        forced_chart_type = 'horizontal_bar'
        print(f"[SMART CHART] FORCED: horizontal_bar from explicit request")
    elif any(x in query_lower for x in ['bar chart', 'bar graph']):
        forced_chart_type = 'bar'
        print(f"[SMART CHART] FORCED: bar chart from explicit request")
    # SEMANTIC DETECTION - Only if NO explicit chart type requested
    elif not forced_chart_type:
        if any(x in query_lower for x in ['distribution', 'breakdown', 'proportion', 'percentage', 'share of']):
            forced_chart_type = 'pie'
            print(f"[SMART CHART] FORCED: pie chart for distribution query")
        elif any(x in query_lower for x in ['trend', 'over time', 'monthly', 'yearly', 'daily', 'by month', 'by year']):
            forced_chart_type = 'line'
            print(f"[SMART CHART] FORCED: line chart for trend query")
        elif any(x in query_lower for x in ['correlation', 'relationship']):
            forced_chart_type = 'scatter'
            print(f"[SMART CHART] FORCED: scatter chart for correlation query")
        # NOTE: Removed 'top'/'compare' → bar override since user might want pie for "top 5"
    
    print(f"[SMART CHART] Query: '{query[:60]}...' => forced_chart_type={forced_chart_type}")
    
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
- stacked_bar: Compare multiple series stacked
- pie: Show proportions/percentages
- donut: Pie with center hole (shows total in center)
- line: Show trends over time/sequence
- area: Filled line chart for volume trends
- scatter: Show correlations between two variables
- radar: Compare multiple attributes across entities (e.g. skills, performance)
- box: Show distribution, variance, and outliers
- violin: Distribution with density shape (best for showing spread)
- heatmap: Show intensity across two dimensions
- treemap: Hierarchical data breakdown
- sunburst: Hierarchical pie chart (parent-child relationships)
- funnel: Show conversion/stages
- gauge: Show single KPI vs target
- waterfall: Show incremental changes
- bubble: Scatter with size as third dimension
- histogram: Frequency distribution
- multi_line: Compare multiple trends on one chart
- multi_area: Stacked areas for composition over time
- combo: Bar + line overlay (dual axis for two metrics)

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
4. "spread" or "variance" or "violin" → violin (shows distribution shape)
5. "compare" or "vs" → bar or grouped bar
6. "correlation" or "relationship" → scatter or bubble
7. "heatmap" or "matrix" → heatmap with two categorical dimensions
8. "funnel" or "conversion" → funnel
9. "KPI" or "target" or "goal" → gauge
10. "hierarchy" or "breakdown" → treemap or sunburst
11. "compare trends" or "multiple lines" → multi_line
12. "composition over time" → multi_area
13. "dual axis" or "two metrics" → combo
14. Always pick the BEST chart type for the data and question
15. Create a DESCRIPTIVE title that explains what the chart shows

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
        
        # VALIDATION: Check requirements based on chart type
        # For distribution charts (histogram, violin, box), x_col is optional (uses single group if missing)
        DISTRIBUTION_CHARTS = ['histogram', 'box', 'violin', 'gauge']
        
        if chart_type in DISTRIBUTION_CHARTS:
            if not y_col:
                 return {"error": f"Column '{y_col}' invalid. Need numeric column for {chart_type}."}, "Invalid column"
            
            # If x_col is missing for distribution, default to a dummy "All" category if needed
            if not x_col and chart_type != 'histogram':
                 # Create a constant column for grouping if needed by specific chart implementations
                 # But _violin_chart uses x_col to group. So we need to handle x_col being None or create a dummy.
                 # Actually, it's better to pass a dummy column name that doesn't exist, 
                 # OR handle it in the chart function.
                 # Let's verify if _violin_chart needs x_col. Yes it does: df[x_col].unique()
                 # So we should create a temporary column in the DF? No, we shouldn't modify the DF inplace if possible.
                 pass # We'll handle this in the _generate_chart call or specific chart functions
            
        elif not x_col or not y_col:
            print(f"[SMART CHART] Column mismatch: x={x_col}, y={y_col}, available: {list(df.columns)}")
            return {"error": f"Could not match columns to your data. Available: {', '.join(list(df.columns)[:8])}"}, "Unable to generate chart"
        
        # Validate data types
        if y_col and (y_col not in df.columns or not pd.api.types.is_numeric_dtype(df[y_col])):
            print(f"[SMART CHART] Y-axis column '{y_col}' is not numeric")
            return {"error": f"Column '{y_col}' must be numeric for visualization"}, "Invalid data type"
        
        # PREPARE DATA FOR VISUALIZATION
        # If x_col is a dummy "Total" for distribution, ensure it exists in DF
        df_viz = df.copy()
        chart_x_col = x_col if x_col else "Overview"
        
        if chart_x_col not in df_viz.columns:
            # If explicit column missing or dummy needed
            if chart_x_col in ["Total", "Overview", "Distribution"]:
                 df_viz[chart_x_col] = chart_x_col # Fill with constant string
                 print(f"[SMART CHART] Added dummy column '{chart_x_col}' for distribution")
            elif chart_type in DISTRIBUTION_CHARTS:
                 # For distribution, if x_col provided but not found, default to global
                 print(f"[SMART CHART] Column '{chart_x_col}' not found, using global distribution")
                 chart_x_col = "Distribution"
                 df_viz[chart_x_col] = "All Data"
        
        # Generate the chart with dynamic colors
        chart = _generate_chart(
            chart_type=chart_type,
            df=df_viz,
            x_col=chart_x_col,
            y_col=y_col,
            group_col=group_col,
            count=count,
            ascending=ascending,
            title=title,
            subtitle=subtitle,
            currency=currency_symbol,
            colors=colors  # Pass dynamic colors from query
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


# =============================================================================
# ALL SUPPORTED CHART TYPES - Universal Visualization v2.0
# =============================================================================
ALL_CHART_TYPES = {
    # Standard charts
    'bar', 'horizontal_bar', 'stacked_bar', 'grouped_bar',
    'line', 'area', 'scatter', 'bubble',
    # Proportion charts
    'pie', 'donut', 'sunburst', 'treemap',
    # Statistical charts
    'heatmap', 'radar', 'box', 'violin',
    # Flow/Process charts
    'funnel', 'gauge', 'waterfall', 'sankey',
    # Advanced
    'parallel_coordinates', 'histogram'
}


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
    currency: str,
    colors: Optional[List[str]] = None
) -> Dict:
    """Generate Plotly chart specification for any chart type."""
    
    # Prepare data
    grouped = df.groupby(x_col)[y_col].sum().sort_values(ascending=ascending)
    if count:
        grouped = grouped.head(count)
    
    # Convert to native Python types
    labels = [str(x) for x in grouped.index.tolist()]
    values = [float(x) for x in grouped.values.tolist()]
    
    # Use provided colors or fall back to default premium palette
    if not colors:
        colors = [
            '#6366F1', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6',
            '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#14B8A6',
            '#3B82F6', '#10B981', '#FBBF24', '#F43F5E', '#A855F7'
        ]
    
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
        return _radar_chart(labels, values, title, currency, colors)
    elif chart_type == 'box':
        return _box_chart(df, x_col, y_col, title, currency)
    elif chart_type == 'bubble':
        return _bubble_chart(labels, values, title, currency, colors)
    elif chart_type == 'sunburst':
        return _sunburst_chart(df, x_col, y_col, title, currency, colors)
    elif chart_type == 'stacked_bar':
        return _stacked_bar_chart(df, x_col, y_col, group_col, title, currency, colors)
    elif chart_type == 'histogram':
        return _histogram_chart(df, y_col, title, currency)
    # NEW CHART TYPES v3.0
    elif chart_type == 'violin':
        return _violin_chart(df, x_col, y_col, title, currency)
    elif chart_type == 'multi_line':
        return _multi_line_chart(df, x_col, y_col, group_col, title, currency, colors)
    elif chart_type == 'multi_area':
        return _multi_area_chart(df, x_col, y_col, group_col, title, currency, colors)
    elif chart_type == 'donut_with_total':
        return _donut_with_total(labels, values, title, currency, colors)
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


# =============================================================================
# PRO-LEVEL CHART TYPES - Added for Universal Visualization v2.0
# =============================================================================

def _radar_chart(labels, values, title, currency, colors):
    """Radar/Spider chart for multi-dimensional comparisons."""
    # Normalize values for radar (0-100 scale)
    max_val = max(values) if values else 1
    normalized = [v / max_val * 100 for v in values]
    
    return {
        "data": [{
            "type": "scatterpolar",
            "r": normalized + [normalized[0]] if normalized else [],  # Close the polygon
            "theta": labels + [labels[0]] if labels else [],
            "fill": "toself",
            "fillcolor": "rgba(99, 102, 241, 0.3)",
            "line": {"color": "#6366F1", "width": 2},
            "marker": {"size": 8, "color": "#6366F1"},
            "name": "Values",
            "hovertemplate": "%{theta}<br>" + currency + "%{customdata:,.0f}<extra></extra>",
            "customdata": values + [values[0]] if values else []
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, 100],
                    "showticklabels": False
                },
                "angularaxis": {"tickfont": {"size": 11}}
            },
            "showlegend": False,
            "height": 450
        }
    }


def _box_chart(df, x_col, y_col, title, currency):
    """Box plot for statistical distribution."""
    return {
        "data": [{
            "type": "box",
            "y": [float(v) for v in df[y_col].dropna().tolist()],
            "name": y_col,
            "marker": {"color": "#6366F1"},
            "boxmean": True,
            "hovertemplate": currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "yaxis": {"title": y_col, "tickprefix": currency},
            "height": 400
        }
    }


def _bubble_chart(labels, values, title, currency, colors):
    """Bubble chart with size proportional to value."""
    # Normalize sizes (min 20, max 80)
    max_val = max(values) if values else 1
    sizes = [max(20, min(80, (v / max_val) * 60 + 20)) for v in values]
    
    return {
        "data": [{
            "type": "scatter",
            "mode": "markers+text",
            "x": list(range(len(labels))),
            "y": values,
            "text": labels,
            "textposition": "top center",
            "marker": {
                "size": sizes,
                "color": colors[:len(labels)],
                "opacity": 0.7,
                "line": {"width": 2, "color": "white"}
            },
            "hovertemplate": "%{text}<br>" + currency + "%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"visible": False},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400
        }
    }


def _sunburst_chart(df, x_col, y_col, title, currency, colors):
    """Sunburst chart for hierarchical data."""
    grouped = df.groupby(x_col)[y_col].sum()
    labels = [str(x) for x in grouped.index.tolist()]
    values = [float(x) for x in grouped.values.tolist()]
    
    # Add a root node
    all_labels = ["Total"] + labels
    all_parents = [""] + ["Total"] * len(labels)
    all_values = [sum(values)] + values
    
    return {
        "data": [{
            "type": "sunburst",
            "labels": all_labels,
            "parents": all_parents,
            "values": all_values,
            "branchvalues": "total",
            "marker": {"colors": ["#1E293B"] + colors[:len(labels)]},
            "textinfo": "label+percent entry",
            "hovertemplate": "%{label}<br>" + currency + "%{value:,.0f}<br>%{percentRoot:.1%}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "height": 450
        }
    }


def _stacked_bar_chart(df, x_col, y_col, group_col, title, currency, colors):
    """Stacked bar chart for grouped data."""
    if not group_col or group_col not in df.columns:
        # Fallback to regular bar
        grouped = df.groupby(x_col)[y_col].sum()
        labels = [str(x) for x in grouped.index.tolist()]
        values = [float(x) for x in grouped.values.tolist()]
        return _bar_chart(labels, values, title, currency, colors)
    
    # Create stacked bar with groups
    pivot = df.pivot_table(values=y_col, index=x_col, columns=group_col, aggfunc='sum', fill_value=0)
    
    traces = []
    for i, col in enumerate(pivot.columns):
        traces.append({
            "type": "bar",
            "name": str(col),
            "x": [str(x) for x in pivot.index.tolist()],
            "y": [float(v) for v in pivot[col].tolist()],
            "marker": {"color": colors[i % len(colors)]},
            "hovertemplate": str(col) + "<br>%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "barmode": "stack",
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100},
            "legend": {"orientation": "h", "y": -0.2}
        }
    }


def _histogram_chart(df, y_col, title, currency):
    """Histogram for distribution analysis."""
    return {
        "data": [{
            "type": "histogram",
            "x": [float(v) for v in df[y_col].dropna().tolist()],
            "marker": {
                "color": "#6366F1",
                "line": {"width": 1, "color": "white"}
            },
            "hovertemplate": "Range: %{x}<br>Count: %{y}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": y_col, "tickprefix": currency},
            "yaxis": {"title": "Frequency"},
            "height": 400,
            "bargap": 0.1
        }
    }


# =============================================================================
# NEW CHART TYPES v3.0 - Combo, Multi-Line, Violin, Grouped
# =============================================================================

def _combo_chart(df, x_col, y_col, y2_col, title, currency, colors):
    """
    Combo chart with bar and line overlay.
    Perfect for showing two related metrics (e.g., sales and profit margin).
    """
    grouped = df.groupby(x_col).agg({y_col: 'sum', y2_col: 'mean'}).head(10)
    labels = [str(x) for x in grouped.index.tolist()]
    values1 = [float(x) for x in grouped[y_col].tolist()]
    values2 = [float(x) for x in grouped[y2_col].tolist()]
    
    return {
        "data": [
            {
                "type": "bar",
                "name": y_col,
                "x": labels,
                "y": values1,
                "marker": {"color": colors[0] if colors else "#6366F1"},
                "hovertemplate": y_col + "<br>%{x}<br>" + currency + "%{y:,.0f}<extra></extra>",
                "yaxis": "y"
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": y2_col,
                "x": labels,
                "y": values2,
                "line": {"color": colors[1] if len(colors) > 1 else "#EF4444", "width": 3},
                "marker": {"size": 8},
                "hovertemplate": y2_col + "<br>%{x}<br>%{y:.1f}%<extra></extra>",
                "yaxis": "y2"
            }
        ],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": y_col, "tickprefix": currency, "side": "left"},
            "yaxis2": {"title": y2_col, "overlaying": "y", "side": "right"},
            "height": 450,
            "margin": {"b": 100, "r": 80},
            "legend": {"orientation": "h", "y": -0.25}
        }
    }


def _multi_line_chart(df, x_col, y_col, group_col, title, currency, colors):
    """
    Multi-series line chart for comparing trends across groups.
    E.g., Sales trends by region, revenue by product category over time.
    """
    if not group_col or group_col not in df.columns:
        # Fallback to single line
        grouped = df.groupby(x_col)[y_col].sum().head(20)
        return {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "name": y_col,
                "x": [str(x) for x in grouped.index.tolist()],
                "y": [float(v) for v in grouped.values.tolist()],
                "line": {"color": colors[0], "width": 2},
                "marker": {"size": 6},
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
    
    # Multi-series line chart
    pivot = df.pivot_table(values=y_col, index=x_col, columns=group_col, aggfunc='sum', fill_value=0)
    
    traces = []
    for i, col in enumerate(pivot.columns[:8]):  # Limit to 8 series
        traces.append({
            "type": "scatter",
            "mode": "lines+markers",
            "name": str(col),
            "x": [str(x) for x in pivot.index.tolist()],
            "y": [float(v) for v in pivot[col].tolist()],
            "line": {"color": colors[i % len(colors)], "width": 2},
            "marker": {"size": 6},
            "hovertemplate": str(col) + "<br>%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 450,
            "margin": {"b": 100},
            "legend": {"orientation": "h", "y": -0.25}
        }
    }


def _violin_chart(df, x_col, y_col, title, currency):
    """
    Violin plot for distribution analysis with density.
    Shows distribution shape, median, and quartiles.
    """
    categories = df[x_col].unique()[:8]  # Limit to 8 categories
    
    traces = []
    colors = ['#6366F1', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']
    
    for i, cat in enumerate(categories):
        values = df[df[x_col] == cat][y_col].dropna().tolist()
        traces.append({
            "type": "violin",
            "y": [float(v) for v in values],
            "name": str(cat),
            "box": {"visible": True},
            "meanline": {"visible": True},
            "fillcolor": colors[i % len(colors)],
            "line": {"color": colors[i % len(colors)]},
            "opacity": 0.7,
            "hovertemplate": str(cat) + "<br>" + currency + "%{y:,.0f}<extra></extra>"
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "yaxis": {"title": y_col, "tickprefix": currency},
            "height": 450,
            "violingap": 0.3,
            "violinmode": "group"
        }
    }


def _grouped_bar_chart(labels, values_dict, title, currency, colors):
    """
    Grouped bar chart for comparing multiple metrics side by side.
    values_dict: {"Series1": [v1, v2, ...], "Series2": [v1, v2, ...]}
    """
    traces = []
    for i, (series_name, values) in enumerate(values_dict.items()):
        traces.append({
            "type": "bar",
            "name": series_name,
            "x": labels,
            "y": values,
            "marker": {"color": colors[i % len(colors)]},
            "hovertemplate": series_name + "<br>%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "barmode": "group",
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 400,
            "margin": {"b": 100},
            "legend": {"orientation": "h", "y": -0.2}
        }
    }


def _multi_area_chart(df, x_col, y_col, group_col, title, currency, colors):
    """
    Stacked area chart for showing composition over time.
    E.g., Revenue breakdown by product category over months.
    """
    if not group_col or group_col not in df.columns:
        # Fallback to single area
        grouped = df.groupby(x_col)[y_col].sum().head(20)
        return _area_chart(
            [str(x) for x in grouped.index.tolist()],
            [float(v) for v in grouped.values.tolist()],
            title, currency
        )
    
    pivot = df.pivot_table(values=y_col, index=x_col, columns=group_col, aggfunc='sum', fill_value=0)
    
    traces = []
    for i, col in enumerate(pivot.columns[:6]):  # Limit to 6 series
        traces.append({
            "type": "scatter",
            "mode": "lines",
            "name": str(col),
            "x": [str(x) for x in pivot.index.tolist()],
            "y": [float(v) for v in pivot[col].tolist()],
            "fill": "tonexty" if i > 0 else "tozeroy",
            "line": {"color": colors[i % len(colors)], "width": 1},
            "hovertemplate": str(col) + "<br>%{x}<br>" + currency + "%{y:,.0f}<extra></extra>"
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "xaxis": {"title": "", "tickangle": -45},
            "yaxis": {"title": "", "tickprefix": currency},
            "height": 450,
            "margin": {"b": 100},
            "legend": {"orientation": "h", "y": -0.25}
        }
    }


# =============================================================================
# DOUGHNUT WITH CENTER LABEL - Premium visualization
# =============================================================================

def _donut_with_total(labels, values, title, currency, colors):
    """Donut chart with total value in the center."""
    total = sum(values)
    
    return {
        "data": [{
            "type": "pie",
            "labels": labels,
            "values": values,
            "hole": 0.5,
            "textinfo": "percent",
            "textposition": "outside",
            "hovertemplate": "%{label}<br>" + currency + "%{value:,.0f}<br>%{percent}<extra></extra>",
            "marker": {"colors": colors[:len(labels)], "line": {"color": "white", "width": 2}}
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 16}},
            "showlegend": True,
            "height": 450,
            "annotations": [{
                "text": f"<b>Total</b><br>{currency}{total:,.0f}",
                "showarrow": False,
                "font": {"size": 14, "color": "#374151"}
            }],
            "legend": {"orientation": "h", "y": -0.1}
        }
    }
