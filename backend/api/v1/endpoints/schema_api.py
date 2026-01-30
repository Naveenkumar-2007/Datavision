"""
Unified Schema API Endpoint
============================
Single source of truth for frontend schema consumption.
Returns detected schema metadata for any uploaded dataset.

This endpoint is the CONTRACT between backend and frontend.
All UI elements should derive from this schema response.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)

from utils.paths import get_user_paths
from config.settings import Settings

# Import schema detection modules
try:
    from core.schema_detector import detect_schema, DataSchema, ColumnType, ColumnRole
except ImportError:
    detect_schema = None
    DataSchema = None

try:
    from core.schema_intelligence import (
        UniversalSchemaAnalyzer, 
        SchemaIntelligence, 
        SchemaStorage,
        DynamicAnalyticsGenerator
    )
except ImportError:
    UniversalSchemaAnalyzer = None
    SchemaIntelligence = None

router = APIRouter()


def _load_user_data(user_id: str) -> Optional[pd.DataFrame]:
    """Load all user's uploaded data into a single DataFrame."""
    try:
        paths = get_user_paths(user_id)
        # get_user_paths returns 'files' key, not 'uploads'
        uploads_dir = paths.get("files")
        
        print(f"📂 [SCHEMA API] Looking for files in: {uploads_dir}")
        logger.info(f"📂 [SCHEMA API] Looking for files in: {uploads_dir}")
        
        if not uploads_dir or not Path(uploads_dir).exists():
            logger.warning(f"⚠️ [SCHEMA API] Directory doesn't exist: {uploads_dir}")
            return None
        
        all_data = []
        for file_path in Path(uploads_dir).glob("*"):
            if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                try:
                    logger.info(f"📄 [SCHEMA API] Loading file: {file_path.name}")
                    if file_path.suffix.lower() == '.csv':
                        # FIXED: Force pandas to infer numeric types correctly
                        df = pd.read_csv(
                            file_path,
                            low_memory=False,  # Read entire file to infer types
                            na_values=['', 'NA', 'N/A', 'null', 'NULL'],  # Recognize NA values
                            keep_default_na=True,  # Keep pandas default NA handling
                        )
                    else:
                        df = pd.read_excel(file_path)
                    
                    df['_source_file'] = file_path.name
                    all_data.append(df)
                    logger.info(f"✅ [SCHEMA API] Loaded {len(df)} rows from {file_path.name}")
                    if len(df) > 0:
                        logger.info(f"📊 [SCHEMA API] Column dtypes: {dict(df.dtypes)}")
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"✅ [SCHEMA API] Total: {len(combined)} rows from {len(all_data)} files")
            return combined
        
        print(f"⚠️ [SCHEMA API] No CSV/Excel files found in {uploads_dir}")
        return None
    except Exception as e:
        print(f"Error loading user data: {e}")
        import traceback
        traceback.print_exc()
        return None


def _get_cached_schema(user_id: str) -> Optional[Dict]:
    """Load cached schema from storage if exists."""
    try:
        paths = get_user_paths(user_id)
        schema_dir = paths.get("storage", Path("storage")) / user_id / "schemas"
        
        if not schema_dir.exists():
            return None
        
        # Get most recent schema file
        schema_files = list(schema_dir.glob("*_schema.json"))
        if not schema_files:
            return None
        
        latest = max(schema_files, key=lambda x: x.stat().st_mtime)
        with open(latest, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading cached schema: {e}")
        return None


def _detect_date_range(df: pd.DataFrame, time_column: Optional[str]) -> Optional[Dict]:
    """Detect the date range from the time column."""
    if not time_column or time_column not in df.columns:
        return None
    
    try:
        dates = pd.to_datetime(df[time_column], errors='coerce').dropna()
        if dates.empty:
            return None
        
        return {
            "start": dates.min().isoformat(),
            "end": dates.max().isoformat(),
            "column": time_column
        }
    except Exception:
        return None


@router.get("/{user_id}")
async def get_schema(user_id: str, refresh: bool = Query(False)):
    """
    Get unified schema for user's uploaded data.
    
    This is the SINGLE SOURCE OF TRUTH for frontend.
    All UI elements should derive from this response.
    
    Args:
        user_id: User identifier
        refresh: If True, re-analyze data instead of using cache
    
    Returns:
        Complete schema intelligence with:
        - domain: Detected data domain (Sales, HR, Healthcare, etc.)
        - metrics: All numeric columns suitable for aggregation
        - dimensions: All categorical/entity columns for grouping
        - time_column: Primary date column for time-series
        - date_range: Start/end dates if time column exists
        - suggested_analyses: AI-suggested analytical queries
    """
    try:
        # Try cached schema first
        if not refresh:
            cached = _get_cached_schema(user_id)
            if cached:
                # Add live date range if possible
                df = _load_user_data(user_id)
                if df is not None:
                    cached["date_range"] = _detect_date_range(df, cached.get("time_column"))
                    cached["row_count"] = len(df)
                return cached
        
        # Load data
        df = _load_user_data(user_id)
        
        if df is None or df.empty:
            return {
                "has_data": False,
                "message": "No data uploaded. Upload CSV or Excel files to get started.",
                "domain": None,
                "metrics": [],
                "dimensions": [],
                "time_column": None,
                "date_range": None,
                "columns": []
            }
        
        # Use AI-powered schema analyzer if available
        if UniversalSchemaAnalyzer:
            analyzer = UniversalSchemaAnalyzer()
            schema = analyzer.analyze_dataframe(df, "combined_data")
            
            # Convert to frontend-friendly format
            result = {
                "has_data": True,
                "domain": schema.domain,
                "domain_confidence": schema.domain_confidence,
                "business_context": schema.business_context,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": [col.to_dict() for col in schema.columns],
                "metrics": [
                    {
                        "name": col.name,
                        "type": col.detected_type,
                        "semantic_role": col.semantic_role,
                        "business_meaning": col.business_meaning,
                        "total": float(pd.to_numeric(df[col.name].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True), errors='coerce').fillna(0).sum()),
                        "average": float(pd.to_numeric(df[col.name].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True), errors='coerce').fillna(0).mean()),
                        "min": float(pd.to_numeric(df[col.name].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True), errors='coerce').fillna(0).min()),
                        "max": float(pd.to_numeric(df[col.name].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True), errors='coerce').fillna(0).max()),
                    }
                    for col in schema.columns if col.is_key_metric
                ],
                "dimensions": [
                    {
                        "name": col.name,
                        "type": col.detected_type,
                        "semantic_role": col.semantic_role,
                        "business_meaning": col.business_meaning,
                        "unique_count": int(df[col.name].nunique()),
                        "sample_values": df[col.name].dropna().head(5).astype(str).tolist()
                    }
                    for col in schema.columns if col.is_groupable
                ],
                "time_column": schema.time_column,
                "date_range": _detect_date_range(df, schema.time_column),
                "suggested_analyses": [a.to_dict() for a in schema.suggested_analyses],
                "data_quality": schema.data_quality.to_dict(),
                "chart_recommendations": _generate_chart_recommendations(schema, df),
                "generated_at": datetime.now().isoformat()
            }
            
            return result
        
        # Fallback to basic schema detector
        elif detect_schema:
            schema = detect_schema(df, "combined_data")
            
            # Build metrics list from amount columns
            metrics = []
            for col_name, col_info in schema.columns.items():
                if col_info.detected_role in [ColumnRole.AMOUNT, ColumnRole.QUANTITY]:
                    values = pd.to_numeric(df[col_name].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True), errors='coerce').fillna(0)
                    metrics.append({
                        "name": col_name,
                        "type": col_info.detected_type,
                        "semantic_role": col_info.detected_role,
                        "business_meaning": col_name.replace("_", " ").title(),
                        "total": float(values.sum()),
                        "average": float(values.mean()),
                        "min": float(values.min()),
                        "max": float(values.max()),
                    })
            
            # Build dimensions list from entity/category columns
            dimensions = []
            for col_name, col_info in schema.columns.items():
                if col_info.detected_role in [ColumnRole.ENTITY, ColumnRole.CATEGORY]:
                    dimensions.append({
                        "name": col_name,
                        "type": col_info.detected_type,
                        "semantic_role": col_info.detected_role,
                        "business_meaning": col_name.replace("_", " ").title(),
                        "unique_count": int(df[col_name].nunique()),
                        "sample_values": df[col_name].dropna().head(5).astype(str).tolist()
                    })
            
            return {
                "has_data": True,
                "domain": "Other",
                "domain_confidence": 0.5,
                "business_context": "Uploaded business data",
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": [col.to_dict() for col in schema.columns.values()],
                "metrics": metrics,
                "dimensions": dimensions,
                "time_column": schema.best_date_col,
                "date_range": _detect_date_range(df, schema.best_date_col),
                "suggested_analyses": [],
                "chart_recommendations": [],
                "generated_at": datetime.now().isoformat()
            }
        
        else:
            # Ultra-basic fallback
            return {
                "has_data": True,
                "domain": "Other",
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "metrics": [],
                "dimensions": [],
                "time_column": None,
                "date_range": None,
                "message": "Schema analyzers not available"
            }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _generate_chart_recommendations(schema: 'SchemaIntelligence', df: pd.DataFrame) -> List[Dict]:
    """
    Generate chart type recommendations based on schema.
    
    Rules:
    - time vs metric → line chart
    - category vs metric → bar chart
    - single metric distribution → histogram
    - category contribution → pie chart
    - numeric vs numeric → scatter plot
    """
    recommendations = []
    
    metric_cols = [c for c in schema.columns if c.is_key_metric]
    dimension_cols = [c for c in schema.columns if c.is_groupable]
    
    # Time-series line charts
    if schema.time_column:
        for metric in metric_cols[:3]:  # Limit to top 3
            recommendations.append({
                "chart_type": "line",
                "title": f"{metric.name.replace('_', ' ').title()} Over Time",
                "x_column": schema.time_column,
                "y_column": metric.name,
                "description": f"Trend of {metric.business_meaning} over time"
            })
    
    # Bar charts for category vs metric
    for dim in dimension_cols[:3]:
        for metric in metric_cols[:2]:
            if dim.detected_type == "category":
                recommendations.append({
                    "chart_type": "bar",
                    "title": f"{metric.name.replace('_', ' ').title()} by {dim.name.replace('_', ' ').title()}",
                    "x_column": dim.name,
                    "y_column": metric.name,
                    "description": f"Compare {metric.business_meaning} across {dim.business_meaning}"
                })
    
    # Histogram for metric distribution
    for metric in metric_cols[:2]:
        recommendations.append({
            "chart_type": "histogram",
            "title": f"Distribution of {metric.name.replace('_', ' ').title()}",
            "x_column": metric.name,
            "y_column": None,
            "description": f"Frequency distribution of {metric.business_meaning}"
        })
    
    # Pie chart for category contribution
    if dimension_cols and metric_cols:
        primary_metric = metric_cols[0]
        primary_dim = dimension_cols[0]
        recommendations.append({
            "chart_type": "pie",
            "title": f"{primary_metric.name.replace('_', ' ').title()} by {primary_dim.name.replace('_', ' ').title()}",
            "x_column": primary_dim.name,
            "y_column": primary_metric.name,
            "description": f"Contribution breakdown of {primary_metric.business_meaning}"
        })
    
    # Scatter plot for numeric vs numeric
    if len(metric_cols) >= 2:
        recommendations.append({
            "chart_type": "scatter",
            "title": f"{metric_cols[0].name.replace('_', ' ').title()} vs {metric_cols[1].name.replace('_', ' ').title()}",
            "x_column": metric_cols[0].name,
            "y_column": metric_cols[1].name,
            "description": f"Correlation between {metric_cols[0].business_meaning} and {metric_cols[1].business_meaning}"
        })
    
    return recommendations


@router.get("/{user_id}/metrics")
async def get_schema_metrics(user_id: str):
    """Get only the metric columns from schema."""
    schema = await get_schema(user_id)
    return {
        "metrics": schema.get("metrics", []),
        "primary_metric": schema.get("metrics", [{}])[0].get("name") if schema.get("metrics") else None
    }


@router.get("/{user_id}/dimensions")
async def get_schema_dimensions(user_id: str):
    """Get only the dimension columns from schema."""
    schema = await get_schema(user_id)
    return {
        "dimensions": schema.get("dimensions", []),
        "time_column": schema.get("time_column"),
        "date_range": schema.get("date_range")
    }


@router.get("/{user_id}/chart-data")
async def get_chart_data(
    user_id: str,
    chart_type: str = Query(..., description="line|bar|pie|histogram|scatter"),
    x_column: str = Query(..., description="X-axis column"),
    y_column: Optional[str] = Query(None, description="Y-axis column (optional for histogram)"),
    group_by: Optional[str] = Query(None, description="Group by column"),
    start_date: Optional[str] = Query(None, description="Filter start date"),
    end_date: Optional[str] = Query(None, description="Filter end date"),
    limit: int = Query(20, description="Max items to return")
):
    """
    Get chart-ready data based on selected columns.
    
    This endpoint generates aggregated data suitable for charting,
    fully driven by the column selections from the schema.
    """
    try:
        df = _load_user_data(user_id)
        
        if df is None or df.empty:
            return {"data": [], "message": "No data available"}
        
        # Apply date filter if provided
        schema = await get_schema(user_id)
        time_col = schema.get("time_column")
        
        if start_date and end_date and time_col and time_col in df.columns:
            try:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                df = df[(df[time_col] >= start_date) & (df[time_col] <= end_date)]
            except Exception as e:
                print(f"Date filter error: {e}")
        
        # Validate columns exist
        if x_column not in df.columns:
            return {"data": [], "error": f"Column {x_column} not found"}
        
        if y_column and y_column not in df.columns:
            return {"data": [], "error": f"Column {y_column} not found"}
        
        # Clean numeric columns
        def clean_numeric(col):
            return pd.to_numeric(
                df[col].astype(str).str.replace(r'[$€£₹,\s]', '', regex=True),
                errors='coerce'
            ).fillna(0)
        
        # Generate data based on chart type
        if chart_type == "line":
            # Time series - aggregate by date
            if time_col and time_col in df.columns:
                df_temp = df.copy()
                df_temp['_date'] = pd.to_datetime(df_temp[time_col], errors='coerce')
                df_temp['_value'] = clean_numeric(y_column)
                
                daily = df_temp.groupby(df_temp['_date'].dt.date)['_value'].sum().reset_index()
                daily.columns = ['date', 'value']
                daily = daily.sort_values('date')
                
                return {
                    "chart_type": "line",
                    "x_column": x_column,
                    "y_column": y_column,
                    "data": [
                        {"x": str(row['date']), "y": float(row['value'])}
                        for _, row in daily.iterrows()
                    ]
                }
        
        elif chart_type == "bar":
            # Category breakdown
            df_temp = df.copy()
            df_temp['_value'] = clean_numeric(y_column) if y_column else 1
            
            grouped = df_temp.groupby(x_column)['_value'].sum().sort_values(ascending=False).head(limit)
            
            return {
                "chart_type": "bar",
                "x_column": x_column,
                "y_column": y_column,
                "data": [
                    {"x": str(name), "y": float(value)}
                    for name, value in grouped.items()
                ]
            }
        
        elif chart_type == "pie":
            # Contribution breakdown
            df_temp = df.copy()
            df_temp['_value'] = clean_numeric(y_column) if y_column else 1
            
            grouped = df_temp.groupby(x_column)['_value'].sum().sort_values(ascending=False).head(limit)
            total = grouped.sum()
            
            return {
                "chart_type": "pie",
                "x_column": x_column,
                "y_column": y_column,
                "data": [
                    {
                        "name": str(name),
                        "value": float(value),
                        "percentage": round(value / total * 100, 1) if total > 0 else 0
                    }
                    for name, value in grouped.items()
                ]
            }
        
        elif chart_type == "histogram":
            # Distribution of single metric
            values = clean_numeric(x_column)
            
            # Calculate bins using numpy
            import numpy as np
            hist, bin_edges = np.histogram(values, bins=min(20, len(values.unique())))
            
            return {
                "chart_type": "histogram",
                "x_column": x_column,
                "data": [
                    {
                        "bin_start": float(bin_edges[i]),
                        "bin_end": float(bin_edges[i+1]),
                        "count": int(hist[i])
                    }
                    for i in range(len(hist))
                ]
            }
        
        elif chart_type == "scatter":
            # Two columns required
            if not y_column:
                return {"data": [], "error": "Scatter plot requires two columns"}
            
            # Check if x is numeric or categorical
            is_x_numeric = pd.to_numeric(df[x_column].iloc[:100].astype(str).str.replace(r'[\$,€£¥₹\s]', '', regex=True), errors='coerce').notna().mean() > 0.5
            
            if is_x_numeric:
                x_values = clean_numeric(x_column)
            else:
                # Map categories to numbers for scatter plot
                unique_cats = df[x_column].unique()
                cat_map = {cat: i for i, cat in enumerate(unique_cats)}
                x_values = df[x_column].map(cat_map)
                cat_labels = {i: str(cat) for i, cat in enumerate(unique_cats)}
            
            y_values = clean_numeric(y_column)
            
            df_scatter = pd.DataFrame({'x': x_values, 'y': y_values})
            if not is_x_numeric:
                df_scatter['label'] = df[x_column]
                
            if len(df_scatter) > 500:
                df_scatter = df_scatter.sample(n=500, random_state=42)
            
            return {
                "chart_type": "scatter",
                "x_column": x_column,
                "y_column": y_column,
                "is_x_categorical": not is_x_numeric,
                "data": [
                    {
                        "x": float(row['x']), 
                        "y": float(row['y']), 
                        "label": str(row['label']) if not is_x_numeric else None
                    }
                    for _, row in df_scatter.iterrows()
                ]
            }
        
        return {"data": [], "error": f"Unsupported chart type: {chart_type}"}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"data": [], "error": str(e)}
