"""
Chart Generation API - Creates Plotly JSON for real-time visualizations
Enterprise-grade charts from user's uploaded data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from graph.query import revenue_dataframe, load_graph
from utils.paths import get_user_paths
from config.settings import Settings

router = APIRouter()


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


def get_user_data(user_id: str) -> pd.DataFrame:
    """Get user's revenue data from uploaded files"""
    try:
        paths = get_user_paths(user_id)
        Settings.GRAPH_DIR = paths["graph"]
        df = revenue_dataframe(user_id)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        print(f"Error getting user data: {e}")
        return pd.DataFrame()


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
    """Generate product/category bar chart"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find product column
    product_col = None
    for col in df.columns:
        if 'product' in col.lower() or 'item' in col.lower() or 'name' in col.lower():
            product_col = col
            break
    
    if product_col is None:
        product_col = df.columns[0]
    
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
    
    # Aggregate by product
    product_revenue = df.groupby(product_col)[amount_col].sum().sort_values(ascending=True).tail(10)
    
    colors = ['#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', 
              '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16']
    
    plotly_json = {
        "data": [{
            "x": product_revenue.values.tolist(),
            "y": product_revenue.index.tolist(),
            "type": "bar",
            "orientation": "h",
            "marker": {"color": colors[:len(product_revenue)]},
            "text": [f"${v:,.0f}" for v in product_revenue.values],
            "textposition": "outside"
        }],
        "layout": {
            "title": {"text": "Top Products by Revenue", "font": {"size": 18, "color": "#e5e7eb"}},
            "xaxis": {"title": "Revenue ($)", "gridcolor": "#374151", "color": "#9ca3af"},
            "yaxis": {"title": "", "gridcolor": "#374151", "color": "#9ca3af"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "margin": {"l": 150, "r": 80, "t": 50, "b": 50}
        }
    }
    
    return plotly_json


def generate_customer_pie_chart(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate customer distribution pie chart"""
    if df.empty:
        return {"error": "No data available"}
    
    # Find customer column
    customer_col = None
    for col in df.columns:
        if 'customer' in col.lower() or 'client' in col.lower() or 'name' in col.lower():
            customer_col = col
            break
    
    if customer_col is None:
        customer_col = df.columns[0]
    
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
    
    # Top 5 customers + Others
    customer_revenue = df.groupby(customer_col)[amount_col].sum().sort_values(ascending=False)
    top_5 = customer_revenue.head(5)
    others = customer_revenue[5:].sum()
    
    labels = top_5.index.tolist()
    values = top_5.values.tolist()
    
    if others > 0:
        labels.append("Others")
        values.append(others)
    
    colors = ['#10b981', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6', '#6b7280']
    
    plotly_json = {
        "data": [{
            "labels": labels,
            "values": values,
            "type": "pie",
            "hole": 0.4,
            "marker": {"colors": colors[:len(labels)]},
            "textinfo": "label+percent",
            "textposition": "outside"
        }],
        "layout": {
            "title": {"text": "Revenue by Customer", "font": {"size": 18, "color": "#e5e7eb"}},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#e5e7eb"},
            "showlegend": True,
            "legend": {"x": 1, "y": 0.5, "font": {"color": "#9ca3af"}}
        }
    }
    
    return plotly_json


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
async def generate_chart(request: ChartRequest):
    """Generate Plotly chart from user's data"""
    try:
        df = get_user_data(request.user_id)
        
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
