"""
PREDICT ENGINE - ML-Powered Forecasting System
===============================================

🤖 REAL MACHINE LEARNING - Not Just LLM Prompts!

This engine uses ACTUAL scikit-learn algorithms:
- Linear Regression
- Polynomial Regression  
- Random Forest
- Gradient Boosting

Features:
✅ Real ML predictions with confidence intervals
✅ Feature importance analysis
✅ Matplotlib/Seaborn visualizations (base64 embedded)
✅ Cross-validation for accuracy
✅ Auto-algorithm selection

YOUR DATA ONLY - Never uses external benchmarks!
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.llm import chat

logger = logging.getLogger(__name__)


class PredictEngine:
    """
    🤖 ML-POWERED PREDICT ENGINE
    
    This is NOT an LLM wrapper - it uses REAL scikit-learn!
    
    Capabilities:
    - Real ML algorithms (Linear, Polynomial, Forest, Gradient)
    - 95% Confidence Intervals (statistical)
    - Feature Importance (which columns drive prediction)
    - Matplotlib/Seaborn visualizations
    - Cross-validation for accuracy estimation
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.ml_predictor = None
        self.ml_visualizer = None
        self._init_ml_components()
    
    def _init_ml_components(self):
        """Initialize ML components lazily"""
        try:
            from core.ml_predictor import MLPredictor
            from core.ml_visualizer import MLVisualizer
            self.ml_predictor = MLPredictor()
            self.ml_visualizer = MLVisualizer()
            logger.info("✅ ML components loaded successfully")
        except ImportError as e:
            logger.warning(f"ML components not available: {e}")
    
    def _detect_target_column(self, df: pd.DataFrame, query: str) -> Optional[str]:
        """Auto-detect which column to predict based on query"""
        if df is None or df.empty:
            return None
        
        query_lower = query.lower()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Look for query keywords matching column names
        for col in numeric_cols:
            col_lower = col.lower()
            if col_lower in query_lower or any(word in col_lower for word in query_lower.split()):
                return col
        
        # Common target keywords
        target_keywords = ['sales', 'revenue', 'profit', 'amount', 'total', 'count', 'value', 'price']
        for col in numeric_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in target_keywords):
                return col
        
        # Return first numeric column
        return numeric_cols[0] if numeric_cols else None
    
    async def process(
        self,
        query: str,
        context: str = "",
        df: pd.DataFrame = None,
        forecast_periods: int = 6
    ) -> Dict[str, Any]:
        """
        Process a prediction query with REAL ML.
        
        Flow:
        1. Detect target column from query
        2. Run ML prediction (scikit-learn)
        3. Generate matplotlib visualizations
        4. Add LLM interpretation
        5. Return comprehensive result
        """
        
        start_time = datetime.now()
        logger.info(f"🤖 ML PREDICT ENGINE: Processing '{query[:50]}...'")
        
        ml_result = None
        ml_charts = []
        
        # Run ML prediction if we have data
        if df is not None and not df.empty and self.ml_predictor:
            try:
                # Detect target column
                target_col = self._detect_target_column(df, query)
                logger.info(f"🎯 Target column detected: {target_col}")
                
                # Run ML prediction
                ml_result = self.ml_predictor.predict(
                    df=df,
                    target_column=target_col,
                    forecast_periods=forecast_periods
                )
                
                if ml_result.success:
                    logger.info(f"✅ ML Prediction successful: {ml_result.algorithm}, R2={ml_result.metrics.get('r2_score', 'N/A')}")
                    
                    # Generate visualizations
                    if self.ml_visualizer:
                        # Get historical values
                        if target_col and target_col in df.columns:
                            historical = df[target_col].dropna().tolist()
                        else:
                            historical = df.select_dtypes(include=[np.number]).iloc[:, 0].tolist()
                        
                        # Create prediction summary chart
                        summary_chart = self.ml_visualizer.create_prediction_summary(
                            historical=historical,
                            predictions=ml_result.predictions,
                            lower_bound=ml_result.lower_bound,
                            upper_bound=ml_result.upper_bound,
                            importance=ml_result.feature_importance,
                            title=f"ML Forecast: {target_col or 'Values'}"
                        )
                        if summary_chart.get('image'):
                            ml_charts.append(summary_chart)
                        
                        # Create correlation heatmap if multiple numeric columns
                        numeric_cols = df.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) >= 3:
                            corr_chart = self.ml_visualizer.create_correlation_heatmap(
                                df=df,
                                title="Variable Correlations"
                            )
                            if corr_chart.get('image'):
                                ml_charts.append(corr_chart)
                
            except Exception as e:
                logger.error(f"ML Prediction error: {e}")
        
        # Build response with ML results
        if ml_result and ml_result.success:
            formatted = self._format_ml_response(ml_result, query, context)
            confidence = ml_result.confidence_score
        else:
            # Fallback to LLM-only prediction
            formatted = await self._llm_prediction(query, context)
            confidence = 0.5
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "answer": formatted,
            "mode": "predict",
            "confidence": confidence,
            "execution_time": f"{execution_time:.2f}s",
            "features_used": self._get_features_used(ml_result),
            "sources": ["Your Data Patterns", "ML Analysis"]
        }
        
        # Add ML-specific info
        if ml_result and ml_result.success:
            result["ml_algorithm"] = ml_result.algorithm
            result["ml_metrics"] = ml_result.metrics
            result["accuracy_tiers"] = {
                "tier1": f"High Confidence ({int(ml_result.confidence_score * 100)}%)",
                "tier2": f"Predictions: {ml_result.predictions}",
                "tier3": f"Range: {ml_result.lower_bound} to {ml_result.upper_bound}"
            }
        
        # Add ML charts
        if ml_charts:
            result["ml_charts"] = ml_charts
        
        return result
    
    def _format_ml_response(self, ml_result, query: str, context: str) -> str:
        """Format ML prediction result into readable response"""
        
        trend_emoji = {"up": "📈", "down": "📉", "stable": "➡️"}.get(ml_result.trend, "📊")
        conf_pct = int(ml_result.confidence_score * 100)
        
        # Build response
        response = f"""🤖 **ML-Powered Prediction Analysis**

{trend_emoji} **{ml_result.insight}**

---

## 🎯 Forecast Results

| Period | Prediction | 95% CI Lower | 95% CI Upper |
|--------|-----------|--------------|--------------|"""
        
        for i, (pred, low, high) in enumerate(zip(ml_result.predictions, ml_result.lower_bound, ml_result.upper_bound), 1):
            response += f"\n| Period {i} | **{pred:,.2f}** | {low:,.2f} | {high:,.2f} |"
        
        response += f"""

## 📊 Model Performance
- **Algorithm**: {ml_result.algorithm.replace('_', ' ').title()}
- **Confidence**: {conf_pct}%
- **R² Score**: {ml_result.metrics.get('r2_score', 'N/A')}
- **RMSE**: {ml_result.metrics.get('rmse', 'N/A')}
- **Data Points**: {ml_result.metrics.get('data_points', 'N/A')}"""
        
        # Feature importance if available
        if ml_result.feature_importance:
            response += "\n\n## 🔑 Key Drivers"
            for feature, importance in sorted(ml_result.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]:
                bar_len = int(importance * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                response += f"\n- **{feature}**: {bar} {importance:.1%}"
        
        response += f"""

---
🤖 *Powered by scikit-learn | Real ML - Not just LLM prompts!*"""
        
        return response
    
    async def _llm_prediction(self, query: str, context: str) -> str:
        """Fallback LLM-only prediction when ML isn't possible"""
        
        predict_prompt = f"""You are DataVision Predict - a forecasting expert.

⚠️ CRITICAL - STRICT DATA GROUNDING:
1. ONLY use the user's personal data below for predictions
2. NEVER use industry averages or external benchmarks
3. Base ALL forecasts on actual patterns in THIS data

📊 USER'S PERSONAL DATA:
{context[:5000] if context else "No data available. Please upload files with historical data."}

🔮 PREDICTION REQUEST: {query}

Provide a clear, data-grounded prediction with:
1. **High Confidence** prediction (what the data strongly suggests)
2. **Range** (optimistic to pessimistic based on data variance)
3. **Key factors** that could affect the outcome

⚠️ All numbers must come from the actual data - never fabricate!"""

        try:
            response = chat(predict_prompt, temperature=0.4, max_tokens=1500)
            return f"""🔮 **Prediction Analysis**

{response}

---
⚠️ *Note: ML algorithms require numerical data. This is an LLM-based interpretation.*"""
        except Exception as e:
            return f"Prediction error: {str(e)}"
    
    def _get_features_used(self, ml_result) -> List[str]:
        """Get list of features used"""
        features = ["Data Grounding"]
        if ml_result and ml_result.success:
            features.extend([
                f"ML: {ml_result.algorithm}",
                "95% Confidence Intervals",
                "Feature Importance",
                "Cross-Validation"
            ])
        else:
            features.extend(["LLM Analysis", "3-Tier Forecasting"])
        return features


async def predict_response(
    user_id: str,
    query: str,
    context: str = "",
    df = None
) -> Dict[str, Any]:
    """Quick function for prediction response"""
    engine = PredictEngine(user_id)
    return await engine.process(query, context, df)


def predict_response_sync(
    user_id: str,
    query: str,
    context: str = ""
) -> str:
    """Synchronous prediction response"""
    
    prompt = f"""You are DataVision Predict - a forecasting expert.

⚠️ CRITICAL: Use ONLY the user's data below. NEVER industry benchmarks!

📊 USER'S HISTORICAL DATA:
{context[:3500] if context else "Need user data to predict. Ask them to upload files."}

🔮 PREDICT: {query}

Provide THREE tiers of prediction based ONLY on data above:
1. **High Confidence** (80%+): [prediction based on strong trends in THIS data]
2. **Moderate** (50-80%): [assumes THIS data's patterns continue]  
3. **Scenarios**: [best/worst case using THIS data's growth rates]

⚠️ All numbers must come from the data above - never use external benchmarks.

YOUR PREDICTION:"""

    try:
        response = chat(prompt, temperature=0.4, max_tokens=1500)
        return f"🔮 **Prediction** (Based on YOUR data)\n\n{response}"
    except Exception as e:
        return f"Prediction error: {str(e)}"
