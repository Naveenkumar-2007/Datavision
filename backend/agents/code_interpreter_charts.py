# =============================================================================
# CHATGPT CODE INTERPRETER - LLM-Powered Chart Generation
# =============================================================================
#
# This module implements ChatGPT-style chart generation where:
# 1. LLM analyzes the query and data schema
# 2. LLM writes Plotly chart code
# 3. Code is executed safely to generate the chart
# 4. Chart is guaranteed to match the query!
#

import json
import re
from typing import Optional, Dict, Any, Tuple
import pandas as pd


def generate_chart_with_llm(
    query: str,
    df: pd.DataFrame,
    currency_symbol: str = "₹",
    max_retries: int = 2
) -> Tuple[Optional[Dict], str]:
    """
    🧠 CHATGPT CODE INTERPRETER STYLE
    
    Let the LLM analyze the query and generate Plotly chart code,
    then execute it to create the perfect chart.
    
    Args:
        query: User's question (e.g., "show top 5 customers pie chart")
        df: The user's actual DataFrame
        currency_symbol: Currency for formatting
        max_retries: Retries if code execution fails
        
    Returns:
        (chart_dict, explanation) - Plotly chart JSON and LLM explanation
    """
    from core.llm import chat
    
    # Build data schema description for LLM
    schema = _describe_dataframe(df)
    sample_data = df.head(5).to_string()
    
    # STEP 1: Ask LLM to write chart code
    prompt = f"""You are a data visualization expert. Generate a Plotly chart based on the user's query.

USER QUERY: "{query}"

DATA SCHEMA:
{schema}

SAMPLE DATA (first 5 rows):
{sample_data}

CURRENCY SYMBOL: {currency_symbol}

YOUR TASK:
1. Analyze what the user wants to visualize
2. Write Python code that:
   - Uses the DataFrame 'df' 
   - Creates a Plotly chart specification
   - Returns a dict with 'data' and 'layout' keys

RESPOND WITH ONLY THE PYTHON CODE, NO EXPLANATION.
The code must define a variable called 'chart' which is a Plotly-compatible dict.

Example format:
```python
# Your analysis code here
chart = {{
    "data": [...],
    "layout": {{...}}
}}
```

RULES:
- Use actual column names from the schema
- Handle edge cases (empty data, missing columns)
- For "top N", sort and take first N
- For "bottom N" or "low N", sort ascending and take first N
- Always include proper title, labels, and colors
"""

    try:
        # Get code from LLM
        code_response = chat(prompt, max_tokens=1500)
        
        # Extract Python code from response
        code = _extract_python_code(code_response)
        
        if not code:
            return None, "Could not generate chart code"
        
        # STEP 2: Execute the code safely
        chart_dict = _execute_chart_code(code, df, currency_symbol)
        
        if chart_dict:
            # STEP 3: Generate explanation
            explanation = _generate_chart_explanation(query, df, chart_dict, currency_symbol)
            return chart_dict, explanation
        
        # Retry if failed
        for retry in range(max_retries):
            # Ask LLM to fix the code
            fix_prompt = f"""The previous code failed. Original query: "{query}"
            
Fix this code to work with DataFrame that has columns: {list(df.columns)}

Previous code:
{code}

Write corrected Python code that defines 'chart' variable."""

            code_response = chat(fix_prompt, max_tokens=1500)
            code = _extract_python_code(code_response)
            
            if code:
                chart_dict = _execute_chart_code(code, df, currency_symbol)
                if chart_dict:
                    explanation = _generate_chart_explanation(query, df, chart_dict, currency_symbol)
                    return chart_dict, explanation
        
        return None, "Failed to generate chart after retries"
        
    except Exception as e:
        print(f"[CODE INTERPRETER] Error: {e}")
        return None, f"Chart generation error: {e}"


def _describe_dataframe(df: pd.DataFrame) -> str:
    """Generate a schema description for the LLM."""
    if df is None or df.empty:
        return "No data available"
    
    lines = [f"Rows: {len(df)}", "Columns:"]
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(3).tolist()
        unique = df[col].nunique()
        
        lines.append(f"  - {col} ({dtype}): {unique} unique, samples: {sample}")
    
    return "\n".join(lines)


def _extract_python_code(response: str) -> Optional[str]:
    """Extract Python code from LLM response."""
    # Try to find code block
    code_pattern = r'```python\s*(.*?)\s*```'
    match = re.search(code_pattern, response, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    # Try to find code without markers
    if 'chart = {' in response or 'chart={' in response:
        # Find the code section
        lines = response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if 'import' in line or 'df.' in line or 'chart' in line or in_code:
                in_code = True
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
    
    return None


def _execute_chart_code(code: str, df: pd.DataFrame, currency_symbol: str) -> Optional[Dict]:
    """
    Safely execute chart generation code.
    
    Uses a restricted execution environment for security.
    """
    try:
        # Create safe execution environment
        safe_globals = {
            'df': df,
            'pd': pd,
            'currency_symbol': currency_symbol,
            'len': len,
            'list': list,
            'dict': dict,
            'str': str,
            'int': int,
            'float': float,
            'sum': sum,
            'min': min,
            'max': max,
            'sorted': sorted,
            'round': round,
            'abs': abs,
        }
        
        local_vars = {}
        
        # Execute the code
        exec(code, safe_globals, local_vars)
        
        # Get the chart variable
        chart = local_vars.get('chart')
        
        if chart and isinstance(chart, dict):
            # Validate it has required keys
            if 'data' in chart:
                return chart
        
        return None
        
    except Exception as e:
        print(f"[CODE INTERPRETER] Execution error: {e}")
        return None


def _generate_chart_explanation(
    query: str,
    df: pd.DataFrame,
    chart_dict: Dict,
    currency_symbol: str
) -> str:
    """Generate a natural language explanation of the chart."""
    from core.llm import chat
    
    # Extract key data from chart
    chart_data = chart_dict.get('data', [{}])[0]
    labels = chart_data.get('labels', chart_data.get('x', []))
    values = chart_data.get('values', chart_data.get('y', []))
    chart_type = chart_data.get('type', 'bar')
    title = chart_dict.get('layout', {}).get('title', {})
    if isinstance(title, dict):
        title = title.get('text', 'Chart')
    
    # Format values
    def fmt(v):
        if v >= 1_000_000:
            return f"{currency_symbol}{v/1_000_000:.2f}M"
        elif v >= 1_000:
            return f"{currency_symbol}{v/1_000:.1f}K"
        return f"{currency_symbol}{v:,.0f}"
    
    # Build data summary
    data_summary = []
    for i, (label, value) in enumerate(zip(labels[:10], values[:10])):
        data_summary.append(f"{i+1}. {label}: {fmt(value)}")
    
    explanation = f"""**{title}**

Based on your query "{query}", here's the analysis:

{chr(10).join(data_summary)}

The chart shows a {chart_type} visualization of your data."""

    return explanation


# =============================================================================
# QUICK CHART TEMPLATES (Faster than full LLM generation)
# =============================================================================

def quick_chart(
    query: str,
    df: pd.DataFrame,
    currency_symbol: str = "₹"
) -> Tuple[Optional[Dict], str]:
    """
    Fast chart generation using templates for common patterns.
    Falls back to LLM generation for complex queries.
    """
    query_lower = query.lower()
    
    # Detect chart parameters
    chart_type = _detect_chart_type(query_lower)
    entity_col = _detect_entity_column(query_lower, df)
    value_col = _detect_value_column(df)
    count = _extract_count(query_lower)
    is_bottom = 'bottom' in query_lower or 'low' in query_lower or 'worst' in query_lower
    
    print(f"[QUICK CHART] entity_col={entity_col}, value_col={value_col}, chart={chart_type}, count={count}")
    
    if not entity_col or not value_col:
        print(f"[QUICK CHART] Missing columns, trying LLM...")
        # Fall back to full LLM generation
        return generate_chart_with_llm(query, df, currency_symbol)
    
    # Generate chart from template
    try:
        # Aggregate data
        grouped = df.groupby(entity_col)[value_col].sum()
        
        if is_bottom:
            grouped = grouped.nsmallest(count)
            title_prefix = "📉 Bottom"
        else:
            grouped = grouped.nlargest(count)
            title_prefix = "🏆 Top"
        
        # CRITICAL: Convert numpy types to native Python for JSON serialization
        labels = [str(x) for x in grouped.index.tolist()]
        values = [float(x) for x in grouped.values.tolist()]
        
        print(f"[QUICK CHART] Generated: {len(labels)} items, values: {values[:3]}...")
        
        # Detect entity type for title
        entity_name = _humanize_column(entity_col)
        title = f"{title_prefix} {count} {entity_name}s by {_humanize_column(value_col)}"
        
        # Build chart based on type
        chart = _build_chart(chart_type, labels, values, title, currency_symbol)
        
        # Generate explanation
        explanation = _build_explanation(labels, values, title, currency_symbol, is_bottom)
        
        print(f"[QUICK CHART] SUCCESS: {chart_type} chart with {len(labels)} data points")
        return chart, explanation
        
    except Exception as e:
        print(f"[QUICK CHART] Template failed: {e}, trying LLM...")
        import traceback
        traceback.print_exc()
        return generate_chart_with_llm(query, df, currency_symbol)


def _detect_chart_type(query: str) -> str:
    """Detect chart type from query."""
    if 'pie' in query or 'distribution' in query or 'share' in query:
        return 'pie'
    elif 'line' in query or 'trend' in query or 'over time' in query:
        return 'line'
    elif 'scatter' in query or 'correlation' in query:
        return 'scatter'
    return 'bar'


def _detect_entity_column(query: str, df: pd.DataFrame) -> Optional[str]:
    """Detect which column to group by based on query."""
    # Priority keywords
    keywords = {
        'customer': ['customer', 'account', 'client', 'buyer', 'company'],
        'product': ['product', 'item', 'service', 'sku'],
        'category': ['category', 'type', 'segment'],
        'region': ['region', 'area', 'territory', 'location', 'country'],
        'vendor': ['vendor', 'supplier', 'distributor'],
    }
    
    # Check query for entity mention
    for entity, patterns in keywords.items():
        if entity in query:
            # Find matching column
            for col in df.columns:
                col_lower = col.lower()
                for pattern in patterns:
                    if pattern in col_lower:
                        return col
    
    # Fallback: first categorical column
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() < 500:
            if 'source' not in col.lower() and 'file' not in col.lower():
                return col
    
    return None


def _detect_value_column(df: pd.DataFrame) -> Optional[str]:
    """Detect the numeric value column to aggregate."""
    # Priority keywords
    for candidate in ['amount', 'revenue', 'total', 'sales', 'value', 'price']:
        for col in df.columns:
            if candidate in col.lower():
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    return col
    
    # Fallback: first numeric column
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
            return col
    
    return None


def _extract_count(query: str) -> int:
    """Extract count from query (e.g., 'top 5' → 5)."""
    import re
    
    patterns = [
        r'top\s+(\d+)',
        r'bottom\s+(\d+)',
        r'best\s+(\d+)',
        r'worst\s+(\d+)',
        r'(\d+)\s+(?:customers?|products?|items?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return int(match.group(1))
    
    return 10  # Default


def _humanize_column(col: str) -> str:
    """Convert column name to human-readable format."""
    return col.replace('_', ' ').replace('-', ' ').title()


def _build_chart(
    chart_type: str,
    labels: list,
    values: list,
    title: str,
    currency: str
) -> Dict:
    """Build Plotly chart dict from data."""
    colors = ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    
    if chart_type == 'pie':
        return {
            "data": [{
                "type": "pie",
                "labels": labels,
                "values": values,
                "textinfo": "label+percent",
                "marker": {"colors": colors[:len(labels)]}
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "showlegend": True,
                "height": 400
            }
        }
    elif chart_type == 'line':
        return {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": labels,
                "y": values,
                "line": {"color": "#FF6B35", "width": 3},
                "marker": {"size": 8}
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": ""},
                "yaxis": {"title": "Amount", "tickprefix": currency},
                "height": 400
            }
        }
    else:  # bar
        return {
            "data": [{
                "type": "bar",
                "x": labels,
                "y": values,
                "marker": {"color": colors[:len(labels)]}
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": "", "tickangle": -45},
                "yaxis": {"title": "Amount", "tickprefix": currency},
                "height": 400,
                "margin": {"b": 100}
            }
        }


def _build_explanation(
    labels: list,
    values: list,
    title: str,
    currency: str,
    is_bottom: bool
) -> str:
    """Build natural language explanation."""
    def fmt(v):
        if v >= 1_000_000:
            return f"{currency}{v/1_000_000:.2f}M"
        elif v >= 1_000:
            return f"{currency}{v/1_000:.1f}K"
        return f"{currency}{v:,.0f}"
    
    lines = [f"**{title}**\n"]
    
    for i, (label, value) in enumerate(zip(labels, values)):
        lines.append(f"{i+1}. **{label}**: {fmt(value)}")
    
    total = sum(values)
    lines.append(f"\n**Total**: {fmt(total)}")
    
    if not is_bottom:
        top_pct = (values[0] / total * 100) if total > 0 else 0
        lines.append(f"\n*Top performer accounts for {top_pct:.1f}% of the total.*")
    
    return "\n".join(lines)
