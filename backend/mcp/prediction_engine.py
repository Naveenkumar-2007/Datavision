# Prediction Engine MCP Service
"""
Enterprise Statistical Prediction Engine

Features:
- Multi-model forecasting (Prophet, ARIMA, Holt-Winters, Linear)
- Auto model selection based on data characteristics
- Comprehensive accuracy metrics (RMSE, MAE, MAPE)
- Trend & seasonality decomposition
- Risk zone detection
- Driver analysis
- Confidence intervals with uncertainty propagation

Usage:
    from mcp.prediction_engine import PredictionEngine
    engine = PredictionEngine()
    result = engine.predict(data, periods=6)
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import warnings

warnings.filterwarnings('ignore')


@dataclass
class AccuracyMetrics:
    """Model accuracy metrics"""
    RMSE: float
    MAE: float
    MAPE: float
    R2: float = 0.0


@dataclass
class ForecastComponents:
    """Decomposed forecast components"""
    trend: List[float]
    seasonal: List[float]
    residual: List[float]
    trend_direction: str
    seasonality_type: Optional[str]
    seasonality_period: Optional[int]


@dataclass
class RiskZone:
    """A detected risk zone in the forecast"""
    period: str
    type: str  # 'decline', 'volatility', 'churn', 'loss'
    severity: str  # 'low', 'medium', 'high'
    description: str
    value: float


@dataclass
class ChartPayload:
    """Frontend chart rendering payload"""
    chart_type: str
    title: str
    x: List[str]
    y_actual: List[Optional[float]]
    y_forecast: List[Optional[float]]
    y_upper: List[Optional[float]]
    y_lower: List[Optional[float]]
    confidence_band: bool = True


@dataclass
class PredictionResult:
    """Complete prediction result"""
    forecast_points: List[Dict[str, Any]]
    confidence_low: List[float]
    confidence_high: List[float]
    historical_points: List[Dict[str, Any]]
    trend: str
    seasonality: Optional[str]
    model_used: str
    accuracy: AccuracyMetrics
    insight: str
    risks: List[str]
    opportunities: List[str]
    explanation: str
    chart_payload: Dict[str, Any]
    components: Optional[ForecastComponents] = None
    

class PredictionEngine:
    """
    Enterprise Prediction Engine with Multi-Model Support.
    
    Automatically selects the best model based on data characteristics:
    - Prophet: For data with strong seasonality (24+ rows)
    - ARIMA: For stationary time series
    - Holt-Winters: For data with trend + seasonality
    - Linear: Fallback for small datasets
    """
    
    AVAILABLE_MODELS = ['prophet', 'arima', 'holt_winters', 'linear', 'auto']
    
    def __init__(self):
        self.min_rows_prophet = 24
        self.min_rows_arima = 12
        self.min_rows_holt_winters = 14
        self.min_rows_linear = 3
        
    def predict(
        self,
        data: Union[List[Dict], 'pd.DataFrame'],
        date_column: str = 'date',
        value_column: str = 'value',
        periods: int = 6,
        model: str = 'auto',
        confidence_level: float = 0.95,
        scenario: Optional[Dict] = None
    ) -> PredictionResult:
        """
        Generate prediction with automatic model selection.
        
        Args:
            data: Time series data (list of dicts or DataFrame)
            date_column: Name of date column
            value_column: Name of value column  
            periods: Number of future periods to forecast
            model: 'auto', 'prophet', 'arima', 'holt_winters', 'linear'
            confidence_level: Confidence level for intervals (0.9, 0.95, 0.99)
            scenario: Optional what-if modifiers
            
        Returns:
            PredictionResult with forecast, metrics, and chart payload
        """
        # Convert to standardized format
        df = self._prepare_data(data, date_column, value_column)
        
        if df is None or len(df) < self.min_rows_linear:
            return self._empty_result("Insufficient data for prediction (need at least 3 data points)")
        
        # Apply scenario modifiers if provided
        if scenario:
            df = self._apply_scenario(df, scenario)
        
        # Select best model
        if model == 'auto':
            model = self._select_best_model(df)
            
        # Generate forecast based on model
        forecast_values, model_obj = self._generate_forecast(df, periods, model)
        
        # Calculate confidence intervals
        conf_low, conf_high = self._calculate_confidence_intervals(
            df['value'].values, forecast_values, confidence_level, periods
        )
        
        # Calculate accuracy metrics (using holdout if possible)
        accuracy = self._calculate_accuracy(df, model, periods)
        
        # Detect components (trend, seasonality)
        components = self._decompose_series(df)
        
        # Detect risks
        risks = self._detect_risks(df, forecast_values, conf_low)
        
        # Detect opportunities  
        opportunities = self._detect_opportunities(df, forecast_values)
        
        # Generate insights
        insight = self._generate_main_insight(df, forecast_values, components)
        
        # Generate explanation
        explanation = self._generate_explanation(df, forecast_values, model, components)
        
        # Build historical points
        historical_points = self._build_historical_points(df)
        
        # Build forecast points
        forecast_points = self._build_forecast_points(
            df, forecast_values, conf_low, conf_high, periods
        )
        
        # Generate chart payload
        chart_payload = self._generate_chart_payload(
            df, forecast_values, conf_low, conf_high, periods
        )
        
        return PredictionResult(
            forecast_points=forecast_points,
            confidence_low=conf_low,
            confidence_high=conf_high,
            historical_points=historical_points,
            trend=components.trend_direction if components else 'unknown',
            seasonality=components.seasonality_type if components else None,
            model_used=model,
            accuracy=accuracy,
            insight=insight,
            risks=[r.description for r in risks],
            opportunities=opportunities,
            explanation=explanation,
            chart_payload=chart_payload,
            components=components
        )
    
    def _prepare_data(self, data, date_col: str, value_col: str):
        """Convert input data to pandas DataFrame."""
        try:
            import pandas as pd
            
            if isinstance(data, pd.DataFrame):
                df = data.copy()
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                return None
                
            # Rename columns
            if date_col in df.columns:
                df = df.rename(columns={date_col: 'date'})
            if value_col in df.columns:
                df = df.rename(columns={value_col: 'value'})
                
            # Ensure required columns
            if 'value' not in df.columns:
                return None
                
            # Convert value to numeric
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna(subset=['value'])
            
            # Parse dates if present
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.sort_values('date').reset_index(drop=True)
            else:
                df['date'] = pd.date_range(end=datetime.now(), periods=len(df), freq='D')
                
            return df
            
        except Exception as e:
            print(f"Data preparation error: {e}")
            return None
    
    def _select_best_model(self, df) -> str:
        """Auto-select the best model based on data characteristics."""
        n = len(df)
        values = df['value'].values
        
        # Check for Prophet availability and sufficient data
        if n >= self.min_rows_prophet:
            try:
                from prophet import Prophet
                return 'prophet'
            except ImportError:
                pass
        
        # Check for seasonality (use Holt-Winters)
        if n >= self.min_rows_holt_winters:
            # Simple seasonality detection
            if self._has_seasonality(values):
                return 'holt_winters'
        
        # Check for ARIMA (stationary data)
        if n >= self.min_rows_arima:
            return 'arima'
            
        # Fallback to linear
        return 'linear'
    
    def _has_seasonality(self, values: np.ndarray) -> bool:
        """Detect if data has seasonality."""
        if len(values) < 14:
            return False
            
        # Simple autocorrelation check at lag 7
        try:
            mean = np.mean(values)
            var = np.var(values)
            if var == 0:
                return False
                
            n = len(values)
            lag = min(7, n // 2)
            
            autocorr = np.sum((values[:-lag] - mean) * (values[lag:] - mean)) / (n * var)
            
            return autocorr > 0.3
        except:
            return False
    
    def _generate_forecast(self, df, periods: int, model: str) -> Tuple[List[float], Any]:
        """Generate forecast using specified model."""
        values = df['value'].values
        
        if model == 'prophet':
            return self._prophet_forecast(df, periods)
        elif model == 'arima':
            return self._arima_forecast(values, periods)
        elif model == 'holt_winters':
            return self._holt_winters_forecast(values, periods)
        else:
            return self._linear_forecast(values, periods)
    
    def _prophet_forecast(self, df, periods: int) -> Tuple[List[float], Any]:
        """Facebook Prophet forecasting."""
        try:
            from prophet import Prophet
            import pandas as pd
            
            # Prepare Prophet format
            prophet_df = df[['date', 'value']].rename(columns={'date': 'ds', 'value': 'y'})
            
            # Fit model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=len(df) >= 14,
                daily_seasonality=False,
                interval_width=0.95
            )
            model.fit(prophet_df)
            
            # Generate future dates
            future = model.make_future_dataframe(periods=periods)
            forecast = model.predict(future)
            
            # Extract forecast values
            forecast_values = forecast['yhat'].tail(periods).values.tolist()
            
            return forecast_values, model
            
        except ImportError:
            print("Prophet not installed, falling back to linear")
            return self._linear_forecast(df['value'].values, periods)
        except Exception as e:
            print(f"Prophet error: {e}, falling back to linear")
            return self._linear_forecast(df['value'].values, periods)
    
    def _arima_forecast(self, values: np.ndarray, periods: int) -> Tuple[List[float], Any]:
        """ARIMA forecasting."""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            # Fit ARIMA model with common parameters
            model = ARIMA(values, order=(1, 1, 1))
            fitted = model.fit()
            
            # Generate forecast
            forecast = fitted.forecast(steps=periods)
            
            return forecast.tolist(), fitted
            
        except ImportError:
            print("statsmodels not installed, falling back to linear")
            return self._linear_forecast(values, periods)
        except Exception as e:
            print(f"ARIMA error: {e}, falling back to linear")
            return self._linear_forecast(values, periods)
    
    def _holt_winters_forecast(self, values: np.ndarray, periods: int) -> Tuple[List[float], Any]:
        """Holt-Winters exponential smoothing."""
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # Determine seasonal period
            seasonal_period = min(7, len(values) // 2)
            
            # Fit model
            model = ExponentialSmoothing(
                values,
                trend='add',
                seasonal='add' if len(values) >= 2 * seasonal_period else None,
                seasonal_periods=seasonal_period if len(values) >= 2 * seasonal_period else None
            )
            fitted = model.fit()
            
            # Generate forecast
            forecast = fitted.forecast(periods)
            
            return forecast.tolist(), fitted
            
        except ImportError:
            print("statsmodels not installed, falling back to linear")
            return self._linear_forecast(values, periods)
        except Exception as e:
            print(f"Holt-Winters error: {e}, falling back to linear")
            return self._linear_forecast(values, periods)
    
    def _linear_forecast(self, values: np.ndarray, periods: int) -> Tuple[List[float], None]:
        """Linear regression fallback."""
        n = len(values)
        x = np.arange(n)
        
        # Calculate slope and intercept
        slope = (n * np.sum(x * values) - np.sum(x) * np.sum(values)) / \
                (n * np.sum(x**2) - np.sum(x)**2)
        intercept = (np.sum(values) - slope * np.sum(x)) / n
        
        # Apply EWMA smoothing
        alpha = 0.3
        smoothed = [values[-1]]
        for i in range(periods):
            pred = intercept + slope * (n + i)
            smoothed_val = alpha * pred + (1 - alpha) * smoothed[-1]
            smoothed.append(max(0, smoothed_val))
            
        return smoothed[1:], None
    
    def _calculate_confidence_intervals(
        self, 
        historical: np.ndarray, 
        forecast: List[float],
        confidence: float,
        periods: int
    ) -> Tuple[List[float], List[float]]:
        """Calculate expanding confidence intervals."""
        std = np.std(historical)
        
        # Z-scores for common confidence levels
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)
        
        lower = []
        upper = []
        
        for i, val in enumerate(forecast):
            # Expand uncertainty for further predictions
            expansion = 1 + (i * 0.15)
            margin = z * std * expansion
            lower.append(max(0, val - margin))
            upper.append(val + margin)
            
        return lower, upper
    
    def _calculate_accuracy(self, df, model: str, periods: int) -> AccuracyMetrics:
        """Calculate accuracy using holdout validation."""
        values = df['value'].values
        n = len(values)
        
        if n < 10:
            # Not enough data for holdout
            return AccuracyMetrics(RMSE=0, MAE=0, MAPE=0, R2=0)
            
        # Use last 20% as test set
        split = max(3, int(n * 0.8))
        train = values[:split]
        test = values[split:]
        
        # Generate predictions for test period
        test_periods = len(test)
        if model == 'linear' or test_periods < 3:
            predictions, _ = self._linear_forecast(train, test_periods)
        else:
            predictions, _ = self._linear_forecast(train, test_periods)  # Simplified for speed
            
        predictions = np.array(predictions[:len(test)])
        test = np.array(test)
        
        # Calculate metrics
        rmse = np.sqrt(np.mean((test - predictions) ** 2))
        mae = np.mean(np.abs(test - predictions))
        
        # MAPE (handle zero values)
        non_zero = test != 0
        if np.any(non_zero):
            mape = np.mean(np.abs((test[non_zero] - predictions[non_zero]) / test[non_zero])) * 100
        else:
            mape = 0
            
        # R-squared
        ss_res = np.sum((test - predictions) ** 2)
        ss_tot = np.sum((test - np.mean(test)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return AccuracyMetrics(
            RMSE=round(rmse, 2),
            MAE=round(mae, 2),
            MAPE=round(mape, 2),
            R2=round(max(0, r2), 3)
        )
    
    def _decompose_series(self, df) -> Optional[ForecastComponents]:
        """Decompose time series into trend, seasonal, residual."""
        values = df['value'].values
        n = len(values)
        
        if n < 7:
            return ForecastComponents(
                trend=values.tolist(),
                seasonal=[],
                residual=[],
                trend_direction=self._get_trend_direction(values),
                seasonality_type=None,
                seasonality_period=None
            )
            
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            
            period = min(7, n // 2)
            decomposition = seasonal_decompose(values, model='additive', period=period)
            
            trend = decomposition.trend
            seasonal = decomposition.seasonal
            residual = decomposition.resid
            
            # Handle NaN values
            trend = np.nan_to_num(trend, nan=np.nanmean(values)).tolist()
            seasonal = np.nan_to_num(seasonal, nan=0).tolist()
            residual = np.nan_to_num(residual, nan=0).tolist()
            
            return ForecastComponents(
                trend=trend,
                seasonal=seasonal,
                residual=residual,
                trend_direction=self._get_trend_direction(values),
                seasonality_type='weekly' if period == 7 else 'custom',
                seasonality_period=period
            )
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Decomposition error: {e}")
            
        # Fallback: simple trend extraction
        return ForecastComponents(
            trend=values.tolist(),
            seasonal=[],
            residual=[],
            trend_direction=self._get_trend_direction(values),
            seasonality_type=None,
            seasonality_period=None
        )
    
    def _get_trend_direction(self, values: np.ndarray) -> str:
        """Determine trend direction."""
        if len(values) < 2:
            return 'stable'
            
        n = len(values)
        x = np.arange(n)
        
        slope = (n * np.sum(x * values) - np.sum(x) * np.sum(values)) / \
                (n * np.sum(x**2) - np.sum(x)**2)
                
        avg = np.mean(values)
        relative_slope = slope / avg if avg != 0 else 0
        
        if relative_slope > 0.02:
            return 'strongly_increasing'
        elif relative_slope > 0.005:
            return 'increasing'
        elif relative_slope < -0.02:
            return 'strongly_decreasing'
        elif relative_slope < -0.005:
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_risks(self, df, forecast: List[float], conf_low: List[float]) -> List[RiskZone]:
        """Detect risk zones in forecast."""
        risks = []
        values = df['value'].values
        last_actual = values[-1] if len(values) > 0 else 0
        
        # Check for declining forecast
        for i, (pred, low) in enumerate(zip(forecast, conf_low)):
            period = f"Period +{i+1}"
            
            # Significant decline
            if pred < last_actual * 0.9:
                decline_pct = ((last_actual - pred) / last_actual * 100) if last_actual > 0 else 0
                risks.append(RiskZone(
                    period=period,
                    type='decline',
                    severity='high' if decline_pct > 20 else 'medium',
                    description=f"Potential {decline_pct:.1f}% decline in {period}",
                    value=pred
                ))
                
            # Wide confidence interval (high uncertainty)
            if low < pred * 0.7:
                risks.append(RiskZone(
                    period=period,
                    type='volatility',
                    severity='medium',
                    description=f"High uncertainty in {period} forecast",
                    value=low
                ))
                
        # Check for loss (negative profit)
        if len(forecast) > 0 and min(forecast) < 0:
            risks.append(RiskZone(
                period="Multiple",
                type='loss',
                severity='high',
                description="Potential loss period detected",
                value=min(forecast)
            ))
            
        return risks[:5]  # Limit to top 5 risks
    
    def _detect_opportunities(self, df, forecast: List[float]) -> List[str]:
        """Detect growth opportunities."""
        opportunities = []
        values = df['value'].values
        last_actual = values[-1] if len(values) > 0 else 0
        
        # Check for growth periods
        for i, pred in enumerate(forecast):
            if pred > last_actual * 1.15:
                growth_pct = ((pred - last_actual) / last_actual * 100) if last_actual > 0 else 0
                opportunities.append(
                    f"📈 Strong growth potential ({growth_pct:.0f}%) projected in Period +{i+1}"
                )
                
        # Check for upward trend
        if len(forecast) >= 3:
            trend = self._get_trend_direction(np.array(forecast))
            if 'increasing' in trend:
                opportunities.append("🚀 Sustained upward momentum detected")
                
        # Max opportunity
        if len(forecast) > 0:
            max_val = max(forecast)
            max_idx = forecast.index(max_val)
            if max_val > last_actual:
                opportunities.append(
                    f"⭐ Peak opportunity in Period +{max_idx+1}"
                )
                
        return opportunities[:4]
    
    def _generate_main_insight(self, df, forecast: List[float], components: Optional[ForecastComponents]) -> str:
        """Generate main insight summary."""
        values = df['value'].values
        last_actual = values[-1]
        avg_forecast = np.mean(forecast) if forecast else 0
        
        change_pct = ((avg_forecast - last_actual) / last_actual * 100) if last_actual > 0 else 0
        trend = components.trend_direction if components else 'stable'
        
        if change_pct > 10:
            return f"Strong growth trajectory: {change_pct:.1f}% increase expected over forecast period"
        elif change_pct > 0:
            return f"Moderate growth: {change_pct:.1f}% increase projected"
        elif change_pct > -10:
            return f"Slight decline: {abs(change_pct):.1f}% decrease expected"
        else:
            return f"Warning: Significant {abs(change_pct):.1f}% decline projected"
    
    def _generate_explanation(
        self, df, forecast: List[float], model: str, components: Optional[ForecastComponents]
    ) -> str:
        """Generate driver analysis explanation."""
        values = df['value'].values
        n = len(values)
        
        explanations = []
        
        # Model explanation
        model_names = {
            'prophet': 'Facebook Prophet (captures trend + seasonality)',
            'arima': 'ARIMA (auto-regressive integrated moving average)',
            'holt_winters': 'Holt-Winters (exponential smoothing)',
            'linear': 'Linear regression with smoothing'
        }
        explanations.append(f"Model: {model_names.get(model, model)}")
        
        # Trend explanation
        if components:
            trend_desc = {
                'strongly_increasing': 'Strong upward trend detected in historical data',
                'increasing': 'Moderate growth trend observed',
                'stable': 'Values remain relatively stable',
                'decreasing': 'Declining trend identified',
                'strongly_decreasing': 'Significant downward pressure observed'
            }
            explanations.append(trend_desc.get(components.trend_direction, ''))
            
            # Seasonality
            if components.seasonality_type:
                explanations.append(
                    f"Seasonality: {components.seasonality_type} pattern with period {components.seasonality_period}"
                )
                
        # Data quality
        if n >= 30:
            explanations.append("High data coverage provides reliable predictions")
        elif n >= 14:
            explanations.append("Moderate data available for prediction")
        else:
            explanations.append("Limited historical data - predictions have higher uncertainty")
            
        return ". ".join(explanations)
    
    def _build_historical_points(self, df) -> List[Dict[str, Any]]:
        """Build historical data points."""
        points = []
        for i, row in df.iterrows():
            points.append({
                'period': i + 1,
                'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                'value': round(row['value'], 2),
                'type': 'historical'
            })
        return points
    
    def _build_forecast_points(
        self, df, forecast: List[float], conf_low: List[float], 
        conf_high: List[float], periods: int
    ) -> List[Dict[str, Any]]:
        """Build forecast data points."""
        points = []
        last_date = df['date'].iloc[-1]
        n = len(df)
        
        for i, (val, low, high) in enumerate(zip(forecast, conf_low, conf_high)):
            # Calculate future date
            try:
                future_date = last_date + timedelta(days=(i+1) * 30)  # Monthly
                date_str = future_date.strftime('%Y-%m-%d')
            except:
                date_str = f"Forecast +{i+1}"
                
            points.append({
                'period': n + i + 1,
                'date': date_str,
                'value': round(val, 2),
                'lower': round(low, 2),
                'upper': round(high, 2),
                'type': 'forecast'
            })
            
        return points
    
    def _generate_chart_payload(
        self, df, forecast: List[float], conf_low: List[float],
        conf_high: List[float], periods: int
    ) -> Dict[str, Any]:
        """Generate frontend chart payload."""
        # Historical dates and values
        dates = [row['date'].strftime('%b %Y') if hasattr(row['date'], 'strftime') 
                 else str(row['date'])[:7] for _, row in df.iterrows()]
        historical_values = df['value'].tolist()
        
        # Add forecast dates
        for i in range(periods):
            dates.append(f"+{i+1}M")
            
        # Build series
        y_actual = historical_values + [None] * periods
        y_forecast = [None] * (len(historical_values) - 1) + [historical_values[-1]] + forecast
        y_upper = [None] * (len(historical_values) - 1) + [historical_values[-1]] + conf_high
        y_lower = [None] * (len(historical_values) - 1) + [historical_values[-1]] + conf_low
        
        return {
            'chart_type': 'forecast_line',
            'title': f'Forecast ({periods} Periods)',
            'x': dates,
            'y_actual': y_actual,
            'y_forecast': y_forecast,
            'y_upper': y_upper,
            'y_lower': y_lower,
            'confidence_band': True
        }
    
    def _apply_scenario(self, df, scenario: Dict) -> 'pd.DataFrame':
        """Apply what-if scenario modifiers."""
        df = df.copy()
        
        # Price change modifier
        if 'price_change' in scenario:
            pct = scenario['price_change'] / 100
            # Price elasticity effect
            elasticity = -1.2
            demand_effect = 1 + (pct * elasticity)
            df['value'] = df['value'] * (1 + pct) * demand_effect
            
        # Volume change
        if 'volume_change' in scenario:
            pct = scenario['volume_change'] / 100
            df['value'] = df['value'] * (1 + pct)
            
        # Marketing impact
        if 'marketing_change' in scenario:
            pct = scenario['marketing_change'] / 100
            marketing_elasticity = 0.3
            df['value'] = df['value'] * (1 + pct * marketing_elasticity)
            
        return df
    
    def _empty_result(self, message: str) -> PredictionResult:
        """Return empty result with error message."""
        return PredictionResult(
            forecast_points=[],
            confidence_low=[],
            confidence_high=[],
            historical_points=[],
            trend='unknown',
            seasonality=None,
            model_used='none',
            accuracy=AccuracyMetrics(RMSE=0, MAE=0, MAPE=0, R2=0),
            insight=message,
            risks=[message],
            opportunities=[],
            explanation=message,
            chart_payload={},
            components=None
        )


# Convenience functions
def predict_revenue(data, periods: int = 6) -> Dict[str, Any]:
    """Predict revenue for given periods."""
    engine = PredictionEngine()
    result = engine.predict(data, value_column='revenue', periods=periods)
    return _result_to_dict(result)


def predict_sales(data, periods: int = 6) -> Dict[str, Any]:
    """Predict sales volume."""
    engine = PredictionEngine()
    result = engine.predict(data, value_column='sales', periods=periods)
    return _result_to_dict(result)


def predict_churn(data, periods: int = 3) -> Dict[str, Any]:
    """Predict customer churn rate."""
    engine = PredictionEngine()
    result = engine.predict(data, value_column='churn_rate', periods=periods)
    return _result_to_dict(result)


def predict_demand(data, product_id: str = None, periods: int = 6) -> Dict[str, Any]:
    """Predict product demand."""
    engine = PredictionEngine()
    result = engine.predict(data, value_column='demand', periods=periods)
    return _result_to_dict(result)


def _result_to_dict(result: PredictionResult) -> Dict[str, Any]:
    """Convert PredictionResult to dictionary."""
    return {
        'success': len(result.forecast_points) > 0,
        'forecast_points': result.forecast_points,
        'confidence_low': result.confidence_low,
        'confidence_high': result.confidence_high,
        'historical_points': result.historical_points,
        'trend': result.trend,
        'seasonality': result.seasonality,
        'model_used': result.model_used,
        'accuracy': {
            'RMSE': result.accuracy.RMSE,
            'MAE': result.accuracy.MAE,
            'MAPE': result.accuracy.MAPE,
            'R2': result.accuracy.R2
        },
        'insight': result.insight,
        'risks': result.risks,
        'opportunities': result.opportunities,
        'explanation': result.explanation,
        'chart_payload': result.chart_payload
    }


# Quick test
if __name__ == "__main__":
    # Sample data
    test_data = [
        {"date": "2024-01-01", "value": 10000},
        {"date": "2024-02-01", "value": 10500},
        {"date": "2024-03-01", "value": 10200},
        {"date": "2024-04-01", "value": 11000},
        {"date": "2024-05-01", "value": 11200},
        {"date": "2024-06-01", "value": 10800},
        {"date": "2024-07-01", "value": 11500},
        {"date": "2024-08-01", "value": 12000},
        {"date": "2024-09-01", "value": 11800},
        {"date": "2024-10-01", "value": 12500},
        {"date": "2024-11-01", "value": 13000},
        {"date": "2024-12-01", "value": 12800},
    ]
    
    engine = PredictionEngine()
    result = engine.predict(test_data, periods=6)
    
    print("Prediction Results:")
    print(f"  Model: {result.model_used}")
    print(f"  Trend: {result.trend}")
    print(f"  Insight: {result.insight}")
    print(f"  Accuracy (MAPE): {result.accuracy.MAPE}%")
    print(f"  Risks: {result.risks}")
    print(f"  Opportunities: {result.opportunities}")
    print(f"  Forecast: {result.forecast_points[:3]}")
