"""
Premium Charts - Financial & KPI Visualizations
=================================================

Advanced chart types not in the standard library:
- Gauge / Speedometer
- Sankey Flow Diagram
- Radar / Spider Chart  
- Bullet Chart
- Multi-KPI Indicator Row
- Candlestick
- Treemap/Sunburst (hierarchical)

All using FREE Plotly (open-source).
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json


class PremiumCharts:
    """
    Premium financial and KPI visualization charts.
    Uses FREE Plotly.
    """
    
    DEFAULT_COLORS = ["#f97316", "#3b82f6", "#22c55e", "#a855f7", "#ef4444",
                      "#06b6d4", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"]
    
    @staticmethod
    def gauge(
        value: float,
        title: str = "KPI",
        min_val: float = 0,
        max_val: float = 100,
        thresholds: Dict[str, float] = None
    ) -> Dict:
        """Create gauge/speedometer chart for KPIs"""
        
        if thresholds is None:
            thresholds = {"danger": 30, "warning": 70, "good": max_val}
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 24, 'color': '#ffffff'}},
            number={'font': {'size': 48, 'color': '#ffffff'}},
            gauge={
                'axis': {'range': [min_val, max_val], 'tickcolor': '#ffffff'},
                'bar': {'color': "#2196F3"},
                'bgcolor': "rgba(0,0,0,0.3)",
                'borderwidth': 2,
                'bordercolor': "rgba(255,255,255,0.3)",
                'steps': [
                    {'range': [min_val, thresholds.get("danger", 30)], 'color': "#EF5350"},
                    {'range': [thresholds.get("danger", 30), thresholds.get("warning", 70)], 'color': "#FFC107"},
                    {'range': [thresholds.get("warning", 70), max_val], 'color': "#26A69A"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font={'color': '#ffffff'},
            margin=dict(l=20, r=20, t=60, b=20),
            height=300
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def radar(
        categories: List[str],
        values: List[float],
        title: str = "Performance Radar",
        fill: bool = True
    ) -> Dict:
        """Create radar/spider chart for multi-dimensional comparison"""
        
        # Close the polygon
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself' if fill else 'none',
            fillcolor='rgba(33, 150, 243, 0.3)',
            line=dict(color='#2196F3', width=2),
            marker=dict(size=8, color='#2196F3')
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    color='#ffffff',
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                angularaxis=dict(
                    color='#ffffff',
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            title=dict(text=title, font=dict(color='#ffffff', size=16)),
            font=dict(color='#ffffff'),
            showlegend=False,
            margin=dict(l=60, r=60, t=60, b=60)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def sankey(
        sources: List[str],
        targets: List[str],
        values: List[float],
        title: str = "Flow Diagram"
    ) -> Dict:
        """Create Sankey diagram for flow analysis"""
        
        # Get unique labels
        all_labels = list(set(sources + targets))
        
        # Convert names to indices
        source_idx = [all_labels.index(s) for s in sources]
        target_idx = [all_labels.index(t) for t in targets]
        
        # Generate colors
        colors = PremiumCharts.DEFAULT_COLORS[:len(all_labels)]
        
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="rgba(255,255,255,0.3)", width=0.5),
                label=all_labels,
                color=colors
            ),
            link=dict(
                source=source_idx,
                target=target_idx,
                value=values,
                color='rgba(100,100,100,0.4)'
            )
        )])
        
        fig.update_layout(
            title=dict(text=title, font=dict(color='#ffffff', size=16)),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def bullet(
        value: float,
        target: float,
        title: str = "Progress",
        ranges: List[float] = None
    ) -> Dict:
        """Create bullet chart for goal tracking"""
        
        if ranges is None:
            ranges = [target * 0.5, target * 0.75, target * 1.2]
        
        fig = go.Figure(go.Indicator(
            mode="number+gauge",
            value=value,
            domain={'x': [0.1, 1], 'y': [0.3, 0.7]},
            title={'text': title, 'font': {'color': '#ffffff'}},
            number={'font': {'color': '#ffffff'}},
            gauge={
                'shape': "bullet",
                'axis': {'range': [0, max(ranges)], 'tickcolor': '#ffffff'},
                'bgcolor': 'rgba(0,0,0,0.3)',
                'threshold': {
                    'line': {'color': "#EF5350", 'width': 3},
                    'thickness': 0.9,
                    'value': target
                },
                'steps': [
                    {'range': [0, ranges[0]], 'color': "rgba(239, 83, 80, 0.4)"},
                    {'range': [ranges[0], ranges[1]], 'color': "rgba(255, 193, 7, 0.4)"},
                    {'range': [ranges[1], ranges[2]], 'color': "rgba(38, 166, 154, 0.4)"}
                ],
                'bar': {'color': "#2196F3", 'thickness': 0.6}
            }
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            height=200,
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def kpi_cards(kpis: List[Dict[str, Any]]) -> Dict:
        """
        Create a row of KPI indicator cards.
        
        Each KPI should have: value, title, optional delta, prefix, suffix
        """
        
        n = len(kpis)
        if n == 0:
            return {"error": "No KPIs provided"}
        
        fig = make_subplots(
            rows=1, cols=n,
            specs=[[{"type": "indicator"}] * n]
        )
        
        for i, kpi in enumerate(kpis):
            mode = "number+delta" if kpi.get("delta") else "number"
            
            indicator = go.Indicator(
                mode=mode,
                value=kpi.get("value", 0),
                number={
                    'prefix': kpi.get("prefix", ""),
                    'suffix': kpi.get("suffix", ""),
                    'font': {'size': 36, 'color': '#ffffff'}
                },
                title={
                    'text': kpi.get("title", ""),
                    'font': {'size': 14, 'color': '#9ca3af'}
                },
                delta={
                    'reference': kpi.get("value", 0) - kpi.get("delta", 0),
                    'relative': True,
                    'position': 'bottom'
                } if kpi.get("delta") else None
            )
            
            fig.add_trace(indicator, row=1, col=i+1)
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            height=180,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#ffffff')
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def treemap(
        df: pd.DataFrame,
        path: List[str],
        values_col: str,
        title: str = "Breakdown"
    ) -> Dict:
        """Create treemap for hierarchical data"""
        
        fig = px.treemap(
            df,
            path=path,
            values=values_col,
            title=title,
            color_discrete_sequence=PremiumCharts.DEFAULT_COLORS
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def sunburst(
        df: pd.DataFrame,
        path: List[str],
        values_col: str,
        title: str = "Composition"
    ) -> Dict:
        """Create sunburst chart for hierarchical composition"""
        
        fig = px.sunburst(
            df,
            path=path,
            values=values_col,
            title=title,
            color_discrete_sequence=PremiumCharts.DEFAULT_COLORS
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod
    def candlestick(
        df: pd.DataFrame,
        date_col: str,
        open_col: str,
        high_col: str,
        low_col: str,
        close_col: str,
        title: str = "Price Movement"
    ) -> Dict:
        """Create candlestick chart for financial data"""
        
        fig = go.Figure(data=[go.Candlestick(
            x=df[date_col],
            open=df[open_col],
            high=df[high_col],
            low=df[low_col],
            close=df[close_col],
            increasing_line_color='#26A69A',
            decreasing_line_color='#EF5350'
        )])
        
        fig.update_layout(
            title=dict(text=title, font=dict(color='#ffffff', size=16)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                color='#ffffff',
                rangeslider=dict(visible=False)
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.1)',
                color='#ffffff'
            ),
            font=dict(color='#ffffff'),
            margin=dict(l=50, r=20, t=50, b=50)
        )
        
        return json.loads(fig.to_json())
    
    @staticmethod  
    def heatmap(
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        value_col: str,
        title: str = "Heatmap"
    ) -> Dict:
        """Create heatmap for correlation / intensity visualization"""
        
        # Pivot for heatmap
        pivot_df = df.pivot_table(index=y_col, columns=x_col, values=value_col, aggfunc='sum')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns.tolist(),
            y=pivot_df.index.tolist(),
            colorscale='Viridis',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(color='#ffffff', size=16)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(color='#ffffff'),
            yaxis=dict(color='#ffffff'),
            font=dict(color='#ffffff'),
            margin=dict(l=80, r=20, t=50, b=80)
        )
        
        return json.loads(fig.to_json())


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_gauge(value: float, title: str, max_val: float = 100) -> Dict:
    """Quick gauge chart"""
    return PremiumCharts.gauge(value, title, max_val=max_val)


def create_radar(categories: List[str], values: List[float], title: str = "Radar") -> Dict:
    """Quick radar chart"""
    return PremiumCharts.radar(categories, values, title)


def create_kpi_row(kpis: List[Dict]) -> Dict:
    """Quick KPI row. Each kpi: {value, title, delta?, prefix?, suffix?}"""
    return PremiumCharts.kpi_cards(kpis)


def create_sankey(sources: List[str], targets: List[str], values: List[float]) -> Dict:
    """Quick sankey diagram"""
    return PremiumCharts.sankey(sources, targets, values)


# Test
if __name__ == "__main__":
    # Test Gauge
    gauge = PremiumCharts.gauge(75, "Customer Satisfaction", max_val=100)
    print("✅ Gauge chart created")
    
    # Test Radar
    radar = PremiumCharts.radar(
        ["Sales", "Marketing", "Product", "Support", "Engineering"],
        [80, 65, 90, 75, 85]
    )
    print("✅ Radar chart created")
    
    # Test KPI Cards
    kpis = PremiumCharts.kpi_cards([
        {"value": 1250000, "title": "Revenue", "prefix": "$", "delta": 125000},
        {"value": 1250, "title": "Customers", "delta": 150},
        {"value": 3.2, "title": "Churn %", "suffix": "%", "delta": -0.5}
    ])
    print("✅ KPI cards created")
    
    # Test Sankey
    sankey = PremiumCharts.sankey(
        ["Marketing", "Marketing", "Sales", "Sales"],
        ["Leads", "Website", "Closed", "Lost"],
        [40, 60, 70, 30]
    )
    print("✅ Sankey diagram created")
    
    print("\n✅ All premium charts working!")
