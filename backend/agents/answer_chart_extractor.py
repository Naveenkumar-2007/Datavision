# =============================================================================
# CHATGPT-STYLE CHART GENERATION - From Answer Data
# =============================================================================
#
# This module extracts chart data directly from LLM answers to ensure
# charts match the text response exactly - just like real ChatGPT!
#

from typing import Optional, Dict, List, Any, Tuple
import re
import json


def extract_chart_data_from_answer(
    answer: str,
    query: str,
    df=None,
    currency_symbol: str = "₹"
) -> Optional[Dict]:
    """
    🧠 CHATGPT-STYLE: Extract chart data from LLM's text answer.
    
    Instead of generating charts separately, we extract the data
    that the LLM mentioned in its answer and visualize THAT.
    
    Args:
        answer: The LLM's text response
        query: User's original query
        df: Optional DataFrame for validation
        currency_symbol: Currency symbol used
        
    Returns:
        Chart specification dict or None
    """
    # Detect what kind of chart is needed
    query_lower = query.lower()
    
    # ===========================================================================
    # STEP 1: Detect chart type from query
    # ===========================================================================
    chart_type = "bar"  # Default
    if "pie" in query_lower or "distribution" in query_lower or "share" in query_lower:
        chart_type = "pie"
    elif "line" in query_lower or "trend" in query_lower or "over time" in query_lower:
        chart_type = "line"
    elif "bar" in query_lower or "top" in query_lower or "ranking" in query_lower:
        chart_type = "bar"
    
    # ===========================================================================
    # STEP 2: Extract structured data from answer
    # ===========================================================================
    
    # Pattern 1: Markdown table extraction
    table_data = _extract_table_from_markdown(answer)
    if table_data:
        return _create_chart_from_table(table_data, chart_type, query, currency_symbol)
    
    # Pattern 2: Numbered list with values (e.g., "1. Glovo Ltd - $1,153,500")
    list_data = _extract_list_from_answer(answer)
    if list_data:
        return _create_chart_from_list(list_data, chart_type, query, currency_symbol)
    
    # Pattern 3: Inline mentions (e.g., "Your top customer is Glovo Ltd with $1.15M")
    inline_data = _extract_inline_data(answer, currency_symbol)
    if inline_data:
        return _create_chart_from_list(inline_data, chart_type, query, currency_symbol)
    
    return None


def _extract_table_from_markdown(answer: str) -> Optional[List[Dict]]:
    """
    Extract data from markdown tables in the answer.
    
    Properly parses tables like:
    | Customer | Revenue |
    |----------|---------|
    | Glovo Ltd | $1,153,500 |
    """
    lines = answer.split('\n')
    
    # Find table start (header row)
    table_start = -1
    for i, line in enumerate(lines):
        # Table header has at least 2 pipe characters and no separator
        if line.count('|') >= 2 and '---' not in line and '===' not in line:
            # Check if next line is separator
            if i + 1 < len(lines) and ('---' in lines[i + 1] or '===' in lines[i + 1]):
                table_start = i
                break
    
    if table_start < 0:
        return None
    
    # Parse header
    header_line = lines[table_start]
    headers = []
    for cell in header_line.split('|'):
        cell = cell.strip()
        # Clean markdown formatting
        cell = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)  # Remove bold
        cell = re.sub(r'\*([^*]+)\*', r'\1', cell)  # Remove italic
        if cell and cell not in ['', '-', '---']:
            headers.append(cell)
    
    if len(headers) < 2:
        return None
    
    # Parse data rows (skip header and separator)
    rows = []
    for i in range(table_start + 2, len(lines)):
        line = lines[i].strip()
        
        # Stop at empty line or non-table line
        if not line or '|' not in line:
            break
        
        # Parse cells
        cells = []
        for cell in line.split('|'):
            cell = cell.strip()
            # Clean markdown formatting
            cell = re.sub(r'\*\*([^*]+)\*\*', r'\1', cell)  # Remove bold
            cell = re.sub(r'\*([^*]+)\*', r'\1', cell)  # Remove italic
            cell = cell.replace('\u202f', '')  # Remove narrow non-breaking space
            if cell and cell not in ['', '-', '---']:
                cells.append(cell)
        
        if len(cells) >= 2:
            row_dict = {}
            for j, header in enumerate(headers):
                if j < len(cells):
                    row_dict[header] = cells[j]
            if row_dict:
                rows.append(row_dict)
    
    # Validate we have actual data, not markdown artifacts
    if rows:
        # Check first row doesn't contain markdown syntax
        first_row_values = list(rows[0].values())
        for val in first_row_values:
            if '|' in str(val) or '---' in str(val):
                return None  # Still has markdown artifacts
    
    return rows if rows else None



def _extract_list_from_answer(answer: str) -> Optional[List[Dict]]:
    """Extract data from numbered or bulleted lists."""
    # Pattern: "1. Name - $1,234,567" or "• Name: $1,234,567"
    patterns = [
        r'(?:\d+\.|•|-)\s*([^:\-–—]+?)[\s:\-–—]+[₹$€£]?([\d,]+(?:\.\d+)?)',
        r'(?:\d+\.|•|-)\s*\*\*([^*]+)\*\*.*?[₹$€£]?([\d,]+(?:\.\d+)?)',
    ]
    
    items = []
    for pattern in patterns:
        matches = re.findall(pattern, answer)
        for match in matches:
            name = match[0].strip()
            value_str = match[1].replace(',', '')
            try:
                value = float(value_str)
                if value > 0:
                    items.append({'name': name, 'value': value})
            except ValueError:
                continue
    
    # Deduplicate by name
    seen = set()
    unique_items = []
    for item in items:
        if item['name'] not in seen:
            seen.add(item['name'])
            unique_items.append(item)
    
    return unique_items[:10] if unique_items else None


def _extract_inline_data(answer: str, currency_symbol: str = "₹") -> Optional[List[Dict]]:
    """Extract entity-value pairs mentioned inline in the answer."""
    # Pattern: "Customer_Name with $1,234,567" or "Customer_Name ($1,234,567)"
    patterns = [
        r'(\b[A-Z][a-zA-Z0-9_\s]+?)\s+(?:with|at|generated|earned)\s+[₹$€£]?([\d,]+(?:\.\d+)?)',
        r'(\b[A-Z][a-zA-Z0-9_\s]+?)\s*\([₹$€£]?([\d,]+(?:\.\d+)?)\)',
        r'\*\*([^*]+?)\*\*.*?[₹$€£]?([\d,]+(?:\.\d+)?)',
    ]
    
    items = []
    for pattern in patterns:
        matches = re.findall(pattern, answer)
        for match in matches:
            name = match[0].strip()
            # Skip common phrases
            if name.lower() in ['your', 'the', 'total', 'revenue', 'amount', 'average']:
                continue
            value_str = match[1].replace(',', '')
            try:
                value = float(value_str)
                if value > 0 and len(name) > 2:
                    items.append({'name': name, 'value': value})
            except ValueError:
                continue
    
    return items[:10] if items else None


def _create_chart_from_table(
    table_data: List[Dict],
    chart_type: str,
    query: str,
    currency_symbol: str
) -> Dict:
    """Create chart specification from table data."""
    if not table_data:
        return None
    
    # Find the name column (first text column)
    name_col = None
    value_col = None
    
    first_row = table_data[0]
    for key, val in first_row.items():
        # Detect name column
        if name_col is None and not _is_numeric(val):
            name_col = key
        # Detect value column (contains numbers)
        elif _is_numeric(val):
            value_col = key
    
    if not name_col or not value_col:
        return None
    
    # Extract names and values
    names = []
    values = []
    for row in table_data:
        name = row.get(name_col, '')
        value_str = row.get(value_col, '0')
        try:
            # Clean value string
            value_clean = re.sub(r'[^\d.]', '', str(value_str))
            value = float(value_clean) if value_clean else 0
            names.append(name)
            values.append(value)
        except ValueError:
            continue
    
    return _build_plotly_chart(names, values, chart_type, query, currency_symbol)


def _create_chart_from_list(
    list_data: List[Dict],
    chart_type: str,
    query: str,
    currency_symbol: str
) -> Dict:
    """Create chart specification from list data."""
    if not list_data:
        return None
    
    names = [item['name'] for item in list_data]
    values = [item['value'] for item in list_data]
    
    return _build_plotly_chart(names, values, chart_type, query, currency_symbol)


def _build_plotly_chart(
    names: List[str],
    values: List[float],
    chart_type: str,
    query: str,
    currency_symbol: str
) -> Dict:
    """Build a Plotly chart specification."""
    # Generate title from query
    title = _generate_chart_title(query, names)
    
    # Format values for display
    def format_value(v):
        if v >= 1_000_000:
            return f"{currency_symbol}{v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"{currency_symbol}{v/1_000:.1f}K"
        else:
            return f"{currency_symbol}{v:,.0f}"
    
    if chart_type == "pie":
        return {
            "data": [{
                "type": "pie",
                "labels": names,
                "values": values,
                "textinfo": "label+percent",
                "hovertemplate": "%{label}<br>" + currency_symbol + "%{value:,.0f}<br>%{percent}<extra></extra>",
                "marker": {
                    "colors": ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                               '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'][:len(names)]
                }
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "showlegend": True,
                "height": 400
            }
        }
    elif chart_type == "line":
        return {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": names,
                "y": values,
                "line": {"color": "#FF6B35", "width": 3},
                "marker": {"size": 8}
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": ""},
                "yaxis": {"title": "Amount", "tickprefix": currency_symbol},
                "height": 400
            }
        }
    else:  # bar chart (default)
        return {
            "data": [{
                "type": "bar",
                "x": names,
                "y": values,
                "text": [format_value(v) for v in values],
                "textposition": "auto",
                "marker": {
                    "color": ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'][:len(names)]
                }
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": "", "tickangle": -45},
                "yaxis": {"title": "Amount", "tickprefix": currency_symbol},
                "height": 400,
                "margin": {"b": 100}
            }
        }


def _generate_chart_title(query: str, names: List[str]) -> str:
    """Generate a chart title from the query."""
    query_lower = query.lower()
    
    # Extract entity type from query
    entity = "Items"
    if "customer" in query_lower:
        entity = "Customers"
    elif "product" in query_lower:
        entity = "Products"
    elif "region" in query_lower:
        entity = "Regions"
    elif "category" in query_lower:
        entity = "Categories"
    
    # Detect top vs bottom
    if "bottom" in query_lower or "low" in query_lower or "worst" in query_lower:
        return f"📉 Bottom {len(names)} {entity} by Revenue"
    elif "top" in query_lower or "best" in query_lower or "highest" in query_lower:
        return f"🏆 Top {len(names)} {entity} by Revenue"
    elif "vs" in query_lower or "compare" in query_lower:
        return f"📊 {entity} Comparison"
    else:
        return f"📊 {entity} by Revenue"


def _is_numeric(value: str) -> bool:
    """Check if a value looks numeric."""
    if not value:
        return False
    cleaned = re.sub(r'[₹$€£,%\s]', '', str(value))
    try:
        float(cleaned)
        return True
    except ValueError:
        return False
