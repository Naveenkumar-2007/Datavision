"""
🤖 ML PREDICTION MCP v2.0
=========================

REAL ML predictions using trained AutoML models!
NOT LLM-generated guesses - actual sklearn/XGBoost predictions.

Features:
- Uses trained model from automl_engine
- Extracts features from natural language
- Makes REAL predictions
- Generates Plotly charts based on ML results
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Import AutoML engine
try:
    from ml.automl_engine import automl_engine
    AUTOML_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    logger.warning("AutoML engine not available")


class MLPredictionMCP:
    """
    MCP for REAL ML Predictions using trained models.
    
    This makes ACTUAL predictions using sklearn/XGBoost - not LLM guesses!
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load trained model"""
        if not AUTOML_AVAILABLE:
            return False
        
        try:
            self.model_loaded = automl_engine.load(self.user_id)
            if self.model_loaded:
                logger.info(f"✅ ML Model loaded: {automl_engine.model_name}")
            return self.model_loaded
        except Exception as e:
            logger.error(f"Model load error: {e}")
            return False
    
    def predict_from_query(self, query: str, df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Make REAL prediction from natural language query.
        
        Returns actual ML prediction, not LLM guess!
        """
        result = {
            "success": False,
            "prediction": None,
            "confidence": None,
            "explanation": "",
            "chart": None,
            "is_real_ml": False
        }
        
        if not self.model_loaded:
            result["explanation"] = "⚠️ No trained model. Go to AutoML → Train a model first!"
            return result
        
        # Extract features from query
        feature_values = self._extract_features(query, df)
        
        if not feature_values and df is not None and not df.empty:
            # Use sample row if no features extracted
            sample = df.iloc[0].to_dict()
            feature_values = {k: v for k, v in sample.items() 
                             if k in automl_engine.feature_columns}
        
        if not feature_values:
            # Show what features are needed
            result["explanation"] = self._get_feature_prompt()
            result["success"] = True
            return result
        
        # Make REAL prediction using trained model
        try:
            pred = automl_engine.predict(feature_values)
            
            result["success"] = True
            result["is_real_ml"] = True
            result["prediction"] = pred.get("prediction")
            result["confidence"] = pred.get("confidence")
            result["probability"] = pred.get("probability")
            result["model"] = pred.get("model")
            
            # Build response with real prediction
            result["explanation"] = self._format_real_prediction(
                prediction=result["prediction"],
                confidence=result["confidence"],
                feature_values=feature_values
            )
            
            # Generate Plotly chart based on prediction
            result["chart"] = self._generate_prediction_chart(
                prediction=result["prediction"],
                confidence=result["confidence"],
                feature_values=feature_values
            )
            
            logger.info(f"✅ Real ML Prediction: {result['prediction']}")
            
        except Exception as e:
            result["explanation"] = f"Prediction error: {str(e)}"
            logger.error(f"Prediction error: {e}")
        
        return result
    
    def _extract_features(self, query: str, df: pd.DataFrame = None) -> Dict[str, Any]:
        """Extract feature values from query"""
        values = {}
        query_lower = query.lower()
        
        if not self.model_loaded:
            return values
        
        features = automl_engine.feature_columns
        metadata = {m['name']: m for m in automl_engine.feature_metadata}
        
        # Pattern 1: explicit "feature=value"
        pattern = r'(\w+)\s*[=:]\s*([\d.]+|\w+)'
        for feat, val in re.findall(pattern, query):
            for real_feat in features:
                if feat.lower() in real_feat.lower() or real_feat.lower() in feat.lower():
                    try:
                        values[real_feat] = float(val)
                    except:
                        values[real_feat] = val
                    break
        
        # Pattern 2: Common patterns
        patterns = [
            (r'age\s*(?:is|of|:)?\s*(\d+)', ['age']),
            (r'(\d+)\s*(?:years?\s*)?old', ['age']),
            (r'(\d+)\s*(?:years?|yrs?)\s*(?:experience|exp)', ['experience', 'years', 'time']),
            (r'ejection\s*(?:fraction)?\s*(?:is|of|:)?\s*(\d+)', ['ejection_fraction', 'ejection']),
            (r'creatinine\s*(?:is|of|:)?\s*([\d.]+)', ['serum_creatinine', 'creatinine']),
            (r'sodium\s*(?:is|of|:)?\s*(\d+)', ['serum_sodium', 'sodium']),
            (r'platelets?\s*(?:is|of|:)?\s*(\d+)', ['platelets']),
            (r'(?:has\s+)?diabetes\s*(?:is|=)?\s*(\d|yes|no|true|false)?', ['diabetes']),
            (r'(?:has\s+)?anaemia\s*(?:is|=)?\s*(\d|yes|no|true|false)?', ['anaemia']),
            (r'(?:has\s+)?high\s*(?:blood\s*)?pressure\s*(?:is|=)?\s*(\d|yes|no|true|false)?', ['high_blood_pressure']),
            (r'smok(?:ing|er|e)?\s*(?:is|=)?\s*(\d|yes|no|true|false)?', ['smoking']),
            (r'sex\s*(?:is|=)?\s*(\d|male|female|m|f)', ['sex']),
        ]
        
        for pattern, keywords in patterns:
            match = re.search(pattern, query_lower)
            if match:
                raw_val = match.group(1) if match.groups() else '1'
                # Convert yes/no/true/false to 1/0
                if raw_val in ['yes', 'true', 'male', 'm']:
                    val = 1
                elif raw_val in ['no', 'false', 'female', 'f']:
                    val = 0
                elif raw_val is None:
                    val = 1  # Mentioned = has it
                else:
                    try:
                        val = float(raw_val)
                    except:
                        val = 1
                
                for kw in keywords:
                    for feat in features:
                        if kw in feat.lower():
                            values[feat] = val
                            break
        
        # Fill remaining features with defaults from metadata
        for feat in features:
            if feat not in values:
                meta = metadata.get(feat, {})
                if meta.get('type') == 'numeric':
                    values[feat] = meta.get('default', meta.get('mean', 0))
                elif meta.get('type') == 'categorical':
                    values[feat] = meta.get('default', 0)
        
        return values
    
    def _format_real_prediction(self, prediction: Any, confidence: float, feature_values: Dict) -> str:
        """Format the real ML prediction result"""
        
        task = automl_engine.task_type
        model = automl_engine.model_name
        target = automl_engine.target_column
        
        is_classification = 'classification' in task
        
        # Prediction label
        if is_classification:
            pred_label = "Class" if prediction in [0, 1, '0', '1'] else "Prediction"
            pred_emoji = "✅" if str(prediction) == "0" else "⚠️"
        else:
            pred_label = target
            pred_emoji = "📊"
        
        response = f"""## 🤖 REAL ML Prediction

{pred_emoji} **{pred_label}**: **{prediction}**
"""
        
        if confidence:
            conf_pct = int(confidence * 100)
            conf_bar = "🟢" if conf_pct > 70 else "🟡" if conf_pct > 50 else "🔴"
            response += f"**Confidence**: {conf_bar} {conf_pct}%\n"
        
        response += f"""
---

### Model Info
- **Model**: {model}
- **Task**: {task.replace('_', ' ').title()}
- **Target**: {target}

### Features Used
"""
        # Show top 8 features
        for i, (feat, val) in enumerate(list(feature_values.items())[:8]):
            if isinstance(val, float):
                response += f"- **{feat}**: {val:,.2f}\n"
            else:
                response += f"- **{feat}**: {val}\n"
        
        response += """
---
*🤖 This is a REAL ML prediction using your trained model, not an LLM guess!*
"""
        return response
    
    def _generate_prediction_chart(self, prediction: Any, confidence: float, feature_values: Dict) -> str:
        """Generate Plotly chart JSON for the prediction"""
        
        is_classification = 'classification' in automl_engine.task_type
        
        if is_classification:
            # Classification: Prediction probability pie chart
            prob = confidence if confidence else 0.8
            chart = {
                "data": [{
                    "type": "pie",
                    "values": [prob * 100, (1 - prob) * 100],
                    "labels": [f"Class {prediction}", f"Not Class {prediction}"],
                    "marker": {
                        "colors": ["#22c55e" if str(prediction) == "0" else "#ef4444", "#e5e7eb"]
                    },
                    "hole": 0.4,
                    "textinfo": "label+percent"
                }],
                "layout": {
                    "title": f"Prediction: {automl_engine.target_column} = {prediction}",
                    "showlegend": True,
                    "paper_bgcolor": "#f8f9fa",
                    "font": {"color": "#1f2937"}
                }
            }
        else:
            # Regression: Feature values bar chart
            features = list(feature_values.keys())[:6]
            values = [feature_values[f] for f in features]
            
            chart = {
                "data": [{
                    "type": "bar",
                    "x": features,
                    "y": values,
                    "marker": {
                        "color": "#3b82f6"
                    }
                }],
                "layout": {
                    "title": f"Prediction: {automl_engine.target_column} = {prediction}",
                    "xaxis": {"title": "Features"},
                    "yaxis": {"title": "Values"},
                    "paper_bgcolor": "#f8f9fa",
                    "font": {"color": "#1f2937"}
                }
            }
        
        return f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    def _get_feature_prompt(self) -> str:
        """Get prompt showing required features"""
        response = f"""## 🤖 ML Model Ready!

**Model**: {automl_engine.model_name}
**Task**: {automl_engine.task_type.replace('_', ' ').title()}
**Predicting**: {automl_engine.target_column}

---

### To make a prediction, provide values like:

"""
        for meta in automl_engine.feature_metadata[:8]:
            name = meta['name']
            if meta['type'] == 'numeric':
                default = meta.get('default', 50)
                response += f"- **{name}**: {default:.0f}\n"
            elif meta['type'] == 'categorical':
                opts = meta.get('options', [])[:3]
                response += f"- **{name}**: {', '.join(str(o) for o in opts)}\n"
        
        response += f"""
---

### Example Query:
"Predict {automl_engine.target_column} for age=60, ejection_fraction=35"
"""
        return response
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if not self.model_loaded:
            return {"trained": False}
        
        return {
            "trained": True,
            "model_name": automl_engine.model_name,
            "task_type": automl_engine.task_type,
            "target_column": automl_engine.target_column,
            "features": automl_engine.feature_columns,
            "n_features": len(automl_engine.feature_columns)
        }


def run_ml_prediction(query: str, user_id: str, df: pd.DataFrame = None) -> Dict[str, Any]:
    """Quick function for ML prediction"""
    mcp = MLPredictionMCP(user_id)
    result = mcp.predict_from_query(query, df)
    
    # Combine explanation with chart
    if result.get("chart"):
        result["explanation"] += result["chart"]
    
    return result


def get_ml_model_context(user_id: str) -> str:
    """Get ML model context for LLM prompts"""
    mcp = MLPredictionMCP(user_id)
    info = mcp.get_model_info()
    
    if not info.get("trained"):
        return ""
    
    return f"""
[TRAINED ML MODEL AVAILABLE]
- Model: {info['model_name']}
- Task: {info['task_type']}
- Target: {info['target_column']}
- Features: {info['n_features']}

Use this model for predictions instead of guessing!
"""
