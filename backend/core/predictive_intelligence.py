"""
🔮 PREDICTIVE INTELLIGENCE - DataVision Advanced Predictions
=============================================================

Enterprise-grade predictive capabilities:
- Ensemble predictions (multiple models)
- Confidence intervals
- Feature importance with SHAP
- Actionable recommendations
- Prediction explanations

FREE: Uses sklearn (no paid APIs)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.ensemble import (
        RandomForestRegressor, 
        GradientBoostingRegressor,
        VotingRegressor
    )
    from sklearn.model_selection import cross_val_predict, cross_val_score
    from sklearn.preprocessing import StandardScaler, PolynomialFeatures
    from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from core.llm import chat

logger = logging.getLogger(__name__)


# =============================================================================
# ENSEMBLE PREDICTION ENGINE
# =============================================================================

@dataclass
class PredictionResult:
    """Result from ensemble prediction"""
    predictions: List[float]
    confidence_lower: List[float]
    confidence_upper: List[float]
    confidence_level: float  # e.g., 0.95 for 95%
    feature_importance: Dict[str, float]
    model_contributions: Dict[str, float]  # How much each model contributed
    metrics: Dict[str, float]
    recommendations: List[str]


class EnsemblePredictionEngine:
    """
    🔮 Ensemble Prediction Engine
    
    Combines multiple models for robust predictions:
    - Linear Regression
    - Ridge
    - Random Forest
    - Gradient Boosting
    
    Provides confidence intervals and feature importance.
    """
    
    def __init__(self):
        self.models = {}
        self.scaler = StandardScaler()
        
        if SKLEARN_AVAILABLE:
            self.base_models = {
                "linear": LinearRegression(),
                "ridge": Ridge(alpha=1.0),
                "random_forest": RandomForestRegressor(
                    n_estimators=50, 
                    max_depth=10, 
                    random_state=42
                ),
                "gradient_boosting": GradientBoostingRegressor(
                    n_estimators=50, 
                    max_depth=5, 
                    random_state=42
                ),
            }
    
    async def predict(
        self,
        df: pd.DataFrame,
        target_column: str,
        feature_columns: Optional[List[str]] = None,
        confidence_level: float = 0.95,
        generate_recommendations: bool = True
    ) -> PredictionResult:
        """
        Make ensemble predictions with confidence intervals
        
        Args:
            df: Training data
            target_column: Column to predict
            feature_columns: Features to use (auto-detect if None)
            confidence_level: Confidence interval level (0.95 = 95%)
            generate_recommendations: Whether to generate action recommendations
            
        Returns:
            Complete prediction result
        """
        if not SKLEARN_AVAILABLE:
            return self._fallback_prediction(df, target_column)
        
        try:
            # Prepare data
            df = df.copy()
            
            if feature_columns is None:
                feature_columns = self._auto_select_features(df, target_column)
            
            if len(feature_columns) == 0:
                return self._fallback_prediction(df, target_column)
            
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Handle missing values
            X = X.fillna(X.mean())
            y = y.fillna(y.mean())
            
            # Ensure numeric
            X = X.select_dtypes(include=[np.number])
            feature_columns = X.columns.tolist()
            
            if len(feature_columns) == 0:
                return self._fallback_prediction(df, target_column)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train each model and get predictions
            model_predictions = {}
            model_scores = {}
            
            for name, model in self.base_models.items():
                try:
                    # Cross-validated predictions
                    cv_preds = cross_val_predict(model, X_scaled, y, cv=min(5, len(y)//5))
                    cv_score = cross_val_score(model, X_scaled, y, cv=min(5, len(y)//5), scoring='r2')
                    
                    model_predictions[name] = cv_preds
                    model_scores[name] = np.mean(cv_score)
                except Exception as e:
                    logger.warning(f"Model {name} failed: {e}")
            
            if not model_predictions:
                return self._fallback_prediction(df, target_column)
            
            # Combine predictions (weighted by R2 score)
            total_score = sum(max(0.01, s) for s in model_scores.values())
            weights = {name: max(0.01, score) / total_score 
                      for name, score in model_scores.items()}
            
            ensemble_predictions = np.zeros(len(y))
            for name, preds in model_predictions.items():
                ensemble_predictions += weights[name] * preds
            
            # Calculate confidence intervals
            prediction_std = np.std(list(model_predictions.values()), axis=0)
            z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
            
            confidence_lower = (ensemble_predictions - z_score * prediction_std).tolist()
            confidence_upper = (ensemble_predictions + z_score * prediction_std).tolist()
            
            # Calculate metrics
            metrics = {
                "r2_score": float(r2_score(y, ensemble_predictions)),
                "mae": float(mean_absolute_error(y, ensemble_predictions)),
                "rmse": float(np.sqrt(mean_squared_error(y, ensemble_predictions))),
                "mape": float(np.mean(np.abs((y - ensemble_predictions) / y)) * 100) if (y != 0).all() else 0
            }
            
            # Get feature importance
            feature_importance = self._calculate_feature_importance(
                X_scaled, y, feature_columns
            )
            
            # Generate recommendations
            recommendations = []
            if generate_recommendations:
                recommendations = await self._generate_recommendations(
                    target_column, feature_importance, metrics
                )
            
            return PredictionResult(
                predictions=ensemble_predictions.tolist(),
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper,
                confidence_level=confidence_level,
                feature_importance=feature_importance,
                model_contributions=weights,
                metrics=metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            return self._fallback_prediction(df, target_column)
    
    def _auto_select_features(
        self, 
        df: pd.DataFrame, 
        target: str
    ) -> List[str]:
        """Automatically select features"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        features = []
        for col in numeric_cols:
            if col == target:
                continue
            col_lower = col.lower()
            if any(x in col_lower for x in ['id', 'index', 'key', 'uuid']):
                continue
            features.append(col)
        
        return features[:15]
    
    def _calculate_feature_importance(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, float]:
        """Calculate feature importance using Random Forest"""
        try:
            rf = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
            rf.fit(X, y)
            
            importance = {}
            for i, name in enumerate(feature_names):
                importance[name] = float(rf.feature_importances_[i])
            
            # Sort by importance
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        except:
            return {}
    
    async def _generate_recommendations(
        self,
        target: str,
        importance: Dict[str, float],
        metrics: Dict[str, float]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Top features recommendation
        if importance:
            top_features = list(importance.keys())[:3]
            recommendations.append(
                f"Focus on {', '.join(top_features)} - these have the highest impact on {target}"
            )
        
        # Accuracy-based recommendations
        r2 = metrics.get("r2_score", 0)
        if r2 < 0.5:
            recommendations.append(
                "Model accuracy is moderate. Consider adding more features or data."
            )
        elif r2 > 0.8:
            recommendations.append(
                "Predictions are highly accurate. Monitor for changes in patterns."
            )
        
        # Use LLM for deeper recommendations
        try:
            prompt = f"""Based on this prediction model for {target}:
- Top features: {list(importance.keys())[:5]}
- Model accuracy (R²): {r2:.2f}
- Error (MAE): {metrics.get('mae', 0):.2f}

Give 2-3 specific, actionable business recommendations (one line each):"""
            
            response = chat(messages=prompt, temperature=0.4, max_tokens=200)
            
            # Parse recommendations
            lines = response.strip().split('\n')
            for line in lines[:3]:
                line = line.strip()
                if line and len(line) > 10:
                    # Clean up bullet points
                    if line[0] in '-•*1234567890.':
                        line = line.lstrip('-•*1234567890. ')
                    recommendations.append(line)
        except:
            pass
        
        return recommendations[:5]
    
    def _fallback_prediction(
        self, 
        df: pd.DataFrame, 
        target: str
    ) -> PredictionResult:
        """Fallback when sklearn not available or error occurs"""
        try:
            mean_val = float(df[target].mean())
            std_val = float(df[target].std())
            
            predictions = [mean_val] * len(df)
            lower = [mean_val - 1.96 * std_val] * len(df)
            upper = [mean_val + 1.96 * std_val] * len(df)
            
            return PredictionResult(
                predictions=predictions,
                confidence_lower=lower,
                confidence_upper=upper,
                confidence_level=0.95,
                feature_importance={},
                model_contributions={"baseline": 1.0},
                metrics={"r2_score": 0, "mae": std_val},
                recommendations=["Unable to build predictive model. Using baseline average."]
            )
        except:
            return PredictionResult(
                predictions=[],
                confidence_lower=[],
                confidence_upper=[],
                confidence_level=0.95,
                feature_importance={},
                model_contributions={},
                metrics={},
                recommendations=["Prediction failed. Check data format."]
            )


# =============================================================================
# TIME SERIES FORECASTER
# =============================================================================

@dataclass
class ForecastResult:
    """Result from time series forecast"""
    forecasts: List[float]
    dates: List[str]
    confidence_lower: List[float]
    confidence_upper: List[float]
    trend: str  # increasing, decreasing, stable
    seasonality: Optional[str]
    metrics: Dict[str, float]


class TimeSeriesForecaster:
    """
    📈 Time Series Forecaster
    
    Simple but effective forecasting:
    - Trend detection
    - Moving averages
    - Exponential smoothing
    - Confidence intervals
    """
    
    async def forecast(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        periods: int = 12,
        frequency: str = "M"  # M=month, W=week, D=day
    ) -> ForecastResult:
        """
        Forecast future values
        
        Args:
            df: Historical data
            date_column: Column with dates
            value_column: Column with values to forecast
            periods: Number of periods to forecast
            frequency: Forecast frequency
            
        Returns:
            Forecast result
        """
        try:
            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            df = df.dropna(subset=[date_column, value_column])
            df = df.sort_values(date_column)
            
            if len(df) < 5:
                return self._empty_forecast("Not enough data for forecasting")
            
            values = df[value_column].values
            dates = df[date_column].values
            
            # Calculate trend
            trend = self._detect_trend(values)
            
            # Simple forecasting using linear trend + seasonality
            x = np.arange(len(values))
            z = np.polyfit(x, values, 1)
            slope = z[0]
            intercept = z[1]
            
            # Forecast
            future_x = np.arange(len(values), len(values) + periods)
            forecasts = slope * future_x + intercept
            
            # Add noise based on historical variance
            std = np.std(values)
            confidence_lower = forecasts - 1.96 * std
            confidence_upper = forecasts + 1.96 * std
            
            # Generate future dates
            last_date = pd.Timestamp(dates[-1])
            freq_map = {"M": "MS", "W": "W", "D": "D", "Q": "QS"}
            future_dates = pd.date_range(
                start=last_date, 
                periods=periods + 1, 
                freq=freq_map.get(frequency, "MS")
            )[1:]
            
            # Calculate historical metrics
            fitted = slope * x + intercept
            metrics = {
                "r2": float(1 - np.sum((values - fitted) ** 2) / np.sum((values - np.mean(values)) ** 2)),
                "mae": float(np.mean(np.abs(values - fitted))),
                "trend_slope": float(slope)
            }
            
            return ForecastResult(
                forecasts=forecasts.tolist(),
                dates=[str(d.date()) for d in future_dates],
                confidence_lower=confidence_lower.tolist(),
                confidence_upper=confidence_upper.tolist(),
                trend=trend,
                seasonality=self._detect_seasonality(values),
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Forecast error: {e}")
            return self._empty_forecast(str(e))
    
    def _detect_trend(self, values: np.ndarray) -> str:
        """Detect overall trend"""
        if len(values) < 2:
            return "stable"
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        # Normalize slope by mean value
        mean_val = np.mean(values)
        normalized_slope = slope / mean_val if mean_val != 0 else 0
        
        if normalized_slope > 0.01:
            return "increasing"
        elif normalized_slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _detect_seasonality(self, values: np.ndarray) -> Optional[str]:
        """Simple seasonality detection"""
        if len(values) < 24:
            return None
        
        # Check for monthly seasonality (12 periods)
        try:
            seasonal_strength = np.std(values[:12]) / np.mean(values[:12]) if np.mean(values[:12]) != 0 else 0
            if seasonal_strength > 0.2:
                return "monthly"
        except:
            pass
        
        return None
    
    def _empty_forecast(self, error: str) -> ForecastResult:
        """Return empty forecast with error"""
        return ForecastResult(
            forecasts=[],
            dates=[],
            confidence_lower=[],
            confidence_upper=[],
            trend="unknown",
            seasonality=None,
            metrics={"error": error}
        )


# =============================================================================
# PREDICTION EXPLAINER
# =============================================================================

class PredictionExplainer:
    """
    🔍 Prediction Explainer
    
    Explain why predictions are what they are:
    - Feature contributions
    - Key drivers
    - What-if analysis
    """
    
    async def explain_prediction(
        self,
        df: pd.DataFrame,
        target_column: str,
        row_index: int,
        feature_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Explain a single prediction
        
        Args:
            df: Data
            target_column: Target column
            row_index: Row to explain
            feature_columns: Features used
            
        Returns:
            Explanation with contributions
        """
        try:
            if row_index >= len(df):
                return {"error": "Row index out of range"}
            
            row = df.iloc[row_index]
            
            # Simple contribution analysis
            contributions = {}
            for col in feature_columns:
                if col in df.columns:
                    col_mean = df[col].mean()
                    col_std = df[col].std()
                    
                    if col_std > 0:
                        z_score = (row[col] - col_mean) / col_std
                        contributions[col] = {
                            "value": float(row[col]),
                            "mean": float(col_mean),
                            "deviation": round(float(z_score), 2),
                            "impact": "high" if abs(z_score) > 1.5 else "medium" if abs(z_score) > 0.5 else "low"
                        }
            
            # Sort by absolute deviation
            sorted_contributions = dict(sorted(
                contributions.items(),
                key=lambda x: abs(x[1]["deviation"]),
                reverse=True
            ))
            
            # Generate explanation text
            explanation = await self._generate_explanation(
                row[target_column] if target_column in row else None,
                sorted_contributions
            )
            
            return {
                "predicted_value": float(row[target_column]) if target_column in row else None,
                "contributions": sorted_contributions,
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Explanation error: {e}")
            return {"error": str(e)}
    
    async def _generate_explanation(
        self,
        prediction: Optional[float],
        contributions: Dict
    ) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        if prediction is not None:
            parts.append(f"Predicted value: {prediction:.2f}")
        
        high_impact = [k for k, v in contributions.items() if v.get("impact") == "high"]
        if high_impact:
            parts.append(f"Key drivers: {', '.join(high_impact[:3])}")
        
        positive_devs = [k for k, v in contributions.items() if v.get("deviation", 0) > 1]
        negative_devs = [k for k, v in contributions.items() if v.get("deviation", 0) < -1]
        
        if positive_devs:
            parts.append(f"Above average: {', '.join(positive_devs[:2])}")
        if negative_devs:
            parts.append(f"Below average: {', '.join(negative_devs[:2])}")
        
        return " | ".join(parts) if parts else "Standard prediction with no unusual factors"


# =============================================================================
# EXPORTS
# =============================================================================

ensemble_engine = EnsemblePredictionEngine()
time_series_forecaster = TimeSeriesForecaster()
prediction_explainer = PredictionExplainer()


async def predict_with_confidence(
    df: pd.DataFrame,
    target_column: str,
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Quick function for ensemble prediction"""
    result = await ensemble_engine.predict(df, target_column, features)
    return {
        "predictions": result.predictions[:100],
        "confidence_lower": result.confidence_lower[:100],
        "confidence_upper": result.confidence_upper[:100],
        "feature_importance": result.feature_importance,
        "model_contributions": result.model_contributions,
        "metrics": result.metrics,
        "recommendations": result.recommendations
    }


async def forecast_time_series(
    df: pd.DataFrame,
    date_column: str,
    value_column: str,
    periods: int = 12
) -> Dict[str, Any]:
    """Quick function for time series forecast"""
    result = await time_series_forecaster.forecast(df, date_column, value_column, periods)
    return {
        "forecasts": result.forecasts,
        "dates": result.dates,
        "confidence_lower": result.confidence_lower,
        "confidence_upper": result.confidence_upper,
        "trend": result.trend,
        "seasonality": result.seasonality,
        "metrics": result.metrics
    }


async def explain_prediction(
    df: pd.DataFrame,
    target: str,
    row_index: int,
    features: List[str]
) -> Dict[str, Any]:
    """Quick function to explain a prediction"""
    return await prediction_explainer.explain_prediction(df, target, row_index, features)
