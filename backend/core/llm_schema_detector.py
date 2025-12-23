# LLM-Based Schema Detector
"""
$5M Enterprise Feature: LLM understands ANY file schema dynamically.

THIS IS THE CORE FIX for handling new file uploads.

Instead of pattern matching like:
    if 'customer' in column_name.lower(): ...

We ask the LLM:
    "What does each column represent?"

This works for ANY file with ANY column names.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import json


@dataclass
class SchemaUnderstanding:
    """LLM's understanding of a file's schema"""
    amount_column: Optional[str] = None      # Revenue/price/total column
    entity_column: Optional[str] = None      # Customer/company/client column
    product_column: Optional[str] = None     # Product/item/service column
    date_column: Optional[str] = None        # Date/time column
    category_column: Optional[str] = None    # Category/type column
    quantity_column: Optional[str] = None    # Quantity/count column
    
    data_type: str = "unknown"               # "sales", "invoices", "inventory", etc.
    currency_detected: Optional[str] = None  # "USD", "INR", "EUR", etc.
    confidence: float = 0.5
    
    original_columns: List[str] = None       # Original column names from file
    column_mapping: Dict[str, str] = None    # Maps semantic role -> actual column name


def understand_schema_with_llm(
    df: pd.DataFrame,
    filename: str = "",
    max_sample_rows: int = 5
) -> SchemaUnderstanding:
    """
    Use LLM to understand ANY file's schema - NO PATTERN MATCHING.
    
    This is the key function that makes the system work like ChatGPT.
    It understands:
    - "Company Name" = customer entity
    - "Invoice Total" = amount column
    - "Contract Value" = amount column
    - ANY column naming convention
    
    Args:
        df: DataFrame from uploaded file
        filename: Name of the file for context
        max_sample_rows: How many sample rows to show LLM
        
    Returns:
        SchemaUnderstanding with mapped columns
    """
    try:
        from core.llm import chat
    except ImportError:
        # Fallback to pattern-based detection if LLM not available
        return _fallback_pattern_detection(df)
    
    # Prepare column information for LLM
    columns = list(df.columns)
    
    # Get sample data (first few rows)
    sample_data = df.head(max_sample_rows).to_dict('records')
    
    # Get column statistics
    column_info = []
    for col in columns:
        dtype = str(df[col].dtype)
        sample_values = df[col].dropna().head(3).tolist()
        unique_count = df[col].nunique()
        
        column_info.append({
            "name": col,
            "type": dtype,
            "samples": sample_values[:3],
            "unique": unique_count
        })
    
    system_prompt = """You are a data schema expert analyzing business files.

Your task: Identify what each column represents in this business data.

RESPOND WITH ONLY JSON in this exact format:
{
    "amount_column": "column name for revenue/price/total/value (or null)",
    "entity_column": "column name for customer/company/client/buyer (or null)",
    "product_column": "column name for product/item/service (or null)",
    "date_column": "column name for date/time (or null)",
    "category_column": "column name for category/type/segment (or null)",
    "quantity_column": "column name for quantity/count/units (or null)",
    "data_type": "invoices|sales|orders|inventory|customer_list|other",
    "currency_detected": "USD|EUR|INR|GBP|null (detect from data values)",
    "confidence": 0.0-1.0
}

RULES:
1. Look at ACTUAL sample data to understand columns, not just names
2. "Company Name", "Customer", "Client", "Buyer", "Account" all → entity_column
3. "Total", "Amount", "Revenue", "Value", "Price", "Contract Value" → amount_column
4. Look for currency symbols ($, ₹, €, £) in data to detect currency
5. Be confident - this is critical for the system to work"""

    user_prompt = f"""Analyze this file: "{filename}"

Columns ({len(columns)}):
{json.dumps(column_info, indent=2)}

Sample data:
{json.dumps(sample_data[:3], indent=2, default=str)}

Identify the semantic meaning of each column. Return JSON only."""

    try:
        response = chat(
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            data = json.loads(json_match.group())
            
            # Build column mapping
            column_mapping = {}
            if data.get("amount_column"):
                column_mapping["amount"] = data["amount_column"]
            if data.get("entity_column"):
                column_mapping["entity"] = data["entity_column"]
            if data.get("product_column"):
                column_mapping["product"] = data["product_column"]
            if data.get("date_column"):
                column_mapping["date"] = data["date_column"]
            if data.get("category_column"):
                column_mapping["category"] = data["category_column"]
            if data.get("quantity_column"):
                column_mapping["quantity"] = data["quantity_column"]
            
            understanding = SchemaUnderstanding(
                amount_column=data.get("amount_column"),
                entity_column=data.get("entity_column"),
                product_column=data.get("product_column"),
                date_column=data.get("date_column"),
                category_column=data.get("category_column"),
                quantity_column=data.get("quantity_column"),
                data_type=data.get("data_type", "unknown"),
                currency_detected=data.get("currency_detected"),
                confidence=float(data.get("confidence", 0.7)),
                original_columns=columns,
                column_mapping=column_mapping
            )
            
            print(f"[LLM SCHEMA] Detected: entity={understanding.entity_column}, "
                  f"amount={understanding.amount_column}, product={understanding.product_column}, "
                  f"date={understanding.date_column}, currency={understanding.currency_detected}")
            
            return understanding
            
    except Exception as e:
        print(f"[LLM SCHEMA] LLM detection failed: {e}")
    
    # Fallback to pattern-based
    return _fallback_pattern_detection(df)


def _fallback_pattern_detection(df: pd.DataFrame) -> SchemaUnderstanding:
    """Fallback pattern-based detection if LLM fails - IMPROVED FOR MORE PATTERNS"""
    columns = [str(c).lower().replace('_', ' ') for c in df.columns]  # Normalize underscores
    original_columns = list(df.columns)
    
    column_mapping = {}
    
    # Amount patterns - EXPANDED to handle variations
    amount_patterns = [
        'amount', 'total', 'revenue', 'price', 'value', 'cost', 'sales',
        'contract', 'invoice amount', 'usd', 'inr', 'eur', 'gbp',
        'payment', 'sum', 'money', 'fee', 'charge'
    ]
    amount_col = None
    for col, orig in zip(columns, original_columns):
        if any(p in col for p in amount_patterns):
            amount_col = orig
            column_mapping["amount"] = orig
            break
    
    # If no pattern match, use first numeric column with $, ₹, etc.
    if not amount_col:
        for orig in original_columns:
            if df[orig].dtype in ['float64', 'int64']:
                amount_col = orig
                column_mapping["amount"] = orig
                break
            elif df[orig].dtype == 'object':
                # Check if contains currency symbols
                sample = str(df[orig].iloc[0]) if len(df) > 0 else ""
                if any(sym in sample for sym in ['$', '₹', '€', '£', '¥']):
                    amount_col = orig
                    column_mapping["amount"] = orig
                    break
    
    # Entity patterns - EXPANDED
    entity_patterns = [
        'customer', 'client', 'company', 'buyer', 'account', 'name',
        'organization', 'org', 'firm', 'vendor', 'supplier', 'partner',
        'business', 'entity'
    ]
    entity_col = None
    for col, orig in zip(columns, original_columns):
        if any(p in col for p in entity_patterns):
            entity_col = orig
            column_mapping["entity"] = orig
            break
    
    # Date patterns - EXPANDED
    date_patterns = [
        'date', 'time', 'created', 'invoice date', 'order date',
        'purchase', 'transaction', 'timestamp', 'datetime', 'period',
        'month', 'year', 'day'
    ]
    date_col = None
    for col, orig in zip(columns, original_columns):
        if any(p in col for p in date_patterns):
            date_col = orig
            column_mapping["date"] = orig
            break
    
    # Product/Service patterns - NEW
    product_patterns = [
        'product', 'item', 'service', 'sku', 'goods', 'description',
        'category', 'type', 'line'
    ]
    product_col = None
    for col, orig in zip(columns, original_columns):
        if any(p in col for p in product_patterns):
            product_col = orig
            column_mapping["product"] = orig
            break
    
    # Detect currency from amount column values
    currency_detected = "USD"  # Default
    if amount_col and len(df) > 0:
        try:
            sample = str(df[amount_col].iloc[0])
            if '$' in sample:
                currency_detected = "USD"
            elif '₹' in sample:
                currency_detected = "INR"
            elif '€' in sample:
                currency_detected = "EUR"
            elif '£' in sample:
                currency_detected = "GBP"
        except:
            pass
    
    print(f"[LLM SCHEMA] Fallback detected: entity={entity_col}, amount={amount_col}, "
          f"date={date_col}, product={product_col}, currency={currency_detected}")
    
    return SchemaUnderstanding(
        amount_column=amount_col,
        entity_column=entity_col,
        date_column=date_col,
        product_column=product_col,
        currency_detected=currency_detected,
        original_columns=original_columns,
        column_mapping=column_mapping,
        confidence=0.6
    )


def get_aggregated_data(
    df: pd.DataFrame,
    schema: SchemaUnderstanding,
    group_by: str = "entity",  # "entity", "product", "date", "category"
    metric: str = "sum"        # "sum", "count", "mean"
) -> pd.DataFrame:
    """
    Aggregate data using the detected schema.
    
    This replaces hardcoded:
        df.groupby('customer')['amount'].sum()
    
    With dynamic:
        df.groupby(schema.entity_column)[schema.amount_column].sum()
    """
    # Determine grouping column
    group_col_map = {
        "entity": schema.entity_column,
        "product": schema.product_column,
        "date": schema.date_column,
        "category": schema.category_column
    }
    
    group_col = group_col_map.get(group_by)
    if not group_col or group_col not in df.columns:
        print(f"[LLM SCHEMA] Cannot group by {group_by} - column not found")
        return pd.DataFrame()
    
    # Determine value column
    value_col = schema.amount_column
    if not value_col or value_col not in df.columns:
        # Try to find any numeric column
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            value_col = numeric_cols[0]
        else:
            print(f"[LLM SCHEMA] No numeric column found for aggregation")
            return pd.DataFrame()
    
    # Perform aggregation
    try:
        if metric == "sum":
            result = df.groupby(group_col)[value_col].sum().reset_index()
        elif metric == "count":
            result = df.groupby(group_col).size().reset_index(name='count')
        elif metric == "mean":
            result = df.groupby(group_col)[value_col].mean().reset_index()
        else:
            result = df.groupby(group_col)[value_col].sum().reset_index()
        
        # Rename columns to standard names for downstream compatibility
        if group_by in ["entity", "product", "category"]:
            result.columns = ['name', 'value']
        
        return result.sort_values('value', ascending=False)
        
    except Exception as e:
        print(f"[LLM SCHEMA] Aggregation failed: {e}")
        return pd.DataFrame()


def get_time_series_data(
    df: pd.DataFrame,
    schema: SchemaUnderstanding,
    freq: str = "M"  # "D"=daily, "W"=weekly, "M"=monthly
) -> pd.DataFrame:
    """
    Get time series data using detected date column.
    
    Returns DataFrame with 'date' and 'value' columns for charting.
    """
    if not schema.date_column or schema.date_column not in df.columns:
        print(f"[LLM SCHEMA] No date column for time series")
        return pd.DataFrame()
    
    value_col = schema.amount_column
    if not value_col or value_col not in df.columns:
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        value_col = numeric_cols[0] if len(numeric_cols) > 0 else None
    
    if not value_col:
        return pd.DataFrame()
    
    try:
        df_copy = df.copy()
        df_copy['_date'] = pd.to_datetime(df_copy[schema.date_column], errors='coerce')
        df_copy = df_copy[df_copy['_date'].notna()]
        
        if df_copy.empty:
            return pd.DataFrame()
        
        # Group by period
        df_copy['_period'] = df_copy['_date'].dt.to_period(freq)
        result = df_copy.groupby('_period')[value_col].sum().reset_index()
        result.columns = ['date', 'value']
        result['date'] = result['date'].astype(str)
        
        return result
        
    except Exception as e:
        print(f"[LLM SCHEMA] Time series failed: {e}")
        return pd.DataFrame()


# Cache for schema understanding per file
_schema_cache: Dict[str, SchemaUnderstanding] = {}


def get_cached_schema(file_hash: str) -> Optional[SchemaUnderstanding]:
    """Get cached schema understanding for a file"""
    return _schema_cache.get(file_hash)


def cache_schema(file_hash: str, schema: SchemaUnderstanding):
    """Cache schema understanding for a file"""
    _schema_cache[file_hash] = schema
    print(f"[LLM SCHEMA] Cached schema for {file_hash}")
