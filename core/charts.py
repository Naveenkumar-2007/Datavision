# Chart Generation Module
"""
Generate real charts and visualizations for business data.

Features:
- Revenue charts (bar, line, pie)
- Trend analysis charts
- Prediction charts with forecasting
- Customer/Product comparisons
"""

import matplotlib
matplotlib.use('Agg')  # Non-GUI backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import io
import base64
import uuid


# Chart styling for dark theme
CHART_STYLE = {
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#1a1a2e',
    'axes.edgecolor': '#4a4a6a',
    'axes.labelcolor': '#e0e0e0',
    'text.color': '#e0e0e0',
    'xtick.color': '#a0a0a0',
    'ytick.color': '#a0a0a0',
    'grid.color': '#3a3a5a',
    'legend.facecolor': '#2a2a4a',
    'legend.edgecolor': '#4a4a6a'
}

# Color palette
COLORS = {
    'primary': '#8b5cf6',      # Purple
    'secondary': '#06b6d4',    # Cyan
    'success': '#10b981',      # Green
    'warning': '#f59e0b',      # Amber
    'danger': '#ef4444',       # Red
    'info': '#3b82f6',         # Blue
    'gradient': ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#3b82f6']
}


def apply_dark_style():
    """Apply dark theme to matplotlib"""
    plt.style.use('dark_background')
    for key, value in CHART_STYLE.items():
        plt.rcParams[key] = value
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10


def generate_revenue_bar_chart(
    data: Dict[str, float],
    title: str = "Revenue by Category",
    currency_symbol: str = "₹",
    highlight_top: bool = True,
    highlight_bottom: bool = True
) -> str:
    """
    Generate a bar chart for revenue data.
    
    Returns:
        Base64 encoded image string
    """
    apply_dark_style()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    categories = list(data.keys())
    values = list(data.values())
    
    # Create color array
    colors = [COLORS['primary']] * len(values)
    
    if highlight_top and values:
        max_idx = values.index(max(values))
        colors[max_idx] = COLORS['success']
    
    if highlight_bottom and values:
        min_idx = values.index(min(values))
        colors[min_idx] = COLORS['danger']
    
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=0.5)
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{currency_symbol}{val:,.0f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                color='white')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Category', fontsize=11)
    ax.set_ylabel(f'Revenue ({currency_symbol})', fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    # Rotate labels if many categories
    if len(categories) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    return _save_chart(fig)


def generate_trend_line_chart(
    data: Dict[str, float],
    title: str = "Revenue Trend",
    currency_symbol: str = "₹",
    show_prediction: bool = False,
    prediction_periods: int = 3
) -> str:
    """
    Generate a line chart for trend data.
    
    Returns:
        Base64 encoded image string
    """
    apply_dark_style()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    periods = list(data.keys())
    values = list(data.values())
    
    # Plot actual data
    ax.plot(periods, values, marker='o', markersize=8, linewidth=2.5,
            color=COLORS['primary'], label='Actual')
    
    # Fill area under curve
    ax.fill_between(periods, values, alpha=0.2, color=COLORS['primary'])
    
    # Add prediction if requested
    if show_prediction and len(values) >= 2:
        # Simple linear prediction
        x_numeric = np.arange(len(values))
        z = np.polyfit(x_numeric, values, 1)
        p = np.poly1d(z)
        
        # Extend for prediction
        future_x = np.arange(len(values), len(values) + prediction_periods)
        future_periods = [f"Period +{i+1}" for i in range(prediction_periods)]
        future_values = p(future_x)
        
        # Plot prediction line
        all_periods = periods + future_periods
        all_values = values + list(future_values)
        
        ax.plot(all_periods[len(values)-1:], [values[-1]] + list(future_values),
                marker='o', markersize=6, linewidth=2, linestyle='--',
                color=COLORS['warning'], label='Predicted')
        
        ax.fill_between(all_periods[len(values)-1:], [values[-1]] + list(future_values),
                       alpha=0.1, color=COLORS['warning'])
    
    # Add value labels
    for i, (period, val) in enumerate(zip(periods, values)):
        ax.annotate(f'{currency_symbol}{val:,.0f}',
                   (period, val), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=8,
                   color='white')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Period', fontsize=11)
    ax.set_ylabel(f'Revenue ({currency_symbol})', fontsize=11)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left')
    
    # Rotate labels if needed
    if len(periods) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    return _save_chart(fig)


def generate_prediction_chart(
    historical_data: Dict[str, float],
    prediction_months: int = 3,
    title: str = "Revenue Prediction",
    currency_symbol: str = "₹",
    growth_scenario: str = "moderate"  # conservative, moderate, aggressive
) -> Tuple[str, Dict]:
    """
    Generate prediction chart with multiple scenarios.
    
    Returns:
        Tuple of (base64 image, prediction data dict)
    """
    apply_dark_style()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    periods = list(historical_data.keys())
    values = list(historical_data.values())
    
    # Calculate growth rates
    growth_rates = {
        'conservative': 0.02,   # 2% monthly
        'moderate': 0.05,       # 5% monthly
        'aggressive': 0.10      # 10% monthly
    }
    
    rate = growth_rates.get(growth_scenario, 0.05)
    
    # Plot historical data
    ax.plot(range(len(values)), values, marker='o', markersize=8, linewidth=2.5,
            color=COLORS['primary'], label='Historical')
    ax.fill_between(range(len(values)), values, alpha=0.2, color=COLORS['primary'])
    
    # Generate predictions
    last_value = values[-1]
    predictions = []
    
    for i in range(prediction_months):
        predicted = last_value * (1 + rate) ** (i + 1)
        predictions.append(predicted)
    
    # Create prediction x-axis
    pred_x = range(len(values) - 1, len(values) + prediction_months)
    pred_y = [last_value] + predictions
    
    # Plot prediction
    ax.plot(pred_x, pred_y, marker='s', markersize=6, linewidth=2.5,
            linestyle='--', color=COLORS['success'], label=f'Prediction ({growth_scenario.title()})')
    ax.fill_between(pred_x, pred_y, alpha=0.15, color=COLORS['success'])
    
    # Add confidence band
    upper_band = [v * 1.15 for v in pred_y]
    lower_band = [v * 0.85 for v in pred_y]
    ax.fill_between(pred_x, lower_band, upper_band, alpha=0.1, color=COLORS['warning'],
                   label='Confidence Range (±15%)')
    
    # Labels
    all_labels = periods + [f"+{i+1} month" for i in range(prediction_months)]
    ax.set_xticks(range(len(all_labels)))
    ax.set_xticklabels(all_labels, rotation=45, ha='right')
    
    # Add value annotations
    for i, val in enumerate(values):
        ax.annotate(f'{currency_symbol}{val:,.0f}',
                   (i, val), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=8, color='white')
    
    for i, val in enumerate(predictions):
        ax.annotate(f'{currency_symbol}{val:,.0f}',
                   (len(values) + i, val), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=8, color=COLORS['success'])
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Period', fontsize=11)
    ax.set_ylabel(f'Revenue ({currency_symbol})', fontsize=11)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper left')
    
    plt.tight_layout()
    
    # Prepare prediction data
    prediction_data = {
        'scenario': growth_scenario,
        'growth_rate': rate * 100,
        'predictions': {
            f"+{i+1} month": round(pred, 2)
            for i, pred in enumerate(predictions)
        },
        'total_predicted_growth': round((predictions[-1] - last_value) / last_value * 100, 2)
    }
    
    return _save_chart(fig), prediction_data


def generate_pie_chart(
    data: Dict[str, float],
    title: str = "Revenue Distribution",
    currency_symbol: str = "₹"
) -> str:
    """
    Generate a pie chart for distribution data.
    
    Returns:
        Base64 encoded image string
    """
    apply_dark_style()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    labels = list(data.keys())
    values = list(data.values())
    
    # Use gradient colors
    colors = COLORS['gradient'][:len(values)]
    if len(values) > len(colors):
        colors = colors * (len(values) // len(colors) + 1)
    colors = colors[:len(values)]
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct='%1.1f%%',
        colors=colors, explode=[0.02] * len(values),
        shadow=True, startangle=90
    )
    
    # Style text
    for text in texts:
        text.set_color('white')
        text.set_fontsize(10)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add legend with values
    legend_labels = [f'{l}: {currency_symbol}{v:,.0f}' for l, v in zip(labels, values)]
    ax.legend(wedges, legend_labels, title="Values", loc="center left",
             bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    
    return _save_chart(fig)


def generate_comparison_chart(
    data: Dict[str, Dict[str, float]],
    title: str = "Comparison",
    currency_symbol: str = "₹"
) -> str:
    """
    Generate a grouped bar chart for comparisons.
    
    Args:
        data: Dict like {"Category1": {"A": 100, "B": 200}, "Category2": {...}}
    
    Returns:
        Base64 encoded image string
    """
    apply_dark_style()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    categories = list(data.keys())
    sub_categories = list(data[categories[0]].keys())
    
    x = np.arange(len(categories))
    width = 0.8 / len(sub_categories)
    
    colors = COLORS['gradient'][:len(sub_categories)]
    
    for i, (sub_cat, color) in enumerate(zip(sub_categories, colors)):
        values = [data[cat].get(sub_cat, 0) for cat in categories]
        offset = (i - len(sub_categories)/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=sub_cat, color=color)
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{currency_symbol}{val:,.0f}',
                   ha='center', va='bottom', fontsize=8, color='white')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Category', fontsize=11)
    ax.set_ylabel(f'Value ({currency_symbol})', fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    return _save_chart(fig)


def _save_chart(fig) -> str:
    """Save chart and return base64 string"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    buffer.seek(0)
    
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def save_chart_to_file(base64_image: str, filename: str = None) -> str:
    """Save base64 image to file and return path"""
    from config.settings import Settings
    
    if filename is None:
        filename = f"chart_{uuid.uuid4().hex[:8]}.png"
    
    chart_dir = Settings.STORAGE / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = chart_dir / filename
    
    # Remove data URL prefix
    if base64_image.startswith('data:image'):
        base64_image = base64_image.split(',')[1]
    
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(base64_image))
    
    return str(filepath)


# Convenience functions
def generate_customer_revenue_chart(df: pd.DataFrame, currency_symbol: str = "₹") -> str:
    """Generate customer revenue chart from dataframe"""
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    customer_rev = df.groupby('customer')[amount_col].sum().to_dict()
    return generate_revenue_bar_chart(customer_rev, "💰 Customer Revenue", currency_symbol)


def generate_product_revenue_chart(df: pd.DataFrame, currency_symbol: str = "₹") -> str:
    """Generate product revenue chart from dataframe"""
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    product_rev = df.groupby('product')[amount_col].sum().to_dict()
    return generate_pie_chart(product_rev, "📦 Product Revenue Distribution", currency_symbol)


def generate_monthly_trend_chart(df: pd.DataFrame, currency_symbol: str = "₹", 
                                 show_prediction: bool = False) -> str:
    """Generate monthly trend chart from dataframe"""
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    if 'date' in df.columns:
        df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
        df_dated = df[df['date_parsed'].notna()].copy()
        
        if not df_dated.empty:
            df_dated['month'] = df_dated['date_parsed'].dt.strftime('%Y-%m')
            monthly = df_dated.groupby('month')[amount_col].sum().to_dict()
            return generate_trend_line_chart(monthly, "📈 Monthly Revenue Trend", 
                                            currency_symbol, show_prediction)
    
    return None
