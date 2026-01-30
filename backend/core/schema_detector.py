# Universal Schema Detector
"""
Content-Based Column Type Detection

Analyzes actual data values to classify columns, NOT column names.
Works with ANY uploaded data regardless of naming conventions.

Column Types:
- NUMERIC: Numbers (amounts, prices, quantities, values)
- DATETIME: Parseable dates/timestamps (for time-series)
- CATEGORICAL: Low-cardinality text (products, categories, statuses)
- IDENTIFIER: High-cardinality unique text (IDs, order numbers)
- TEXT: Free-form descriptions

Usage:
    from core.schema_detector import detect_schema, get_best_columns
    
    schema = detect_schema(df, filename="sales.xlsx")
    amount_col = schema['best_amount_col']
    date_col = schema['best_date_col']
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
from datetime import datetime

# Column type classifications
class ColumnType:
    NUMERIC = "numeric"
    DATETIME = "datetime"
    CATEGORICAL = "categorical"
    IDENTIFIER = "identifier"
    TEXT = "text"
    UNKNOWN = "unknown"

# Business role classifications
class ColumnRole:
    AMOUNT = "amount"          # Money values (revenue, price, cost)
    QUANTITY = "quantity"      # Count values (units, orders)
    DATE = "date"              # Time-series axis
    ENTITY = "entity"          # Things to group by (customer, product)
    CATEGORY = "category"      # Classification (type, status)
    ID = "id"                  # Unique identifiers
    DESCRIPTION = "description"# Free text

@dataclass
class ColumnInfo:
    """Detected information about a single column"""
    name: str
    dtype: str
    detected_type: str
    detected_role: str
    unique_count: int
    null_count: int
    sample_values: List[Any]
    numeric_stats: Optional[Dict] = None
    
    def to_dict(self):
        return asdict(self)

@dataclass
class DataSchema:
    """Complete schema for a dataset"""
    filename: str
    detected_at: str
    row_count: int
    columns: Dict[str, ColumnInfo]
    best_amount_col: Optional[str]
    best_date_col: Optional[str]
    best_entity_cols: List[str]
    best_category_cols: List[str]
    
    def to_dict(self):
        result = {
            "filename": self.filename,
            "detected_at": self.detected_at,
            "row_count": self.row_count,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
            "best_amount_col": self.best_amount_col,
            "best_date_col": self.best_date_col,
            "best_entity_cols": self.best_entity_cols,
            "best_category_cols": self.best_category_cols,
        }
        return result


def detect_column_type(series: pd.Series, col_name: str) -> Tuple[str, str]:
    """
    Detect column type and business role by analyzing data content.
    
    Returns: (column_type, column_role)
    """
    # Skip if mostly null
    non_null = series.dropna()
    if len(non_null) == 0:
        return ColumnType.UNKNOWN, ColumnRole.DESCRIPTION
    
    # Sample for performance (max 100 rows)
    sample = non_null.head(100)
    unique_count = series.nunique()
    total_count = len(series)
    cardinality_ratio = unique_count / total_count if total_count > 0 else 0
    
    # -------------------------------------------------------------------
    # STEP 1: Check if already datetime dtype
    # -------------------------------------------------------------------
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnType.DATETIME, ColumnRole.DATE
    
    # -------------------------------------------------------------------
    # STEP 2: Check if already numeric dtype
    # -------------------------------------------------------------------
    if pd.api.types.is_numeric_dtype(series):
        # Distinguish amount vs quantity
        col_lower = col_name.lower()
        if any(x in col_lower for x in ['amount', 'price', 'cost', 'total', 'revenue', 'value', 'fee', 'payment']):
            return ColumnType.NUMERIC, ColumnRole.AMOUNT
        elif any(x in col_lower for x in ['qty', 'quantity', 'count', 'units', 'number']):
            return ColumnType.NUMERIC, ColumnRole.QUANTITY
        else:
            # Check value range - amounts typically > 1, quantities are small integers
            if series.mean() > 100:
                return ColumnType.NUMERIC, ColumnRole.AMOUNT
            else:
                return ColumnType.NUMERIC, ColumnRole.QUANTITY
    
    # -------------------------------------------------------------------
    # STEP 3: For object/string columns, try parsing
    # -------------------------------------------------------------------
    
    # Try datetime parsing
    try:
        parsed_dates = pd.to_datetime(sample, errors='coerce')
        valid_dates = parsed_dates.notna().sum()
        if valid_dates >= len(sample) * 0.7:  # 70%+ valid dates
            return ColumnType.DATETIME, ColumnRole.DATE
    except:
        pass
    
    # Try numeric parsing (handles currency symbols like $, ₹, €)
    try:
        cleaned = sample.astype(str).str.replace(r'[$€£₹,\s]', '', regex=True)
        parsed_nums = pd.to_numeric(cleaned, errors='coerce')
        valid_nums = parsed_nums.notna().sum()
        if valid_nums >= len(sample) * 0.7:  # 70%+ valid numbers
            col_lower = col_name.lower()
            if any(x in col_lower for x in ['amount', 'price', 'cost', 'total', 'revenue', 'value']):
                return ColumnType.NUMERIC, ColumnRole.AMOUNT
            else:
                return ColumnType.NUMERIC, ColumnRole.AMOUNT  # Default to amount for money-like values
    except:
        pass
    
    # -------------------------------------------------------------------
    # STEP 4: Categorical vs Identifier vs Text
    # -------------------------------------------------------------------
    col_lower = col_name.lower()
    
    # High cardinality unique values = likely identifier
    if cardinality_ratio > 0.9:
        if any(x in col_lower for x in ['id', 'code', 'number', 'ref', 'key']):
            return ColumnType.IDENTIFIER, ColumnRole.ID
        return ColumnType.IDENTIFIER, ColumnRole.ID
    
    # Low cardinality = categorical
    if unique_count <= 50 or cardinality_ratio < 0.3:
        # PRIORITY CHECK: Columns ending with _type, _category, _status are always CATEGORY
        if any(col_lower.endswith(x) for x in ['_type', '_category', '_status', '_class', '_group', '_segment']):
            return ColumnType.CATEGORICAL, ColumnRole.CATEGORY
        # Check for type/category keywords in middle of name
        if any(x in col_lower for x in ['type', 'category', 'status', 'class', 'group', 'segment']) and \
           not any(x in col_lower for x in ['name', 'title']):
            return ColumnType.CATEGORICAL, ColumnRole.CATEGORY
        
        # Columns ending with _name are ENTITY (customer_name, product_name)
        if col_lower.endswith('_name') or col_lower.endswith('name'):
            return ColumnType.CATEGORICAL, ColumnRole.ENTITY
            
        # Entity keywords
        if any(x in col_lower for x in ['customer', 'client', 'buyer', 'user', 'account', 'vendor', 'supplier']):
            return ColumnType.CATEGORICAL, ColumnRole.ENTITY
        elif any(x in col_lower for x in ['product', 'item', 'service', 'sku']):
            return ColumnType.CATEGORICAL, ColumnRole.ENTITY
        else:
            return ColumnType.CATEGORICAL, ColumnRole.CATEGORY
    
    # Medium cardinality with text = entity names
    if 50 < unique_count <= 500:
        return ColumnType.CATEGORICAL, ColumnRole.ENTITY
    
    # Long text = descriptions
    avg_length = sample.astype(str).str.len().mean()
    if avg_length > 50:
        return ColumnType.TEXT, ColumnRole.DESCRIPTION
    
    return ColumnType.CATEGORICAL, ColumnRole.CATEGORY


def detect_schema(df: pd.DataFrame, filename: str = "unknown") -> DataSchema:
    """
    Analyze a DataFrame and detect the schema with column types and roles.
    
    Args:
        df: DataFrame to analyze
        filename: Source filename for metadata
        
    Returns:
        DataSchema with detected column information
    """
    if df is None or df.empty:
        return DataSchema(
            filename=filename,
            detected_at=datetime.now().isoformat(),
            row_count=0,
            columns={},
            best_amount_col=None,
            best_date_col=None,
            best_entity_cols=[],
            best_category_cols=[],
        )
    
    columns = {}
    amount_candidates = []
    date_candidates = []
    entity_candidates = []
    category_candidates = []
    
    for col in df.columns:
        series = df[col]
        col_type, col_role = detect_column_type(series, col)
        
        # Build column info
        info = ColumnInfo(
            name=col,
            dtype=str(series.dtype),
            detected_type=col_type,
            detected_role=col_role,
            unique_count=series.nunique(),
            null_count=int(series.isna().sum()),
            sample_values=series.dropna().head(5).tolist(),
            numeric_stats=None
        )
        
        # Add numeric stats if applicable
        if col_type == ColumnType.NUMERIC:
            try:
                info.numeric_stats = {
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "mean": float(series.mean()),
                    "sum": float(series.sum()),
                }
            except:
                pass
        
        columns[col] = info
        
        # Track candidates for "best" columns
        if col_role == ColumnRole.AMOUNT:
            amount_candidates.append((col, series.sum() if pd.api.types.is_numeric_dtype(series) else 0))
        elif col_role == ColumnRole.DATE:
            date_candidates.append((col, series.notna().sum()))
        elif col_role == ColumnRole.ENTITY:
            entity_candidates.append(col)
        elif col_role == ColumnRole.CATEGORY:
            category_candidates.append(col)
    
    # Select best columns (highest sum for amount, most non-null for date)
    best_amount = max(amount_candidates, key=lambda x: x[1])[0] if amount_candidates else None
    best_date = max(date_candidates, key=lambda x: x[1])[0] if date_candidates else None
    
    return DataSchema(
        filename=filename,
        detected_at=datetime.now().isoformat(),
        row_count=len(df),
        columns=columns,
        best_amount_col=best_amount,
        best_date_col=best_date,
        best_entity_cols=entity_candidates[:5],  # Top 5 entities
        best_category_cols=category_candidates[:5],  # Top 5 categories
    )


def save_schema(schema: DataSchema, user_id: str, storage_base: Path) -> Path:
    """Save detected schema to user's schema folder."""
    schema_dir = storage_base / user_id / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = schema.filename.replace(" ", "_").replace(".", "_")
    schema_path = schema_dir / f"{safe_name}_schema.json"
    
    with open(schema_path, 'w') as f:
        json.dump(schema.to_dict(), f, indent=2, default=str)
    
    return schema_path


def load_schema(user_id: str, filename: str, storage_base: Path) -> Optional[DataSchema]:
    """Load previously detected schema from storage."""
    safe_name = filename.replace(" ", "_").replace(".", "_")
    schema_path = storage_base / user_id / "schemas" / f"{safe_name}_schema.json"
    
    if not schema_path.exists():
        return None
    
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct DataSchema from dict
        columns = {
            k: ColumnInfo(**v) for k, v in data.get("columns", {}).items()
        }
        
        return DataSchema(
            filename=data["filename"],
            detected_at=data["detected_at"],
            row_count=data["row_count"],
            columns=columns,
            best_amount_col=data.get("best_amount_col"),
            best_date_col=data.get("best_date_col"),
            best_entity_cols=data.get("best_entity_cols", []),
            best_category_cols=data.get("best_category_cols", []),
        )
    except Exception as e:
        print(f"Error loading schema: {e}")
        return None


def get_best_columns(df: pd.DataFrame, filename: str = "data") -> Dict[str, Optional[str]]:
    """
    Convenience function to get best columns for visualization.
    
    Returns:
        Dict with 'amount', 'date', 'entity', 'category' keys
    """
    schema = detect_schema(df, filename)
    return {
        "amount": schema.best_amount_col,
        "date": schema.best_date_col,
        "entity": schema.best_entity_cols[0] if schema.best_entity_cols else None,
        "category": schema.best_category_cols[0] if schema.best_category_cols else None,
        "schema": schema,
    }


# Quick test
if __name__ == "__main__":
    # Test with sample data
    test_df = pd.DataFrame({
        "order_id": ["ORD001", "ORD002", "ORD003"],
        "customer_name": ["Alice", "Bob", "Charlie"],
        "product_type": ["Electronics", "Electronics", "Clothing"],
        "total_amount": ["₹1,500.00", "₹2,300.50", "₹800.00"],
        "order_date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        "quantity": [1, 2, 1],
    })
    
    schema = detect_schema(test_df, "test_orders.xlsx")
    print(f"Best amount col: {schema.best_amount_col}")
    print(f"Best date col: {schema.best_date_col}")
    print(f"Entity cols: {schema.best_entity_cols}")
    print(f"Category cols: {schema.best_category_cols}")
    for col, info in schema.columns.items():
        print(f"  {col}: {info.detected_type} / {info.detected_role}")
