"""
Interactive Charts Module - Enterprise-Grade Plotly Visualizations
$500K Quality with Interactive Hover, Tooltips, Animations

Returns JSON chart configurations for frontend Plotly.js rendering
"""

from typing import Dict, List, Optional, Tuple
import json

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Premium Color Palette
ENTERPRISE_COLORS = [
    '#8B5CF6',  # Vibrant Purple (primary)
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

# Dark Theme Configuration for Plotly
DARK_LAYOUT = {
    'paper_bgcolor': '#0F0F0F',
    'plot_bgcolor': '#1A1A1A',
    'font': {'color': '#E5E5E5', 'family': 'Inter, system-ui, sans-serif'},
    'title': {'font': {'size': 18, 'color': '#FFFFFF'}},
    'xaxis': {
        'gridcolor': '#2A2A2A',
        'linecolor': '#3A3A3A',
        'tickfont': {'color': '#B0B0B0'}
    },
    'yaxis': {
        'gridcolor': '#2A2A2A',
        'linecolor': '#3A3A3A',
        'tickfont': {'color': '#B0B0B0'}
    },
    'legend': {'font': {'color': '#E5E5E5'}},
    'hoverlabel': {
        'bgcolor': '#2D2D2D',
        'font_size': 14,
        'font_family': 'Inter, system-ui, sans-serif'
    }
}

# Light Theme Configuration for Plotly
LIGHT_LAYOUT = {
    'paper_bgcolor': '#FFFFFF',
    'plot_bgcolor': '#F8F9FA',
    'font': {'color': '#1F2937', 'family': 'Inter, system-ui, sans-serif'},
    'title': {'font': {'size': 18, 'color': '#111827'}},
    'xaxis': {
        'gridcolor': '#E5E7EB',
        'linecolor': '#D1D5DB',
        'tickfont': {'color': '#4B5563'}
    },
    'yaxis': {
        'gridcolor': '#E5E7EB',
        'linecolor': '#D1D5DB',
        'tickfont': {'color': '#4B5563'}
    },
    'legend': {'font': {'color': '#1F2937'}},
    'hoverlabel': {
        'bgcolor': '#FFFFFF',
        'font_size': 14,
        'font_family': 'Inter, system-ui, sans-serif',
        'bordercolor': '#D1D5DB'
    }
}


def get_theme_layout(theme: str = 'dark') -> dict:
    """
    Get the appropriate layout configuration based on theme
    Args:
        theme: 'dark' or 'light'
    Returns:
        Layout dictionary for Plotly
    """
    return LIGHT_LAYOUT if theme == 'light' else DARK_LAYOUT


def generate_interactive_customer_chart(df, currency_symbol: str = '₹', top_n: int = 10) -> Optional[Dict]:
    """
    Generate interactive customer revenue bar chart with hover tooltips
    Returns JSON for frontend Plotly.js rendering
    """
    if not PLOTLY_AVAILABLE:
        return None
    
    if 'customer' not in df.columns:
        return None
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    # Group by customer
    customer_data = df.groupby('customer').agg({
        amount_col: 'sum',
        'customer': 'count'
    }).rename(columns={'customer': 'orders'})
    customer_data = customer_data.sort_values(amount_col, ascending=True).tail(top_n)
    
    # Calculate percentage share
    total_revenue = df[amount_col].sum()
    customer_data['pct_share'] = (customer_data[amount_col] / total_revenue * 100).round(1)
    customer_data['avg_order'] = (customer_data[amount_col] / customer_data['orders']).round(2)
    
    # Create hover text with rich info
    hover_text = [
        f"<b>{customer}</b><br>" +
        f"Revenue: {currency_symbol}{rev:,.2f}<br>" +
        f"Orders: {orders}<br>" +
        f"Avg Order: {currency_symbol}{avg:,.2f}<br>" +
        f"Share: {pct:.1f}%"
        for customer, rev, orders, avg, pct in zip(
            customer_data.index,
            customer_data[amount_col],
            customer_data['orders'],
            customer_data['avg_order'],
            customer_data['pct_share']
        )
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=customer_data.index.tolist(),
        x=customer_data[amount_col].tolist(),
        orientation='h',
        marker=dict(
            color=customer_data[amount_col].tolist(),
            colorscale=[[0, ENTERPRISE_COLORS[1]], [1, ENTERPRISE_COLORS[0]]],
            line=dict(width=0)
        ),
        text=[f"{currency_symbol}{v:,.0f}" for v in customer_data[amount_col]],
        textposition='outside',
        textfont=dict(color='#E5E5E5', size=11),
        hovertext=hover_text,
        hoverinfo='text',
        hoverlabel=dict(bgcolor='#2D2D2D', font_size=13)
    ))
    
    fig.update_layout(
        title=dict(text='📊 Top Customers by Revenue', x=0.5),
        xaxis_title=f'Revenue ({currency_symbol})',
        height=max(400, top_n * 45),
        margin=dict(l=20, r=120, t=60, b=40),
        **DARK_LAYOUT
    )
    
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))


def generate_interactive_product_chart(df, currency_symbol: str = '₹', top_n: int = 8) -> Optional[Dict]:
    """
    Generate interactive product donut chart with hover tooltips
    """
    if not PLOTLY_AVAILABLE:
        return None
    
    if 'product' not in df.columns:
        return None
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    product_data = df.groupby('product').agg({
        amount_col: 'sum',
        'product': 'count'
    }).rename(columns={'product': 'units'})
    product_data = product_data.sort_values(amount_col, ascending=False).head(top_n)
    
    total = product_data[amount_col].sum()
    product_data['pct'] = (product_data[amount_col] / total * 100).round(1)
    
    fig = go.Figure(data=[go.Pie(
        labels=product_data.index.tolist(),
        values=product_data[amount_col].tolist(),
        hole=0.45,
        marker=dict(colors=ENTERPRISE_COLORS[:len(product_data)]),
        textinfo='label+percent',
        textposition='outside',
        hovertemplate=(
            "<b>%{label}</b><br>" +
            f"Revenue: {currency_symbol}%{{value:,.2f}}<br>" +
            "Share: %{percent}<extra></extra>"
        ),
        hoverlabel=dict(bgcolor='#2D2D2D', font_size=13)
    )])
    
    fig.update_layout(
        title=dict(text='📦 Product Revenue Distribution', x=0.5),
        height=500,
        annotations=[dict(
            text=f"<b>Total</b><br>{currency_symbol}{total:,.0f}",
            x=0.5, y=0.5, font_size=16, showarrow=False,
            font=dict(color='#E5E5E5')
        )],
        **DARK_LAYOUT
    )
    
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))


def generate_interactive_trend_chart(df, currency_symbol: str = '₹', show_prediction: bool = True) -> Optional[Dict]:
    """
    Generate interactive monthly trend line chart with hover and prediction
    """
    if not PLOTLY_AVAILABLE:
        return None
    
    if 'date' not in df.columns:
        return None
    
    import pandas as pd
    import numpy as np
    
    amount_col = 'amount' if 'amount' in df.columns else 'total_amount'
    
    df_temp = df.copy()
    df_temp['date_parsed'] = pd.to_datetime(df_temp['date'], errors='coerce')
    df_dated = df_temp[df_temp['date_parsed'].notna()].copy()
    
    if df_dated.empty or len(df_dated) < 2:
        return None
    
    df_dated['month'] = df_dated['date_parsed'].dt.to_period('M').astype(str)
    monthly = df_dated.groupby('month')[amount_col].sum().reset_index()
    
    fig = go.Figure()
    
    # Actual trend line with fill
    fig.add_trace(go.Scatter(
        x=monthly['month'].tolist(),
        y=monthly[amount_col].tolist(),
        mode='lines+markers',
        name='Revenue',
        line=dict(color=ENTERPRISE_COLORS[0], width=3),
        marker=dict(size=10, color=ENTERPRISE_COLORS[0]),
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate=(
            "<b>%{x}</b><br>" +
            f"Revenue: {currency_symbol}%{{y:,.2f}}<extra></extra>"
        )
    ))
    
    # Add prediction if requested
    if show_prediction and len(monthly) >= 3:
        x_num = np.arange(len(monthly))
        y = monthly[amount_col].values
        z = np.polyfit(x_num, y, 1)
        p = np.poly1d(z)
        
        # Predict next 3 months
        future_months = []
        last_date = pd.to_datetime(monthly['month'].iloc[-1])
        for i in range(1, 4):
            future_months.append((last_date + pd.DateOffset(months=i)).strftime('%Y-%m'))
        
        future_x = np.arange(len(monthly), len(monthly) + 3)
        future_y = p(future_x)
        
        fig.add_trace(go.Scatter(
            x=future_months,
            y=future_y.tolist(),
            mode='lines+markers',
            name='Predicted',
            line=dict(color=ENTERPRISE_COLORS[2], width=3, dash='dash'),
            marker=dict(size=10, symbol='diamond', color=ENTERPRISE_COLORS[2]),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Predicted: {currency_symbol}%{{y:,.2f}}<extra></extra>"
            )
        ))
        
        # Add confidence band
        conf_upper = future_y * 1.15
        conf_lower = future_y * 0.85
        
        fig.add_trace(go.Scatter(
            x=future_months + future_months[::-1],
            y=conf_upper.tolist() + conf_lower[::-1].tolist(),
            fill='toself',
            fillcolor='rgba(16, 185, 129, 0.15)',
            line=dict(color='rgba(0,0,0,0)'),
            name='Confidence Band',
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title=dict(text='📈 Revenue Trend & Prediction', x=0.5),
        xaxis_title='Month',
        yaxis_title=f'Revenue ({currency_symbol})',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        **DARK_LAYOUT
    )
    
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))


def generate_interactive_prediction_chart(
    monthly_data: Dict[str, float],
    prediction_months: int = 3,
    currency_symbol: str = '₹'
) -> Tuple[Optional[Dict], Dict]:
    """
    Generate fully interactive prediction chart with confidence bands
    Returns (chart_json, prediction_data)
    """
    if not PLOTLY_AVAILABLE:
        return None, {}
    
    import numpy as np
    
    months = list(monthly_data.keys())
    values = list(monthly_data.values())
    
    if len(values) < 2:
        return None, {}
    
    # Calculate prediction using linear regression
    x = np.arange(len(values))
    z = np.polyfit(x, values, 1)
    p = np.poly1d(z)
    
    growth_rate = z[0] / np.mean(values) if np.mean(values) > 0 else 0
    scenario = "growth" if growth_rate > 0.02 else "stable" if growth_rate > -0.02 else "decline"
    
    # Future predictions
    future_x = np.arange(len(values), len(values) + prediction_months)
    predictions = p(future_x)
    
    # Confidence bands
    conf_upper = predictions * 1.15
    conf_lower = predictions * 0.85
    
    # Labels
    future_labels = [f'+{i+1}M' for i in range(prediction_months)]
    
    fig = go.Figure()
    
    # Actual data
    fig.add_trace(go.Scatter(
        x=months,
        y=values,
        mode='lines+markers',
        name='Actual',
        line=dict(color=ENTERPRISE_COLORS[0], width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(139, 92, 246, 0.2)',
        hovertemplate=f"<b>%{{x}}</b><br>Revenue: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))
    
    # Prediction color based on scenario
    pred_color = ENTERPRISE_COLORS[2] if scenario == 'growth' else ENTERPRISE_COLORS[3] if scenario == 'stable' else ENTERPRISE_COLORS[4]
    
    # Predicted data
    fig.add_trace(go.Scatter(
        x=future_labels,
        y=predictions.tolist(),
        mode='lines+markers',
        name='Predicted',
        line=dict(color=pred_color, width=3, dash='dash'),
        marker=dict(size=10, symbol='diamond'),
        hovertemplate=f"<b>%{{x}}</b><br>Predicted: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))
    
    # Confidence band
    fig.add_trace(go.Scatter(
        x=future_labels + future_labels[::-1],
        y=conf_upper.tolist() + conf_lower[::-1].tolist(),
        fill='toself',
        fillcolor=f'rgba({int(pred_color[1:3], 16)}, {int(pred_color[3:5], 16)}, {int(pred_color[5:7], 16)}, 0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Confidence ±15%',
        hoverinfo='skip'
    ))
    
    # Add scenario annotation
    scenario_emoji = '📈' if scenario == 'growth' else '📊' if scenario == 'stable' else '📉'
    fig.add_annotation(
        x=1, y=1.05, xref='paper', yref='paper',
        text=f"{scenario_emoji} {scenario.title()} Trend",
        showarrow=False,
        font=dict(size=14, color=pred_color),
        bgcolor='rgba(26, 26, 26, 0.8)',
        borderpad=8
    )
    
    fig.update_layout(
        title=dict(text=f'🔮 Revenue Prediction ({prediction_months} Months)', x=0.5),
        xaxis_title='Period',
        yaxis_title=f'Revenue ({currency_symbol})',
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        **DARK_LAYOUT
    )
    
    # Build prediction metadata
    pred_data = {
        'scenario': scenario,
        'growth_rate': round(growth_rate * 100, 2),
        'total_predicted_growth': round(((predictions[-1] - values[-1]) / values[-1]) * 100 if values[-1] > 0 else 0, 2),
        'predictions': {f'+{i+1} Month': round(v, 2) for i, v in enumerate(predictions)},
        'confidence_range': {
            'upper': [round(v, 2) for v in conf_upper],
            'lower': [round(v, 2) for v in conf_lower]
        }
    }
    
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)), pred_data


def generate_interactive_comparison_chart(
    data1: Dict[str, float],
    data2: Dict[str, float],
    label1: str = "Current",
    label2: str = "Previous",
    title: str = "Period Comparison",
    currency_symbol: str = '₹'
) -> Optional[Dict]:
    """
    Generate interactive grouped bar chart for comparisons
    """
    if not PLOTLY_AVAILABLE:
        return None
    
    all_keys = list(set(list(data1.keys()) + list(data2.keys())))
    values1 = [data1.get(k, 0) for k in all_keys]
    values2 = [data2.get(k, 0) for k in all_keys]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=label1,
        x=all_keys,
        y=values1,
        marker_color=ENTERPRISE_COLORS[0],
        hovertemplate=f"<b>%{{x}}</b><br>{label1}: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        name=label2,
        x=all_keys,
        y=values2,
        marker_color=ENTERPRISE_COLORS[1],
        hovertemplate=f"<b>%{{x}}</b><br>{label2}: {currency_symbol}%{{y:,.2f}}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text=f'📊 {title}', x=0.5),
        barmode='group',
        xaxis_title='Category',
        yaxis_title=f'Amount ({currency_symbol})',
        height=450,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        **DARK_LAYOUT
    )
    
    return json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))
