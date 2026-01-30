# MCP Data Cleaner Module
"""
Data cleaning and preprocessing tools for MCP integration.

Features:
- Table cleaning and normalization
- Number formatting (currency, percentages)
- Date normalization
- Deduplication
- Missing value handling
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any, Union
import re
from datetime import datetime


@dataclass
class CleaningOptions:
    """Options for data cleaning"""
    remove_empty_rows: bool = True
    remove_empty_cols: bool = True
    strip_whitespace: bool = True
    normalize_case: bool = False
    handle_missing: str = "keep"  # "keep", "remove", "fill"
    fill_value: Any = None


def clean_table(
    data: Union[Dict, List[Dict], Any],
    options: Optional[CleaningOptions] = None
) -> Dict:
    """
    Clean and normalize tabular data.
    
    Args:
        data: DataFrame dict, list of dicts, or pandas DataFrame
        options: Cleaning configuration
        
    Returns:
        Cleaned data as dict
    """
    options = options or CleaningOptions()
    
    try:
        import pandas as pd
        
        # Convert to DataFrame
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            return {"error": "Unsupported data type", "data": None}
        
        # Strip whitespace from string columns
        if options.strip_whitespace:
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Remove empty rows
        if options.remove_empty_rows:
            df = df.dropna(how='all')
        
        # Remove empty columns
        if options.remove_empty_cols:
            df = df.dropna(axis=1, how='all')
        
        # Handle missing values
        if options.handle_missing == "remove":
            df = df.dropna()
        elif options.handle_missing == "fill" and options.fill_value is not None:
            df = df.fillna(options.fill_value)
        
        # Normalize case
        if options.normalize_case:
            for col in df.select_dtypes(include=['object']).columns:
                df[col] = df[col].str.lower()
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "rows": len(df),
            "columns": list(df.columns)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


def format_numbers(
    data: Any,
    columns: List[str],
    format_type: str = "decimal",
    decimal_places: int = 2,
    currency_symbol: str = "₹"
) -> Dict:
    """
    Format and standardize numeric columns.
    
    Args:
        data: DataFrame or dict
        columns: Columns to format
        format_type: "decimal", "currency", "percentage", "integer"
        decimal_places: Number of decimal places
        currency_symbol: Symbol for currency formatting
        
    Returns:
        Data with formatted numbers
    """
    try:
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        for col in columns:
            if col not in df.columns:
                continue
            
            # Clean and convert to numeric
            df[col] = _clean_numeric_column(df[col])
            
            if format_type == "currency":
                df[col] = df[col].apply(
                    lambda x: f"{currency_symbol}{x:,.{decimal_places}f}" if pd.notna(x) else ""
                )
            elif format_type == "percentage":
                df[col] = df[col].apply(
                    lambda x: f"{x:.{decimal_places}f}%" if pd.notna(x) else ""
                )
            elif format_type == "integer":
                df[col] = df[col].apply(
                    lambda x: f"{int(x):,}" if pd.notna(x) else ""
                )
            else:  # decimal
                df[col] = df[col].apply(
                    lambda x: f"{x:,.{decimal_places}f}" if pd.notna(x) else ""
                )
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "formatted_columns": columns
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


def _clean_numeric_column(series) -> Any:
    """Clean a column to numeric values"""
    import pandas as pd
    
    def clean_value(val):
        if pd.isna(val):
            return None
        
        # Convert to string and clean
        val_str = str(val)
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[₹$€£,\s]', '', val_str)
        
        # Handle percentage
        if '%' in val_str:
            cleaned = cleaned.replace('%', '')
            try:
                return float(cleaned)
            except:
                return None
        
        try:
            return float(cleaned)
        except:
            return None
    
    return series.apply(clean_value)


def normalize_dates(
    data: Any,
    date_columns: List[str],
    output_format: str = "%Y-%m-%d"
) -> Dict:
    """
    Normalize date formats across data.
    
    Args:
        data: DataFrame or dict
        date_columns: Columns containing dates
        output_format: Desired output format
        
    Returns:
        Data with normalized dates
    """
    try:
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        # Common date formats to try
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%d %B %Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        
        for col in date_columns:
            if col not in df.columns:
                continue
            
            df[col] = df[col].apply(
                lambda x: _parse_and_format_date(x, date_formats, output_format)
            )
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "normalized_columns": date_columns,
            "output_format": output_format
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


def _parse_and_format_date(
    value: Any,
    input_formats: List[str],
    output_format: str
) -> str:
    """Parse date with multiple formats and output in standard format"""
    import pandas as pd
    
    if pd.isna(value) or value == '':
        return ''
    
    value_str = str(value).strip()
    
    # Try pandas parsing first (handles many formats)
    try:
        parsed = pd.to_datetime(value_str)
        return parsed.strftime(output_format)
    except:
        pass
    
    # Try specific formats
    for fmt in input_formats:
        try:
            parsed = datetime.strptime(value_str, fmt)
            return parsed.strftime(output_format)
        except:
            continue
    
    # Return original if parsing fails
    return value_str


def deduplicate_rows(
    data: Any,
    subset: Optional[List[str]] = None,
    keep: str = "first"
) -> Dict:
    """
    Remove duplicate rows from data.
    
    Args:
        data: DataFrame or dict
        subset: Columns to consider for duplicates (None = all)
        keep: "first", "last", or False (remove all duplicates)
        
    Returns:
        Deduplicated data
    """
    try:
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        original_count = len(df)
        
        df = df.drop_duplicates(subset=subset, keep=keep)
        
        removed_count = original_count - len(df)
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "original_rows": original_count,
            "remaining_rows": len(df),
            "removed_duplicates": removed_count
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


def fill_missing_values(
    data: Any,
    strategy: str = "mean",
    columns: Optional[List[str]] = None,
    fill_value: Any = None
) -> Dict:
    """
    Fill missing values in data.
    
    Args:
        data: DataFrame or dict
        strategy: "mean", "median", "mode", "forward", "backward", "value"
        columns: Columns to fill (None = all)
        fill_value: Value to use when strategy is "value"
        
    Returns:
        Data with filled values
    """
    try:
        import pandas as pd
        
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        cols = columns or df.columns.tolist()
        
        for col in cols:
            if col not in df.columns:
                continue
            
            if strategy == "mean":
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median":
                if df[col].dtype in ['int64', 'float64']:
                    df[col] = df[col].fillna(df[col].median())
            elif strategy == "mode":
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
            elif strategy == "forward":
                df[col] = df[col].fillna(method='ffill')
            elif strategy == "backward":
                df[col] = df[col].fillna(method='bfill')
            elif strategy == "value" and fill_value is not None:
                df[col] = df[col].fillna(fill_value)
        
        return {
            "success": True,
            "data": df.to_dict(orient='records'),
            "strategy": strategy,
            "processed_columns": cols
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


def detect_anomalies(
    data: Any,
    columns: List[str],
    method: str = "zscore",
    threshold: float = 3.0
) -> Dict:
    """
    Detect anomalies in numeric columns.
    
    Args:
        data: DataFrame or dict
        columns: Numeric columns to check
        method: "zscore", "iqr"
        threshold: Z-score threshold or IQR multiplier
        
    Returns:
        Data with anomaly flags
    """
    try:
        import pandas as pd
        import numpy as np
        
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        
        anomalies = {}
        
        for col in columns:
            if col not in df.columns or df[col].dtype not in ['int64', 'float64']:
                continue
            
            if method == "zscore":
                mean = df[col].mean()
                std = df[col].std()
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    anomaly_mask = z_scores > threshold
                else:
                    anomaly_mask = pd.Series([False] * len(df))
            else:  # IQR
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                anomaly_mask = (df[col] < lower) | (df[col] > upper)
            
            anomalies[col] = {
                "count": int(anomaly_mask.sum()),
                "indices": list(df[anomaly_mask].index)
            }
        
        return {
            "success": True,
            "anomalies": anomalies,
            "method": method,
            "threshold": threshold
        }
        
    except Exception as e:
        return {"success": False, "error": str(e), "anomalies": None}
