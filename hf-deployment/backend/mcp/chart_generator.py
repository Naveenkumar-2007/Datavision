# Chart Generator MCP Service
"""
Enterprise Chart Payload Generator

Generates frontend-compatible chart payloads for:
- Forecast line charts with confidence bands
- Scenario comparison bar charts
- Churn distribution charts
- Risk heatmaps
- Driver waterfall charts
- Multi-dataset overlay charts

Usage:
    from mcp.chart_generator import ChartGenerator
    generator = ChartGenerator()
    payload = generator.forecast_chart(prediction_result)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


@dataclass
class ChartPayload:
    """Base chart payload for frontend rendering"""
    chart_type: str
    title: str
    x: List[str]
    series: List[Dict[str, Any]]
    options: Dict[str, Any]
    

class ChartGenerator:
    """
    Enterprise Chart Payload Generator.
    
    Generates structured payloads compatible with:
    - Recharts (React)
    - Chart.js
    - Custom chart components
    """
    
    # Chart type constants
    FORECAST_LINE = 'forecast_line'
    SCENARIO_BAR = 'scenario_bar'
    CHURN_DIST = 'churn_distribution'
    RISK_HEATMAP = 'risk_heatmap'
    DRIVER_WATERFALL = 'driver_waterfall'
    COMPARISON_OVERLAY = 'comparison_overlay'
    PROFIT_LOSS = 'profit_loss_curve'
    
    def __init__(self):
        self.default_colors = {
            'primary': '#f97316',      # Orange
            'secondary': '#3b82f6',    # Blue
            'success': '#22c55e',      # Green
            'danger': '#ef4444',       # Red
            'warning': '#eab308',      # Yellow
            'muted': '#6b7280',        # Gray
            'confidence': 'rgba(249, 115, 22, 0.2)',  # Orange transparent
        }
        
    def forecast_chart(
        self,
        historical: List[Dict],
        forecast: List[Dict],
        title: str = "Forecast",
        currency: str = "₹",
        show_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Generate forecast line chart with confidence bands.
        
        Args:
            historical: List of {date, value} for historical data
            forecast: List of {date, value, lower, upper} for forecast
            title: Chart title
            currency: Currency symbol
            show_confidence: Whether to show confidence bands
            
        Returns:
            Chart payload for frontend
        """
        # Build x-axis labels
        x_labels = []
        for h in historical:
            date = h.get('date', '')
            if hasattr(date, 'strftime'):
                x_labels.append(date.strftime('%b %Y'))
            else:
                x_labels.append(str(date)[:10])
                
        for f in forecast:
            date = f.get('date', '')
            if hasattr(date, 'strftime'):
                x_labels.append(date.strftime('%b %Y'))
            else:
                x_labels.append(str(date)[:10])
        
        # Build series data
        n_historical = len(historical)
        n_total = n_historical + len(forecast)
        
        # Historical series (actual values)
        y_actual = [h.get('value') for h in historical] + [None] * len(forecast)
        
        # Forecast series (with connection to last historical point)
        y_forecast = [None] * (n_historical - 1)
        if historical:
            y_forecast.append(historical[-1].get('value'))  # Connect point
        y_forecast.extend([f.get('value') for f in forecast])
        
        # Confidence bands
        y_upper = [None] * n_historical
        y_lower = [None] * n_historical
        
        if show_confidence:
            for f in forecast:
                y_upper.append(f.get('upper', f.get('value') * 1.1))
                y_lower.append(f.get('lower', f.get('value') * 0.9))
        
        return {
            'chart_type': self.FORECAST_LINE,
            'title': title,
            'x': x_labels,
            'y_actual': y_actual,
            'y_forecast': y_forecast,
            'y_upper': y_upper if show_confidence else [],
            'y_lower': y_lower if show_confidence else [],
            'confidence_band': show_confidence,
            'currency': currency,
            'series': [
                {
                    'name': 'Historical',
                    'data': y_actual,
                    'type': 'line',
                    'color': self.default_colors['secondary'],
                    'strokeWidth': 3,
                    'dot': True
                },
                {
                    'name': 'Forecast',
                    'data': y_forecast,
                    'type': 'line',
                    'color': self.default_colors['primary'],
                    'strokeWidth': 3,
                    'strokeDasharray': '8 4',
                    'dot': True
                }
            ],
            'options': {
                'animationDuration': 1000,
                'showGrid': True,
                'showLegend': True,
                'yAxisFormatter': f'{currency}{{value}}',
                'tooltipFormatter': f'{currency}{{value:,.0f}}'
            }
        }
    
    def scenario_chart(
        self,
        scenarios: List[Dict],
        metric: str = 'profit',
        title: str = "Scenario Comparison",
        currency: str = "₹",
        best_scenario: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate scenario comparison bar chart.
        
        Args:
            scenarios: List of scenario dicts with name, revenue, profit, risk
            metric: Which metric to compare ('revenue', 'profit')
            title: Chart title
            currency: Currency symbol
            best_scenario: Name of recommended scenario
            
        Returns:
            Chart payload for frontend
        """
        x_labels = [s.get('name', f'Scenario {i+1}') for i, s in enumerate(scenarios)]
        values = [s.get(metric, 0) for s in scenarios]
        changes = [s.get('change_pct', 0) for s in scenarios]
        risks = [s.get('risk', 'medium') for s in scenarios]
        
        # Determine bar colors
        colors = []
        for i, s in enumerate(scenarios):
            name = s.get('name', '')
            if name == best_scenario:
                colors.append(self.default_colors['success'])
            elif name == 'Current State':
                colors.append(self.default_colors['secondary'])
            elif s.get('risk') == 'high':
                colors.append(self.default_colors['danger'])
            else:
                colors.append(self.default_colors['primary'])
        
        return {
            'chart_type': self.SCENARIO_BAR,
            'title': title,
            'x': x_labels,
            'values': values,
            'changes': changes,
            'risks': risks,
            'colors': colors,
            'best_scenario': best_scenario,
            'currency': currency,
            'series': [
                {
                    'name': metric.capitalize(),
                    'data': values,
                    'type': 'bar',
                    'colors': colors
                }
            ],
            'options': {
                'animationDuration': 800,
                'barRadius': 8,
                'showLabels': True,
                'labelPosition': 'top',
                'highlightBest': True
            }
        }
    
    def churn_chart(
        self,
        churn_data: List[Dict],
        title: str = "Churn Prediction"
    ) -> Dict[str, Any]:
        """
        Generate churn probability distribution chart.
        
        Args:
            churn_data: List of {segment, probability, count}
            title: Chart title
            
        Returns:
            Chart payload for frontend
        """
        segments = [d.get('segment', f'Segment {i+1}') for i, d in enumerate(churn_data)]
        probabilities = [d.get('probability', 0) for d in churn_data]
        counts = [d.get('count', 0) for d in churn_data]
        
        # Color by risk level
        colors = []
        for prob in probabilities:
            if prob > 0.3:
                colors.append(self.default_colors['danger'])
            elif prob > 0.15:
                colors.append(self.default_colors['warning'])
            else:
                colors.append(self.default_colors['success'])
        
        return {
            'chart_type': self.CHURN_DIST,
            'title': title,
            'x': segments,
            'probabilities': probabilities,
            'counts': counts,
            'colors': colors,
            'series': [
                {
                    'name': 'Churn Risk',
                    'data': [p * 100 for p in probabilities],  # Convert to percentage
                    'type': 'bar',
                    'colors': colors
                },
                {
                    'name': 'Customer Count',
                    'data': counts,
                    'type': 'line',
                    'color': self.default_colors['muted'],
                    'yAxisId': 'right'
                }
            ],
            'options': {
                'showDualAxis': True,
                'leftAxisLabel': 'Churn Risk (%)',
                'rightAxisLabel': 'Customer Count',
                'highlightHighRisk': True
            }
        }
    
    def profit_loss_chart(
        self,
        data: List[Dict],
        title: str = "Profit/Loss Analysis",
        currency: str = "₹"
    ) -> Dict[str, Any]:
        """
        Generate profit vs loss curve chart.
        
        Args:
            data: List of {period, revenue, cost, profit}
            title: Chart title
            currency: Currency symbol
            
        Returns:
            Chart payload for frontend
        """
        periods = [d.get('period', f'P{i+1}') for i, d in enumerate(data)]
        revenues = [d.get('revenue', 0) for d in data]
        costs = [d.get('cost', 0) for d in data]
        profits = [d.get('profit', r - c) for d, r, c in zip(data, revenues, costs)]
        
        # Calculate cumulative profit
        cumulative = []
        total = 0
        for p in profits:
            total += p
            cumulative.append(total)
        
        # Determine profit/loss colors for each point
        profit_colors = [
            self.default_colors['success'] if p >= 0 else self.default_colors['danger']
            for p in profits
        ]
        
        return {
            'chart_type': self.PROFIT_LOSS,
            'title': title,
            'x': periods,
            'revenues': revenues,
            'costs': costs,
            'profits': profits,
            'cumulative': cumulative,
            'currency': currency,
            'series': [
                {
                    'name': 'Revenue',
                    'data': revenues,
                    'type': 'area',
                    'color': self.default_colors['secondary'],
                    'fillOpacity': 0.3
                },
                {
                    'name': 'Cost',
                    'data': costs,
                    'type': 'area',
                    'color': self.default_colors['danger'],
                    'fillOpacity': 0.3
                },
                {
                    'name': 'Profit',
                    'data': profits,
                    'type': 'bar',
                    'colors': profit_colors
                }
            ],
            'options': {
                'showBreakeven': True,
                'breakEvenLine': 0,
                'highlightProfit': True
            }
        }
    
    def comparison_overlay_chart(
        self,
        datasets: List[Dict],
        title: str = "Multi-Dataset Comparison"
    ) -> Dict[str, Any]:
        """
        Generate multi-dataset overlay chart.
        
        Args:
            datasets: List of {name, data, color} where data is [{x, y}]
            title: Chart title
            
        Returns:
            Chart payload for frontend
        """
        # Find all unique x values
        all_x = set()
        for ds in datasets:
            for point in ds.get('data', []):
                all_x.add(point.get('x', ''))
        x_labels = sorted(list(all_x))
        
        # Build series
        series = []
        colors = [
            self.default_colors['primary'],
            self.default_colors['secondary'],
            self.default_colors['success'],
            self.default_colors['warning'],
            self.default_colors['danger']
        ]
        
        for i, ds in enumerate(datasets):
            name = ds.get('name', f'Dataset {i+1}')
            color = ds.get('color', colors[i % len(colors)])
            data_dict = {p.get('x'): p.get('y') for p in ds.get('data', [])}
            values = [data_dict.get(x) for x in x_labels]
            
            series.append({
                'name': name,
                'data': values,
                'type': 'line',
                'color': color,
                'strokeWidth': 2
            })
        
        return {
            'chart_type': self.COMPARISON_OVERLAY,
            'title': title,
            'x': x_labels,
            'series': series,
            'options': {
                'showLegend': True,
                'legendPosition': 'top',
                'enableHover': True,
                'showDots': True
            }
        }
    
    def driver_waterfall_chart(
        self,
        drivers: List[Dict],
        title: str = "Driver Analysis",
        currency: str = "₹"
    ) -> Dict[str, Any]:
        """
        Generate driver waterfall chart (what caused the change).
        
        Args:
            drivers: List of {name, impact, type} where type is 'increase' or 'decrease'
            title: Chart title
            currency: Currency symbol
            
        Returns:
            Chart payload for frontend
        """
        names = [d.get('name', f'Driver {i+1}') for i, d in enumerate(drivers)]
        impacts = [d.get('impact', 0) for d in drivers]
        types = [d.get('type', 'increase' if d.get('impact', 0) >= 0 else 'decrease') 
                 for d in drivers]
        
        # Calculate running total for waterfall
        running = [0]
        for impact in impacts:
            running.append(running[-1] + impact)
        
        colors = [
            self.default_colors['success'] if t == 'increase' else self.default_colors['danger']
            for t in types
        ]
        
        return {
            'chart_type': self.DRIVER_WATERFALL,
            'title': title,
            'x': names,
            'impacts': impacts,
            'running_total': running[1:],
            'types': types,
            'colors': colors,
            'currency': currency,
            'series': [
                {
                    'name': 'Impact',
                    'data': impacts,
                    'type': 'waterfall',
                    'colors': colors
                }
            ],
            'options': {
                'showConnectors': True,
                'showTotalBar': True,
                'startLabel': 'Start',
                'endLabel': 'End'
            }
        }
    
    def risk_heatmap(
        self,
        risk_matrix: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "Risk Assessment"
    ) -> Dict[str, Any]:
        """
        Generate risk heatmap.
        
        Args:
            risk_matrix: 2D array of risk scores (0-1)
            x_labels: Column labels
            y_labels: Row labels
            title: Chart title
            
        Returns:
            Chart payload for frontend
        """
        # Flatten matrix to points
        points = []
        for i, row in enumerate(risk_matrix):
            for j, val in enumerate(row):
                # Determine color based on risk level
                if val > 0.7:
                    color = self.default_colors['danger']
                elif val > 0.4:
                    color = self.default_colors['warning']
                else:
                    color = self.default_colors['success']
                    
                points.append({
                    'x': j,
                    'y': i,
                    'value': val,
                    'color': color,
                    'label': f'{val:.1%}'
                })
        
        return {
            'chart_type': self.RISK_HEATMAP,
            'title': title,
            'x_labels': x_labels,
            'y_labels': y_labels,
            'points': points,
            'matrix': risk_matrix,
            'options': {
                'showLabels': True,
                'colorScale': {
                    'low': self.default_colors['success'],
                    'medium': self.default_colors['warning'],
                    'high': self.default_colors['danger']
                },
                'cellRadius': 4
            }
        }


# Convenience functions
def generate_forecast_chart(prediction_result: Dict) -> Dict[str, Any]:
    """Generate forecast chart from prediction result."""
    generator = ChartGenerator()
    return generator.forecast_chart(
        historical=prediction_result.get('historical_points', []),
        forecast=prediction_result.get('forecast_points', []),
        title=f"Revenue Forecast ({len(prediction_result.get('forecast_points', []))} Periods)"
    )


def generate_scenario_chart(simulation_result: Dict) -> Dict[str, Any]:
    """Generate scenario chart from simulation result."""
    generator = ChartGenerator()
    return generator.scenario_chart(
        scenarios=simulation_result.get('scenarios', []),
        best_scenario=simulation_result.get('best_scenario')
    )


# Quick test
if __name__ == "__main__":
    generator = ChartGenerator()
    
    # Test forecast chart
    historical = [
        {'date': '2024-01', 'value': 10000},
        {'date': '2024-02', 'value': 10500},
        {'date': '2024-03', 'value': 11000},
    ]
    forecast = [
        {'date': '2024-04', 'value': 11500, 'lower': 10500, 'upper': 12500},
        {'date': '2024-05', 'value': 12000, 'lower': 10800, 'upper': 13200},
    ]
    
    chart = generator.forecast_chart(historical, forecast, "Test Forecast")
    print("Forecast Chart:")
    print(f"  Type: {chart['chart_type']}")
    print(f"  X Labels: {chart['x']}")
    print(f"  Series: {len(chart['series'])}")
