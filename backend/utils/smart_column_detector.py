"""
Smart Column Detector - AI-powered column mapping for any business data
Enterprise-grade $500K product feature
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import re
from difflib import SequenceMatcher


# Column type patterns with priority weights
COLUMN_PATTERNS = {
    'amount': {
        'exact': ['amount', 'revenue', 'sales', 'total', 'price', 'value', 'cost', 'payment', 'income', 'profit'],
        'contains': ['amount', 'revenue', 'sales', 'total', 'price', 'value', 'cost', 'usd', 'inr', 'eur', 'gbp', 'contract'],
        'regex': [r'.*_amount$', r'.*_price$', r'.*_value$', r'.*_total$', r'.*_revenue$', r'annual.*value'],
        'weight': 1.0
    },
    'customer': {
        'exact': ['customer', 'client', 'company', 'buyer', 'account', 'customer_name', 'client_name'],
        'contains': ['customer', 'client', 'company', 'buyer', 'account', 'name'],
        'regex': [r'.*customer.*', r'.*client.*', r'.*company.*name.*'],
        'weight': 0.9
    },
    'product': {
        'exact': ['product', 'item', 'sku', 'service', 'goods', 'product_name', 'item_name'],
        'contains': ['product', 'item', 'sku', 'service', 'goods', 'description'],
        'regex': [r'.*product.*', r'.*item.*', r'.*service.*'],
        'weight': 0.9
    },
    'date': {
        'exact': ['date', 'order_date', 'transaction_date', 'created_at', 'timestamp', 'created', 'ordered'],
        'contains': ['date', 'timestamp', 'created', 'ordered', 'time'],
        'regex': [r'.*date$', r'.*_at$', r'.*time.*'],
        'weight': 0.8
    },
    'quantity': {
        'exact': ['quantity', 'qty', 'units', 'count', 'volume', 'num', 'number'],
        'contains': ['quantity', 'qty', 'units', 'count', 'volume'],
        'regex': [r'.*qty.*', r'.*quantity.*', r'.*count.*', r'.*units.*'],
        'weight': 0.7
    },
    'category': {
        'exact': ['category', 'type', 'segment', 'industry', 'sector', 'group'],
        'contains': ['category', 'type', 'segment', 'industry', 'sector'],
        'regex': [r'.*category.*', r'.*segment.*', r'.*industry.*'],
        'weight': 0.6
    },
    'region': {
        'exact': ['region', 'country', 'location', 'city', 'state', 'area', 'territory'],
        'contains': ['region', 'country', 'location', 'city', 'state', 'geo'],
        'regex': [r'.*region.*', r'.*country.*', r'.*location.*'],
        'weight': 0.6
    },
    'id': {
        'exact': ['id', 'invoice_id', 'order_id', 'transaction_id', 'customer_id', 'product_id'],
        'contains': ['_id', 'number', 'no.', 'num'],
        'regex': [r'.*_id$', r'.*_no$', r'.*_number$'],
        'weight': 0.5
    }
}

# Currency symbols and patterns
CURRENCY_INDICATORS = ['$', '€', '£', '₹', '¥', 'USD', 'EUR', 'GBP', 'INR', 'JPY']


def similarity_score(str1: str, str2: str) -> float:
    """Calculate string similarity using SequenceMatcher"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def detect_column_type(column_name: str, sample_values: List) -> Tuple[str, float]:
    """
    Detect the semantic type of a column based on name and sample values
    Returns: (column_type, confidence_score)
    """
    col_lower = column_name.lower().strip().replace(' ', '_')
    best_match = ('unknown', 0.0)
    
    for col_type, patterns in COLUMN_PATTERNS.items():
        score = 0.0
        
        # Exact match (highest priority)
        if col_lower in patterns['exact']:
            score = 1.0 * patterns['weight']
        
        # Contains match
        elif any(p in col_lower for p in patterns['contains']):
            score = 0.8 * patterns['weight']
        
        # Regex match
        elif any(re.match(r, col_lower) for r in patterns['regex']):
            score = 0.7 * patterns['weight']
        
        # Fuzzy similarity match
        else:
            max_similarity = max(similarity_score(col_lower, p) for p in patterns['exact'])
            if max_similarity > 0.6:
                score = max_similarity * 0.6 * patterns['weight']
        
        # Boost score based on value analysis
        if sample_values and score > 0:
            value_boost = analyze_values_for_type(col_type, sample_values)
            score = min(1.0, score + value_boost)
        
        if score > best_match[1]:
            best_match = (col_type, score)
    
    return best_match


def analyze_values_for_type(col_type: str, sample_values: List) -> float:
    """Analyze sample values to boost confidence for a column type"""
    if not sample_values:
        return 0.0
    
    # Filter out None/NaN values
    valid_values = [v for v in sample_values if v is not None and str(v).strip() != '' and str(v).lower() != 'nan']
    if not valid_values:
        return 0.0
    
    if col_type == 'amount':
        # Check for numeric values or currency symbols
        numeric_count = 0
        currency_count = 0
        for v in valid_values[:20]:
            str_v = str(v)
            if any(c in str_v for c in CURRENCY_INDICATORS):
                currency_count += 1
            try:
                cleaned = re.sub(r'[^\d.-]', '', str_v)
                if cleaned and float(cleaned) > 0:
                    numeric_count += 1
            except:
                pass
        
        if currency_count > len(valid_values[:20]) * 0.3:
            return 0.3
        if numeric_count > len(valid_values[:20]) * 0.8:
            return 0.15
    
    elif col_type == 'date':
        # Check for date-like values
        date_count = 0
        for v in valid_values[:20]:
            str_v = str(v)
            if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', str_v) or \
               re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', str_v):
                date_count += 1
        if date_count > len(valid_values[:20]) * 0.5:
            return 0.2
    
    elif col_type == 'quantity':
        # Check for small integers
        int_count = 0
        for v in valid_values[:20]:
            try:
                num = float(v)
                if num == int(num) and 0 < num < 10000:
                    int_count += 1
            except:
                pass
        if int_count > len(valid_values[:20]) * 0.8:
            return 0.1
    
    return 0.0


def smart_detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Intelligently detect and map columns to standard business fields
    Returns: {'standard_field': 'actual_column_name', ...}
    """
    if df is None or df.empty:
        return {}
    
    results = {}
    column_scores = {}
    
    # First pass: Score all columns for all types
    for col in df.columns:
        sample_values = df[col].head(20).tolist()
        col_type, confidence = detect_column_type(col, sample_values)
        
        if confidence > 0.3:  # Minimum confidence threshold
            if col_type not in column_scores:
                column_scores[col_type] = []
            column_scores[col_type].append((col, confidence))
    
    # Second pass: Assign best match for each type (avoid duplicates)
    used_columns = set()
    for col_type in ['amount', 'customer', 'product', 'date', 'quantity', 'category', 'region']:
        if col_type in column_scores:
            # Sort by confidence, highest first
            candidates = sorted(column_scores[col_type], key=lambda x: x[1], reverse=True)
            for col, confidence in candidates:
                if col not in used_columns:
                    results[col_type] = col
                    used_columns.add(col)
                    break
    
    print(f"📊 Smart Column Detection Results:")
    for field, col in results.items():
        print(f"   {field}: {col}")
    
    return results


def get_data_profile(df: pd.DataFrame) -> Dict:
    """
    Generate a comprehensive data profile for the uploaded data
    Returns profile with detected columns, data quality, and recommendations
    """
    if df is None or df.empty:
        return {'error': 'No data available', 'has_data': False}
    
    column_mapping = smart_detect_columns(df)
    
    # Determine data type
    has_amount = 'amount' in column_mapping
    has_customer = 'customer' in column_mapping
    has_product = 'product' in column_mapping
    has_date = 'date' in column_mapping
    has_quantity = 'quantity' in column_mapping
    
    # Classify data type
    if has_amount and (has_customer or has_product):
        data_type = 'sales_data'
        analysis_mode = 'revenue'
    elif has_quantity and has_product:
        data_type = 'inventory_data'
        analysis_mode = 'quantity'
    elif has_customer and not has_amount:
        data_type = 'customer_data'
        analysis_mode = 'count'
    elif has_product and not has_amount:
        data_type = 'product_catalog'
        analysis_mode = 'count'
    else:
        data_type = 'general_data'
        analysis_mode = 'count'
    
    # Calculate data quality score
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    quality_score = max(0, min(100, int((1 - null_cells / total_cells) * 100)))
    
    # Generate recommendations
    recommendations = []
    if not has_amount:
        recommendations.append("Add a revenue/amount column for financial analysis")
    if not has_date:
        recommendations.append("Add date column to enable trend analysis")
    if not has_customer and not has_product:
        recommendations.append("Add customer or product columns for segmentation")
    
    return {
        'has_data': True,
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': list(df.columns),
        'detected_mapping': column_mapping,
        'data_type': data_type,
        'analysis_mode': analysis_mode,
        'quality_score': quality_score,
        'recommendations': recommendations,
        'has_amount': has_amount,
        'has_customer': has_customer,
        'has_product': has_product,
        'has_date': has_date,
        'has_quantity': has_quantity
    }


def apply_column_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Create a standardized DataFrame with mapped columns
    """
    result_df = pd.DataFrame()
    
    for standard_name, actual_column in mapping.items():
        if actual_column in df.columns:
            result_df[standard_name] = df[actual_column]
    
    # Keep original columns too for reference
    for col in df.columns:
        if col not in result_df.columns:
            result_df[f'_original_{col}'] = df[col]
    
    return result_df
