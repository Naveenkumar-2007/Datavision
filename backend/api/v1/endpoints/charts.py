"""
Chart Generation API - Creates Plotly JSON for real-time visualizations
Enterprise-grade charts from user's uploaded data
ChatGPT Pro-level visualizations with premium styling
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from graph.query import revenue_dataframe, load_graph
from utils.paths import get_user_paths
from config.settings import Settings

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# SECURITY HELPER - JWT Authentication
# =============================================================================

def get_secure_user_id(body_user_id: str, x_user_id: Optional[str], authorization: Optional[str]) -> str:
    """
    Get verified user_id from JWT token or headers.
    Priority: JWT token > X-User-ID header > Body data
    """
    # 1. Try JWT token first (most secure)
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            from core.auth import decode_jwt_token
            payload = decode_jwt_token(token)
            if payload and payload.get("sub"):
                return payload["sub"]
        except Exception as e:
            logger.debug(f"JWT decode failed: {e}")
    
    # 2. Try X-User-ID header (from authenticated frontend)
    if x_user_id and x_user_id != "default":
        return x_user_id
    
    # 3. Fallback to body data (least secure)
    if body_user_id and body_user_id != "default":
        logger.warning(f"Using body user_id: {body_user_id} - consider using JWT")
        return body_user_id
    
    # 4. Generate guest fingerprint
    import hashlib
    import time
    return f"guest_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"

# ============================================================================
# PREMIUM COLOR PALETTES - ChatGPT Pro-Level Visualizations
# ============================================================================

PREMIUM_COLORS = {
    "vibrant": [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", 
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"
    ],
    "ocean": [
        "#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A",
        "#0096C7", "#48CAE4", "#ADE8F4", "#03045E", "#0466C8"
    ],
    "sunset": [
        "#FF6B35", "#F7C59F", "#EFEFD0", "#004E89", "#1A659E",
        "#FF9F1C", "#FFBF69", "#CBF3F0", "#2EC4B6", "#E71D36"
    ],
    "forest": [
        "#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2",
        "#B7E4C7", "#D8F3DC", "#1B4332", "#081C15", "#3A5A40"
    ],
    "royal": [
        "#7B2CBF", "#9D4EDD", "#C77DFF", "#E0AAFF", "#5A189A",
        "#6A4C93", "#8B5CF6", "#A78BFA", "#C4B5FD", "#EDE9FE"
    ],
    "neon": [
        "#00FF87", "#00D9FF", "#FF00E5", "#FFE000", "#FF6B00",
        "#00FF41", "#00F5FF", "#FF007A", "#FFD700", "#FF4500"
    ],
    "professional": [
        "#10B981", "#06B6D4", "#F59E0B", "#EF4444", "#8B5CF6",
        "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16"
    ]
}

# Premium chart styling template - HIGH CONTRAST for better visibility
CHART_STYLE = {
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#1F2937"},  # Dark gray for better visibility
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "colorway": PREMIUM_COLORS["vibrant"],
    "title": {"font": {"size": 22, "color": "#111827", "weight": "bold"}},
    "xaxis": {
        "gridcolor": "rgba(156, 163, 175, 0.2)",
        "color": "#374151",  # High contrast labels
        "linecolor": "rgba(107, 114, 128, 0.4)",
        "tickfont": {"size": 12, "color": "#4B5563"}
    },
    "yaxis": {
        "gridcolor": "rgba(156, 163, 175, 0.2)",
        "color": "#374151",  # High contrast labels
        "linecolor": "rgba(107, 114, 128, 0.4)",
        "tickfont": {"size": 12, "color": "#4B5563"}
    },
    "legend": {
        "bgcolor": "rgba(255,255,255,0.7)",  # Semi-transparent background for legend
        "bordercolor": "rgba(209, 213, 219, 0.5)",
        "font": {"color": "#1F2937", "size": 12},
        "orientation": "h",
        "y": -0.2
    },
    "hoverlabel": {
        "bgcolor": "#FFFFFF",
        "bordercolor": "#D1D5DB",
        "font": {"color": "#111827", "size": 14}
    },
    "margin": {"l": 60, "r": 40, "t": 80, "b": 80}
}

def get_color_palette(style: str = "vibrant", count: int = 10) -> List[str]:
    """Get premium color palette with gradient support"""
    palette = PREMIUM_COLORS.get(style, PREMIUM_COLORS["vibrant"])
    # Extend if needed
    while len(palette) < count:
        palette = palette + palette
    return palette[:count]

def apply_premium_layout(layout: dict, title: str) -> dict:
    """Apply premium styling to chart layout"""
    return {
        **layout,
        "title": {"text": title, "font": CHART_STYLE["title"]["font"]},
        "font": CHART_STYLE["font"],
        "paper_bgcolor": CHART_STYLE["paper_bgcolor"],
        "plot_bgcolor": CHART_STYLE["plot_bgcolor"],
        "hoverlabel": CHART_STYLE["hoverlabel"],
        "xaxis": {**layout.get("xaxis", {}), **CHART_STYLE["xaxis"]},
        "yaxis": {**layout.get("yaxis", {}), **CHART_STYLE["yaxis"]},
        "legend": {**layout.get("legend", {}), **CHART_STYLE["legend"]},
        "margin": CHART_STYLE["margin"]
    }


class ChartRequest(BaseModel):
    user_id: str
    chart_type: str  # line, bar, pie, area, scatter, prediction
    data_source: str = "revenue"  # revenue, customers, products
    time_period: Optional[str] = "all"  # all, month, quarter, year


class ChartResponse(BaseModel):
    chart_type: str
    plotly_json: Dict[str, Any]
    summary: str
    data_points: int


# ============================================================================
# ⚡ DATAFRAME CACHE - Prevents reloading on every query
# ============================================================================
import time as _time

_df_cache: Dict[str, Tuple[pd.DataFrame, float]] = {}
_DF_CACHE_TTL = 300  # 5 minutes cache TTL

def _get_cached_df(user_id: str) -> Optional[pd.DataFrame]:
    """Get DataFrame from cache if not expired."""
    if user_id in _df_cache:
        df, timestamp = _df_cache[user_id]
        if _time.time() - timestamp < _DF_CACHE_TTL:
            print(f"[CACHE] ⚡ Using cached DataFrame for user {user_id}")
            return df
        else:
            print(f"[CACHE] Cache expired for user {user_id}")
            del _df_cache[user_id]
    return None

def _set_cached_df(user_id: str, df: pd.DataFrame):
    """Store DataFrame in cache."""
    _df_cache[user_id] = (df, _time.time())
    print(f"[CACHE] Cached DataFrame for user {user_id} ({len(df)} rows)")

def clear_user_cache(user_id: str):
    """Clear cache for a specific user (call when they upload new files)."""
    if user_id in _df_cache:
        del _df_cache[user_id]
        print(f"[CACHE] Cleared cache for user {user_id}")


def get_user_data(user_id: str) -> pd.DataFrame:
    """
    Get user's uploaded data - PRESERVES ORIGINAL COLUMNS for ANY domain.
    Works with HR data, Sales data, Finance data, or any structured data.
    
    ⚡ CACHED: Uses in-memory cache to avoid reloading on every query.
    
    Returns the raw DataFrame with original column names like:
    - HR: Department, Salary, Employee
    - Sales: Customer, Product, Amount
    - Finance: Category, Value, Date
    """
    # ⚡ Check cache first
    cached_df = _get_cached_df(user_id)
    if cached_df is not None:
        return cached_df
    
    try:
        from utils.paths import STORAGE_BASE
        
        all_dfs = []
        
        # 1. Load directly from user's uploaded files
        user_files_dir = STORAGE_BASE / user_id / "files"
        if user_files_dir.exists():
            for file_path in user_files_dir.glob("*.*"):
                if file_path.suffix.lower() not in ['.csv', '.xlsx', '.xls']:
                    continue
                
                try:
                    print(f"[DATA] Loading file: {file_path.name}")
                    
                    if file_path.suffix.lower() == '.csv':
                        df = pd.read_csv(file_path)
                    else:
                        df = pd.read_excel(file_path)
                    
                    if not df.empty:
                        # Keep original column names - no transformation!
                        df['_source_file'] = file_path.name
                        all_dfs.append(df)
                        print(f"[DATA] Loaded {len(df)} rows with columns: {list(df.columns)}")
                        
                except Exception as e:
                    print(f"[DATA] Error loading {file_path}: {e}")
                    continue

        # 2. ⚡ Fetch LIVE Pipelines (Postgres, Snowflake)
        try:
            import psycopg2
            import os
            # Connect to datavision DB
            db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:Naveen%402007@127.0.0.1:5432/datavision")
            sync_url = db_url.replace("+asyncpg", "") # Convert async url to sync for psycopg2
            
            with psycopg2.connect(sync_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, source_type, host, database_name, credentials, target_table FROM data_connections WHERE user_id = %s", (user_id,))
                    connections = cur.fetchall()
            
            for conn_row in connections:
                c_id, source_type, host, database_name, credentials, target_table = conn_row
                
                try:
                    if source_type.lower() in ('postgres', 'postgresql') and target_table:
                        from urllib.parse import quote_plus
                        safe_credentials = quote_plus(credentials) if credentials else ""
                        conn_str = f"postgresql://postgres:{safe_credentials}@{host}/{database_name}"
                        query = f"SELECT * FROM {target_table} LIMIT 500000"
                        live_df = pd.read_sql(query, conn_str)
                        
                        if not live_df.empty:
                            live_df['_source_file'] = f"Live: {target_table} (PostgreSQL)"
                            all_dfs.append(live_df)
                            print(f"[DATA] Loaded {len(live_df)} rows from Live Postgres {target_table}")
                            
                    elif source_type.lower() == 'snowflake' and target_table:
                        try:
                            import snowflake.connector
                            ctx = snowflake.connector.connect(
                                user='admin',
                                password=credentials,
                                account=host,
                                database=database_name,
                                schema='PUBLIC'
                            )
                            query = f"SELECT * FROM {target_table} LIMIT 500000"
                            live_df = pd.read_sql(query, ctx)
                            ctx.close()
                            if not live_df.empty:
                                live_df['_source_file'] = f"Live: {target_table} (Snowflake)"
                                all_dfs.append(live_df)
                        except ImportError:
                            print("[DATA] Snowflake connector not installed, skipping.")
                        except Exception as e:
                            print(f"[DATA] Snowflake connection failed: {e}")
                            
                except Exception as e:
                    print(f"[DATA] Error loading live connection {c_id}: {e}")
                    
        except Exception as e:
            print(f"[DATA] Failed to fetch live connections from DB: {e}")
        
        if not all_dfs:
            print(f"[DATA] No files or live connections for user {user_id}")
            return pd.DataFrame()
            
        # If multiple files/streams, try to combine
        if len(all_dfs) == 1:
            result_df = all_dfs[0]
        else:
            # Check if they have same columns
            first_cols = set(all_dfs[0].columns)
            can_concat = all(set(df.columns) == first_cols for df in all_dfs)
            
            if can_concat:
                result_df = pd.concat(all_dfs, ignore_index=True)
            else:
                # Return largest file/stream if they can't be concatenated safely
                result_df = max(all_dfs, key=len)
        
        # ⚡ Cache the result
        _set_cached_df(user_id, result_df)
        return result_df
        
        # Fallback to revenue_dataframe for backward compatibility
        print(f"[DATA] No files found, falling back to revenue_dataframe")
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        fallback_df = revenue_dataframe(user_id)
        if not fallback_df.empty:
            _set_cached_df(user_id, fallback_df)
        return fallback_df
        
    except Exception as e:
        print(f"[DATA] Error getting user data: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def auto_detect_columns(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """
    Automatically detect the best categorical and numeric columns from ANY dataset.
    Works with HR data, sales data, or any structured data.
    
    Returns: {"category": col_name, "numeric": col_name, "title": suggested_title}
    """
    query_lower = query.lower()
    
    # All columns
    all_cols = list(df.columns)
    
    # Identify column types
    categorical_cols = []
    numeric_cols = []
    
    for col in all_cols:
        col_lower = col.lower()
        # Skip ID and date columns for categorical
        if any(x in col_lower for x in ['id', 'date', 'time', 'index']):
            continue
            
        if df[col].dtype in ['int64', 'float64']:
            numeric_cols.append(col)
        elif df[col].dtype == 'object' or str(df[col].dtype) == 'category':
            # Check if it's a valid categorical (not too many unique values)
            if df[col].nunique() <= 50:
                categorical_cols.append(col)
    
    # Priority 1: Match query terms to actual columns
    matched_cat = None
    matched_num = None
    
    for col in categorical_cols:
        if col.lower() in query_lower or query_lower in col.lower():
            matched_cat = col
            break
    
    for col in numeric_cols:
        if col.lower() in query_lower or query_lower in col.lower():
            matched_num = col
            break
    
    # Priority 2: Use known column patterns
    category_patterns = ['department', 'dept', 'category', 'product', 'customer', 'region', 'type', 'status', 'name']
    numeric_patterns = ['salary', 'amount', 'revenue', 'total', 'sales', 'price', 'cost', 'count', 'value', 'performance', 'rating']
    
    if not matched_cat:
        for pattern in category_patterns:
            for col in categorical_cols:
                if pattern in col.lower():
                    matched_cat = col
                    break
            if matched_cat:
                break
    
    if not matched_num:
        for pattern in numeric_patterns:
            for col in numeric_cols:
                if pattern in col.lower():
                    matched_num = col
                    break
            if matched_num:
                break
    
    # Priority 3: Fall back to first available
    if not matched_cat and categorical_cols:
        matched_cat = categorical_cols[0]
    if not matched_num and numeric_cols:
        matched_num = numeric_cols[0]
    
    # Generate title
    if matched_cat and matched_num:
        title = f"Total {matched_num} by {matched_cat}"
    else:
        title = "Data Analysis"
    
    return {
        "category": matched_cat,
        "numeric": matched_num,
        "title": title,
        "all_categorical": categorical_cols,
        "all_numeric": numeric_cols
    }


def generate_area_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate area chart for cumulative data representation"""
    if df.empty: return {"error": "No data"}
    
    detected = auto_detect_columns(df, query)
    x_col = detected.get("category")
    y_col = detected.get("numeric")
    
    if not x_col or not y_col: return {"error": "Need data for area chart"}
    
    # Sort for area chart consistency
    df = df.sort_values(by=x_col)
    
    trace = {
        "x": df[x_col].tolist(),
        "y": df[y_col].tolist(),
        "type": "scatter",
        "mode": "lines",
        "fill": "tozeroy",
        "line": {"color": "#8b5cf6", "width": 2},
        "fillcolor": "rgba(139, 92, 246, 0.2)"
    }
    
    return apply_premium_layout({
        "data": [trace],
        "layout": {"xaxis": {"title": x_col}, "yaxis": {"title": y_col}}
    }, f"Cumulative {y_col} by {x_col}")

def generate_comparison_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate multi-series comparison chart (e.g., Cat1 vs Cat2 for Metric)"""
    if df.empty: return {"error": "No data"}
    
    params = extract_chart_params_from_query(query)
    detected = auto_detect_columns(df, query)
    
    cat_col = detected.get("category")
    num_col = detected.get("numeric")
    
    if not cat_col or not num_col: return {"error": "Insufficient data for comparison"}
    
    # Check for a second categorical column for multi-series
    all_cats = detected.get("all_categorical")
    series_col = all_cats[1] if len(all_cats) > 1 else None
    
    if not series_col:
        # Fallback to simple bar if no series found
        return generate_dynamic_bar_chart(df, group_col=cat_col, metric_col=num_col)
        
    # Pivot for multi-series
    pivot = df.pivot_table(index=cat_col, columns=series_col, values=num_col, aggfunc='sum').head(10)
    
    data = []
    colors = get_color_palette("professional", len(pivot.columns))
    
    for i, col in enumerate(pivot.columns):
        data.append({
            "x": pivot.index.tolist(),
            "y": pivot[col].tolist(),
            "type": "bar",
            "name": str(col),
            "marker": {"color": colors[i]}
        })
        
    return apply_premium_layout({
        "data": data,
        "layout": {
            "barmode": "group",
            "xaxis": {"title": cat_col},
            "yaxis": {"title": num_col}
        }
    }, f"{num_col} Comparison: {cat_col} by {series_col}")


def generate_revenue_trend_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate revenue trend line chart"""
    if df.empty:
        return {"error": "No data available"}
    
    # Aggregate by date if date column exists
    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            date_col = col
            break
    
    amount_col = None
    for col in df.columns:
        if 'amount' in col.lower() or 'revenue' in col.lower() or 'total' in col.lower():
            amount_col = col
            break
    
    if amount_col is None:
        # Find numeric column
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    if amount_col is None:
        return {"error": "No numeric data found"}
    
    # Create chart data
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(date_col)
        x_data = df[date_col].dt.strftime('%Y-%m-%d').tolist()
        cumulative = df[amount_col].cumsum().tolist()
    else:
        x_data = list(range(1, len(df) + 1))
        cumulative = df[amount_col].cumsum().tolist()
    
    plotly_json = {
        "data": [{
            "x": x_data,
            "y": cumulative,
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Cumulative Revenue",
            "line": {"color": "#10b981", "width": 3},
            "marker": {"size": 6},
            "fill": "tozeroy",
            "fillcolor": "rgba(16, 185, 129, 0.1)"
        }],
        "layout": {
            "title": {"text": "Revenue Trend", "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": "Date", "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "Revenue ($)", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "hovermode": "x unified"
        }
    }
    
    return plotly_json


def generate_product_bar_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate bar chart - auto-detects best columns if product/amount not found"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find category column (product, item, name, or any categorical)
    product_col = None
    for col in df.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ['product', 'item', 'category', 'department', 'name', 'type']):
            product_col = col
            break
    
    # Find amount column (any numeric)
    amount_col = None
    for col in df.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ['amount', 'revenue', 'total', 'salary', 'sales', 'price', 'value']):
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    # Fallback: use auto-detection
    if not product_col or not amount_col:
        detected = auto_detect_columns(df)
        if not product_col:
            product_col = detected.get("category")
        if not amount_col:
            amount_col = detected.get("numeric")
    
    # Final fallback to first columns
    if not product_col:
        for col in df.columns:
            if df[col].dtype == 'object' and df[col].nunique() <= 50:
                product_col = col
                break
    if not amount_col:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    if not product_col or not amount_col:
        return {"error": f"Could not find suitable columns. Available: {list(df.columns)}"}
    
    print(f"[CHART] product_bar using: category={product_col}, numeric={amount_col}")
    
    # Aggregate by product
    try:
        product_revenue = df.groupby(product_col)[amount_col].sum().sort_values(ascending=True).tail(10)
    except Exception as e:
        return {"error": f"Aggregation failed: {str(e)}"}
    
    if product_revenue.empty or product_revenue.sum() == 0:
        return {"error": "No data after aggregation"}
    
    colors = [
        '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
    ]
    
    title = f"Top 10 {product_col} by {amount_col}"
    
    plotly_json = {
        "data": [{
            "x": product_revenue.values.tolist(),
            "y": product_revenue.index.tolist(),
            "type": "bar",
            "orientation": "h",
            "marker": {"color": colors[:len(product_revenue)]},
            "text": [f"{v:,.0f}" for v in product_revenue.values],
            "textposition": "outside"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": amount_col, "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 150, "r": 80, "t": 50, "b": 50}
        }
    }
    return plotly_json


def generate_customer_bar_chart(df: pd.DataFrame, limit: int = 10, entity: str = "customer") -> Dict[str, Any]:
    """Generate dynamic bar chart for customers/products with configurable limit"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find entity column based on entity type
    entity_col = None
    if entity == "customer":
        for col in df.columns:
            if 'customer' in col.lower() or 'client' in col.lower():
                entity_col = col
                break
    elif entity == "product":
        for col in df.columns:
            if 'product' in col.lower() or 'item' in col.lower():
                entity_col = col
                break
    
    if entity_col is None:
        entity_col = df.columns[0]
    
    # Find amount column
    amount_col = None
    for col in df.columns:
        if 'amount' in col.lower() or 'revenue' in col.lower() or 'total' in col.lower():
            amount_col = col
            break
    
    if amount_col is None:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    if amount_col is None:
        return {"error": "No numeric data found"}
    
    # Aggregate and limit dynamically
    entity_revenue = df.groupby(entity_col)[amount_col].sum().sort_values(ascending=True).tail(limit)
    
    # Expanded colors for 20+ items
    colors = [
        '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
        '#a855f7', '#22c55e', '#3b82f6', '#f43f5e', '#0ea5e9',
        '#d946ef', '#eab308', '#0284c7', '#78716c', '#dc2626'
    ]
    
    title = f"Top {limit} {entity.title()}s by Revenue"
    
    plotly_json = {
        "data": [{
            "x": entity_revenue.values.tolist(),
            "y": entity_revenue.index.tolist(),
            "type": "bar",
            "orientation": "h",
            "marker": {"color": colors[:len(entity_revenue)]},
            "text": [f"₹{v:,.0f}" for v in entity_revenue.values],
            "textposition": "outside"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": "Revenue (₹)", "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 150, "r": 80, "t": 50, "b": 50}
        }
    }
    
    return plotly_json


def extract_chart_params_from_query(query: str) -> Dict[str, Any]:
    """
    Extract chart parameters from natural language query.
    ChatGPT Pro-level extraction for complex visualization requests.
    """
    import re
    
    params = {
        "limit": 10,
        "entity": None,
        "metric": None,
        "chart_type": "bar", # Default
        "group_by": None,
        "secondary_metric": None,
        "is_comparison": False
    }
    
    q_lower = query.lower()
    
    # Detect Chart Type
    type_map = {
        'trend': ['trend', 'over time', 'daily', 'monthly', 'yearly', 'timeline', 'forecast', 'predict'],
        'pie': ['pie', 'breakdown', 'distribution', 'share', 'proportion', 'segment'],
        'radar': ['radar', 'spider', 'skill', 'attributes', 'comparison', 'profile'],
        'scatter': ['scatter', 'correlation', 'relationship', 'vs', 'versus'],
        'area': ['area', 'stacked', 'cumulative'],
        'box': ['box', 'distribution', 'variance', 'quartile', 'outlier'],
        'line': ['line', 'trend'],
        'bar': ['bar', 'ranking', 'top', 'compare']
    }
    
    for c_type, keywords in type_map.items():
        if any(kw in q_lower for kw in keywords):
            params["chart_type"] = c_type
            break
            
    # Detect limit
    num_match = re.search(r'top\s+(\d+)|(\d+)\s+top|last\s+(\d+)', q_lower)
    if num_match:
        params["limit"] = int(next(g for g in num_match.groups() if g))
        
    # Detect "is comparison"
    if any(kw in q_lower for kw in ['compare', 'vs', 'versus', 'against']):
        params["is_comparison"] = True
        
    # Detect potential metric/entity matches (Fuzzy/Pattern)
    patterns = {
        "metric": ['salary', 'amount', 'revenue', 'total', 'sales', 'price', 'cost', 'count', 'value', 'performance', 'rating'],
        "entity": ['department', 'dept', 'product', 'customer', 'client', 'employee', 'staff', 'region', 'category', 'type']
    }
    
    for p_type, words in patterns.items():
        for word in words:
            if word in q_lower:
                if params[p_type] is None:
                    params[p_type] = word
                elif p_type == "metric" and params["secondary_metric"] is None:
                    params["secondary_metric"] = word
                    
    # Group By Detection
    by_match = re.search(r'by\s+(\w+)', q_lower)
    if by_match:
        params["group_by"] = by_match.group(1)
        
    return params


def generate_radar_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate radar chart for comparison of multiple attributes"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find categorical column (for entities/departments)
    cat_col = None
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() <= 20:
            cat_col = col
            break
    
    if not cat_col:
        return {"error": "No categorical column found for radar chart"}
    
    # Find ALL numeric columns (for attributes)
    num_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
    
    if len(num_cols) < 2:
        return {"error": f"Need at least 2 numeric columns for radar chart. Found: {len(num_cols)}"}
    
    # Limit to 5 attributes max for readability
    num_cols = num_cols[:5]
    
    try:
        # Group by category and calculate mean for each numeric column
        pivot = df.groupby(cat_col)[num_cols].mean().head(5)  # Top 5 entities
        
        if pivot.empty:
            return {"error": "No data after grouping"}
        
        # Create radar traces
        data = []
        colors = ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        for idx, (index, row) in enumerate(pivot.iterrows()):
            data.append({
                "type": "scatterpolar",
                "r": row.values.tolist(),
                "theta": num_cols,
                "fill": "toself",
                "name": str(index),
                "line": {"color": colors[idx % len(colors)]}
            })
        
        return apply_premium_layout({
            "data": data,
            "layout": {
                "polar": {
                    "radialaxis": {
                        "visible": True,
                        "range": [0, float(pivot.values.max()) * 1.1],
                        "tickfont": {"color": "#e5e7eb", "size": 12},
                        "linecolor": "#6b7280",
                        "gridcolor": "#4b5563"
                    },
                    "angularaxis": {
                        "tickfont": {"color": "#f3f4f6", "size": 14},
                        "linecolor": "#6b7280",
                        "gridcolor": "#4b5563"
                    },
                    "bgcolor": "rgba(0,0,0,0)"
                },
                "showlegend": True,
                "legend": {"font": {"color": "#e5e7eb", "size": 12}},
                "font": {"color": "#e5e7eb"}
            }
        }, f"Radar: {', '.join(num_cols[:3])}{'...' if len(num_cols) > 3 else ''}")
        
    except Exception as e:
        return {"error": f"Radar chart generation failed: {str(e)}"}

def generate_scatter_plot(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate scatter plot for correlation analysis"""
    if df.empty: return {"error": "No data"}
    
    detected = auto_detect_columns(df, query)
    num_cols = detected.get("all_numeric")
    cat_col = detected.get("category")
    
    if len(num_cols) < 2: return {"error": "Need 2 numeric columns for scatter"}
    
    x_col, y_col = num_cols[0], num_cols[1]
    
    trace = {
        "x": df[x_col].tolist(),
        "y": df[y_col].tolist(),
        "mode": "markers",
        "type": "scatter",
        "marker": {"size": 10, "opacity": 0.6, "color": "#10b981"}
    }
    
    if cat_col:
        trace["text"] = df[cat_col].tolist()
        
    return apply_premium_layout({
        "data": [trace],
        "layout": {
            "xaxis": {"title": x_col},
            "yaxis": {"title": y_col}
        }
    }, f"Relationship: {x_col} vs {y_col}")

def generate_box_plot(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate box plot for distribution analysis"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find categorical column
    cat_col = None
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() <= 20:
            cat_col = col
            break
    
    # Find numeric column
    num_col = None
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            num_col = col
            break
    
    if not cat_col:
        return {"error": "No categorical column found for box plot"}
    if not num_col:
        return {"error": "No numeric column found for box plot"}
    
    try:
        # Get unique categories (limit to 10 for readability)
        unique_cats = df[cat_col].unique()[:10]
        
        # Create box traces
        data = []
        colors = ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        for idx, cat in enumerate(unique_cats):
            cat_data = df[df[cat_col] == cat][num_col].dropna().tolist()
            if cat_data:  # Only add if there's data
                data.append({
                    "y": cat_data,
                    "type": "box",
                    "name": str(cat),
                    "boxmean": True,
                    "marker": {"color": colors[idx % len(colors)]}
                })
        
        if not data:
            return {"error": "No valid data for box plot after filtering"}
        
        return apply_premium_layout({
            "data": data,
            "layout": {
                "yaxis": {"title": num_col},
                "xaxis": {"title": cat_col}
            }
        }, f"Distribution of {num_col} by {cat_col}")
        
    except Exception as e:
        return {"error": f"Box plot generation failed: {str(e)}"}


# =============================================================================
# NEW DYNAMIC CHART TYPES - Work with ANY data schema
# =============================================================================

def generate_histogram(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate histogram for distribution of a numeric column"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find numeric column from query or first available
    num_col = None
    query_lower = query.lower()
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            if col.lower() in query_lower:
                num_col = col
                break
    
    if not num_col:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                num_col = col
                break
    
    if not num_col:
        return {"error": "No numeric column found for histogram"}
    
    try:
        values = df[num_col].dropna().tolist()
        
        return apply_premium_layout({
            "data": [{
                "x": values,
                "type": "histogram",
                "marker": {"color": "#4ECDC4", "line": {"color": "#1f2937", "width": 1}},
                "opacity": 0.8
            }],
            "layout": {"xaxis": {"title": num_col}, "yaxis": {"title": "Frequency"}, "bargap": 0.05}
        }, f"Distribution of {num_col}")
        
    except Exception as e:
        return {"error": f"Histogram generation failed: {str(e)}"}


def generate_heatmap(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate heatmap for correlation visualization"""
    if df.empty:
        return {"error": "No data available"}
    
    num_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
    
    if len(num_cols) < 2:
        return {"error": f"Need at least 2 numeric columns for heatmap. Found: {len(num_cols)}"}
    
    try:
        num_cols = num_cols[:8]
        corr = df[num_cols].corr()
        
        return apply_premium_layout({
            "data": [{
                "z": corr.values.tolist(),
                "x": num_cols,
                "y": num_cols,
                "type": "heatmap",
                "colorscale": "RdBu",
                "zmin": -1, "zmax": 1,
                "showscale": True
            }],
            "layout": {"xaxis": {"tickangle": -45}}
        }, f"Correlation Heatmap ({len(num_cols)} variables)")
        
    except Exception as e:
        return {"error": f"Heatmap generation failed: {str(e)}"}


def generate_area_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate area chart for cumulative visualization"""
    if df.empty:
        return {"error": "No data available"}
    
    cat_col = None
    num_col = None
    
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() <= 30:
            cat_col = col
            break
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            num_col = col
            break
    
    if not cat_col or not num_col:
        return {"error": "Need categorical and numeric columns for area chart"}
    
    try:
        grouped = df.groupby(cat_col)[num_col].sum().sort_index()
        
        return apply_premium_layout({
            "data": [{
                "x": grouped.index.tolist(),
                "y": grouped.values.tolist(),
                "type": "scatter",
                "mode": "lines",
                "fill": "tozeroy",
                "fillcolor": "rgba(78, 205, 196, 0.4)",
                "line": {"color": "#4ECDC4", "width": 2}
            }],
            "layout": {"xaxis": {"title": cat_col}, "yaxis": {"title": num_col}}
        }, f"Cumulative {num_col} by {cat_col}")
        
    except Exception as e:
        return {"error": f"Area chart generation failed: {str(e)}"}


def generate_funnel_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate funnel chart for progression analysis"""
    if df.empty:
        return {"error": "No data available"}
    
    cat_col = None
    num_col = None
    
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() <= 15:
            cat_col = col
            break
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            num_col = col
            break
    
    if not cat_col or not num_col:
        return {"error": "Need categorical and numeric columns for funnel"}
    
    try:
        grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(8)
        
        return apply_premium_layout({
            "data": [{
                "type": "funnel",
                "y": grouped.index.tolist(),
                "x": grouped.values.tolist(),
                "textinfo": "value+percent initial",
                "marker": {"color": ["#FF6B35", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]}
            }],
            "layout": {}
        }, f"{num_col} Funnel by {cat_col}")
        
    except Exception as e:
        return {"error": f"Funnel chart generation failed: {str(e)}"}


def generate_treemap(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate treemap for hierarchical proportion visualization"""
    if df.empty:
        return {"error": "No data available"}
    
    cat_col = None
    num_col = None
    
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() <= 20:
            cat_col = col
            break
    
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            num_col = col
            break
    
    if not cat_col or not num_col:
        return {"error": "Need categorical and numeric columns for treemap"}
    
    try:
        grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
        
        return apply_premium_layout({
            "data": [{
                "type": "treemap",
                "labels": grouped.index.tolist(),
                "parents": [""] * len(grouped),
                "values": grouped.values.tolist(),
                "textinfo": "label+value+percent root",
                "marker": {"colors": ["#FF6B35", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9"][:len(grouped)]}
            }],
            "layout": {}
        }, f"{num_col} Treemap by {cat_col}")
        
    except Exception as e:
        return {"error": f"Treemap generation failed: {str(e)}"}


def generate_gauge_chart(df: pd.DataFrame, query: str = "") -> Dict[str, Any]:
    """Generate gauge chart for KPI visualization"""
    if df.empty:
        return {"error": "No data available"}
    
    num_col = None
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            num_col = col
            break
    
    if not num_col:
        return {"error": "No numeric column found for gauge"}
    
    try:
        value = df[num_col].mean()
        max_val = df[num_col].max()
        
        return apply_premium_layout({
            "data": [{
                "type": "indicator",
                "mode": "gauge+number+delta",
                "value": value,
                "title": {"text": f"Average {num_col}", "font": {"color": "#e5e7eb"}},
                "delta": {"reference": max_val * 0.7},
                "gauge": {
                    "axis": {"range": [0, max_val], "tickfont": {"color": "#e5e7eb"}},
                    "bar": {"color": "#4ECDC4"},
                    "bgcolor": "#374151",
                    "steps": [
                        {"range": [0, max_val * 0.33], "color": "#ef4444"},
                        {"range": [max_val * 0.33, max_val * 0.66], "color": "#f59e0b"},
                        {"range": [max_val * 0.66, max_val], "color": "#10b981"}
                    ]
                }
            }],
            "layout": {"font": {"color": "#e5e7eb"}}
        }, f"{num_col} Gauge")
        
    except Exception as e:
        return {"error": f"Gauge chart generation failed: {str(e)}"}


def generate_dynamic_bar_chart(df: pd.DataFrame, group_col: str = None, metric_col: str = None, title: str = None, limit: int = 10) -> Dict[str, Any]:
    """
    Generate a bar chart grouped by any column with any metric.
    If columns not specified or not found, AUTO-DETECT from dataframe.
    """
    if df.empty:
        return {"error": "No data available"}
    
    # Step 1: Try to find specified columns with fuzzy matching
    group_column = None
    metric_column = None
    
    if group_col:
        for col in df.columns:
            if group_col.lower() in col.lower() or col.lower() in group_col.lower():
                group_column = col
                break
    
    if metric_col:
        for col in df.columns:
            if metric_col.lower() in col.lower() or col.lower() in metric_col.lower():
                metric_column = col
                break
    
    # Step 2: If not found, AUTO-DETECT columns
    if not group_column or not metric_column:
        print(f"[CHART] Columns not found (group={group_col}, metric={metric_col}), auto-detecting...")
        detected = auto_detect_columns(df)
        
        if not group_column:
            group_column = detected.get("category")
        if not metric_column:
            metric_column = detected.get("numeric")
        if not title:
            title = detected.get("title", "Data Analysis")
    
    # Step 3: Final validation
    if not group_column or not metric_column:
        print(f"[CHART] ERROR: Could not detect columns. Available: {list(df.columns)}")
        return {"error": f"Could not auto-detect columns. Available: {list(df.columns)}"}
    
    if group_column not in df.columns:
        return {"error": f"Column '{group_column}' not found"}
    if metric_column not in df.columns:
        return {"error": f"Column '{metric_column}' not found"}
    
    print(f"[CHART] Using columns: group={group_column}, metric={metric_column}")
    
    # Ensure metric column is numeric
    if not pd.api.types.is_numeric_dtype(df[metric_column]):
        df[metric_column] = pd.to_numeric(df[metric_column], errors='coerce')
    
    # Aggregate by group
    grouped = df.groupby(group_column)[metric_column].sum().sort_values(ascending=True).tail(limit)
    
    if grouped.empty or grouped.sum() == 0:
        return {"error": "No data to visualize after aggregation"}
    
    colors = [
        '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
    ]
    
    final_title = title or f"Total {metric_column} by {group_column}"
    
    plotly_json = {
        "data": [{
            "x": grouped.values.tolist(),
            "y": grouped.index.tolist(),
            "type": "bar",
            "orientation": "h",
            "marker": {"color": colors[:len(grouped)]},
            "text": [f"{v:,.0f}" for v in grouped.values],
            "textposition": "outside"
        }],
        "layout": {
            "title": {"text": final_title, "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": metric_column, "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 150, "r": 80, "t": 50, "b": 50}
        }
    }
    return plotly_json


def generate_donut_chart(df: pd.DataFrame, query: str = "", colors: List[str] = None) -> Dict[str, Any]:
    """Generate donut chart (pie with hole in center)"""
    if df.empty:
        return {"error": "No data available"}
    
    detected = auto_detect_columns(df, query)
    cat_col = detected.get("category")
    num_col = detected.get("numeric")
    
    if not cat_col or not num_col:
        return {"error": "Could not detect columns for donut chart"}
    
    grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
    
    # Use provided colors or get from palette
    if not colors:
        colors = get_color_palette("vibrant", len(grouped))
    
    return apply_premium_layout({
        "data": [{
            "type": "pie",
            "labels": [str(x) for x in grouped.index.tolist()],
            "values": [float(x) for x in grouped.values.tolist()],
            "hole": 0.4,  # This makes it a donut!
            "marker": {"colors": colors[:len(grouped)]},
            "textinfo": "label+percent",
            "hovertemplate": "%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>"
        }],
        "layout": {"height": 400}
    }, f"{num_col} Distribution by {cat_col}")


def generate_sunburst_chart(df: pd.DataFrame, query: str = "", colors: List[str] = None) -> Dict[str, Any]:
    """Generate hierarchical sunburst chart"""
    if df.empty:
        return {"error": "No data available"}
    
    detected = auto_detect_columns(df, query)
    cat_cols = detected.get("all_categorical", [])
    num_col = detected.get("numeric")
    
    if len(cat_cols) < 1 or not num_col:
        return {"error": "Need categorical and numeric columns for sunburst"}
    
    # Use first categorical for main breakdown
    cat_col = cat_cols[0]
    grouped = df.groupby(cat_col)[num_col].sum()
    
    labels = ["Total"] + [str(x) for x in grouped.index]
    parents = [""] + ["Total"] * len(grouped)
    values = [float(grouped.sum())] + [float(v) for v in grouped.values]
    
    # Use provided colors or get from palette
    if not colors:
        colors = get_color_palette("professional", len(labels))
    
    return apply_premium_layout({
        "data": [{
            "type": "sunburst",
            "labels": labels,
            "parents": parents,
            "values": values,
            "branchvalues": "total",
            "marker": {"colors": colors},
            "textinfo": "label+percent entry",
            "hovertemplate": "%{label}<br>%{value:,.0f}<extra></extra>"
        }],
        "layout": {"height": 450}
    }, f"Hierarchical Breakdown: {cat_col}")


def generate_bubble_chart(df: pd.DataFrame, query: str = "", colors: List[str] = None) -> Dict[str, Any]:
    """Generate bubble chart with size proportional to values"""
    if df.empty:
        return {"error": "No data available"}
    
    detected = auto_detect_columns(df, query)
    cat_col = detected.get("category")
    num_col = detected.get("numeric")
    
    if not cat_col or not num_col:
        return {"error": "Could not detect columns for bubble chart"}
    
    grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(15)
    
    # Normalize sizes (min 20, max 80)
    max_val = grouped.max() if len(grouped) > 0 else 1
    sizes = [max(20, min(80, (v / max_val) * 60 + 20)) for v in grouped.values]
    
    # Use provided colors or get from palette
    if not colors:
        colors = get_color_palette("vibrant", len(grouped))
    
    return apply_premium_layout({
        "data": [{
            "type": "scatter",
            "mode": "markers+text",
            "x": list(range(len(grouped))),
            "y": grouped.values.tolist(),
            "text": grouped.index.tolist(),
            "textposition": "top center",
            "marker": {
                "size": sizes,
                "color": colors,
                "opacity": 0.7,
                "line": {"width": 2, "color": "white"}
            },
            "hovertemplate": "%{text}<br>%{y:,.0f}<extra></extra>"
        }],
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"title": num_col},
            "height": 400
        }
    }, f"Bubble Size by {num_col}")


def generate_query_aware_chart(df: pd.DataFrame, query: str) -> Dict[str, Any]:
    """
    Generate chart dynamically based on user query.
    ChatGPT Pro-level dynamic generation for ANY chart type.
    Orchestrates between specialized chart generators and LLM-driven smart_chart.
    
    CRITICAL: Check for EXPLICIT chart type keywords FIRST to respect user intent.
    """
    from agents.smart_chart import smart_chart, get_color_palette_from_query
    
    query_lower = query.lower()
    print(f"[CHART] Orchestrating visualization for: {query[:50]}...")
    
    # ==========================================================================
    # EXTRACT COLOR PREFERENCE FROM QUERY
    # ==========================================================================
    colors = get_color_palette_from_query(query)
    print(f"[CHART] Color palette selected: {colors[:3]}...")
    
    # ==========================================================================
    # STEP 1: PRIORITIZE LLM-DRIVEN SMART CHART (INTELLIGENT AGENT)
    # This handles ALL chart types (violin, radar, pie, etc.) with advanced logic
    # ==========================================================================
    try:
        if 'smart_chart' in globals() or 'smart_chart' in locals():
            currency_symbol, _ = get_user_currency("default")
            print(f"[CHART] 🧠 Attempting Smart Chart for: '{query}'")
            chart_result, _ = smart_chart(query, df, currency_symbol=currency_symbol)
            
            # If successful, return immediately!
            if chart_result and 'error' not in chart_result:
                chart_type = chart_result.get('data', [{}])[0].get('type', 'unknown')
                print(f"✅ [CHART] Smart Chart successful! generated: {chart_type}")
                return chart_result
            else:
                print(f"⚠️ [CHART] Smart Chart returned valid format but marked as error or empty")
    except Exception as e:
        print(f"⚠️ [CHART] Smart Chart failed (falling back to manual): {e}")

    # ==========================================================================
    # STEP 2: MANUAL FALLBACKS (If Smart Chart fails)
    # Check for EXPLICIT chart type keywords to respect user intent
    # ==========================================================================
    
    # PIE CHART - User explicitly asked for pie chart (MUST be first check)
    # Broadened detection: 'pie' alone now triggers pie chart
    if 'pie' in query_lower and 'spider' not in query_lower:
        print(f"[CHART] 🥧 PIE CHART request detected in: '{query}'")
        result = generate_customer_pie_chart(df, colors=colors)
        if result and 'error' not in result:
            print(f"✅ [CHART] Pie chart generated successfully!")
            return result
        else:
            error_msg = result.get('error', 'Unknown') if result else 'None returned'
            print(f"⚠️ [CHART] Pie chart failed: {error_msg}")
    
    # DONUT CHART - User explicitly asked for donut
    if any(kw in query_lower for kw in ['donut', 'doughnut']):
        print(f"[CHART] 🍩 Explicit DONUT CHART request detected")
        result = generate_donut_chart(df, query, colors=colors)
        if result and 'error' not in result:
            print(f"✅ [CHART] Donut chart generated successfully!")
            return result
    
    # SUNBURST CHART - User explicitly asked for sunburst
    if any(kw in query_lower for kw in ['sunburst', 'sun burst', 'hierarchical pie']):
        print(f"[CHART] ☀️ Explicit SUNBURST CHART request detected")
        result = generate_sunburst_chart(df, query, colors=colors)
        if result and 'error' not in result:
            print(f"✅ [CHART] Sunburst chart generated successfully!")
            return result
    
    # BUBBLE CHART - User explicitly asked for bubble
    if any(kw in query_lower for kw in ['bubble chart', 'bubble graph', 'bubble']):
        print(f"[CHART] 🫧 Explicit BUBBLE CHART request detected")
        result = generate_bubble_chart(df, query, colors=colors)
        if result and 'error' not in result:
            print(f"✅ [CHART] Bubble chart generated successfully!")
            return result
    
    # BAR CHART - User explicitly asked for bar chart
    if any(kw in query_lower for kw in ['bar chart', 'bar graph', 'as a bar']):
        print(f"[CHART] 📊 Explicit BAR CHART request detected")
        cols = auto_detect_columns(df, query)
        if cols.get('category') and cols.get('numeric'):
            result = generate_dynamic_bar_chart(df, cols['category'], cols['numeric'], cols['title'])
            if result and 'error' not in result:
                print(f"✅ [CHART] Bar chart generated successfully!")
                return result
    
    # LINE CHART - User explicitly asked for line chart
    if any(kw in query_lower for kw in ['line chart', 'line graph']):
        print(f"[CHART] 📈 Explicit LINE CHART request detected")
        result = generate_revenue_trend_chart(df)
        if result and 'error' not in result:
            print(f"✅ [CHART] Line chart generated successfully!")
            return result
    
    # BOX PLOT - User explicitly asked for box plot
    if 'box' in query_lower and ('plot' in query_lower or 'chart' in query_lower):
        print(f"[CHART] 📦 Explicit BOX PLOT request detected")
        result = generate_box_plot(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Box plot generated successfully!")
            return result
        else:
            print(f"⚠️ [CHART] Box plot failed: {result.get('error', 'Unknown')}")
    
    # RADAR CHART - User explicitly asked for radar
    if 'radar' in query_lower:
        print(f"[CHART] 📡 Explicit RADAR CHART request detected")
        result = generate_radar_chart(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Radar chart generated successfully!")
            return result
        else:
            print(f"⚠️ [CHART] Radar chart failed: {result.get('error', 'Unknown')}")
    
    # SCATTER PLOT - User explicitly asked for scatter
    if 'scatter' in query_lower:
        print(f"[CHART] 📊 Explicit SCATTER PLOT request detected")
        result = generate_scatter_plot(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Scatter plot generated successfully!")
            return result
    
    # HISTOGRAM - User wants frequency distribution
    if 'histogram' in query_lower or 'frequency' in query_lower:
        print(f"[CHART] 📊 Explicit HISTOGRAM request detected")
        result = generate_histogram(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Histogram generated successfully!")
            return result
    
    # HEATMAP - User wants correlation/heatmap
    if 'heatmap' in query_lower or 'correlation' in query_lower:
        print(f"[CHART] 🗺️ Explicit HEATMAP request detected")
        result = generate_heatmap(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Heatmap generated successfully!")
            return result
    
    # AREA CHART - User wants cumulative/area
    if 'area' in query_lower and 'chart' in query_lower:
        print(f"[CHART] 📈 Explicit AREA CHART request detected")
        result = generate_area_chart(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Area chart generated successfully!")
            return result
    
    # FUNNEL CHART - User wants funnel/progression
    if 'funnel' in query_lower:
        print(f"[CHART] 📥 Explicit FUNNEL CHART request detected")
        result = generate_funnel_chart(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Funnel chart generated successfully!")
            return result
    
    # TREEMAP - User wants hierarchical treemap
    if 'treemap' in query_lower or 'tree map' in query_lower:
        print(f"[CHART] 🌳 Explicit TREEMAP request detected")
        result = generate_treemap(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Treemap generated successfully!")
            return result
    
    # GAUGE CHART - User wants KPI gauge
    if 'gauge' in query_lower or 'kpi' in query_lower:
        print(f"[CHART] 🎯 Explicit GAUGE CHART request detected")
        result = generate_gauge_chart(df, query)
        if result and 'error' not in result:
            print(f"✅ [CHART] Gauge chart generated successfully!")
            return result
    
    # COMPARISON - User wants to compare things
    params = extract_chart_params_from_query(query)
    if params["is_comparison"]:
        print(f"[CHART] 🔄 Comparison chart detected")
        result = generate_comparison_chart(df, query)
        if 'error' not in result:
            return result
    
    # PREDICTION - User wants prediction/forecast
    if params["chart_type"] == "prediction" or 'predict' in query_lower or 'forecast' in query_lower:
        print(f"[CHART] 🔮 Prediction chart detected")
        result = generate_prediction_chart(df)
        if 'error' not in result:
            return result
    
    # TREND - User wants trend analysis
    if params["chart_type"] == "trend" or 'trend' in query_lower or 'over time' in query_lower:
        print(f"[CHART] 📈 Trend chart detected")
        result = generate_revenue_trend_chart(df)
        if 'error' not in result:
            return result
    


    # ==========================================================================
    # STEP 3: DYNAMIC BAR/PIE FALLBACK
    # ==========================================================================
    cols = auto_detect_columns(df, query)
    if cols.get('category') and cols.get('numeric'):
        if 'pie' in query_lower or 'donut' in query_lower:
            # 1. Try smart/specific pie chart first
            result = generate_customer_pie_chart(df)
            if 'error' not in result:
                return result
            
            # 2. Desperate Fallback: Force Generic Pie Chart using detected columns
            # This prevents showing a bar chart when user explicitly asked for Pie
            print(f"[CHART] 🥧 Force Generic Pie Chart for: '{query}'")
            return generate_dynamic_pie_chart(
                df, 
                category_col=cols.get('category'), 
                value_col=cols.get('numeric'),
                title=f"Distribution of {cols.get('numeric')} by {cols.get('category')}"
            )
            
        # Default to bar chart for aggregation queries
        result = generate_dynamic_bar_chart(
            df, 
            group_col=cols.get('category'),
            metric_col=cols.get('numeric'),
            title=cols.get('title')
        )

        if 'error' not in result:
            return result
    
    # ==========================================================================
    # STEP 4: LAST RESORT - Return informative error
    # ==========================================================================
    return {
        "error": f"Could not generate visualization for this query. Available columns: {', '.join(df.columns[:5])}"
    }



def generate_customer_pie_chart(df: pd.DataFrame, colors: List[str] = None) -> Dict[str, Any]:
    """Generate pie chart - UNIVERSAL for ANY domain (HR, Sales, etc.)
    
    Args:
        df: DataFrame with the data
        colors: Optional list of colors from query-based palette
    """
    if df.empty:
        return {"error": "No data available"}
    
    # Find grouping column - UNIVERSAL detection for ANY domain
    group_col = None
    group_keywords = [
        # HR
        'department', 'dept', 'team', 'division', 'role', 'position',
        # Sales
        'customer', 'client', 'category', 'product',
        # General
        'region', 'location', 'type', 'group', 'name', 'segment'
    ]
    
    for col in df.columns:
        col_lower = col.lower()
        for kw in group_keywords:
            if kw in col_lower:
                group_col = col
                break
        if group_col:
            break
    
    # Fallback: first text column
    if group_col is None:
        for col in df.columns:
            if df[col].dtype == 'object':
                group_col = col
                break
    
    if group_col is None:
        group_col = df.columns[0]
    
    # Find amount/value column - UNIVERSAL detection for ANY domain
    amount_col = None
    amount_keywords = [
        # HR
        'salary', 'wage', 'pay', 'compensation', 'income',
        # Sales
        'amount', 'revenue', 'total', 'sales', 'price', 'value',
        # General
        'cost', 'sum', 'count', 'quantity'
    ]
    
    for col in df.columns:
        col_lower = col.lower()
        for kw in amount_keywords:
            if kw in col_lower:
                amount_col = col
                break
        if amount_col:
            break
    
    # Fallback: first numeric column
    if amount_col is None:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    if amount_col is None:
        return {"error": "No numeric data found for pie chart"}
    
    print(f"[PIE CHART] Using group_col={group_col}, amount_col={amount_col}")
    
    # Ensure numeric type
    if not pd.api.types.is_numeric_dtype(df[amount_col]):
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    
    # Get ALL items dynamically - no hardcoded limit
    grouped = df.groupby(group_col)[amount_col].sum().sort_values(ascending=False)
    
    if grouped.empty or grouped.sum() == 0:
        return {"error": "No data to visualize after grouping"}
    
    labels = [str(x) for x in grouped.index.tolist()]
    values = [float(x) for x in grouped.values.tolist()]
    
    # Use provided colors or default palette
    if not colors:
        colors = [
            '#10b981', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16',
            '#a855f7', '#22c55e', '#3b82f6', '#f43f5e', '#0ea5e9',
            '#d946ef', '#eab308', '#0284c7', '#78716c', '#dc2626'
        ]
    
    # Extend colors if needed
    while len(colors) < len(labels):
        colors = colors + colors
    
    # Dynamic title based on detected columns
    title = f"{amount_col.replace('_', ' ').title()} by {group_col.replace('_', ' ').title()}"
    
    print(f"[PIE CHART] ✅ Creating pie chart with {len(labels)} slices")
    
    plotly_json = {
        "data": [{
            "labels": labels,
            "values": values,
            "type": "pie",
            "hole": 0.4,
            "marker": {"colors": colors[:len(labels)]},
            "textinfo": "label+percent",
            "textposition": "outside",
            "hovertemplate": "%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>"
        }],
        "layout": {
            "title": {"text": title, "font": {"size": 18, "color": "#e5e7eb"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "showlegend": True,
            "legend": {"x": 1, "y": 0.5, "font": {"color": "#9ca3af"}},
            "height": 450
        }
    }
    
    return plotly_json


def generate_dynamic_pie_chart(
    df: pd.DataFrame, 
    category_col: str, 
    value_col: str, 
    title: str = "Pie Chart"
) -> Dict[str, Any]:
    """
    Force generate a generic pie chart from known columns.
    Used as valid backup when smart detection fails but we have columns.
    """
    if df.empty or not category_col or not value_col:
        return {"error": "Invalid data for pie chart"}
        
    try:
        # Aggregate data properly
        grouped = df.groupby(category_col)[value_col].sum().sort_values(ascending=False)
        
        # Limit to top 20 slices to avoiding crashing functionality
        grouped = grouped.head(20)
        
        labels = [str(x) for x in grouped.index.tolist()]
        values = [float(x) for x in grouped.values.tolist()]
        
        colors = [
            '#10b981', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6',
            '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
        ]
        
        return {
            "data": [{
                "labels": labels,
                "values": values,
                "type": "pie",
                "hole": 0.4, # Donut style looks modern
                "marker": {"colors": colors[:len(labels)]},
                "textinfo": "label+percent",
                "textposition": "outside",
                "hovertemplate": "%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>"
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16, "color": "#e5e7eb"}},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#e5e7eb"},
                "showlegend": True,
                "legend": {"x": 1, "y": 0.5},
                "height": 450
            }
        }
    except Exception as e:
        print(f"Generic pie chart failed: {e}")
        return {"error": str(e)}


def generate_prediction_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate prediction chart with forecast band"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find amount column
    amount_col = None
    for col in df.columns:
        if 'amount' in col.lower() or 'revenue' in col.lower() or 'total' in col.lower():
            amount_col = col
            break
    
    if amount_col is None:
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                amount_col = col
                break
    
    if amount_col is None:
        return {"error": "No numeric data found"}
    
    # Simple linear regression for prediction
    values = df[amount_col].values
    x = np.arange(len(values))
    
    # Fit line
    if len(values) > 1:
        slope, intercept = np.polyfit(x, values, 1)
    else:
        slope, intercept = 0, values[0] if len(values) > 0 else 0
    
    # Predict next 5 periods
    future_x = np.arange(len(values), len(values) + 5)
    predictions = slope * future_x + intercept
    
    # Confidence band (simple ±15%)
    upper_band = predictions * 1.15
    lower_band = predictions * 0.85
    
    # Historical data
    x_data = list(range(1, len(values) + 1))
    
    # Future dates labels
    future_labels = [f"Period {i+1}" for i in future_x]
    
    plotly_json = {
        "data": [
            # Historical data
            {
                "x": x_data,
                "y": values.tolist(),
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Historical",
                "line": {"color": "#10b981", "width": 3},
                "marker": {"size": 8}
            },
            # Prediction line
            {
                "x": list(range(len(values) + 1, len(values) + 6)),
                "y": predictions.tolist(),
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Prediction",
                "line": {"color": "#f59e0b", "width": 3, "dash": "dash"},
                "marker": {"size": 8}
            },
            # Upper confidence band
            {
                "x": list(range(len(values) + 1, len(values) + 6)),
                "y": upper_band.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Upper Bound",
                "line": {"color": "rgba(245, 158, 11, 0.3)", "width": 0},
                "showlegend": False
            },
            # Lower confidence band (fill to upper)
            {
                "x": list(range(len(values) + 1, len(values) + 6)),
                "y": lower_band.tolist(),
                "type": "scatter",
                "mode": "lines",
                "name": "Confidence Band",
                "line": {"color": "rgba(245, 158, 11, 0.3)", "width": 0},
                "fill": "tonexty",
                "fillcolor": "rgba(245, 158, 11, 0.2)"
            }
        ],
        "layout": {
            "title": {"text": "Revenue Prediction (Next 5 Periods)", "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": "Period", "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "Revenue ($)", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 60, "r": 30, "t": 50, "b": 50},
            "legend": {"x": 0, "y": 1.1, "orientation": "h", "font": {"color": "#9ca3af"}},
            "hovermode": "x unified"
        },
        "prediction_summary": {
            "next_period": float(predictions[0]),
            "trend": "up" if slope > 0 else "down",
            "growth_rate": float(slope / intercept * 100) if intercept != 0 else 0
        }
    }
    
    return plotly_json


@router.post("/generate", response_model=ChartResponse)
async def generate_chart(
    request: ChartRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Generate Plotly chart from user's data - SECURED"""
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(request.user_id, x_user_id, authorization)
        df = get_user_data(secure_user_id)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found. Please upload files first.")
        
        chart_type = request.chart_type.lower()
        
        if chart_type in ["line", "trend", "revenue"]:
            plotly_json = generate_revenue_trend_chart(df)
            summary = f"Revenue trend chart with {len(df)} data points"
        elif chart_type in ["bar", "product", "products"]:
            plotly_json = generate_product_bar_chart(df)
            summary = f"Product comparison chart from {len(df)} records"
        elif chart_type in ["pie", "customer", "customers", "distribution"]:
            plotly_json = generate_customer_pie_chart(df)
            summary = f"Customer distribution from {len(df)} records"
        elif chart_type in ["prediction", "forecast", "predict"]:
            plotly_json = generate_prediction_chart(df)
            summary = f"Revenue prediction based on {len(df)} historical points"
        else:
            # Default to revenue trend
            plotly_json = generate_revenue_trend_chart(df)
            summary = f"Revenue trend chart with {len(df)} data points"
        
        return ChartResponse(
            chart_type=chart_type,
            plotly_json=plotly_json,
            summary=summary,
            data_points=len(df)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chart generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-types")
async def get_available_chart_types():
    """Get list of available chart types"""
    return {
        "chart_types": [
            {"id": "trend", "name": "Revenue Trend", "description": "Line chart showing revenue over time"},
            {"id": "bar", "name": "Product Comparison", "description": "Bar chart comparing products"},
            {"id": "pie", "name": "Customer Distribution", "description": "Pie chart of customer revenue"},
            {"id": "prediction", "name": "Revenue Prediction", "description": "Forecast with confidence band"}
        ]
    }
