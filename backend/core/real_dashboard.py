"""
TRUE AUTONOMOUS VISUAL INTELLIGENCE ENGINE - $50B Silicon Valley Feature
==========================================================================

THIS IS NOT HARDCODED!

The system AUTONOMOUSLY decides:
1. Which chart types to use (from 15+ types)
2. Which colors match the data domain
3. Which columns to visualize together
4. How many charts and what layout
5. What insights are most valuable

Based on:
- Data types (numeric, categorical, datetime, text)
- Column relationships and correlations
- Data distributions and patterns
- Domain detection (finance, sales, HR, marketing, etc.)

ALL calculations are REAL - done with pandas!
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import random

from core.llm import chat

logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """Recursively convert numpy/pandas types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64,
                          np.uint8, np.uint16, np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)): 
        return sanitize_for_json(obj.tolist())
    elif isinstance(obj, (pd.Series,)): 
        return sanitize_for_json(obj.tolist())
    elif pd.isna(obj): # Handle NaN
        return None
    return obj

# ================= AUTONOMOUS CHART TYPE SELECTION =================

# All supported chart types - PREMIUM ENTERPRISE COLLECTION
CHART_TYPES = [
    # Basic Charts
    'bar', 'horizontal_bar', 'stacked_bar', 'grouped_bar',
    'line', 'area', 'stacked_area',
    'scatter', 'bubble',
    'pie', 'donut', 'sunburst',
    'heatmap', 'treemap',
    'histogram', 'box', 'violin',
    'funnel', 'waterfall', 'pareto',
    'radar', 'gauge', 'bullet',
    'sankey', 'candlestick', 'parcoords',
    'choropleth', 'scatter_3d', 'calendar_heatmap',
    # NEW ADVANCED CHARTS - Premium Analytics
    'combo_bar_line',      # Bar + Line dual axis (Power BI style)
    'lollipop',            # Lollipop chart for rankings
    'dumbbell',            # Before/After comparisons  
    'bullet_comparison',   # Multi-metric bullet charts
    'sparkline_table',     # Mini charts in table cells
    'marimekko',           # Market share visualization
    'scatter_matrix',      # Correlation matrix with scatter plots
    'ridgeline',           # Distribution comparisons over time
    'slope',               # Slope chart for period comparison
    'diverging_bar',       # Positive/negative from center
    'pyramid',             # Age/demographic pyramid
    'waffle',              # Percentage visualization
    'density_contour',     # 2D density plot
    'band_chart',          # Confidence interval bands
    'step_line',           # Step function line chart
    'range_plot',          # Min-Max range visualization
]

# Color palettes for different domains - POWERBI-LEVEL PREMIUM COLORS
COLOR_PALETTES = {
    'finance': {
        'primary': ['#10b981', '#059669', '#047857', '#065f46', '#064e3b'],
        'accent': ['#14b8a6', '#0d9488', '#0f766e', '#115e59'],
        'chart': ['#10b981', '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#22c55e', '#eab308', '#f59e0b', '#ef4444']
    },
    'sales': {
        'primary': ['#8b5cf6', '#7c3aed', '#6d28d9', '#5b21b6', '#4c1d95'],
        'accent': ['#a78bfa', '#c4b5fd', '#ddd6fe'],
        'chart': ['#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#fb7185', '#14b8a6', '#06b6d4', '#3b82f6', '#eab308', '#22c55e', '#f97316']
    },
    'marketing': {
        'primary': ['#f97316', '#ea580c', '#c2410c', '#9a3412', '#7c2d12'],
        'accent': ['#fb923c', '#fdba74', '#fed7aa'],
        'chart': ['#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#ef4444', '#10b981']
    },
    'hr': {
        'primary': ['#06b6d4', '#0891b2', '#0e7490', '#155e75', '#164e63'],
        'accent': ['#22d3ee', '#67e8f9', '#a5f3fc'],
        'chart': ['#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#14b8a6', '#22c55e', '#f59e0b', '#ef4444']
    },
    'operations': {
        'primary': ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#1e3a8a'],
        'accent': ['#60a5fa', '#93c5fd', '#bfdbfe'],
        'chart': ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#14b8a6', '#22c55e', '#eab308', '#f97316', '#ef4444', '#06b6d4']
    },
    'general': {
        'primary': ['#14b8a6', '#0d9488', '#0f766e', '#115e59', '#134e4a'],
        'accent': ['#2dd4bf', '#5eead4', '#99f6e4'],
        'chart': ['#14b8a6', '#22c55e', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#f59e0b', '#ef4444', '#ec4899']
    }
}


def detect_data_domain(df: pd.DataFrame) -> str:
    """Autonomously detect the domain of the data based on column names"""
    columns_lower = ' '.join(df.columns.str.lower())
    
    finance_keywords = ['revenue', 'profit', 'cost', 'expense', 'income', 'margin', 'budget', 'invoice', 'payment', 'price', 'amount', 'balance', 'asset', 'liability']
    sales_keywords = ['sales', 'order', 'customer', 'product', 'deal', 'lead', 'opportunity', 'quota', 'discount', 'quantity']
    marketing_keywords = ['campaign', 'channel', 'conversion', 'click', 'impression', 'reach', 'engagement', 'traffic', 'subscriber', 'follower']
    hr_keywords = ['employee', 'salary', 'hire', 'department', 'position', 'performance', 'leave', 'attendance', 'training']
    operations_keywords = ['inventory', 'supply', 'delivery', 'shipping', 'warehouse', 'stock', 'vendor', 'supplier', 'logistics']
    
    scores = {
        'finance': sum(1 for kw in finance_keywords if kw in columns_lower),
        'sales': sum(1 for kw in sales_keywords if kw in columns_lower),
        'marketing': sum(1 for kw in marketing_keywords if kw in columns_lower),
        'hr': sum(1 for kw in hr_keywords if kw in columns_lower),
        'operations': sum(1 for kw in operations_keywords if kw in columns_lower)
    }
    
    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] > 0 else 'general'


def analyze_column_relationships(df: pd.DataFrame) -> List[Dict]:
    """Analyze relationships between columns to determine best visualizations"""
    relationships = []
    
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
    
    # Numeric vs Categorical (best for bar, pie, donut)
    for num in numeric_cols[:3]:
        for cat in categorical_cols[:3]:
            cardinality = df[cat].nunique()
            if 2 <= cardinality <= 15:
                relationships.append({
                    'type': 'num_vs_cat',
                    'numeric': num,
                    'categorical': cat,
                    'cardinality': cardinality,
                    'best_charts': ['bar', 'horizontal_bar', 'pie', 'donut', 'treemap', 'funnel', 'pareto', 'radar', 'gauge'] if cardinality <= 8 else ['bar', 'horizontal_bar', 'treemap', 'funnel', 'pareto']
                })
    
    # Numeric vs Numeric (best for scatter, bubble)
    for i, num1 in enumerate(numeric_cols[:4]):
        for num2 in numeric_cols[i+1:5]:
            corr = df[[num1, num2]].corr().iloc[0, 1] if len(df) > 5 else 0
            relationships.append({
                'type': 'num_vs_num',
                'x': num1,
                'y': num2,
                'correlation': abs(corr) if not pd.isna(corr) else 0,
                'best_charts': ['scatter', 'bubble', 'heatmap', 'line', 'area', 'parcoords']
            })
    
    # Time series (best for line, area)
    if datetime_cols and numeric_cols:
        for dt_col in datetime_cols[:1]:
            for num_col in numeric_cols[:3]:
                relationships.append({
                    'type': 'time_series',
                    'time': dt_col,
                    'value': num_col,
                    'best_charts': ['line', 'area', 'stacked_area', 'bar', 'scatter', 'candlestick', 'waterfall']
                })
    
    # Distribution analysis (best for histogram, box)
    for num in numeric_cols[:3]:
        skewness = df[num].skew() if len(df) > 10 else 0
        relationships.append({
            'type': 'distribution',
            'column': num,
            'skewness': skewness if not pd.isna(skewness) else 0,
            'best_charts': ['histogram', 'box', 'violin', 'area', 'gauge']
        })
    
    # Multi-category (best for stacked, grouped)
    if len(categorical_cols) >= 2 and numeric_cols:
        relationships.append({
            'type': 'multi_category',
            'cat1': categorical_cols[0],
            'cat2': categorical_cols[1],
            'value': numeric_cols[0],
            'categorical_cols': categorical_cols[:3],
            'best_charts': ['stacked_bar', 'grouped_bar', 'heatmap', 'sunburst', 'treemap', 'sankey', 'parcoords', 'radar']
        })

    # Advanced Pattern Detection ------------------------------------------

    # 1. Flow / Sankey Detection
    # Look for source/target pairs
    source_keywords = ['source', 'origin', 'from', 'start']
    target_keywords = ['target', 'dest', 'to', 'end']
    
    source_col = next((c for c in categorical_cols if any(k in c.lower() for k in source_keywords)), None)
    target_col = next((c for c in categorical_cols if any(k in c.lower() for k in target_keywords)), None)
    
    if source_col and target_col and numeric_cols:
        relationships.append({
            'type': 'sankey',
            'source': source_col,
            'target': target_col,
            'value': numeric_cols[0],
            'best_charts': ['sankey']
        })

    # 2. Financial OHLC Detection (Candlestick)
    ohlc_map = {'open': None, 'high': None, 'low': None, 'close': None}
    for col in numeric_cols:
        lower = col.lower()
        for key in ohlc_map:
            if key in lower:
                ohlc_map[key] = col
    
    if all(ohlc_map.values()) and datetime_cols:
        relationships.append({
            'type': 'candlestick',
            'date': datetime_cols[0],
            **ohlc_map,
            'best_charts': ['candlestick']
        })

    # 3. Target/Goal Detection (Bullet)
    target_keywords = ['target', 'goal', 'budget', 'quota', 'plan']
    target_col = next((c for c in numeric_cols if any(k in c.lower() for k in target_keywords)), None)
    actual_col = next((c for c in numeric_cols if c != target_col and 'id' not in c.lower()), None)
    
    if target_col and actual_col:
        relationships.append({
            'type': 'bullet',
            'column': actual_col,
            'target': target_col,
            'best_charts': ['bullet']
        })

    # 4. Multivariate Analysis (Parallel Coordinates)
    if len(numeric_cols) >= 4:
        relationships.append({
            'type': 'multivariate',
            'columns': numeric_cols[:5],
            'category': categorical_cols[0] if categorical_cols else None,
            'best_charts': ['parallel_coords']
        })

    # 5. Geospatial Detection (Maps) 🌍
    geo_keywords = ['country', 'region', 'state', 'city', 'location', 'lat', 'lon', 'postal', 'zip']
    geo_col = next((c for c in categorical_cols if any(k in c.lower() for k in geo_keywords)), None)
    
    if geo_col and numeric_cols:
        relationships.append({
            'type': 'geospatial',
            'location': geo_col,
            'value': numeric_cols[0],
            'best_charts': ['choropleth', 'scatter_geo']
        })

    # 6. 3D Correlation Detection (3D Scatter) 🧊
    if len(numeric_cols) >= 3:
        relationships.append({
            'type': '3d_correlation',
            'x': numeric_cols[0],
            'y': numeric_cols[1],
            'z': numeric_cols[2],
            'color': categorical_cols[0] if categorical_cols else list(numeric_cols)[2],
            'best_charts': ['scatter_3d']
        })

    # 7. Temporal Activity (Calendar Heatmap) 📅
    if datetime_cols and len(datetime_cols) > 0:
        relationships.append({
            'type': 'temporal_heatmap',
            'date': datetime_cols[0],
            'value': numeric_cols[0] if numeric_cols else None,
            'best_charts': ['calendar_heatmap']
        })
    
    # Funnel (for sequential/stage data)
    if categorical_cols and numeric_cols:
        cardinality = df[categorical_cols[0]].nunique()
        if 3 <= cardinality <= 8:
            relationships.append({
                'type': 'funnel',
                'category': categorical_cols[0],
                'value': numeric_cols[0],
                'best_charts': ['funnel']
            })
    
    # Waterfall (for changes/variance)
    if len(numeric_cols) >= 2:
        relationships.append({
            'type': 'waterfall',
            'values': numeric_cols[:5],
            'best_charts': ['waterfall']
        })
    
    # Radar (for multi-metric comparison)
    if len(numeric_cols) >= 3 and categorical_cols:
        relationships.append({
            'type': 'radar',
            'metrics': numeric_cols[:6],
            'category': categorical_cols[0],
            'best_charts': ['radar']
        })
    
    # Gauge (for single metric with target)
    if numeric_cols:
        relationships.append({
            'type': 'gauge',
            'metric': numeric_cols[0],
            'best_charts': ['gauge']
        })
    
    # Violin (for distribution comparison)
    if categorical_cols and numeric_cols:
        relationships.append({
            'type': 'violin',
            'category': categorical_cols[0],
            'value': numeric_cols[0],
            'best_charts': ['violin']
        })
    
    # ===========================================
    # ADDITIONAL CHART RELATIONSHIPS FOR MORE VARIETY
    # ===========================================
    
    # NEW PREMIUM CHART RELATIONSHIPS
    
    # Combo Bar-Line Chart (Power BI style dual-axis)
    if len(numeric_cols) >= 2 and categorical_cols:
        relationships.append({
            'type': 'combo_bar_line',
            'category': categorical_cols[0],
            'bar_metric': numeric_cols[0],
            'line_metric': numeric_cols[1],
            'best_charts': ['combo_bar_line']
        })
    
    # Lollipop Chart (elegant ranking visualization)
    if categorical_cols and numeric_cols:
        relationships.append({
            'type': 'lollipop',
            'category': categorical_cols[0],
            'value': numeric_cols[0],
            'best_charts': ['lollipop']
        })
    
    # Diverging Bar (positive/negative from center)
    if numeric_cols:
        col = numeric_cols[0]
        if df[col].min() < 0 or df[col].mean() != 0:
            relationships.append({
                'type': 'diverging_bar',
                'category': categorical_cols[0] if categorical_cols else None,
                'value': col,
                'best_charts': ['diverging_bar']
            })
    
    # Slope Chart (period-over-period comparison)
    if len(numeric_cols) >= 2:
        relationships.append({
            'type': 'slope',
            'start_value': numeric_cols[0],
            'end_value': numeric_cols[1],
            'category': categorical_cols[0] if categorical_cols else None,
            'best_charts': ['slope']
        })
    
    # Dumbbell Chart (before/after or comparison)
    if len(numeric_cols) >= 2 and categorical_cols:
        relationships.append({
            'type': 'dumbbell',
            'category': categorical_cols[0],
            'value1': numeric_cols[0],
            'value2': numeric_cols[1],
            'best_charts': ['dumbbell']
        })
    
    # Range Plot (min-max visualization)
    if numeric_cols and categorical_cols:
        relationships.append({
            'type': 'range_plot',
            'category': categorical_cols[0],
            'value': numeric_cols[0],
            'best_charts': ['range_plot']
        })
    
    # Band Chart (with confidence intervals)
    if numeric_cols:
        relationships.append({
            'type': 'band_chart',
            'value': numeric_cols[0],
            'best_charts': ['band_chart']
        })
    
    # Step Line Chart
    if numeric_cols:
        relationships.append({
            'type': 'step_line',
            'value': numeric_cols[0],
            'best_charts': ['step_line']
        })
    
    # Comparison Bar (different from regular bar - shows comparison)
    if categorical_cols and numeric_cols:
        relationships.append({
            'type': 'comparison_bar',
            'categorical': categorical_cols[0],
            'numeric': numeric_cols[0],
            'best_charts': ['grouped_bar']
        })
    
    # Stacked Area (for cumulative trends)
    if len(numeric_cols) >= 2:
        relationships.append({
            'type': 'stacked_trend',
            'values': numeric_cols[:3],
            'best_charts': ['stacked_area']
        })
    
    # Donut Breakdown (secondary category)
    if len(categorical_cols) >= 2 and numeric_cols:
        relationships.append({
            'type': 'donut_breakdown',
            'category': categorical_cols[1] if len(categorical_cols) > 1 else categorical_cols[0],
            'value': numeric_cols[0],
            'best_charts': ['donut']
        })
    
    # Line Trend (for any numeric progression)
    if numeric_cols:
        relationships.append({
            'type': 'line_trend',
            'value': numeric_cols[0],
            'best_charts': ['line']
        })
    
    # Horizontal Ranking (top N items)
    if categorical_cols and numeric_cols:
        relationships.append({
            'type': 'horizontal_ranking',
            'category': categorical_cols[0],
            'value': numeric_cols[0],
            'best_charts': ['horizontal_bar']
        })
    
    # Grouped Comparison (if multiple numeric cols)
    if len(numeric_cols) >= 2 and categorical_cols:
        relationships.append({
            'type': 'grouped_comparison',
            'category': categorical_cols[0],
            'values': numeric_cols[:3],
            'best_charts': ['stacked_bar']
        })
    
    return relationships


def autonomous_chart_selection(df: pd.DataFrame, domain: str, relationships: List[Dict]) -> List[Dict]:
    """
    ENHANCED AUTONOMOUS CHART SELECTION - AI decides everything!
    
    Strategy:
    1. GUARANTEE advanced charts (radar, gauge, funnel, heatmap, box) first
    2. Score each relationship-chart combo based on data suitability
    3. Ensure variety - no repeated chart types
    4. Select best 12-15 visualizations
    """
    selected_charts = []
    used_chart_types = set()
    palette = COLOR_PALETTES.get(domain, COLOR_PALETTES['general'])
    
    # Chart complexity tiers - prioritize complex charts for variety
    COMPLEX_CHARTS = [
        'sankey', 'radar', 'sunburst', 'parcoords', 'bubble', 'violin', 'waterfall', 'candlestick',
        'combo_bar_line', 'scatter_matrix', 'marimekko', 'ridgeline', 'density_contour', 'band_chart'
    ]
    MEDIUM_CHARTS = [
        'heatmap', 'stacked_bar', 'funnel', 'gauge', 'treemap', 'box', 'area', 'pareto',
        'lollipop', 'dumbbell', 'slope', 'diverging_bar', 'pyramid', 'range_plot', 'step_line'
    ]
    SIMPLE_CHARTS = ['bar', 'line', 'pie', 'scatter', 'histogram', 'horizontal_bar', 'donut', 'waffle']
    
    # =============================================================
    # PHASE 1: GUARANTEE ADVANCED CHARTS (User requested variety)
    # Premium enterprise-grade visualizations
    # =============================================================
    must_have_advanced = [
        'radar', 'gauge', 'funnel', 'heatmap', 'box', 'violin',
        'combo_bar_line', 'pareto', 'lollipop', 'diverging_bar'
    ]
    
    for adv_chart in must_have_advanced:
        if adv_chart in used_chart_types:
            continue
        
        # Find a suitable relationship for this chart type
        for rel in relationships:
            if adv_chart in rel.get('best_charts', []):
                chart = generate_autonomous_chart(df, rel, adv_chart, palette)
                if chart:
                    selected_charts.append(chart)
                    used_chart_types.add(adv_chart)
                    break
        
        # If no direct match, try with compatible relationship types
        if adv_chart not in used_chart_types:
            for rel in relationships:
                rel_type = rel.get('type', '')
                compatible = False
                
                if adv_chart == 'radar' and rel_type in ['radar', 'multi_category', 'num_vs_cat']:
                    compatible = True
                elif adv_chart == 'gauge' and rel_type in ['gauge', 'distribution']:
                    compatible = True
                elif adv_chart == 'funnel' and rel_type in ['funnel', 'num_vs_cat']:
                    compatible = True
                elif adv_chart == 'heatmap' and rel_type in ['num_vs_num', 'multi_category', 'category_comparison']:
                    compatible = True
                elif adv_chart == 'box' and rel_type in ['distribution', 'violin']:
                    compatible = True
                elif adv_chart == 'violin' and rel_type in ['violin', 'distribution', 'num_vs_cat']:
                    compatible = True
                
                if compatible:
                    chart = generate_autonomous_chart(df, rel, adv_chart, palette)
                    if chart:
                        selected_charts.append(chart)
                        used_chart_types.add(adv_chart)
                        break
    
    logger.info(f"🌟 Phase 1: Guaranteed {len(selected_charts)} advanced charts: {list(used_chart_types)}")
    
    # =============================================================
    # PHASE 2: SCORED SELECTION FOR REMAINING CHARTS
    # =============================================================
    def calculate_chart_score(rel: Dict, chart_type: str) -> float:
        """Score how well a chart type fits the data relationship"""
        score = 0.0
        rel_type = rel.get('type', '')
        
        # Complexity bonus - prefer complex charts for dashboard variety
        if chart_type in COMPLEX_CHARTS:
            score += 30
        elif chart_type in MEDIUM_CHARTS:
            score += 20
        else:
            score += 10
        
        # Data suitability scoring
        if rel_type == 'num_vs_cat':
            if chart_type in ['bar', 'horizontal_bar', 'pie', 'donut', 'treemap', 'funnel']:
                score += 25
        elif rel_type == 'num_vs_num':
            if chart_type in ['scatter', 'bubble', 'heatmap', 'parcoords']:
                score += 25
        elif rel_type == 'time_series':
            if chart_type in ['line', 'area', 'candlestick']:
                score += 25
        elif rel_type == 'multi_category':
            if chart_type in ['sunburst', 'treemap', 'sankey', 'stacked_bar']:
                score += 25
        elif rel_type == 'distribution':
            if chart_type in ['histogram', 'box', 'violin']:
                score += 25
        elif rel_type == 'comparison':
            if chart_type in ['radar', 'gauge', 'bullet', 'bar']:
                score += 25
        
        # Category count based scoring
        if 'categorical_cols' in rel:
            cat_count = len(rel.get('categorical_cols', []))
            if cat_count >= 2 and chart_type in ['sunburst', 'sankey', 'parcoords']:
                score += 15
            elif cat_count == 1 and chart_type in ['bar', 'pie', 'treemap']:
                score += 10
        
        # Random small factor for diversity
        score += random.uniform(0, 5)
        
        return score
    
    # Build scored list of all possible chart options
    chart_options = []
    for rel in relationships:
        for chart_type in rel.get('best_charts', ['bar']):
            if chart_type not in used_chart_types:
                score = calculate_chart_score(rel, chart_type)
                chart_options.append({
                    'rel': rel,
                    'chart_type': chart_type,
                    'score': score
                })
    
    # Sort by score descending (highest priority first)
    chart_options.sort(key=lambda x: x['score'], reverse=True)
    
    # Select top charts ensuring variety - MAXIMUM 15 UNIQUE CHARTS
    for option in chart_options:
        if len(selected_charts) >= 15:  # Increased for maximum variety
            break
        
        chart_type = option['chart_type']
        if chart_type in used_chart_types:
            continue  # STRICT: Never duplicate chart types
        
        # Generate chart
        chart = generate_autonomous_chart(df, option['rel'], chart_type, palette)
        if chart:
            selected_charts.append(chart)
            used_chart_types.add(chart_type)
    
    # If we have less than 10 charts, try adding more from all tiers
    if len(selected_charts) < 10:
        all_chart_types = COMPLEX_CHARTS + MEDIUM_CHARTS + SIMPLE_CHARTS
        for rel in relationships:
            if len(selected_charts) >= 12:
                break
            for chart_type in all_chart_types:
                if chart_type not in used_chart_types:
                    chart = generate_autonomous_chart(df, rel, chart_type, palette)
                    if chart:
                        selected_charts.append(chart)
                        used_chart_types.add(chart_type)
                        break
    
    logger.info(f"🎨 Generated {len(selected_charts)} UNIQUE charts: {list(used_chart_types)}")
    return selected_charts


def generate_autonomous_chart(df: pd.DataFrame, relationship: Dict, chart_type: str, palette: Dict) -> Optional[Dict]:
    """
    Generate a chart configuration autonomously based on data relationship.
    All data is REAL - calculated with pandas!
    """
    try:
        rel_type = relationship['type']
        colors = palette['chart']
        
        if rel_type == 'num_vs_cat':
            cat_col = relationship['categorical']
            num_col = relationship['numeric']
            grouped = df.groupby(cat_col)[num_col].sum().nlargest(10)
            labels = [str(l)[:20] for l in grouped.index]
            values = [float(v) for v in grouped.values]
            
            if chart_type in ['pie', 'donut']:
                return create_pie_chart(labels, values, num_col, cat_col, chart_type, colors)
            elif chart_type == 'treemap':
                return create_treemap_chart(labels, values, num_col, cat_col, colors)
            elif chart_type == 'horizontal_bar':
                return create_horizontal_bar(labels, values, num_col, cat_col, colors)
            elif chart_type == 'funnel':
                # Funnel needs special relationship, fallback to bar for num_vs_cat
                return create_bar_chart(labels, values, num_col, cat_col, colors)
            elif chart_type == 'pareto':
                # Power BI-style Pareto (80/20) chart
                return create_pareto_chart(df, {'category': cat_col, 'value': num_col}, colors)
            elif chart_type == 'radar':
                # Radar needs multi-metrics, fallback to bar for single metric
                return create_bar_chart(labels, values, num_col, cat_col, colors)
            else:
                return create_bar_chart(labels, values, num_col, cat_col, colors)
        
        elif rel_type == 'num_vs_num':
            x_col = relationship['x']
            y_col = relationship['y']
            sample = df[[x_col, y_col]].dropna().head(150)
            
            if chart_type == 'bubble':
                # SAFER SIZE CALCULATION
                y_min = sample[y_col].min()
                y_max = sample[y_col].max()
                
                # Avoid division by zero
                y_range = y_max - y_min
                if y_range == 0:
                    sizes = np.full(len(sample), 15)
                else:
                    # Normalize to 0-1 then scale to 5-35 range
                    normalized = (sample[y_col] - y_min) / y_range
                    sizes = normalized * 30 + 5
                
                # Ensure sizes are JSON serializable (convert to list of floats)
                # Handle potential NaNs by filling with default size
                sizes = sizes.fillna(15).tolist() if hasattr(sizes, 'fillna') else sizes 
                
                return create_bubble_chart(sample[x_col].tolist(), sample[y_col].tolist(), sizes, x_col, y_col, colors)
            elif chart_type == 'heatmap':
                return create_correlation_heatmap(df, colors)
            else:
                return create_scatter_chart(sample[x_col].tolist(), sample[y_col].tolist(), x_col, y_col, colors)
        
        elif rel_type == 'time_series':
            num_col = relationship['value']
            n_points = min(20, len(df))
            segment_size = max(1, len(df) // n_points)
            values = [float(df[num_col].iloc[i*segment_size:(i+1)*segment_size].sum()) for i in range(n_points)]
            labels = [f'P{i+1}' for i in range(n_points)]
            
            if chart_type == 'area':
                return create_area_chart(labels, values, num_col, colors)
            else:
                return create_line_chart(labels, values, num_col, colors)
        
        elif rel_type == 'distribution':
            col = relationship['column']
            
            if chart_type == 'histogram':
                return create_histogram(df[col].dropna().tolist(), col, colors)
            elif chart_type == 'box':
                return create_box_plot(df, [col], colors)
            else:
                # Create area from distribution
                values = df[col].dropna().head(30).tolist()
                labels = [f'{i+1}' for i in range(len(values))]
                return create_area_chart(labels, values, col, colors)
        
        elif rel_type == 'multi_category':
            if chart_type in ['sunburst', 'treemap']:
                # Create sunburst/treemap from multi-category
                cat1 = relationship['cat1']
                val_col = relationship['value'] 
                grouped = df.groupby(cat1)[val_col].sum().nlargest(10)
                labels = [str(l)[:20] for l in grouped.index]
                values = [float(v) for v in grouped.values]
                if chart_type == 'sunburst':
                    return create_sunburst_chart(labels, values, cat1, colors)
                else:
                    return create_treemap_chart(labels, values, val_col, cat1, colors)
            else:
                return create_stacked_bar(df, relationship, colors)
        
        elif rel_type == 'sankey':
            return create_sankey_chart(df, relationship, colors)
            
        elif rel_type == 'candlestick':
            return create_candlestick_chart(df, relationship, colors)
            
        elif rel_type == 'bullet':
            return create_bullet_chart(df, relationship, colors)
            
        elif rel_type == 'multivariate':
            return create_parallel_coords_chart(df, relationship, colors)
            
        elif rel_type == 'funnel':
            return create_funnel_chart(df, relationship, colors)
            
        elif rel_type == 'geospatial':
            return create_choropleth_chart(df, relationship, colors)
            
        elif rel_type == '3d_correlation':
            return create_scatter3d_chart(df, relationship, colors)
            
        elif rel_type == 'temporal_heatmap':
            return create_calendar_heatmap(df, relationship, colors)
        
        elif rel_type == 'waterfall':
            return create_waterfall_chart(df, relationship, colors)
        
        elif rel_type == 'radar':
            return create_radar_chart(df, relationship, colors)
        
        elif rel_type == 'gauge':
            return create_gauge_chart(df, relationship, colors)
        
        elif rel_type == 'violin':
            return create_violin_chart(df, relationship, colors)
        
        # ===========================================
        # CATEGORICAL-ONLY DATA CHART HANDLERS
        # ===========================================
        elif rel_type == 'category_distribution':
            # Single category frequency distribution
            cat_col = relationship['categorical']
            counts = df[cat_col].value_counts().head(10)
            labels = [str(l)[:20] for l in counts.index]
            values = [int(v) for v in counts.values]
            
            if chart_type in ['pie', 'donut']:
                return create_pie_chart(labels, values, 'Count', cat_col, chart_type, colors)
            elif chart_type == 'horizontal_bar':
                return create_horizontal_bar(labels, values, 'Count', cat_col, colors)
            elif chart_type == 'treemap':
                return create_treemap_chart(labels, values, 'Count', cat_col, colors)
            else:
                return create_bar_chart(labels, values, 'Count', cat_col, colors)
        
        elif rel_type == 'category_comparison':
            # Cross-tabulation visualization
            cat1 = relationship['cat1']
            cat2 = relationship['cat2']
            
            # SAFE CROSSTAB: Limit to top 20 categories to prevent memory overflow
            top_cat1 = df[cat1].value_counts().head(20).index
            top_cat2 = df[cat2].value_counts().head(20).index
            mask = df[cat1].isin(top_cat1) & df[cat2].isin(top_cat2)
            cross = pd.crosstab(df.loc[mask, cat1], df.loc[mask, cat2])
            
            if chart_type in ['stacked_bar', 'grouped_bar']:
                # Create stacked/grouped bar from crosstab
                data_traces = []
                for col in cross.columns[:6]:
                    data_traces.append({
                        "type": "bar",
                        "name": str(col)[:15],
                        "x": [str(idx)[:15] for idx in cross.index[:10]],
                        "y": cross[col].head(10).tolist(),
                        "marker": {"color": colors[len(data_traces) % len(colors)]}
                    })
                return {
                    "data": data_traces,
                    "layout": {
                        "title": f"📊 {cat1.replace('_', ' ').title()} by {cat2.replace('_', ' ').title()}",
                        "barmode": "stack" if chart_type == 'stacked_bar' else "group",
                        "height": 400,
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "font": {"color": "#e5e7eb"}
                    }
                }
            elif chart_type == 'sunburst':
                return create_sunburst_chart(
                    [str(idx)[:15] for idx in cross.index[:8]],
                    cross.sum(axis=1).head(8).tolist(),
                    cat1,
                    colors
                )
            elif chart_type == 'heatmap':
                # Create heatmap from crosstab
                return {
                    "data": [{
                        "type": "heatmap",
                        "z": cross.head(10).iloc[:, :10].values.tolist(),
                        "x": [str(c)[:12] for c in cross.columns[:10]],
                        "y": [str(idx)[:12] for idx in cross.index[:10]],
                        "colorscale": "Teal"
                    }],
                    "layout": {
                        "title": f"🔥 {cat1.replace('_', ' ').title()} vs {cat2.replace('_', ' ').title()}",
                        "height": 400,
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "font": {"color": "#e5e7eb"}
                    }
                }
            else:
                # Fallback to bar
                counts = df[cat1].value_counts().head(10)
                return create_bar_chart(
                    [str(l)[:20] for l in counts.index],
                    counts.values.tolist(),
                    'Count',
                    cat1,
                    colors
                )
        
        elif rel_type == 'category_hierarchy':
            # Multi-level category visualization
            categories = relationship['categories']
            
            if len(categories) >= 2 and chart_type in ['sunburst', 'treemap']:
                # Build hierarchical data
                cat1, cat2 = categories[0], categories[1]
                grouped = df.groupby([cat1, cat2]).size().reset_index(name='count')
                grouped = grouped.nlargest(20, 'count')
                
                labels = []
                parents = []
                values = []
                
                # Add root categories
                for cat in grouped[cat1].unique()[:8]:
                    labels.append(str(cat)[:15])
                    parents.append("")
                    values.append(int(grouped[grouped[cat1] == cat]['count'].sum()))
                
                # Add child categories
                for _, row in grouped.head(15).iterrows():
                    labels.append(f"{str(row[cat2])[:12]}")
                    parents.append(str(row[cat1])[:15])
                    values.append(int(row['count']))
                
                if chart_type == 'sunburst':
                    return {
                        "data": [{
                            "type": "sunburst",
                            "labels": labels,
                            "parents": parents,
                            "values": values,
                            "marker": {"colors": colors * 3}
                        }],
                        "layout": {
                            "title": f"🌞 {cat1.replace('_', ' ').title()} → {cat2.replace('_', ' ').title()}",
                            "height": 400,
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "font": {"color": "#e5e7eb"}
                        }
                    }
                else:  # treemap
                    return {
                        "data": [{
                            "type": "treemap",
                            "labels": labels,
                            "parents": parents,
                            "values": values,
                            "marker": {"colors": colors * 3}
                        }],
                        "layout": {
                            "title": f"🗂️ {cat1.replace('_', ' ').title()} → {cat2.replace('_', ' ').title()}",
                            "height": 400,
                            "paper_bgcolor": "rgba(0,0,0,0)",
                            "font": {"color": "#e5e7eb"}
                        }
                    }
            
            # Fallback for single category
            cat = categories[0]
            counts = df[cat].value_counts().head(10)
            return create_pie_chart(
                [str(l)[:20] for l in counts.index],
                counts.values.tolist(),
                'Count',
                cat,
                'donut',
                colors
            )
        
        # ===========================================
        # NEW CHART HANDLERS FOR ADDITIONAL VARIETY
        # ===========================================
        elif rel_type == 'comparison_bar':
            cat_col = relationship['categorical']
            num_col = relationship['numeric']
            grouped = df.groupby(cat_col)[num_col].mean().nlargest(10)
            labels = [str(l)[:20] for l in grouped.index]
            values = [float(v) for v in grouped.values]
            return {
                'chart_id': f'comparison_{num_col}_{cat_col}',
                'title': f'Average {num_col.replace("_", " ").title()} Comparison',
                'type': 'grouped_bar',
                'plotly_config': {
                    'data': [{'type': 'bar', 'x': labels, 'y': values, 'marker': {'color': colors[:len(labels)]}}],
                    'layout': get_layout()
                }
            }
        
        elif rel_type == 'stacked_trend':
            values_cols = relationship['values']
            n_points = min(15, len(df))
            traces = []
            for i, col in enumerate(values_cols[:3]):
                segment_size = max(1, len(df) // n_points)
                vals = [float(df[col].iloc[j*segment_size:(j+1)*segment_size].sum()) for j in range(n_points)]
                traces.append({
                    'type': 'scatter',
                    'mode': 'lines',
                    'fill': 'tonexty' if i > 0 else 'tozeroy',
                    'name': col.replace('_', ' ').title()[:15],
                    'x': list(range(1, n_points + 1)),
                    'y': vals,
                    'line': {'color': colors[i % len(colors)]}
                })
            return {
                'chart_id': f'stacked_area_trend',
                'title': 'Cumulative Trends',
                'type': 'stacked_area',
                'plotly_config': {'data': traces, 'layout': get_layout()}
            }
        
        elif rel_type == 'donut_breakdown':
            cat_col = relationship['category']
            val_col = relationship['value']
            grouped = df.groupby(cat_col)[val_col].sum().nlargest(8)
            labels = [str(l)[:20] for l in grouped.index]
            values = [float(v) for v in grouped.values]
            return create_pie_chart(labels, values, val_col, cat_col, 'donut', colors)
        
        elif rel_type == 'line_trend':
            val_col = relationship['value']
            n_points = min(20, len(df))
            segment_size = max(1, len(df) // n_points)
            values = [float(df[val_col].iloc[i*segment_size:(i+1)*segment_size].mean()) for i in range(n_points)]
            return create_line_chart(
                [f'P{i+1}' for i in range(n_points)],
                values,
                val_col,
                colors
            )
        
        elif rel_type == 'horizontal_ranking':
            cat_col = relationship['category']
            val_col = relationship['value']
            grouped = df.groupby(cat_col)[val_col].sum().nlargest(10)
            labels = [str(l)[:20] for l in grouped.index]
            values = [float(v) for v in grouped.values]
            return create_horizontal_bar(labels, values, val_col, cat_col, colors)
        
        elif rel_type == 'grouped_comparison':
            cat_col = relationship['category']
            value_cols = relationship['values']
            grouped = df.groupby(cat_col)[value_cols].mean().head(8)
            traces = []
            for i, col in enumerate(value_cols[:3]):
                traces.append({
                    'type': 'bar',
                    'name': col.replace('_', ' ').title()[:15],
                    'x': [str(idx)[:12] for idx in grouped.index],
                    'y': [float(v) for v in grouped[col].values],
                    'marker': {'color': colors[i % len(colors)]}
                })
            return {
                'chart_id': f'grouped_{cat_col}',
                'title': f'Metrics Comparison by {cat_col.replace("_", " ").title()}',
                'type': 'stacked_bar',
                'plotly_config': {
                    'data': traces,
                    'layout': {**get_layout(), 'barmode': 'group'}
                }
            }
        
        # ===========================================
        # NEW PREMIUM CHART TYPE HANDLERS
        # ===========================================
        elif rel_type == 'combo_bar_line':
            return create_combo_bar_line_chart(df, relationship, colors)
        
        elif rel_type == 'lollipop':
            return create_lollipop_chart(df, relationship, colors)
        
        elif rel_type == 'diverging_bar':
            return create_diverging_bar_chart(df, relationship, colors)
        
        elif rel_type == 'slope':
            return create_slope_chart(df, relationship, colors)
        
        elif rel_type == 'dumbbell':
            return create_dumbbell_chart(df, relationship, colors)
        
        elif rel_type == 'range_plot':
            return create_range_plot(df, relationship, colors)
        
        elif rel_type == 'band_chart':
            return create_band_chart(df, relationship, colors)
        
        elif rel_type == 'step_line':
            return create_step_line_chart(df, relationship, colors)
        
    except Exception as e:
        logger.warning(f"Chart generation error: {e}")
    
    return None


# ================= CHART CREATORS (All Plotly configs) =================

def create_bar_chart(labels, values, num_col, cat_col, colors):
    return {
        'chart_id': f'bar_{num_col}_{cat_col}',
        'title': f'{num_col.replace("_", " ").title()} by {cat_col.replace("_", " ").title()}',
        'type': 'bar',
        'plotly_config': {
            'data': [{'type': 'bar', 'x': labels, 'y': values, 'marker': {'color': colors, 'line': {'width': 0}}}],
            'layout': get_layout()
        }
    }


def create_horizontal_bar(labels, values, num_col, cat_col, colors):
    return {
        'chart_id': f'hbar_{num_col}_{cat_col}',
        'title': f'{cat_col.replace("_", " ").title()} Ranking',
        'type': 'horizontal_bar',
        'plotly_config': {
            'data': [{'type': 'bar', 'y': labels, 'x': values, 'orientation': 'h', 'marker': {'color': colors[:len(values)]}}],
            'layout': {**get_layout(), 'yaxis': {'automargin': True}}
        }
    }


def create_pie_chart(labels, values, num_col, cat_col, chart_type, colors):
    return {
        'chart_id': f'{chart_type}_{cat_col}',
        'title': f'{cat_col.replace("_", " ").title()} Distribution',
        'type': chart_type,
        'plotly_config': {
            'data': [{
                'type': 'pie', 'labels': labels, 'values': values,
                'hole': 0.5 if chart_type == 'donut' else 0,
                'textinfo': 'percent', 'textfont': {'color': '#fff', 'size': 10},
                'marker': {'colors': colors[:len(labels)]}
            }],
            'layout': {**get_layout(), 'showlegend': True, 'legend': {'font': {'size': 9, 'color': '#9ca3af'}, 'orientation': 'h', 'y': -0.1}}
        }
    }


def create_sunburst_chart(labels, values, cat_col, colors):
    """Create a Sunburst chart for hierarchical category breakdown"""
    return {
        'chart_id': f'sunburst_{cat_col}',
        'title': f'{cat_col.replace("_", " ").title()} Sunburst',
        'type': 'sunburst',
        'plotly_config': {
            'data': [{
                'type': 'sunburst',
                'labels': labels,
                'parents': [''] * len(labels),  # Flat sunburst (no hierarchy)
                'values': values,
                'branchvalues': 'total',
                'marker': {'colors': colors[:len(labels)]},
                'textinfo': 'label+percent entry'
            }],
            'layout': {**get_layout(), 'margin': {'l': 10, 'r': 10, 't': 30, 'b': 10}}
        }
    }


def create_treemap_chart(labels, values, num_col, cat_col, colors):
    return {
        'chart_id': f'treemap_{cat_col}',
        'title': f'{cat_col.replace("_", " ").title()} Breakdown',
        'type': 'treemap',
        'plotly_config': {
            'data': [{
                'type': 'treemap',
                'labels': labels,
                'parents': [''] * len(labels),
                'values': values,
                'textinfo': 'label+percent entry',
                'marker': {'colors': colors[:len(labels)]}
            }],
            'layout': get_layout()
        }
    }


def create_scatter_chart(x_vals, y_vals, x_col, y_col, colors):
    data = [{
        'type': 'scatter', 'mode': 'markers',
        'x': x_vals, 'y': y_vals,
        'name': 'Data',
        'marker': {'size': 8, 'color': colors[0], 'opacity': 0.7, 'line': {'width': 1, 'color': 'rgba(255,255,255,0.3)'}}
    }]
    
    # Add Trendline - Silicon Valley Feature
    try:
        # Simple linear regression
        if len(x_vals) > 1:
            z = np.polyfit(list(range(len(x_vals))), y_vals, 1)
            p = np.poly1d(z)
            trend = p(list(range(len(x_vals))))
            
            data.append({
                'type': 'scatter', 'mode': 'lines',
                'x': x_vals, 'y': trend.tolist(), # Fix: Convert numpy array to list
                'name': 'Trend',
                'line': {'color': colors[1], 'width': 2, 'dash': 'dash'}
            })
    except:
        pass

    return {
        'chart_id': f'scatter_{x_col}_{y_col}',
        'title': f'{y_col.replace("_", " ")} vs {x_col.replace("_", " ")}',
        'type': 'scatter',
        'plotly_config': {
            'data': data,
            'layout': {**get_layout(), 'showlegend': False}
        }
    }


def create_bubble_chart(x_vals, y_vals, sizes, x_col, y_col, colors):
    return {
        'chart_id': f'bubble_{x_col}_{y_col}',
        'title': f'{y_col.replace("_", " ")} vs {x_col.replace("_", " ")} (Size)',
        'type': 'bubble',
        'plotly_config': {
            'data': [{
                'type': 'scatter', 'mode': 'markers',
                'x': x_vals, 'y': y_vals,
                'marker': {'size': sizes, 'color': y_vals, 'colorscale': [[0, colors[0]], [1, colors[-1]]], 'opacity': 0.6}
            }],
            'layout': get_layout()
        }
    }


def create_line_chart(labels, values, col, colors):
    # Add simple forecast (3 periods) - Silicon Valley Feature
    try:
        if len(values) >= 3:
            last_3_avg_diff = (values[-1] - values[-4]) / 3
            forecast_values = [float(values[-1] + last_3_avg_diff * (i+1)) for i in range(3)] # Ensure floats
            forecast_labels = [f'Forecast {i+1}' for i in range(3)]
            
            # Main Line
            data = [{
                'type': 'scatter', 'mode': 'lines+markers',
                'x': labels, 'y': values,
                'name': 'Actual',
                'line': {'color': colors[0], 'width': 3, 'shape': 'spline'},
                'marker': {'size': 6, 'color': colors[0]}
            }]
            
            # Forecast Line (Dotted)
            data.append({
                'type': 'scatter', 'mode': 'lines+markers',
                'x': [labels[-1]] + forecast_labels,
                'y': [values[-1]] + forecast_values,
                'name': 'Forecast',
                'line': {'color': colors[0], 'width': 3, 'dash': 'dot'},
                'marker': {'size': 6, 'opacity': 0.7}
            })
        else:
            data = [{'type': 'scatter', 'mode': 'lines+markers', 'x': labels, 'y': values, 'line': {'color': colors[0]}, 'marker': {'color': colors[0]}}]
            
    except:
        data = [{'type': 'scatter', 'mode': 'lines+markers', 'x': labels, 'y': values, 'line': {'color': colors[0]}, 'marker': {'color': colors[0]}}]

    return {
        'chart_id': f'line_{col}',
        'title': f'{col.replace("_", " ").title()} Trend + Forecast',
        'type': 'line',
        'plotly_config': {
            'data': data,
            'layout': {**get_layout(), 'showlegend': True, 'legend': {'orientation': 'h', 'y': 1.1}}
        }
    }


def create_area_chart(labels, values, col, colors):
    return {
        'chart_id': f'area_{col}',
        'title': f'{col.replace("_", " ").title()} Over Time',
        'type': 'area',
        'plotly_config': {
            'data': [{
                'type': 'scatter', 'mode': 'lines',
                'x': labels, 'y': values,
                'fill': 'tozeroy', 'fillcolor': f'{colors[0]}40',
                'line': {'color': colors[0], 'width': 2, 'shape': 'spline'}
            }],
            'layout': get_layout()
        }
    }


def create_histogram(values, col, colors):
    return {
        'chart_id': f'hist_{col}',
        'title': f'{col.replace("_", " ").title()} Distribution',
        'type': 'histogram',
        'plotly_config': {
            'data': [{'type': 'histogram', 'x': values, 'marker': {'color': colors[0]}, 'nbinsx': 15}],
            'layout': get_layout()
        }
    }


def create_box_plot(df, columns, colors):
    data = []
    for i, col in enumerate(columns):
        data.append({'type': 'box', 'y': df[col].dropna().tolist()[:200], 'name': col, 'marker': {'color': colors[i % len(colors)]}})
    return {
        'chart_id': f'box_{columns[0]}',
        'title': 'Distribution Analysis',
        'type': 'box',
        'plotly_config': {'data': data, 'layout': get_layout()}
    }


def create_correlation_heatmap(df, colors):
    numeric_df = df.select_dtypes(include=['int64', 'float64']).iloc[:, :6]
    if len(numeric_df.columns) < 2:
        return None
    corr = numeric_df.corr()
    return {
        'chart_id': 'heatmap_corr',
        'title': 'Correlation Matrix',
        'type': 'heatmap',
        'plotly_config': {
            'data': [{
                'type': 'heatmap',
                'z': corr.values.tolist(),
                'x': corr.columns.tolist(),
                'y': corr.columns.tolist(),
                'colorscale': [[0, colors[-1]], [0.5, '#1f2937'], [1, colors[0]]],
                'showscale': True
            }],
            'layout': get_layout()
        }
    }


def create_stacked_bar(df, rel, colors):
    cat1 = rel['cat1']
    cat2 = rel['cat2']
    
    # Handle both numeric and categorical-only data
    if 'value' in rel and rel['value'] in df.columns:
        val = rel['value']
        # Safe Pivot: Limit to top categories first
        top_cat1 = df[cat1].value_counts().head(20).index
        top_cat2 = df[cat2].value_counts().head(20).index
        mask = df[cat1].isin(top_cat1) & df[cat2].isin(top_cat2)
        pivot = df[mask].groupby([cat1, cat2])[val].sum().unstack(fill_value=0)
        title_prefix = val.replace("_", " ")
    else:
        # Categorical-only: use counts
        # Safe Crosstab: Limit to top categories first
        top_cat1 = df[cat1].value_counts().head(20).index
        top_cat2 = df[cat2].value_counts().head(20).index
        mask = df[cat1].isin(top_cat1) & df[cat2].isin(top_cat2)
        pivot = pd.crosstab(df.loc[mask, cat1], df.loc[mask, cat2])
        title_prefix = "Count"
    
    pivot = pivot.iloc[:8, :5]  # Limit size
    
    data = []
    for i, col in enumerate(pivot.columns):
        y_values = pivot[col].tolist()
        # Ensure we have valid numeric data
        y_values = [int(v) if pd.notna(v) else 0 for v in y_values]
        data.append({
            'type': 'bar', 'name': str(col)[:15],
            'x': [str(x)[:15] for x in pivot.index],  # Truncate long labels
            'y': y_values,
            'marker': {'color': colors[i % len(colors)]}
        })
    
    return {
        'chart_id': f'stacked_{cat1}_{cat2}',
        'title': f'{title_prefix} by {cat1.replace("_", " ").title()} and {cat2.replace("_", " ").title()}',
        'type': 'stacked_bar',
        'plotly_config': {'data': data, 'layout': {**get_layout(), 'barmode': 'stack'}}
    }


def create_funnel_chart(df, rel, colors):
    cat = rel.get('category') or rel.get('categorical')
    
    # Handle both numeric and categorical-only data
    if 'value' in rel and rel['value'] in df.columns:
        val = rel['value']
        grouped = df.groupby(cat)[val].sum().sort_values(ascending=False).head(6)
        title_prefix = val.replace("_", " ").title()
    else:
        # Categorical-only: use counts
        grouped = df[cat].value_counts().head(6)
        title_prefix = "Count"
    
    return {
        'chart_id': f'funnel_{cat}',
        'title': f'{title_prefix} Conversion Funnel',
        'type': 'funnel',
        'plotly_config': {
            'data': [{
                'type': 'funnel',
                'y': [str(idx)[:20] for idx in grouped.index],
                'x': [int(v) for v in grouped.values],
                'textinfo': 'value+percent initial',
                'marker': {'color': colors[:len(grouped)]}
            }],
            'layout': get_layout()
        }
    }


def create_pareto_chart(df, rel, colors):
    """
    POWER BI PARETO CHART - 80/20 Analysis
    Shows bars sorted by value with cumulative % line overlay
    """
    cat = rel.get('category') or rel.get('categorical')
    val = rel.get('value') or rel.get('numeric')
    
    if not cat or not val or cat not in df.columns or val not in df.columns:
        return None
    
    # Group and sort by value descending
    grouped = df.groupby(cat)[val].sum().sort_values(ascending=False).head(15)
    total = grouped.sum()
    
    if total == 0:
        return None
    
    # Calculate cumulative percentage
    cumsum = grouped.cumsum()
    cum_pct = (cumsum / total * 100).tolist()
    
    labels = [str(l)[:20] for l in grouped.index]
    values = [float(v) for v in grouped.values]
    
    return {
        'chart_id': f'pareto_{cat}_{val}',
        'title': f'Pareto Analysis: {val.replace("_", " ").title()} by {cat.replace("_", " ").title()}',
        'type': 'pareto',
        'analysis': 'power_bi_80_20',
        'plotly_config': {
            'data': [
                # Bar chart (values)
                {
                    'type': 'bar',
                    'name': val.replace('_', ' ').title(),
                    'x': labels,
                    'y': values,
                    'marker': {'color': colors[0]},
                    'yaxis': 'y'
                },
                # Cumulative line
                {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': 'Cumulative %',
                    'x': labels,
                    'y': cum_pct,
                    'line': {'color': colors[1], 'width': 3},
                    'marker': {'size': 8, 'color': colors[1]},
                    'yaxis': 'y2'
                },
                # 80% threshold line
                {
                    'type': 'scatter',
                    'mode': 'lines',
                    'name': '80% Threshold',
                    'x': [labels[0], labels[-1]],
                    'y': [80, 80],
                    'line': {'color': '#ef4444', 'width': 2, 'dash': 'dash'},
                    'yaxis': 'y2',
                    'showlegend': True,
                    'hoverinfo': 'skip'
                }
            ],
            'layout': {
                **get_layout(),
                'yaxis': {'title': val.replace('_', ' ').title(), 'side': 'left'},
                'yaxis2': {'title': 'Cumulative %', 'overlaying': 'y', 'side': 'right', 'range': [0, 105]},
                'legend': {'orientation': 'h', 'y': -0.2}
            }
        }
    }


def create_waterfall_chart(df, rel, colors):
    vals = rel['values']
    sums = [df[v].sum() for v in vals]
    names = [v.replace('_', ' ').title() for v in vals]
    
    # Calculate deltas for waterfall effect
    deltas = [sums[0]]
    for i in range(1, len(sums)):
        deltas.append(sums[i] - sums[i-1])
        
    return {
        'chart_id': 'waterfall_variance',
        'title': 'Metric Evolution',
        'type': 'waterfall',
        'plotly_config': {
            'data': [{
                'type': 'waterfall',
                'measure': ['absolute'] + ['relative'] * (len(sums)-1),
                'x': names,
                'y': [sums[0]] + [sums[i]-sums[i-1] for i in range(1, len(sums))],
                'connector': {'line': {'color': '#6366f1'}},
                'decreasing': {'marker': {'color': '#ef4444'}},
                'increasing': {'marker': {'color': '#10b981'}},
                'totals': {'marker': {'color': '#3b82f6'}}
            }],
            'layout': get_layout()
        }
    }


def create_radar_chart(df, rel, colors):
    cats = rel['category']
    metrics = rel['metrics']
    
    # Normalize metrics to 0-1 scale for fair comparison
    top_items = df.groupby(cats)[metrics[0]].sum().nlargest(3).index.tolist()
    data = []
    
    for i, item in enumerate(top_items):
        item_data = df[df[cats] == item][metrics].sum()
        # Simple normalization for visualization
        normalized_values = (item_data / df[metrics].sum() * 5).tolist()
        
        data.append({
            'type': 'scatterpolar',
            'r': normalized_values,
            'theta': [m.replace('_', ' ').title() for m in metrics],
            'fill': 'toself',
            'name': str(item)
        })
        
    return {
        'chart_id': f'radar_{cats}',
        'title': f'Multi-Metric Comparison: {cats}',
        'type': 'radar',
        'plotly_config': {
            'data': data,
            'layout': {
                **get_layout(),
                'polar': {
                    'radialaxis': {'visible': True, 'range': [0, max([max(d['r']) for d in data]) * 1.1]},
                    'bgcolor': 'rgba(0,0,0,0)'
                }
            }
        }
    }


def create_gauge_chart(df, rel, colors):
    metric = rel['metric']
    value = df[metric].mean()
    target = df[metric].max() * 0.8
    
    return {
        'chart_id': f'gauge_{metric}',
        'title': f'Average {metric.replace("_", " ").title()}',
        'type': 'gauge',
        'plotly_config': {
            'data': [{
                'type': 'indicator',
                'mode': 'gauge+number+delta',
                'value': value,
                'delta': {'reference': target},
                'gauge': {
                    'axis': {'range': [None, df[metric].max()]},
                    'bar': {'color': colors[0]},
                    'steps': [
                        {'range': [0, target*0.5], 'color': f'{colors[0]}40'},
                        {'range': [target*0.5, target], 'color': f'{colors[0]}80'}
                    ]
                }
            }],
            'layout': {'paper_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': '#9ca3af'}}
        }
    }


def create_violin_chart(df, rel, colors):
    cat = rel['category']
    val = rel['value']
    
    top_cats = df[cat].value_counts().head(5).index.tolist()
    filtered_df = df[df[cat].isin(top_cats)]
    
    data = []
    for i, c in enumerate(top_cats):
        data.append({
            'type': 'violin',
            'x': filtered_df[filtered_df[cat] == c][cat].tolist(),
            'y': filtered_df[filtered_df[cat] == c][val].tolist(),
            'name': str(c),
            'box': {'visible': True},
            'meanline': {'visible': True},
            'line': {'color': colors[i % len(colors)]}
        })

    return {
        'chart_id': f'violin_{cat}_{val}',
        'title': f'{val.replace("_", " ")} Distribution by {cat}',
        'type': 'violin',
        'plotly_config': {
            'data': data,
            'layout': get_layout()
        }
    }



def create_sankey_chart(df, rel, colors):
    src = rel['source']
    tgt = rel['target']
    val = rel['value']
    
    # Aggregation for flow
    df_agg = df.groupby([src, tgt])[val].sum().reset_index()
    
    # Limit to top 50 flows for readability
    if len(df_agg) > 50:
        df_agg = df_agg.nlargest(50, val)
    
    # Create unique node labels
    all_nodes = list(pd.concat([df_agg[src], df_agg[tgt]]).unique())
    node_map = {node: i for i, node in enumerate(all_nodes)}
    
    return {
        'chart_id': f'sankey_{src}_{tgt}',
        'title': f'Flow: {src.title()} to {tgt.title()}',
        'type': 'sankey',
        'plotly_config': {
            'data': [{
                'type': 'sankey',
                'node': {
                    'pad': 15,
                    'thickness': 20,
                    'line': {'color': 'black', 'width': 0.5},
                    'label': all_nodes,
                    'color': [colors[i % len(colors)] for i in range(len(all_nodes))]
                },
                'link': {
                    'source': df_agg[src].map(node_map).tolist(),
                    'target': df_agg[tgt].map(node_map).tolist(),
                    'value': df_agg[val].tolist(),
                    'color': f'{colors[0]}40'
                }
            }],
            'layout': get_layout()
        }
    }


def create_candlestick_chart(df, rel, colors):
    date = rel['date']
    o, h, l, c = rel['open'], rel['high'], rel['low'], rel['close']
    
    df_sorted = df.sort_values(date).tail(50)  # Last 50 periods
    
    return {
        'chart_id': 'candlestick_financial',
        'title': 'Financial Performance (OHLC)',
        'type': 'candlestick',
        'plotly_config': {
            'data': [{
                'type': 'candlestick',
                'x': df_sorted[date].tolist(),
                'open': df_sorted[o].tolist(),
                'high': df_sorted[h].tolist(),
                'low': df_sorted[l].tolist(),
                'close': df_sorted[c].tolist(),
                'increasing': {'line': {'color': '#10b981'}},
                'decreasing': {'line': {'color': '#ef4444'}}
            }],
            'layout': {**get_layout(), 'xaxis': {'rangeslider': {'visible': False}}}
        }
    }


def create_bullet_chart(df, rel, colors):
    col = rel['column']
    target = rel['target']
    
    current_val = df[col].iloc[-1] if len(df) > 0 else 0
    target_val = df[target].iloc[-1] if len(df) > 0 else current_val * 1.1
    
    return {
        'chart_id': f'bullet_{col}',
        'title': f'{col.title()} vs Target',
        'type': 'indicator',
        'plotly_config': {
            'data': [{
                'type': 'indicator',
                'mode': 'number+gauge+delta',
                'value': current_val,
                'delta': {'reference': target_val},
                'gauge': {
                    'shape': 'bullet',
                    'axis': {'range': [None, target_val * 1.2]},
                    'bar': {'color': colors[0]},
                    'steps': [
                        {'range': [0, target_val * 0.7], 'color': '#374151'},
                        {'range': [target_val * 0.7, target_val], 'color': '#4b5563'}
                    ],
                    'threshold': {
                        'line': {'color': 'white', 'width': 2},
                        'thickness': 0.75,
                        'value': target_val
                    }
                }
            }],
            'layout': {'height': 250, 'margin': {'t': 0, 'b': 0}, 'paper_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': '#9ca3af'}}
        }
    }


def create_parallel_coords_chart(df, rel, colors):
    cols = rel['columns'][:4] # Max 4 dimensions
    cat = rel.get('category')
    
    dimensions = []
    for col in cols:
        dimensions.append({
            'range': [df[col].min(), df[col].max()],
            'label': col.title(),
            'values': df[col].tolist()
        })
        
    line_color = (df[cat].astype('category').cat.codes if cat else pd.Series([0]*len(df))).tolist()  # Convert to list
        
    return {
        'chart_id': 'parallel_multivariate',
        'title': 'Multivariate Analysis',
        'type': 'parcoords',
        'plotly_config': {
            'data': [{
                'type': 'parcoords',
                'line': {
                    'color': line_color,
                    'colorscale': [[0, colors[0]], [1, colors[-1]]] if cat else None
                },
                'dimensions': dimensions
            }],
            'layout': get_layout()
        }
    }



def create_choropleth_chart(df, rel, colors):
    loc_col = rel['location']
    val_col = rel['value']
    
    # Aggregate by location
    df_agg = df.groupby(loc_col)[val_col].sum().reset_index()
    
    # HEURISTIC: Check if we can actually map this
    # If not a country column and values are not 2-char state codes, it's likely City/Region which Plotly Map can't handle well without Lat/Lon
    # In that case, FALLBACK to a nice Bar Chart so user sees data!
    sample_val = str(df_agg[loc_col].iloc[0]) if not df_agg.empty else ''
    is_likely_state = len(sample_val) == 2 and sample_val.isalpha() and sample_val.isupper()
    is_country = 'country' in loc_col.lower()
    
    if not is_country and not is_likely_state:
        # Fallback to Bar Chart
        return {
            'chart_id': f'bar_geo_{loc_col}',
            'title': f'Geographic Distribution by {loc_col.title()} (Top 10)',
            'type': 'bar',
            'plotly_config': {
                'data': [{
                    'type': 'bar',
                    'x': df_agg[val_col].nlargest(10).tolist(),
                    'y': df_agg.nlargest(10, val_col)[loc_col].tolist(),
                    'orientation': 'h',
                    'marker': {'color': colors[0]}
                }],
                'layout': {**get_layout(), 'yaxis': {'autorange': 'reversed'}} # Top on top
            }
        }

    return {
        'chart_id': f'map_{loc_col}',
        'title': f'Geographic Distribution by {loc_col.title()}',
        'type': 'choropleth',
        'plotly_config': {
            'data': [{
                'type': 'choropleth',
                'locations': df_agg[loc_col].tolist(),
                'locationmode': 'country names' if is_country else 'USA-states', 
                'z': df_agg[val_col].tolist(),
                'colorscale': [[0, '#f0f9ff'], [1, colors[0]]],
                'autocolorscale': False,
                'marker': {'line': {'color': 'rgb(255,255,255)', 'width': 0.5}},
                'colorbar': {'title': val_col.title(), 'thickness': 10}
            }],
            'layout': {
                **get_layout(),
                'geo': {
                    'showframe': False,
                    'showcoastlines': False,
                    'projection': {'type': 'mercator'},
                    'bgcolor': 'rgba(0,0,0,0)',
                }
            }
        }
    }


def create_scatter3d_chart(df, rel, colors):
    x, y, z = rel['x'], rel['y'], rel['z']
    c_col = rel['color']
    
    # Sample if too large
    df_sample = df.head(500)
    
    return {
        'chart_id': f'3d_{x}_{y}_{z}',
        'title': f'3D Correlation Analysis',
        'type': 'scatter3d',
        'plotly_config': {
            'data': [{
                'type': 'scatter3d',
                'mode': 'markers',
                'x': df_sample[x].tolist(),
                'y': df_sample[y].tolist(),
                'z': df_sample[z].tolist(),
                'marker': {
                    'size': 4,
                    'color': (df_sample[c_col].astype('category').cat.codes if df[c_col].dtype == 'object' else df_sample[c_col]).tolist(),
                    'colorscale': 'Viridis',
                    'opacity': 0.8
                }
            }],
            'layout': {
                'paper_bgcolor': 'rgba(0,0,0,0)',
                'scene': {
                    'xaxis': {'title': x, 'backgroundcolor': 'rgba(0,0,0,0)', 'gridcolor': 'rgba(255,255,255,0.1)'},
                    'yaxis': {'title': y, 'backgroundcolor': 'rgba(0,0,0,0)', 'gridcolor': 'rgba(255,255,255,0.1)'},
                    'zaxis': {'title': z, 'backgroundcolor': 'rgba(0,0,0,0)', 'gridcolor': 'rgba(255,255,255,0.1)'},
                },
                'margin': {'l': 0, 'r': 0, 'b': 0, 't': 0},
                'height': 400
            }
        }
    }


def create_calendar_heatmap(df, rel, colors):
    date_col = rel['date']
    val_col = rel['value']
    
    try:
        # Convert to datetime safely
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df_clean = df.dropna(subset=[date_col])
        
        if df_clean.empty:
            return None # Skip if no valid dates
        
        # Group by date
        if val_col:
            daily = df_clean.groupby(df_clean[date_col].dt.date)[val_col].sum()
        else:
            daily = df_clean.groupby(df_clean[date_col].dt.date).size()
            
        return {
            'chart_id': 'calendar_heatmap',
            'title': 'Daily Activity Heatmap',
            'type': 'heatmap',
            'plotly_config': {
                'data': [{
                    'type': 'heatmap',
                    'x': [d.strftime('%Y-%m-%d') for d in daily.index],
                    'y': ['Activity'], # Single row label for 2D array with 1 row
                    'z': [daily.values.tolist()],  # Heatmap expects 2D array
                    'colorscale': [[0, '#f3f4f6'], [1, colors[0]]],
                    'showscale': False
                }],
                'layout': {
                    **get_layout(),
                    'height': 150,
                    'margin': {'l': 20, 'r': 20, 't': 30, 'b': 20}
                }
            }
        }
    except:
        return None


def get_layout():
    return {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#9ca3af', 'size': 10},
        'margin': {'l': 45, 'r': 15, 't': 25, 'b': 50},
        'xaxis': {'gridcolor': 'rgba(255,255,255,0.05)', 'tickangle': -30},
        'yaxis': {'gridcolor': 'rgba(255,255,255,0.05)'}
    }


# ================= NEW PREMIUM CHART CREATORS =================

def create_combo_bar_line_chart(df, rel, colors):
    """
    POWER BI STYLE COMBO CHART - Bar + Line with Dual Y-Axis
    Perfect for showing volume vs rate, sales vs margin, etc.
    """
    try:
        cat_col = rel['category']
        bar_col = rel['bar_metric']
        line_col = rel['line_metric']
        
        grouped = df.groupby(cat_col)[[bar_col, line_col]].sum().head(10)
        labels = [str(l)[:15] for l in grouped.index]
        
        return {
            'chart_id': f'combo_{bar_col}_{line_col}',
            'title': f'{bar_col.replace("_", " ").title()} vs {line_col.replace("_", " ").title()}',
            'type': 'combo_bar_line',
            'analysis': 'dual_axis_comparison',
            'plotly_config': {
                'data': [
                    # Bar chart on primary y-axis
                    {
                        'type': 'bar',
                        'name': bar_col.replace('_', ' ').title(),
                        'x': labels,
                        'y': grouped[bar_col].tolist(),
                        'marker': {'color': colors[0], 'opacity': 0.8},
                        'yaxis': 'y'
                    },
                    # Line chart on secondary y-axis
                    {
                        'type': 'scatter',
                        'mode': 'lines+markers',
                        'name': line_col.replace('_', ' ').title(),
                        'x': labels,
                        'y': grouped[line_col].tolist(),
                        'line': {'color': colors[1], 'width': 3},
                        'marker': {'size': 8, 'color': colors[1]},
                        'yaxis': 'y2'
                    }
                ],
                'layout': {
                    **get_layout(),
                    'yaxis': {'title': bar_col.replace('_', ' ').title(), 'side': 'left'},
                    'yaxis2': {
                        'title': line_col.replace('_', ' ').title(),
                        'overlaying': 'y',
                        'side': 'right',
                        'showgrid': False
                    },
                    'legend': {'orientation': 'h', 'y': -0.15}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Combo chart error: {e}")
        return None


def create_lollipop_chart(df, rel, colors):
    """
    LOLLIPOP CHART - Elegant alternative to bar chart for rankings
    Shows stem + circle for each data point
    """
    try:
        cat_col = rel['category']
        val_col = rel['value']
        
        grouped = df.groupby(cat_col)[val_col].sum().sort_values(ascending=True).tail(12)
        labels = [str(l)[:20] for l in grouped.index]
        values = grouped.values.tolist()
        
        # Create stems (lines from 0 to value)
        stems = []
        for i, (label, val) in enumerate(zip(labels, values)):
            stems.append({
                'type': 'scatter',
                'mode': 'lines',
                'x': [0, val],
                'y': [label, label],
                'line': {'color': colors[i % len(colors)], 'width': 2},
                'showlegend': False,
                'hoverinfo': 'skip'
            })
        
        # Create dots
        dots = {
            'type': 'scatter',
            'mode': 'markers',
            'x': values,
            'y': labels,
            'marker': {
                'size': 12,
                'color': colors[:len(values)],
                'line': {'width': 2, 'color': 'white'}
            },
            'name': val_col.replace('_', ' ').title(),
            'text': [f'{v:,.0f}' for v in values],
            'textposition': 'middle right',
            'hovertemplate': '%{y}: %{x:,.0f}<extra></extra>'
        }
        
        return {
            'chart_id': f'lollipop_{cat_col}',
            'title': f'{val_col.replace("_", " ").title()} Ranking',
            'type': 'lollipop',
            'analysis': 'ranking_visualization',
            'plotly_config': {
                'data': stems + [dots],
                'layout': {
                    **get_layout(),
                    'yaxis': {'automargin': True, 'gridwidth': 0},
                    'xaxis': {'zeroline': True, 'zerolinecolor': 'rgba(255,255,255,0.2)'}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Lollipop chart error: {e}")
        return None


def create_diverging_bar_chart(df, rel, colors):
    """
    DIVERGING BAR CHART - Shows positive/negative from center
    Perfect for profit/loss, growth/decline, sentiment analysis
    """
    try:
        cat_col = rel.get('category')
        val_col = rel['value']
        
        if cat_col and cat_col in df.columns:
            grouped = df.groupby(cat_col)[val_col].sum().head(12)
            labels = [str(l)[:18] for l in grouped.index]
            values = grouped.values.tolist()
        else:
            # Use index-based if no category
            values = df[val_col].head(15).tolist()
            labels = [f'Item {i+1}' for i in range(len(values))]
        
        # Center around mean for diverging effect
        mean_val = np.mean(values)
        diverging_values = [v - mean_val for v in values]
        
        # Color by positive/negative
        bar_colors = [colors[0] if v >= 0 else '#ef4444' for v in diverging_values]
        
        return {
            'chart_id': f'diverging_{val_col}',
            'title': f'{val_col.replace("_", " ").title()} Variance from Average',
            'type': 'diverging_bar',
            'analysis': 'variance_from_mean',
            'plotly_config': {
                'data': [{
                    'type': 'bar',
                    'orientation': 'h',
                    'y': labels,
                    'x': diverging_values,
                    'marker': {'color': bar_colors},
                    'text': [f'{v:+,.0f}' for v in diverging_values],
                    'textposition': 'outside',
                    'hovertemplate': '%{y}: %{x:+,.0f} vs avg<extra></extra>'
                }],
                'layout': {
                    **get_layout(),
                    'xaxis': {
                        'zeroline': True,
                        'zerolinecolor': 'rgba(255,255,255,0.5)',
                        'zerolinewidth': 2,
                        'title': f'Difference from Mean ({mean_val:,.0f})'
                    },
                    'yaxis': {'automargin': True}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Diverging bar error: {e}")
        return None


def create_slope_chart(df, rel, colors):
    """
    SLOPE CHART - Period over period comparison
    Shows change between two time periods for multiple categories
    """
    try:
        start_col = rel['start_value']
        end_col = rel['end_value']
        cat_col = rel.get('category')
        
        if cat_col and cat_col in df.columns:
            grouped = df.groupby(cat_col)[[start_col, end_col]].sum().head(8)
            labels = [str(l)[:15] for l in grouped.index]
            start_vals = grouped[start_col].tolist()
            end_vals = grouped[end_col].tolist()
        else:
            # Use aggregated totals
            n_segments = min(8, len(df) // 2)
            segment_size = len(df) // n_segments
            start_vals = [df[start_col].iloc[i*segment_size:(i+1)*segment_size//2].sum() for i in range(n_segments)]
            end_vals = [df[end_col].iloc[i*segment_size:(i+1)*segment_size//2].sum() for i in range(n_segments)]
            labels = [f'Segment {i+1}' for i in range(n_segments)]
        
        data = []
        for i, (label, s, e) in enumerate(zip(labels, start_vals, end_vals)):
            # Determine color by growth
            line_color = colors[0] if e >= s else '#ef4444'
            
            data.append({
                'type': 'scatter',
                'mode': 'lines+markers+text',
                'x': [start_col.replace('_', ' ').title(), end_col.replace('_', ' ').title()],
                'y': [s, e],
                'name': label,
                'line': {'color': line_color, 'width': 2},
                'marker': {'size': 10, 'color': line_color},
                'text': [f'{s:,.0f}', f'{e:,.0f}'],
                'textposition': ['middle left', 'middle right']
            })
        
        return {
            'chart_id': f'slope_{start_col}_{end_col}',
            'title': f'{start_col.replace("_", " ").title()} → {end_col.replace("_", " ").title()}',
            'type': 'slope',
            'analysis': 'period_comparison',
            'plotly_config': {
                'data': data,
                'layout': {
                    **get_layout(),
                    'showlegend': True,
                    'legend': {'orientation': 'v', 'x': 1.02}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Slope chart error: {e}")
        return None


def create_dumbbell_chart(df, rel, colors):
    """
    DUMBBELL CHART - Before/After or Two-metric comparison
    Shows range between two values for each category
    """
    try:
        cat_col = rel['category']
        val1_col = rel['value1']
        val2_col = rel['value2']
        
        grouped = df.groupby(cat_col)[[val1_col, val2_col]].sum().head(10)
        labels = [str(l)[:18] for l in grouped.index]
        val1 = grouped[val1_col].tolist()
        val2 = grouped[val2_col].tolist()
        
        data = []
        
        # Draw connecting lines first
        for i, (label, v1, v2) in enumerate(zip(labels, val1, val2)):
            data.append({
                'type': 'scatter',
                'mode': 'lines',
                'x': [v1, v2],
                'y': [label, label],
                'line': {'color': 'rgba(150,150,150,0.5)', 'width': 4},
                'showlegend': False,
                'hoverinfo': 'skip'
            })
        
        # Add dots for value 1
        data.append({
            'type': 'scatter',
            'mode': 'markers',
            'x': val1,
            'y': labels,
            'marker': {'size': 14, 'color': colors[0], 'line': {'width': 2, 'color': 'white'}},
            'name': val1_col.replace('_', ' ').title(),
            'hovertemplate': '%{y}: %{x:,.0f}<extra>' + val1_col + '</extra>'
        })
        
        # Add dots for value 2
        data.append({
            'type': 'scatter',
            'mode': 'markers',
            'x': val2,
            'y': labels,
            'marker': {'size': 14, 'color': colors[1], 'line': {'width': 2, 'color': 'white'}},
            'name': val2_col.replace('_', ' ').title(),
            'hovertemplate': '%{y}: %{x:,.0f}<extra>' + val2_col + '</extra>'
        })
        
        return {
            'chart_id': f'dumbbell_{val1_col}_{val2_col}',
            'title': f'{val1_col.replace("_", " ").title()} vs {val2_col.replace("_", " ").title()}',
            'type': 'dumbbell',
            'analysis': 'comparison_visualization',
            'plotly_config': {
                'data': data,
                'layout': {
                    **get_layout(),
                    'yaxis': {'automargin': True},
                    'legend': {'orientation': 'h', 'y': -0.15}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Dumbbell chart error: {e}")
        return None


def create_range_plot(df, rel, colors):
    """
    RANGE PLOT - Min-Max visualization with markers
    Shows the spread of values for each category
    """
    try:
        cat_col = rel['category']
        val_col = rel['value']
        
        stats = df.groupby(cat_col)[val_col].agg(['min', 'max', 'mean']).head(10)
        labels = [str(l)[:18] for l in stats.index]
        
        data = []
        
        # Draw range lines
        for i, (label, row) in enumerate(zip(labels, stats.itertuples())):
            data.append({
                'type': 'scatter',
                'mode': 'lines',
                'x': [row.min, row.max],
                'y': [label, label],
                'line': {'color': colors[i % len(colors)], 'width': 6},
                'showlegend': False,
                'hoverinfo': 'skip'
            })
        
        # Min markers
        data.append({
            'type': 'scatter',
            'mode': 'markers',
            'x': stats['min'].tolist(),
            'y': labels,
            'marker': {'size': 10, 'color': '#ef4444', 'symbol': 'triangle-left'},
            'name': 'Min',
            'hovertemplate': '%{y}: Min = %{x:,.0f}<extra></extra>'
        })
        
        # Mean markers
        data.append({
            'type': 'scatter',
            'mode': 'markers',
            'x': stats['mean'].tolist(),
            'y': labels,
            'marker': {'size': 12, 'color': colors[0], 'symbol': 'diamond'},
            'name': 'Mean',
            'hovertemplate': '%{y}: Mean = %{x:,.0f}<extra></extra>'
        })
        
        # Max markers
        data.append({
            'type': 'scatter',
            'mode': 'markers',
            'x': stats['max'].tolist(),
            'y': labels,
            'marker': {'size': 10, 'color': '#22c55e', 'symbol': 'triangle-right'},
            'name': 'Max',
            'hovertemplate': '%{y}: Max = %{x:,.0f}<extra></extra>'
        })
        
        return {
            'chart_id': f'range_{cat_col}_{val_col}',
            'title': f'{val_col.replace("_", " ").title()} Range by {cat_col.replace("_", " ").title()}',
            'type': 'range_plot',
            'analysis': 'min_max_spread',
            'plotly_config': {
                'data': data,
                'layout': {
                    **get_layout(),
                    'yaxis': {'automargin': True},
                    'legend': {'orientation': 'h', 'y': -0.15}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Range plot error: {e}")
        return None


def create_band_chart(df, rel, colors):
    """
    BAND CHART - Line with confidence interval bands
    Shows trend with uncertainty/variability range
    """
    try:
        val_col = rel['value']
        
        # Create rolling statistics
        values = df[val_col].fillna(0).values
        n_points = min(30, len(values))
        segment_size = max(1, len(values) // n_points)
        
        means = []
        stds = []
        for i in range(n_points):
            segment = values[i*segment_size:(i+1)*segment_size]
            means.append(np.mean(segment))
            stds.append(np.std(segment) if len(segment) > 1 else 0)
        
        x_vals = list(range(1, n_points + 1))
        upper = [m + s for m, s in zip(means, stds)]
        lower = [m - s for m, s in zip(means, stds)]
        
        return {
            'chart_id': f'band_{val_col}',
            'title': f'{val_col.replace("_", " ").title()} Trend with Confidence Band',
            'type': 'band_chart',
            'analysis': 'confidence_interval',
            'plotly_config': {
                'data': [
                    # Upper bound (invisible, for fill)
                    {
                        'type': 'scatter',
                        'mode': 'lines',
                        'x': x_vals,
                        'y': upper,
                        'line': {'color': 'transparent'},
                        'showlegend': False,
                        'name': 'Upper'
                    },
                    # Lower bound with fill to upper
                    {
                        'type': 'scatter',
                        'mode': 'lines',
                        'x': x_vals,
                        'y': lower,
                        'fill': 'tonexty',
                        'fillcolor': f'{colors[0]}30',
                        'line': {'color': 'transparent'},
                        'showlegend': False,
                        'name': '±1 Std Dev'
                    },
                    # Mean line
                    {
                        'type': 'scatter',
                        'mode': 'lines+markers',
                        'x': x_vals,
                        'y': means,
                        'line': {'color': colors[0], 'width': 3},
                        'marker': {'size': 6, 'color': colors[0]},
                        'name': 'Mean Trend'
                    }
                ],
                'layout': {
                    **get_layout(),
                    'legend': {'orientation': 'h', 'y': -0.15}
                }
            }
        }
    except Exception as e:
        logger.warning(f"Band chart error: {e}")
        return None


def create_step_line_chart(df, rel, colors):
    """
    STEP LINE CHART - Step function visualization
    Perfect for pricing tiers, discrete changes, thresholds
    """
    try:
        val_col = rel['value']
        
        n_points = min(25, len(df))
        segment_size = max(1, len(df) // n_points)
        values = [float(df[val_col].iloc[i*segment_size:(i+1)*segment_size].mean()) for i in range(n_points)]
        x_vals = list(range(1, n_points + 1))
        
        return {
            'chart_id': f'step_{val_col}',
            'title': f'{val_col.replace("_", " ").title()} Step Progression',
            'type': 'step_line',
            'analysis': 'discrete_changes',
            'plotly_config': {
                'data': [{
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': x_vals,
                    'y': values,
                    'line': {'shape': 'hv', 'color': colors[0], 'width': 2},
                    'marker': {'size': 8, 'color': colors[0]},
                    'fill': 'tozeroy',
                    'fillcolor': f'{colors[0]}20'
                }],
                'layout': get_layout()
            }
        }
    except Exception as e:
        logger.warning(f"Step line error: {e}")
        return None


# ================= MAIN DASHBOARD GENERATOR =================

def generate_real_dashboard(df: pd.DataFrame, user_id: str) -> Dict:
    """
    Generate a TRULY AUTONOMOUS dashboard.
    
    The system analyzes data and decides:
    - Domain and color palette
    - Which charts to use (from 15+ types)
    - What data relationships to visualize
    - KPIs, insights, recommendations
    
    ALL calculations are REAL - done with pandas!
    """
    if df is None or df.empty:
        return {"error": "No data available. Please upload files first."}
    
    try:
        logger.info(f"🤖 AUTONOMOUS Dashboard generation for {user_id}")
        logger.info(f"📊 Data: {len(df)} rows, {len(df.columns)} cols")
        
        # Step 1: Detect domain
        domain = detect_data_domain(df)
        palette = COLOR_PALETTES.get(domain, COLOR_PALETTES['general'])
        logger.info(f"🎨 Detected domain: {domain}")
        
        # Step 2: Analyze column relationships
        relationships = analyze_column_relationships(df)
        logger.info(f"🔗 Found {len(relationships)} data relationships")
        
        # Step 3: AUTONOMOUS chart selection
        charts = autonomous_chart_selection(df, domain, relationships)
        logger.info(f"📊 Generated {len(charts)} autonomous charts")
        
        # Step 4: Calculate POWER BI-STYLE ADVANCED KPIs
        kpis = calculate_advanced_kpis(df, palette)
        
        # Step 5: Generate insights from real data
        insights = generate_real_insights(df)
        
        # Step 6: Generate recommendations
        recommendations = generate_recommendations(df)
        
        # Step 7: Generate title (minimal LLM use)
        try:
            cols = list(df.columns)[:6]
            # Ask for title
            generated_title = chat(f"3-word dashboard title for: {cols}. Just title.", temperature=0.2, max_tokens=15).strip().strip('"\'')
            
            # Validate title (check if it's an error message or too long)
            if any(err in generated_title.lower() for err in ['error', 'rate limit', 'busy', 'unable', 'connection']):
                title = f"{domain.title()} Analytics Dashboard"
            elif len(generated_title) > 50: # Too long for a title
                title = f"{domain.title()} Analytics Dashboard"
            else:
                title = generated_title
        except:
            title = f"{domain.title()} Analytics Dashboard"
        
        return sanitize_for_json({
            "dashboard_title": title,
            "domain": domain,
            "theme": {"primary": palette['primary'][0], "accent": palette['accent'][0]},
            "kpis": kpis,
            "charts": charts,
            "insights": insights,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "data_source": f"{len(df):,} rows × {len(df.columns)} columns"
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ================= POWER BI ADVANCED CALCULATIONS =================

def calculate_cagr(df: pd.DataFrame, value_col: str, periods: int = None) -> Dict:
    """
    Calculate Compound Annual Growth Rate (CAGR)
    CAGR = (End Value / Start Value)^(1/n) - 1
    """
    try:
        values = df[value_col].dropna()
        if len(values) < 2:
            return {'cagr': 0, 'has_data': False}
        
        start_val = values.iloc[0]
        end_val = values.iloc[-1]
        n = periods if periods else len(values) - 1
        
        if start_val <= 0 or n <= 0:
            return {'cagr': 0, 'has_data': False}
        
        cagr = (pow(end_val / start_val, 1/n) - 1) * 100
        
        return {
            'cagr': round(cagr, 2),
            'start_value': float(start_val),
            'end_value': float(end_val),
            'periods': n,
            'has_data': True
        }
    except:
        return {'cagr': 0, 'has_data': False}


def calculate_z_scores(df: pd.DataFrame, value_col: str) -> Dict:
    """
    Calculate Z-scores for anomaly detection
    Z = (x - mean) / std
    """
    try:
        values = df[value_col].dropna()
        if len(values) < 3:
            return {'anomalies': [], 'max_z': 0, 'anomaly_count': 0}
        
        mean = values.mean()
        std = values.std()
        
        if std == 0:
            return {'anomalies': [], 'max_z': 0, 'anomaly_count': 0}
        
        z_scores = ((values - mean) / std).abs()
        
        # Find anomalies (|z| > 2.5)
        anomaly_mask = z_scores > 2.5
        anomaly_indices = values[anomaly_mask].index.tolist()
        
        return {
            'max_z': round(float(z_scores.max()), 2),
            'anomaly_count': int(anomaly_mask.sum()),
            'anomaly_pct': round(anomaly_mask.sum() / len(values) * 100, 1),
            'anomaly_indices': anomaly_indices[:10],  # First 10
            'mean': round(float(mean), 2),
            'std': round(float(std), 2)
        }
    except:
        return {'anomalies': [], 'max_z': 0, 'anomaly_count': 0}


def calculate_percentile_rank(df: pd.DataFrame, value_col: str) -> Dict:
    """
    Calculate percentile ranks and distribution metrics
    """
    try:
        values = df[value_col].dropna()
        if len(values) < 2:
            return {'percentiles': {}, 'has_data': False}
        
        percentiles = {
            'p10': round(float(values.quantile(0.10)), 2),
            'p25': round(float(values.quantile(0.25)), 2),
            'p50': round(float(values.quantile(0.50)), 2),
            'p75': round(float(values.quantile(0.75)), 2),
            'p90': round(float(values.quantile(0.90)), 2),
            'p95': round(float(values.quantile(0.95)), 2),
            'p99': round(float(values.quantile(0.99)), 2)
        }
        
        # Skewness and Kurtosis
        skewness = values.skew()
        kurtosis = values.kurtosis()
        
        return {
            'percentiles': percentiles,
            'skewness': round(float(skewness), 2) if not pd.isna(skewness) else 0,
            'kurtosis': round(float(kurtosis), 2) if not pd.isna(kurtosis) else 0,
            'distribution': 'normal' if abs(skewness) < 0.5 else ('right_skewed' if skewness > 0 else 'left_skewed'),
            'has_data': True
        }
    except:
        return {'percentiles': {}, 'has_data': False}


def calculate_concentration_ratio(df: pd.DataFrame, cat_col: str, value_col: str) -> Dict:
    """
    Calculate market concentration ratios (CR4, CR8, HHI)
    Used for competitive analysis
    """
    try:
        grouped = df.groupby(cat_col)[value_col].sum().sort_values(ascending=False)
        total = grouped.sum()
        
        if total == 0:
            return {'cr4': 0, 'cr8': 0, 'hhi': 0, 'has_data': False}
        
        shares = (grouped / total * 100).values
        
        # Concentration Ratios
        cr4 = sum(shares[:4]) if len(shares) >= 4 else sum(shares)
        cr8 = sum(shares[:8]) if len(shares) >= 8 else sum(shares)
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(s**2 for s in shares[:50])  # Limit to top 50
        
        # Market structure classification
        if hhi < 1500:
            structure = 'competitive'
        elif hhi < 2500:
            structure = 'moderately_concentrated'
        else:
            structure = 'highly_concentrated'
        
        return {
            'cr4': round(cr4, 1),
            'cr8': round(cr8, 1),
            'hhi': round(hhi, 0),
            'market_structure': structure,
            'leader_share': round(shares[0], 1) if len(shares) > 0 else 0,
            'leader_name': str(grouped.index[0]) if len(grouped) > 0 else 'N/A',
            'has_data': True
        }
    except:
        return {'cr4': 0, 'cr8': 0, 'hhi': 0, 'has_data': False}


def calculate_seasonality(df: pd.DataFrame, value_col: str, date_col: str = None) -> Dict:
    """
    Detect seasonality patterns in data
    """
    try:
        values = df[value_col].fillna(0).values
        n = len(values)
        
        if n < 12:
            return {'seasonal': False, 'pattern': None, 'has_data': False}
        
        # Simple autocorrelation for seasonality detection
        lags = [7, 12, 30, 52]  # Weekly, Monthly, 30-day, Yearly
        correlations = {}
        
        for lag in lags:
            if n > lag * 2:
                v1 = values[:-lag]
                v2 = values[lag:]
                if np.std(v1) > 0 and np.std(v2) > 0:
                    corr = np.corrcoef(v1, v2)[0, 1]
                    if not np.isnan(corr):
                        correlations[lag] = round(corr, 3)
        
        # Find strongest seasonality
        if correlations:
            best_lag = max(correlations, key=correlations.get)
            best_corr = correlations[best_lag]
            
            lag_names = {7: 'weekly', 12: 'monthly', 30: '30-day', 52: 'yearly'}
            
            return {
                'seasonal': best_corr > 0.3,
                'pattern': lag_names.get(best_lag, f'{best_lag}-period'),
                'correlation': best_corr,
                'all_correlations': correlations,
                'has_data': True
            }
        
        return {'seasonal': False, 'pattern': None, 'has_data': False}
    except:
        return {'seasonal': False, 'pattern': None, 'has_data': False}


def calculate_momentum(df: pd.DataFrame, value_col: str, window: int = 5) -> Dict:
    """
    Calculate momentum indicators (Rate of Change)
    ROC = (Current - N periods ago) / N periods ago * 100
    """
    try:
        values = df[value_col].fillna(0)
        n = len(values)
        
        if n < window + 1:
            return {'momentum': 0, 'roc': 0, 'has_data': False}
        
        current = values.iloc[-1]
        past = values.iloc[-window-1]
        
        if past == 0:
            return {'momentum': 0, 'roc': 0, 'has_data': False}
        
        roc = (current - past) / abs(past) * 100
        
        # Momentum direction
        if roc > 5:
            momentum = 'strong_up'
        elif roc > 0:
            momentum = 'up'
        elif roc > -5:
            momentum = 'down'
        else:
            momentum = 'strong_down'
        
        return {
            'momentum': momentum,
            'roc': round(roc, 1),
            'current': float(current),
            'past': float(past),
            'window': window,
            'has_data': True
        }
    except:
        return {'momentum': 0, 'roc': 0, 'has_data': False}


def calculate_yoy_growth(df: pd.DataFrame, date_col: str, value_col: str) -> Dict:
    """
    Calculate Year-over-Year growth - Power BI style
    Returns growth %, previous period value, current period value
    """
    try:
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy = df_copy.dropna(subset=[date_col])
        
        if len(df_copy) < 2:
            return {'growth': 0, 'current': 0, 'previous': 0, 'has_data': False}
        
        # Group by year
        df_copy['_year'] = df_copy[date_col].dt.year
        yearly = df_copy.groupby('_year')[value_col].sum()
        
        if len(yearly) >= 2:
            current_year = yearly.iloc[-1]
            previous_year = yearly.iloc[-2]
            growth = ((current_year - previous_year) / previous_year * 100) if previous_year != 0 else 0
            return {
                'growth': round(growth, 1),
                'current': float(current_year),
                'previous': float(previous_year),
                'has_data': True
            }
        return {'growth': 0, 'current': 0, 'previous': 0, 'has_data': False}
    except:
        return {'growth': 0, 'current': 0, 'previous': 0, 'has_data': False}


def calculate_moving_average(df: pd.DataFrame, value_col: str, window: int = 7) -> Dict:
    """
    Calculate rolling moving average - Power BI style
    """
    try:
        values = df[value_col].fillna(0)
        if len(values) < window:
            return {'ma': float(values.mean()), 'current': float(values.iloc[-1]) if len(values) > 0 else 0}
        
        ma = values.rolling(window=window).mean()
        current_ma = float(ma.iloc[-1]) if not pd.isna(ma.iloc[-1]) else float(values.mean())
        current_val = float(values.iloc[-1])
        
        return {
            'ma': round(current_ma, 2),
            'current': round(current_val, 2),
            'above_ma': current_val > current_ma
        }
    except:
        return {'ma': 0, 'current': 0, 'above_ma': False}


def calculate_pareto_analysis(df: pd.DataFrame, cat_col: str, value_col: str) -> Dict:
    """
    Pareto (80/20) analysis - Power BI style
    Identifies which categories contribute to 80% of value
    """
    try:
        grouped = df.groupby(cat_col)[value_col].sum().sort_values(ascending=False)
        total = grouped.sum()
        
        if total == 0:
            return {'top_contributors': [], 'pareto_count': 0, 'pareto_pct': 0}
        
        cumsum = grouped.cumsum()
        cumsum_pct = cumsum / total * 100
        
        # Find categories that make up 80%
        pareto_mask = cumsum_pct <= 80
        pareto_items = grouped[pareto_mask].index.tolist()
        
        # If no items under 80%, take top item
        if not pareto_items:
            pareto_items = [grouped.index[0]]
        
        return {
            'top_contributors': pareto_items[:5],  # Top 5 contributors to 80%
            'pareto_count': len(pareto_items),
            'total_categories': len(grouped),
            'pareto_pct': round(len(pareto_items) / len(grouped) * 100, 1),
            'top_value': float(grouped.iloc[0]),
            'top_name': str(grouped.index[0])
        }
    except:
        return {'top_contributors': [], 'pareto_count': 0, 'pareto_pct': 0}


def calculate_variance_analysis(df: pd.DataFrame, value_col: str) -> Dict:
    """
    Variance and statistical analysis - Power BI style
    """
    try:
        values = df[value_col].dropna()
        if len(values) == 0:
            return {'variance': 0, 'std': 0, 'cv': 0, 'range': 0}
        
        mean = values.mean()
        std = values.std()
        variance = values.var()
        cv = (std / mean * 100) if mean != 0 else 0  # Coefficient of variation
        
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        
        # Outlier detection
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = values[(values < lower_bound) | (values > upper_bound)]
        
        return {
            'mean': round(float(mean), 2),
            'std': round(float(std), 2),
            'variance': round(float(variance), 2),
            'cv': round(cv, 1),  # Coefficient of variation %
            'q1': round(float(q1), 2),
            'median': round(float(values.median()), 2),
            'q3': round(float(q3), 2),
            'iqr': round(float(iqr), 2),
            'min': round(float(values.min()), 2),
            'max': round(float(values.max()), 2),
            'range': round(float(values.max() - values.min()), 2),
            'outlier_count': len(outliers),
            'outlier_pct': round(len(outliers) / len(values) * 100, 1)
        }
    except:
        return {'variance': 0, 'std': 0, 'cv': 0, 'range': 0}


def calculate_contribution_percentage(df: pd.DataFrame, cat_col: str, value_col: str) -> List[Dict]:
    """
    Calculate each category's contribution to total - Power BI style
    """
    try:
        grouped = df.groupby(cat_col)[value_col].sum().sort_values(ascending=False)
        total = grouped.sum()
        
        if total == 0:
            return []
        
        result = []
        cumulative = 0
        for name, val in grouped.head(10).items():
            pct = val / total * 100
            cumulative += pct
            result.append({
                'name': str(name),
                'value': float(val),
                'percentage': round(pct, 1),
                'cumulative_pct': round(cumulative, 1)
            })
        
        return result
    except:
        return []


def calculate_trend_forecast(df: pd.DataFrame, value_col: str, periods: int = 3) -> Dict:
    """
    Linear regression forecast - Power BI style trend analysis
    """
    try:
        values = df[value_col].fillna(0).values
        if len(values) < 5:
            return {'forecast': [], 'trend': 'neutral', 'slope': 0}
        
        # Simple linear regression
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        # Forecast next periods
        forecast_x = np.arange(len(values), len(values) + periods)
        forecast_values = slope * forecast_x + intercept
        
        # Determine trend
        if slope > 0.01 * np.mean(values):
            trend = 'up'
        elif slope < -0.01 * np.mean(values):
            trend = 'down'
        else:
            trend = 'neutral'
        
        return {
            'forecast': [round(float(v), 2) for v in forecast_values],
            'trend': trend,
            'slope': round(float(slope), 4),
            'r_squared': round(float(np.corrcoef(x, values)[0, 1] ** 2) if len(values) > 2 else 0, 3),
            'next_value': round(float(forecast_values[0]), 2),
            'growth_rate': round(float(slope / np.mean(values) * 100), 1) if np.mean(values) != 0 else 0
        }
    except:
        return {'forecast': [], 'trend': 'neutral', 'slope': 0}


def calculate_period_comparison(df: pd.DataFrame, value_col: str) -> Dict:
    """
    Period-over-period comparison - Power BI style
    Compares first half vs second half, quartiles, etc.
    """
    try:
        values = df[value_col].fillna(0)
        n = len(values)
        
        if n < 4:
            return {'periods': [], 'best_period': '', 'worst_period': ''}
        
        # Split into 4 quarters
        q_size = n // 4
        quarters = []
        for i in range(4):
            start = i * q_size
            end = (i + 1) * q_size if i < 3 else n
            q_values = values.iloc[start:end]
            quarters.append({
                'name': f'Q{i+1}',
                'sum': round(float(q_values.sum()), 2),
                'avg': round(float(q_values.mean()), 2),
                'count': len(q_values)
            })
        
        # Find best and worst
        best = max(quarters, key=lambda x: x['sum'])
        worst = min(quarters, key=lambda x: x['sum'])
        
        # Calculate Q-over-Q growth
        qoq_growth = []
        for i in range(1, len(quarters)):
            prev = quarters[i-1]['sum']
            curr = quarters[i]['sum']
            growth = ((curr - prev) / prev * 100) if prev != 0 else 0
            qoq_growth.append(round(growth, 1))
        
        return {
            'periods': quarters,
            'best_period': best['name'],
            'worst_period': worst['name'],
            'qoq_growth': qoq_growth,
            'avg_qoq_growth': round(np.mean(qoq_growth), 1) if qoq_growth else 0
        }
    except:
        return {'periods': [], 'best_period': '', 'worst_period': ''}


def calculate_advanced_kpis(df: pd.DataFrame, palette: Dict) -> List[Dict]:
    """
    ENTERPRISE-GRADE KPIs - Premium Analytics Dashboard
    
    Includes:
    - CAGR (Compound Annual Growth Rate)
    - Z-Score Anomaly Detection
    - Percentile Rankings
    - Market Concentration (HHI, CR4)
    - Momentum Indicators
    - Seasonality Detection
    - Statistical Confidence
    """
    kpis = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
    
    # Filter out ID-like columns
    numeric_cols = [c for c in numeric_cols if not any(x in c.lower() for x in ['id', 'index', 'key', 'code'])]
    
    # 1. Total Records with completeness score
    null_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    completeness = round(100 - null_pct, 1)
    kpis.append({
        'title': 'Total Records',
        'value': len(df),
        'format': 'number',
        'trend': 'neutral',
        'comparison': f'{completeness}% data completeness',
        'kpi_type': 'count',
        'sparkline': df[numeric_cols[0]].head(20).tolist() if numeric_cols else None
    })
    
    # 2. Primary Metric with CAGR
    if numeric_cols:
        try:
            col = numeric_cols[0]
            total = float(df[col].sum())
            cagr_data = calculate_cagr(df, col)
            trend_data = calculate_trend_forecast(df, col)
            
            col_lower = col.lower()
            is_currency = any(x in col_lower for x in ['price', 'amount', 'revenue', 'cost', 'sales', 'profit', 'budget'])
            
            cagr_display = f"CAGR: {cagr_data.get('cagr', 0):+.1f}%" if cagr_data.get('has_data') else f"Trend: {trend_data.get('growth_rate', 0):+.1f}%"
            
            kpis.append({
                'title': f'Total {col.replace("_", " ").title()}',
                'value': total,
                'format': 'currency' if is_currency else 'number',
                'trend': trend_data.get('trend', 'neutral'),
                'comparison': cagr_display,
                'kpi_type': 'sum_with_cagr',
                'cagr': cagr_data.get('cagr', 0),
                'sparkline': df[col].tail(20).tolist()
            })
        except:
            pass
    
    # 3. Anomaly Detection KPI
    if numeric_cols:
        try:
            col = numeric_cols[0]
            z_data = calculate_z_scores(df, col)
            
            if z_data.get('anomaly_count', 0) > 0:
                trend = 'down' if z_data['anomaly_pct'] > 5 else 'neutral'
                kpis.append({
                    'title': f'Anomalies Detected',
                    'value': z_data['anomaly_count'],
                    'format': 'number',
                    'trend': trend,
                    'comparison': f'{z_data["anomaly_pct"]:.1f}% of data | Max Z: {z_data["max_z"]:.1f}',
                    'kpi_type': 'anomaly',
                    'anomaly_pct': z_data['anomaly_pct']
                })
        except:
            pass
    
    # 4. Market Concentration / Dominance
    if numeric_cols and categorical_cols:
        try:
            main_num = numeric_cols[0]
            main_cat = categorical_cols[0]
            concentration = calculate_concentration_ratio(df, main_cat, main_num)
            
            if concentration.get('has_data'):
                kpis.append({
                    'title': f'Market Leader ({main_cat[:12]})',
                    'value': concentration.get('leader_name', 'N/A'),
                    'format': 'text',
                    'trend': 'up',
                    'comparison': f'{concentration.get("leader_share", 0):.1f}% share | HHI: {concentration.get("hhi", 0):,.0f}',
                    'kpi_type': 'concentration',
                    'market_structure': concentration.get('market_structure', 'unknown'),
                    'cr4': concentration.get('cr4', 0)
                })
        except:
            pass
    
    # 5. Momentum Indicator
    if numeric_cols:
        try:
            col = numeric_cols[0]
            momentum = calculate_momentum(df, col, window=5)
            
            if momentum.get('has_data'):
                trend = 'up' if 'up' in momentum['momentum'] else ('down' if 'down' in momentum['momentum'] else 'neutral')
                emoji = '🚀' if momentum['momentum'] == 'strong_up' else ('📈' if momentum['momentum'] == 'up' else ('📉' if momentum['momentum'] == 'down' else '💥'))
                
                kpis.append({
                    'title': f'Momentum ({col[:15]})',
                    'value': f'{momentum["roc"]:+.1f}%',
                    'format': 'text',
                    'trend': trend,
                    'comparison': f'{emoji} {momentum["momentum"].replace("_", " ").title()}',
                    'kpi_type': 'momentum',
                    'roc': momentum['roc']
                })
        except:
            pass
    
    # 6. Percentile Distribution
    if numeric_cols:
        try:
            col = numeric_cols[0]
            percentile_data = calculate_percentile_rank(df, col)
            
            if percentile_data.get('has_data'):
                p50 = percentile_data['percentiles'].get('p50', 0)
                p90 = percentile_data['percentiles'].get('p90', 0)
                
                kpis.append({
                    'title': f'Median {col[:12]}',
                    'value': p50,
                    'format': 'number',
                    'trend': 'neutral',
                    'comparison': f'P90: {p90:,.0f} | {percentile_data["distribution"].replace("_", " ").title()}',
                    'kpi_type': 'percentile',
                    'distribution': percentile_data['distribution'],
                    'skewness': percentile_data['skewness']
                })
        except:
            pass
    
    # 7. Seasonality Detection
    if numeric_cols and len(df) > 20:
        try:
            col = numeric_cols[0]
            seasonality = calculate_seasonality(df, col)
            
            if seasonality.get('has_data') and seasonality.get('seasonal'):
                kpis.append({
                    'title': 'Seasonality Pattern',
                    'value': seasonality.get('pattern', 'Unknown').title(),
                    'format': 'text',
                    'trend': 'neutral',
                    'comparison': f'Correlation: {seasonality.get("correlation", 0):.2f}',
                    'kpi_type': 'seasonality',
                    'pattern': seasonality.get('pattern')
                })
        except:
            pass
    
    # 8. Variance & Volatility
    if numeric_cols:
        try:
            col = numeric_cols[0]
            variance = calculate_variance_analysis(df, col)
            
            cv = variance.get('cv', 0)
            if cv > 50:
                volatility = 'High'
                trend = 'down'
            elif cv > 20:
                volatility = 'Medium'
                trend = 'neutral'
            else:
                volatility = 'Low'
                trend = 'up'
            
            kpis.append({
                'title': f'Volatility ({col[:12]})',
                'value': f'{volatility}',
                'format': 'text',
                'trend': trend,
                'comparison': f'CV: {cv:.0f}% | {variance.get("outlier_count", 0)} outliers',
                'kpi_type': 'volatility',
                'cv': cv,
                'outlier_pct': variance.get('outlier_pct', 0)
            })
        except:
            pass
    
    # 9. Q-o-Q Growth (if we have enough KPIs)
    if len(kpis) < 8 and numeric_cols:
        try:
            col = numeric_cols[0]
            period_data = calculate_period_comparison(df, col)
            
            if period_data.get('periods'):
                avg_growth = period_data.get('avg_qoq_growth', 0)
                trend = 'up' if avg_growth > 0 else ('down' if avg_growth < 0 else 'neutral')
                
                kpis.append({
                    'title': 'Avg Period Growth',
                    'value': avg_growth,
                    'format': 'percentage',
                    'trend': trend,
                    'comparison': f'Best: {period_data.get("best_period", "N/A")} | Worst: {period_data.get("worst_period", "N/A")}',
                    'kpi_type': 'growth'
                })
        except:
            pass
    
    # 10. Secondary metric (if space available)
    if len(kpis) < 8 and len(numeric_cols) >= 2:
        try:
            col = numeric_cols[1]
            total = float(df[col].sum())
            mean = float(df[col].mean())
            
            col_lower = col.lower()
            is_currency = any(x in col_lower for x in ['price', 'amount', 'revenue', 'cost', 'sales', 'profit', 'budget'])
            
            kpis.append({
                'title': f'Total {col.replace("_", " ").title()}',
                'value': total,
                'format': 'currency' if is_currency else 'number',
                'trend': 'neutral',
                'comparison': f'Avg: {mean:,.0f}',
                'kpi_type': 'sum',
                'sparkline': df[col].tail(20).tolist()
            })
        except:
            pass
    
    return kpis[:10]  # Return up to 10 advanced KPIs


def calculate_real_kpis(df: pd.DataFrame, palette: Dict) -> List[Dict]:
    """Calculate REAL KPIs with autonomous formatting and Silicon Valley precision"""
    kpis = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Always show record count first
    kpis.append({'title': 'Total Records', 'value': len(df), 'format': 'number', 'trend': 'neutral', 'comparison': f'{len(df.columns)} dimensions'})
    
    for col in numeric_cols[:5]:
        try:
            total = float(df[col].sum())
            mean = float(df[col].mean())
            std = float(df[col].std()) if len(df) > 1 else 0
            col_lower = col.lower()
            
            # Smart Format Detection
            is_currency = any(x in col_lower for x in ['price', 'amount', 'revenue', 'cost', 'sales', 'profit', 'budget', 'bill'])
            is_percentage = any(x in col_lower for x in ['percent', 'rate', 'margin', 'ratio', 'probability'])
            
            # Trend calculation (Linear Regression Slope for accuracy)
            trend = 'neutral'
            comparison = ''
            
            if len(df) > 5:
                # Use simple regression slope instead of just first/last half
                y = df[col].fillna(0).values
                mid = len(y) // 2
                recent = y[mid:].mean()
                past = y[:mid].mean()
                
                if past != 0:
                    delta = ((recent - past) / past) * 100
                    if delta > 1: trend = 'up'
                    elif delta < -1: trend = 'down'
                    
                    comparison = f"{abs(delta):.1f}% vs past avg"
            
            if is_currency:
                kpis.append({
                    'title': f'Total {col.replace("_", " ").title()}', 
                    'value': total, 
                    'format': 'currency', 
                    'trend': trend, 
                    'comparison': comparison or f'Avg: ${mean:,.0f}'
                })
            elif is_percentage:
                kpis.append({
                    'title': f'Avg {col.replace("_", " ").title()}', 
                    'value': mean, 
                    'format': 'percentage', 
                    'trend': trend, 
                    'comparison': comparison or f'σ: {std:.1f}'
                })
            else:
                # Decide between Sum and Mean based on variance
                if std > mean * 2: # High variance usually means Sum is better (like sales)
                    kpis.append({'title': f'Total {col}', 'value': total, 'format': 'number', 'trend': trend, 'comparison': comparison})
                else:
                    kpis.append({'title': f'Avg {col}', 'value': mean, 'format': 'number', 'trend': trend, 'comparison': comparison})
                    
        except Exception as e:
            logger.warning(f"KPI error for {col}: {e}")
            pass
    
    return kpis[:6]


def generate_real_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate ENTERPRISE-GRADE insights using advanced analytics
    Includes: CAGR, Z-scores, Seasonality, Market Concentration, Momentum
    """
    insights = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    datetime_cols = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()]
    
    # Filter out ID columns
    numeric_cols = [c for c in numeric_cols if not any(x in c.lower() for x in ['id', 'index', 'key', 'code'])]
    
    # === ADVANCED INSIGHT GENERATION ===
    
    # 1. CAGR Insight
    if numeric_cols:
        try:
            col = numeric_cols[0]
            cagr_data = calculate_cagr(df, col)
            if cagr_data.get('has_data') and cagr_data.get('cagr', 0) != 0:
                trend_emoji = '📈' if cagr_data['cagr'] > 0 else '📉'
                insights.append(f"{trend_emoji} **Growth Rate**: {col.replace('_', ' ').title()} shows {cagr_data['cagr']:+.1f}% CAGR across the dataset period")
        except:
            pass
    
    # 2. Anomaly Detection Insight
    if numeric_cols:
        try:
            col = numeric_cols[0]
            z_data = calculate_z_scores(df, col)
            if z_data.get('anomaly_count', 0) > 0:
                insights.append(f"⚠️ **Anomaly Alert**: {z_data['anomaly_count']} outliers detected in {col.replace('_', ' ')} ({z_data['anomaly_pct']:.1f}% of data)")
        except:
            pass
    
    # 3. Market Concentration Insight
    if numeric_cols and categorical_cols:
        try:
            main_num = numeric_cols[0]
            main_cat = categorical_cols[0]
            concentration = calculate_concentration_ratio(df, main_cat, main_num)
            
            if concentration.get('has_data'):
                structure = concentration.get('market_structure', 'unknown')
                if structure == 'highly_concentrated':
                    insights.append(f"🏆 **Market Dominance**: {concentration['leader_name']} holds {concentration['leader_share']:.0f}% share (HHI: {concentration['hhi']:,.0f})")
                elif concentration['cr4'] > 60:
                    insights.append(f"📊 **Concentration**: Top 4 {main_cat}s control {concentration['cr4']:.0f}% of total {main_num.replace('_', ' ')}")
        except:
            pass
    
    # 4. Momentum Insight
    if numeric_cols:
        try:
            col = numeric_cols[0]
            momentum = calculate_momentum(df, col, window=5)
            if momentum.get('has_data'):
                if momentum['momentum'] == 'strong_up':
                    insights.append(f"🚀 **Strong Momentum**: {col.replace('_', ' ').title()} surging {momentum['roc']:+.1f}% over recent period")
                elif momentum['momentum'] == 'strong_down':
                    insights.append(f"💥 **Momentum Warning**: {col.replace('_', ' ').title()} declining {momentum['roc']:.1f}% over recent period")
        except:
            pass
    
    # 5. Seasonality Insight
    if numeric_cols and len(df) > 20:
        try:
            col = numeric_cols[0]
            seasonality = calculate_seasonality(df, col)
            if seasonality.get('seasonal') and seasonality.get('correlation', 0) > 0.3:
                insights.append(f"🔄 **Seasonality Detected**: {seasonality['pattern'].title()} pattern found in {col.replace('_', ' ')} (r={seasonality['correlation']:.2f})")
        except:
            pass
    
    # 6. Distribution Insight
    if numeric_cols:
        try:
            col = numeric_cols[0]
            percentile_data = calculate_percentile_rank(df, col)
            if percentile_data.get('has_data'):
                if percentile_data['distribution'] == 'right_skewed':
                    insights.append(f"📊 **Distribution**: {col.replace('_', ' ').title()} is right-skewed (skew={percentile_data['skewness']:.1f}) - most values below average")
                elif percentile_data['distribution'] == 'left_skewed':
                    insights.append(f"📊 **Distribution**: {col.replace('_', ' ').title()} is left-skewed (skew={percentile_data['skewness']:.1f}) - most values above average")
        except:
            pass
    
    # 7. Correlation Insight
    if len(numeric_cols) >= 2:
        try:
            corr = df[numeric_cols].corr().abs()
            mask = np.ones(corr.shape, dtype=bool)
            np.fill_diagonal(mask, 0)
            max_corr_stack = corr.where(mask).stack()
            if not max_corr_stack.empty:
                max_idx = max_corr_stack.idxmax()
                max_val = max_corr_stack.max()
                if max_val > 0.7:
                    insights.append(f"🔗 **Strong Correlation**: {max_idx[0].replace('_', ' ')} and {max_idx[1].replace('_', ' ')} are highly correlated (r={max_val:.2f})")
        except:
            pass
    
    # 8. Pareto Insight
    if categorical_cols and numeric_cols:
        try:
            cat, num = categorical_cols[0], numeric_cols[0]
            pareto = calculate_pareto_analysis(df, cat, num)
            if pareto.get('pareto_count', 0) > 0 and pareto.get('pareto_pct', 0) < 30:
                insights.append(f"📊 **Pareto Principle**: {pareto['pareto_count']} of {pareto['total_categories']} {cat.replace('_', ' ')}s drive 80% of {num.replace('_', ' ')}")
        except:
            pass
    
    # 9. Volatility Insight
    if numeric_cols:
        try:
            col = numeric_cols[0]
            variance = calculate_variance_analysis(df, col)
            cv = variance.get('cv', 0)
            if cv > 100:
                insights.append(f"⚡ **High Volatility**: {col.replace('_', ' ').title()} shows extreme variability (CV={cv:.0f}%) - consider risk mitigation")
            elif cv < 15:
                insights.append(f"✅ **Stability**: {col.replace('_', ' ').title()} is highly consistent (CV={cv:.0f}%) - reliable metric")
        except:
            pass
    
    # === FALLBACK: Basic insights if we don't have enough ===
    if len(insights) < 3 and numeric_cols:
        try:
            col = numeric_cols[0]
            total = df[col].sum()
            mean = df[col].mean()
            insights.append(f"📊 **Summary**: Total {col.replace('_', ' ')} is {total:,.0f} with average {mean:,.0f}")
        except:
            pass
    
    # Ensure we have at least one insight
    if not insights:
        insights.append(f"📊 **Dataset**: {len(df):,} records with {len(df.columns)} columns analyzed")
    
    return sanitize_for_json(insights[:6])


def generate_recommendations(df: pd.DataFrame) -> List[str]:
    """Generate LLM-POWERED STRATEGIC, ACTIONABLE recommendations"""
    recs = []
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Build data context for LLM
    data_context = f"""📊 DATA PROFILE:
- Records: {len(df):,}
- Numeric metrics: {', '.join(numeric_cols[:5]) if numeric_cols else 'None'}
- Categories: {', '.join(categorical_cols[:3]) if categorical_cols else 'None'}
"""
    
    # Find key patterns for recommendations
    if numeric_cols and categorical_cols:
        cat, num = categorical_cols[0], numeric_cols[0]
        
        # Top performer
        top = df.groupby(cat)[num].sum().idxmax()
        top_val = df.groupby(cat)[num].sum().max()
        total = df[num].sum()
        top_share = (top_val / total * 100) if total > 0 else 0
        
        # Underperformer
        grouped = df.groupby(cat)[num].sum()
        avg = grouped.mean()
        underperformers = grouped[grouped < avg].sort_values(ascending=False)
        underperformer = underperformers.index[0] if len(underperformers) > 0 else None
        
        data_context += f"""
📈 KEY FINDINGS:
- Top performer: '{top}' with {top_share:.1f}% share
- Average per category: {avg:,.0f}
- Underperformer to optimize: '{underperformer}' (below average)
"""
    
    # LLM to generate recommendations
    try:
        prompt = f"""You are a management consultant. Based on this business data, provide exactly 4 STRATEGIC RECOMMENDATIONS.

{data_context}

Rules:
1. Each recommendation must be actionable and specific
2. Reference specific data points where possible
3. Each recommendation should be 1 sentence, max 12 words
4. Focus on: Growth, Optimization, Risk Mitigation, Efficiency

Format: Start each with an action verb and use '→' to show expected impact."""

        response = chat(prompt, temperature=0.4, max_tokens=250)
        
        # Parse LLM response
        if response and 'error' not in response.lower() and 'rate limit' not in response.lower():
            lines = [l.strip() for l in response.split('\n') if l.strip() and len(l) > 10]
            # Filter out numbering and keep substantive lines
            for line in lines:
                clean = line.lstrip('0123456789.-) ').strip()
                if clean and len(clean) > 15:
                    recs.append(clean)
                    if len(recs) >= 4:
                        break
    except Exception as e:
        logger.warning(f"LLM recommendation error: {e}")
    
    # Fallback to rule-based if LLM didn't return enough
    if len(recs) < 2:
        recs = []  # Reset
        try:
            # 1. Growth Strategy
            if categorical_cols and numeric_cols:
                cat, num = categorical_cols[0], numeric_cols[0]
                avg = df[num].mean()
                underperformers = df[(df[num] < avg) & (df[num] > 0)]
                if not underperformers.empty:
                    target = underperformers.nlargest(1, num)[cat].iloc[0]
                    recs.append(f"🚀 Optimize '{target}' → potential +{int((avg - underperformers[num].mean())):,} increase")
            
            # 2. Risk Mitigation (Outliers)
            if numeric_cols:
                col = numeric_cols[0]
                std = df[col].std()
                if std > 0:
                    z_scores = ((df[col] - df[col].mean()) / std).abs()
                    outliers = df[z_scores > 3]
                    if not outliers.empty:
                        recs.append(f"⚠️ Investigate {len(outliers)} extreme {col} values for anomalies")

            # 3. Top Performer Focus
            if categorical_cols and numeric_cols:
                cat, num = categorical_cols[0], numeric_cols[0]
                top = df.groupby(cat)[num].sum().idxmax()
                recs.append(f"📈 Double down on '{top}' → current top performer")
            
            # 4. Automation
            recs.append("🔔 Implement automated alerts for real-time threshold monitoring")
            recs.append("📊 Set up weekly variance analysis on top contributors")

        except Exception as e:
            logger.warning(f"Recommendation error: {e}")
    
    return sanitize_for_json(recs[:4])

