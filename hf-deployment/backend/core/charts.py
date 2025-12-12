"""
Premium Charts Module - Enterprise-Grade Visualizations
$50K Quality with Vibrant Colors, Dark Theme, and Animations
"""

import base64
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Premium Color Palettes
VIBRANT_COLORS = [
    '#8B5CF6',  # Purple (primary)
    '#06B6D4',  # Cyan
    '#10B981',  # Emerald
    '#F59E0B',  # Amber
    '#EF4444',  # Red
    '#EC4899',  # Pink
    '#3B82F6',  # Blue
    '#14B8A6',  # Teal
    '#F97316',  # Orange
    '#6366F1',  # Indigo
]

GRADIENT_COLORS = {
    'purple': ['#7C3AED', '#8B5CF6', '#A78BFA'],
    'cyan': ['#0891B2', '#06B6D4', '#22D3EE'],
    'emerald': ['#059669', '#10B981', '#34D399'],
    'amber': ['#D97706', '#F59E0B', '#FBBF24'],
}

# Dark Theme Configuration
DARK_THEME = {
    'bg_color': '#0F0F0F',
    'card_bg': '#1A1A1A',
    'text_color': '#E5E5E5',
    'grid_color': '#2A2A2A',
    'accent': '#8B5CF6',
}

# Light Theme Configuration
LIGHT_THEME = {
    'bg_color': '#FFFFFF',
    'card_bg': '#F8F9FA',
    'text_color': '#1F2937',
    'grid_color': '#E5E7EB',
    'accent': '#7C3AED',
}


def _setup_dark_theme(fig, ax):
    """Apply premium dark theme to chart"""
    fig.patch.set_facecolor(DARK_THEME['bg_color'])
    ax.set_facecolor(DARK_THEME['card_bg'])
    ax.spines['bottom'].set_color(DARK_THEME['grid_color'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(DARK_THEME['grid_color'])
    ax.tick_params(colors=DARK_THEME['text_color'])
    ax.xaxis.label.set_color(DARK_THEME['text_color'])
    ax.yaxis.label.set_color(DARK_THEME['text_color'])
    ax.title.set_color(DARK_THEME['text_color'])
    ax.grid(True, alpha=0.2, color=DARK_THEME['grid_color'])


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor=fig.get_facecolor(), edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{img_base64}"


def generate_customer_revenue_chart(df, currency_symbol: str = '₹', top_n: int = 10) -> str:
    """
    Generate premium customer revenue bar chart with gradient colors
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    if 'customer' not in df.columns:
        return ""
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    customer_revenue = df.groupby('customer')[amount_col].sum().sort_values(ascending=True).tail(top_n)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    _setup_dark_theme(fig, ax)
    
    # Create gradient bars
    y_pos = np.arange(len(customer_revenue))
    colors = [VIBRANT_COLORS[i % len(VIBRANT_COLORS)] for i in range(len(customer_revenue))]
    
    bars = ax.barh(y_pos, customer_revenue.values, color=colors, height=0.7, edgecolor='none')
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, customer_revenue.values)):
        ax.text(val + max(customer_revenue.values) * 0.02, bar.get_y() + bar.get_height()/2,
                f'{currency_symbol}{val:,.0f}', va='center', color=DARK_THEME['text_color'], 
                fontsize=10, fontweight='bold')
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(customer_revenue.index, fontsize=11)
    ax.set_xlabel(f'Revenue ({currency_symbol})', fontsize=12, fontweight='bold')
    ax.set_title('📊 Top Customers by Revenue', fontsize=14, fontweight='bold', pad=20)
    
    # Add subtle glow effect
    ax.axvline(x=0, color=DARK_THEME['accent'], linewidth=2, alpha=0.3)
    
    plt.tight_layout()
    return _fig_to_base64(fig)


def generate_product_revenue_chart(df, currency_symbol: str = '₹', top_n: int = 8) -> str:
    """
    Generate premium product pie/donut chart with vibrant colors
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    if 'product' not in df.columns:
        return ""
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    product_revenue = df.groupby('product')[amount_col].sum().sort_values(ascending=False).head(top_n)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(DARK_THEME['bg_color'])
    
    # Create donut chart
    colors = VIBRANT_COLORS[:len(product_revenue)]
    wedges, texts, autotexts = ax.pie(
        product_revenue.values, 
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor=DARK_THEME['bg_color'], linewidth=3)
    )
    
    # Style percentage labels
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    # Add legend
    legend = ax.legend(
        wedges, 
        [f'{name}: {currency_symbol}{val:,.0f}' for name, val in zip(product_revenue.index, product_revenue.values)],
        loc='center left', 
        bbox_to_anchor=(1, 0.5),
        fontsize=10,
        frameon=False
    )
    for text in legend.get_texts():
        text.set_color(DARK_THEME['text_color'])
    
    # Add center circle with total
    total = product_revenue.sum()
    ax.text(0, 0, f'Total\n{currency_symbol}{total:,.0f}', 
            ha='center', va='center', fontsize=14, fontweight='bold',
            color=DARK_THEME['text_color'])
    
    ax.set_title('📦 Product Revenue Distribution', fontsize=14, fontweight='bold', 
                 color=DARK_THEME['text_color'], pad=20)
    
    plt.tight_layout()
    return _fig_to_base64(fig)


def generate_monthly_trend_chart(df, currency_symbol: str = '₹', show_prediction: bool = True) -> Optional[str]:
    """
    Generate premium monthly trend line chart with gradient fill
    """
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    if 'date' not in df.columns:
        return None
    
    import pandas as pd
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    df_temp = df.copy()
    df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
    df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
    
    if df_dated.empty:
        return None
    
    df_dated['month'] = df_dated['date_parsed'].dt.to_period('M')
    monthly = df_dated.groupby('month')[amount_col].sum()
    
    if len(monthly) < 2:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_theme(fig, ax)
    
    x = np.arange(len(monthly))
    y = monthly.values
    
    # Plot line with gradient fill
    line, = ax.plot(x, y, color=VIBRANT_COLORS[0], linewidth=3, marker='o', markersize=8)
    ax.fill_between(x, y, alpha=0.3, color=VIBRANT_COLORS[0])
    
    # Add value labels
    for i, (xi, yi) in enumerate(zip(x, y)):
        ax.annotate(f'{currency_symbol}{yi:,.0f}', (xi, yi), 
                   textcoords="offset points", xytext=(0, 10),
                   ha='center', fontsize=9, color=DARK_THEME['text_color'])
    
    # Add prediction if requested
    if show_prediction and len(monthly) >= 3:
        # Simple linear prediction
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        future_x = np.array([len(x), len(x)+1, len(x)+2])
        future_y = p(future_x)
        
        ax.plot(future_x, future_y, color=VIBRANT_COLORS[3], linewidth=3, 
                linestyle='--', marker='D', markersize=8, label='Predicted')
        ax.fill_between(future_x, future_y, alpha=0.2, color=VIBRANT_COLORS[3])
        ax.legend(loc='upper left', frameon=False)
    
    # Labels
    ax.set_xticks(x)
    ax.set_xticklabels([str(m) for m in monthly.index], rotation=45, ha='right')
    ax.set_ylabel(f'Revenue ({currency_symbol})', fontsize=12, fontweight='bold')
    ax.set_title('📈 Monthly Revenue Trend', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return _fig_to_base64(fig)


def generate_prediction_chart(monthly_data: Dict[str, float], prediction_months: int = 3,
                              title: str = "Revenue Prediction", 
                              currency_symbol: str = '₹') -> Tuple[str, Dict]:
    """
    Generate premium prediction chart with confidence bands
    """
    if not MATPLOTLIB_AVAILABLE:
        return "", {}
    
    months = list(monthly_data.keys())
    values = list(monthly_data.values())
    
    if len(values) < 2:
        return "", {}
    
    fig, ax = plt.subplots(figsize=(14, 7))
    _setup_dark_theme(fig, ax)
    
    x_actual = np.arange(len(values))
    
    # Calculate prediction
    z = np.polyfit(x_actual, values, 1)
    p = np.poly1d(z)
    
    growth_rate = z[0] / np.mean(values) if np.mean(values) > 0 else 0
    scenario = "growth" if growth_rate > 0.02 else "stable" if growth_rate > -0.02 else "decline"
    
    # Future predictions
    x_pred = np.arange(len(values), len(values) + prediction_months)
    predictions = p(x_pred)
    
    # Confidence bands (±15%)
    conf_upper = predictions * 1.15
    conf_lower = predictions * 0.85
    
    # Plot actual data with gradient
    ax.plot(x_actual, values, color=VIBRANT_COLORS[0], linewidth=3, marker='o', 
            markersize=10, label='Actual Revenue', zorder=3)
    ax.fill_between(x_actual, values, alpha=0.3, color=VIBRANT_COLORS[0])
    
    # Plot predictions with confidence band
    pred_color = VIBRANT_COLORS[2] if scenario == "growth" else VIBRANT_COLORS[3] if scenario == "stable" else VIBRANT_COLORS[4]
    ax.plot(x_pred, predictions, color=pred_color, linewidth=3, linestyle='--',
            marker='D', markersize=10, label='Predicted', zorder=3)
    ax.fill_between(x_pred, conf_lower, conf_upper, alpha=0.2, color=pred_color, label='Confidence Band')
    
    # Add value labels
    for i, (xi, yi) in enumerate(zip(x_actual, values)):
        ax.annotate(f'{currency_symbol}{yi:,.0f}', (xi, yi),
                   textcoords="offset points", xytext=(0, 15),
                   ha='center', fontsize=9, fontweight='bold', color=DARK_THEME['text_color'])
    
    for i, (xi, yi) in enumerate(zip(x_pred, predictions)):
        ax.annotate(f'{currency_symbol}{yi:,.0f}', (xi, yi),
                   textcoords="offset points", xytext=(0, 15),
                   ha='center', fontsize=9, fontweight='bold', color=pred_color)
    
    # Labels
    all_labels = months + [f'+{i+1}M' for i in range(prediction_months)]
    ax.set_xticks(np.arange(len(all_labels)))
    ax.set_xticklabels(all_labels, rotation=45, ha='right')
    ax.set_ylabel(f'Revenue ({currency_symbol})', fontsize=12, fontweight='bold')
    ax.set_title(f'🔮 {title}', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', frameon=False)
    
    # Add scenario indicator
    scenario_text = f"{'📈 Growth' if scenario == 'growth' else '📊 Stable' if scenario == 'stable' else '📉 Decline'} Trend"
    ax.text(0.98, 0.98, scenario_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', horizontalalignment='right',
            color=pred_color, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=DARK_THEME['card_bg'], alpha=0.8))
    
    plt.tight_layout()
    
    # Build prediction data
    pred_data = {
        'scenario': scenario,
        'growth_rate': growth_rate * 100,
        'total_predicted_growth': ((predictions[-1] - values[-1]) / values[-1]) * 100 if values[-1] > 0 else 0,
        'predictions': {f'+{i+1} Month': round(v, 2) for i, v in enumerate(predictions)}
    }
    
    return _fig_to_base64(fig), pred_data


def generate_revenue_bar_chart(data: Dict[str, float], title: str = "Revenue Comparison",
                                currency_symbol: str = '₹') -> str:
    """
    Generate premium vertical bar chart for comparisons
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    fig, ax = plt.subplots(figsize=(12, 6))
    _setup_dark_theme(fig, ax)
    
    labels = list(data.keys())
    values = list(data.values())
    
    x = np.arange(len(labels))
    colors = [VIBRANT_COLORS[i % len(VIBRANT_COLORS)] for i in range(len(labels))]
    
    bars = ax.bar(x, values, color=colors, width=0.6, edgecolor='none')
    
    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values) * 0.02,
                f'{currency_symbol}{val:,.0f}', ha='center', va='bottom',
                fontsize=10, fontweight='bold', color=DARK_THEME['text_color'])
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=11)
    ax.set_ylabel(f'Amount ({currency_symbol})', fontsize=12, fontweight='bold')
    ax.set_title(f'📊 {title}', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return _fig_to_base64(fig)


def generate_pie_chart(data: Dict[str, float], title: str = "Distribution",
                       currency_symbol: str = '₹') -> str:
    """
    Generate premium donut pie chart
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(DARK_THEME['bg_color'])
    
    labels = list(data.keys())
    values = list(data.values())
    colors = VIBRANT_COLORS[:len(labels)]
    
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor=DARK_THEME['bg_color'], linewidth=3)
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # Legend
    legend = ax.legend(
        wedges,
        [f'{l}: {currency_symbol}{v:,.0f}' for l, v in zip(labels, values)],
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        frameon=False
    )
    for text in legend.get_texts():
        text.set_color(DARK_THEME['text_color'])
    
    # Center total
    total = sum(values)
    ax.text(0, 0, f'Total\n{currency_symbol}{total:,.0f}',
            ha='center', va='center', fontsize=14, fontweight='bold',
            color=DARK_THEME['text_color'])
    
    ax.set_title(f'📊 {title}', fontsize=14, fontweight='bold',
                 color=DARK_THEME['text_color'], pad=20)
    
    plt.tight_layout()
    return _fig_to_base64(fig)


def generate_comparison_chart(data1: Dict[str, float], data2: Dict[str, float],
                               label1: str = "Current", label2: str = "Previous",
                               title: str = "Comparison", currency_symbol: str = '₹') -> str:
    """
    Generate side-by-side comparison bar chart
    """
    if not MATPLOTLIB_AVAILABLE:
        return ""
    
    fig, ax = plt.subplots(figsize=(14, 7))
    _setup_dark_theme(fig, ax)
    
    # Get common keys or all keys
    all_keys = list(set(list(data1.keys()) + list(data2.keys())))
    values1 = [data1.get(k, 0) for k in all_keys]
    values2 = [data2.get(k, 0) for k in all_keys]
    
    x = np.arange(len(all_keys))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, values1, width, label=label1, color=VIBRANT_COLORS[0])
    bars2 = ax.bar(x + width/2, values2, width, label=label2, color=VIBRANT_COLORS[1])
    
    # Add value labels
    for bar, val in zip(bars1, values1):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{currency_symbol}{val:,.0f}', ha='center', va='bottom',
                    fontsize=8, color=DARK_THEME['text_color'])
    
    for bar, val in zip(bars2, values2):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{currency_symbol}{val:,.0f}', ha='center', va='bottom',
                    fontsize=8, color=DARK_THEME['text_color'])
    
    ax.set_xticks(x)
    ax.set_xticklabels(all_keys, rotation=45, ha='right')
    ax.set_ylabel(f'Amount ({currency_symbol})', fontsize=12, fontweight='bold')
    ax.set_title(f'📊 {title}', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', frameon=False)
    
    plt.tight_layout()
    return _fig_to_base64(fig)
