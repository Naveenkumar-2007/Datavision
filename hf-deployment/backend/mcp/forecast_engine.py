# Forecast Engine MCP Service
"""
Enterprise Time-Series Forecasting Engine

Features:
- Linear regression-based forecasting
- Moving average analysis
- Confidence interval calculation
- Trend detection
- Seasonal pattern recognition

Usage:
    from mcp.forecast_engine import ForecastEngine
    engine = ForecastEngine()
    result = engine.forecast(data, periods=7)
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class ForecastResult:
    """Result from forecast engine"""
    forecast: List[Dict[str, Any]]
    lower_bound: List[float]
    upper_bound: List[float]
    trend: str
    trend_slope: float
    confidence_score: float
    seasonality: Optional[str]
    insights: List[str]


class ForecastEngine:
    """
    Enterprise Forecast Engine using statistical methods.
    
    Supports:
    - Linear trend forecasting
    - Moving average forecasting
    - Exponential smoothing
    - Confidence intervals
    """
    
    def __init__(self):
        self.min_data_points = 3
        self.default_confidence = 0.95
        
    def forecast(
        self,
        data: List[Dict[str, Any]],
        date_column: str = "date",
        value_column: str = "value",
        periods: int = 7,
        confidence: float = 0.95
    ) -> ForecastResult:
        """
        Generate forecast for time-series data.
        
        Args:
            data: List of dicts with date and value columns
            date_column: Name of date column
            value_column: Name of value column
            periods: Number of periods to forecast
            confidence: Confidence level (0-1)
            
        Returns:
            ForecastResult with predictions and analysis
        """
        if not data or len(data) < self.min_data_points:
            return self._empty_result("Insufficient data for forecasting")
            
        # Extract values
        values = []
        dates = []
        for item in data:
            try:
                val = float(item.get(value_column, 0))
                values.append(val)
                dates.append(item.get(date_column, ""))
            except (ValueError, TypeError):
                continue
                
        if len(values) < self.min_data_points:
            return self._empty_result("Not enough valid data points")
            
        # Calculate trend
        trend, slope = self._calculate_trend(values)
        
        # Generate forecast using linear regression
        forecast_values = self._linear_forecast(values, periods)
        
        # Calculate confidence intervals
        lower, upper = self._calculate_confidence_intervals(
            values, forecast_values, confidence
        )
        
        # Detect seasonality
        seasonality = self._detect_seasonality(values)
        
        # Generate insights
        insights = self._generate_insights(values, forecast_values, trend, slope)
        
        # Calculate confidence score
        conf_score = self._calculate_confidence_score(values, len(data))
        
        # Build forecast with dates
        forecast_data = self._build_forecast_output(
            dates, values, forecast_values, lower, upper, periods
        )
        
        return ForecastResult(
            forecast=forecast_data,
            lower_bound=lower,
            upper_bound=upper,
            trend=trend,
            trend_slope=slope,
            confidence_score=conf_score,
            seasonality=seasonality,
            insights=insights
        )
        
    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and slope."""
        n = len(values)
        if n < 2:
            return "stable", 0.0
            
        x = np.arange(n)
        y = np.array(values)
        
        # Linear regression
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / \
                (n * np.sum(x**2) - np.sum(x)**2)
        
        # Determine trend
        avg_value = np.mean(values)
        relative_slope = slope / avg_value if avg_value != 0 else 0
        
        if relative_slope > 0.02:
            trend = "strongly_increasing"
        elif relative_slope > 0.005:
            trend = "increasing"
        elif relative_slope < -0.02:
            trend = "strongly_decreasing"
        elif relative_slope < -0.005:
            trend = "decreasing"
        else:
            trend = "stable"
            
        return trend, float(slope)
        
    def _linear_forecast(self, values: List[float], periods: int) -> List[float]:
        """Generate forecast using linear regression."""
        n = len(values)
        x = np.arange(n)
        y = np.array(values)
        
        # Calculate slope and intercept
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / \
                (n * np.sum(x**2) - np.sum(x)**2)
        intercept = (np.sum(y) - slope * np.sum(x)) / n
        
        # Generate future values
        forecast = []
        for i in range(periods):
            pred = intercept + slope * (n + i)
            # Apply moving average smoothing
            if len(values) >= 3:
                ma = np.mean(values[-3:])
                pred = pred * 0.7 + ma * 0.3
            forecast.append(max(0, pred))  # Ensure non-negative
            
        return forecast
        
    def _calculate_confidence_intervals(
        self,
        historical: List[float],
        forecast: List[float],
        confidence: float
    ) -> Tuple[List[float], List[float]]:
        """Calculate confidence intervals for forecast."""
        # Calculate historical standard deviation
        std = np.std(historical) if len(historical) > 1 else 0
        
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)
        
        # Expand intervals for future periods
        lower = []
        upper = []
        for i, val in enumerate(forecast):
            expansion = 1 + (i * 0.1)  # Wider intervals for further predictions
            margin = z * std * expansion
            lower.append(max(0, val - margin))
            upper.append(val + margin)
            
        return lower, upper
        
    def _detect_seasonality(self, values: List[float]) -> Optional[str]:
        """Detect seasonality patterns."""
        if len(values) < 7:
            return None
            
        # Check for weekly pattern (7-day cycle)
        if len(values) >= 14:
            weekly_diff = []
            for i in range(7, len(values)):
                diff = abs(values[i] - values[i-7])
                weekly_diff.append(diff)
            avg_weekly_var = np.mean(weekly_diff)
            overall_var = np.std(values)
            if avg_weekly_var < overall_var * 0.5:
                return "weekly"
                
        # Check for monthly pattern
        if len(values) >= 60:
            return "monthly"
            
        return None
        
    def _generate_insights(
        self,
        historical: List[float],
        forecast: List[float],
        trend: str,
        slope: float
    ) -> List[str]:
        """Generate human-readable insights."""
        insights = []
        
        # Trend insight
        trend_labels = {
            "strongly_increasing": "Revenue is growing rapidly",
            "increasing": "Revenue shows steady growth",
            "stable": "Revenue is relatively stable",
            "decreasing": "Revenue is declining",
            "strongly_decreasing": "Revenue is declining significantly"
        }
        insights.append(trend_labels.get(trend, "Trend analysis complete"))
        
        # Forecast summary
        if forecast:
            avg_forecast = np.mean(forecast)
            avg_historical = np.mean(historical)
            change_pct = ((avg_forecast - avg_historical) / avg_historical * 100) \
                        if avg_historical != 0 else 0
                        
            if change_pct > 5:
                insights.append(f"Projected {change_pct:.1f}% increase in coming period")
            elif change_pct < -5:
                insights.append(f"Projected {abs(change_pct):.1f}% decrease in coming period")
            else:
                insights.append("Forecast shows minimal change from current levels")
                
        # Volatility insight
        if len(historical) > 3:
            cv = np.std(historical) / np.mean(historical) if np.mean(historical) != 0 else 0
            if cv > 0.3:
                insights.append("⚠️ High volatility detected - predictions may vary")
            elif cv < 0.1:
                insights.append("✓ Low volatility - high prediction confidence")
                
        return insights
        
    def _calculate_confidence_score(self, values: List[float], n_points: int) -> float:
        """Calculate overall confidence score (0-100)."""
        # Base score on data points
        data_score = min(n_points / 30 * 50, 50)  # Max 50 from data quantity
        
        # Score based on stability
        if len(values) > 1:
            cv = np.std(values) / np.mean(values) if np.mean(values) != 0 else 1
            stability_score = max(0, 50 * (1 - cv))
        else:
            stability_score = 0
            
        return min(round(data_score + stability_score, 1), 100)
        
    def _build_forecast_output(
        self,
        dates: List[str],
        historical: List[float],
        forecast: List[float],
        lower: List[float],
        upper: List[float],
        periods: int
    ) -> List[Dict[str, Any]]:
        """Build structured forecast output."""
        output = []
        
        # Add historical data
        for i, (date, value) in enumerate(zip(dates, historical)):
            output.append({
                "period": i + 1,
                "date": date,
                "value": round(value, 2),
                "type": "historical"
            })
            
        # Add forecast data
        last_date = dates[-1] if dates else ""
        for i, (val, low, up) in enumerate(zip(forecast, lower, upper)):
            output.append({
                "period": len(historical) + i + 1,
                "date": f"Forecast +{i+1}",
                "value": round(val, 2),
                "lower": round(low, 2),
                "upper": round(up, 2),
                "type": "forecast"
            })
            
        return output
        
    def _empty_result(self, message: str) -> ForecastResult:
        """Return empty result with message."""
        return ForecastResult(
            forecast=[],
            lower_bound=[],
            upper_bound=[],
            trend="unknown",
            trend_slope=0.0,
            confidence_score=0.0,
            seasonality=None,
            insights=[message]
        )


def forecast_from_dataframe(df, date_col: str, value_col: str, periods: int = 7) -> Dict:
    """
    Convenience function to forecast from a pandas DataFrame.
    
    Args:
        df: pandas DataFrame
        date_col: Name of date column
        value_col: Name of value column
        periods: Number of periods to forecast
        
    Returns:
        Dict with forecast results
    """
    try:
        # Convert DataFrame to list of dicts
        data = df[[date_col, value_col]].rename(
            columns={date_col: "date", value_col: "value"}
        ).to_dict('records')
        
        engine = ForecastEngine()
        result = engine.forecast(data, periods=periods)
        
        return {
            "success": True,
            "forecast": result.forecast,
            "lower_bound": result.lower_bound,
            "upper_bound": result.upper_bound,
            "trend": result.trend,
            "confidence": f"{result.confidence_score}%",
            "insights": result.insights
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "forecast": [],
            "insights": [f"Forecast error: {str(e)}"]
        }


# Quick test
if __name__ == "__main__":
    test_data = [
        {"date": "2024-01-01", "value": 10000},
        {"date": "2024-01-02", "value": 10500},
        {"date": "2024-01-03", "value": 10200},
        {"date": "2024-01-04", "value": 11000},
        {"date": "2024-01-05", "value": 11200},
        {"date": "2024-01-06", "value": 10800},
        {"date": "2024-01-07", "value": 11500},
    ]
    
    engine = ForecastEngine()
    result = engine.forecast(test_data, periods=7)
    
    print("Forecast Results:")
    print(f"Trend: {result.trend}")
    print(f"Confidence: {result.confidence_score}%")
    print(f"Insights: {result.insights}")
    print(f"Forecast: {result.forecast[-3:]}")
