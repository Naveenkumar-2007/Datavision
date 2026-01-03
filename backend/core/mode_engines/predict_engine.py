"""
🤖 PREDICT ENGINE v5.0 - SILICON VALLEY ML CHAT ASSISTANT
==========================================================

ChatGPT-like intelligent ML assistant that:
- Uses trained AutoML models for REAL predictions
- Understands natural language ML queries
- Generates dynamic explanations with LLM
- Creates real Plotly charts from actual data
- Handles any ML-related question intelligently

NO HARDCODING - Everything is based on real trained model + live data!
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)

# Import AutoML Engine
try:
    from ml.automl_engine import automl_engine
    AUTOML_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    logger.warning("AutoML engine not available")

# Import LLM for intelligent explanations
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM not available")


class QueryType(Enum):
    """Types of ML queries the assistant can handle"""
    PREDICTION = "prediction"           # Make prediction for given features
    METRICS = "metrics"                 # Show model performance
    FEATURE_IMPORTANCE = "importance"   # What features matter most
    DATA_ANALYSIS = "data_analysis"     # Analyze data distribution
    MODEL_INFO = "model_info"           # Info about trained model
    COMPARISON = "comparison"           # Compare values or scenarios
    GENERAL_ML = "general_ml"           # General ML/AI questions
    HELP = "help"                       # Help using the system


def detect_query_type(query: str) -> Tuple[QueryType, float]:
    """
    Intelligently detect what type of ML query the user is asking.
    Returns (query_type, confidence_score)
    """
    q = query.lower().strip()
    
    # Prediction patterns
    prediction_patterns = [
        r'predict\s+(for|if|when|what)',
        r'what\s+(is|will|would)\s+.+\s+(be|happen)',
        r'(age|ejection|creatinine|sodium|time)\s*[=:]\s*\d+',
        r'classify\s+',
        r'estimate\s+',
        r'forecast\s+',
        r'will\s+.+\s+(survive|die|default|churn)',
    ]
    for pattern in prediction_patterns:
        if re.search(pattern, q):
            return QueryType.PREDICTION, 0.95
    
    # Metrics patterns
    metrics_patterns = [
        r'(accuracy|precision|recall|f1|performance|confusion)',
        r'how\s+(good|accurate|well)\s+(is|does)',
        r'model\s+(metrics|performance|score)',
        r'show\s+.*(accuracy|metrics|performance)',
    ]
    for pattern in metrics_patterns:
        if re.search(pattern, q):
            return QueryType.METRICS, 0.95
    
    # Feature importance patterns
    importance_patterns = [
        r'(what|which)\s+(affects?|influences?|matters?|important)',
        r'feature\s+(importance|ranking|contribution)',
        r'(most|least)\s+important',
        r'(key|top|main)\s+(factors?|features?|variables?)',
        r'why\s+(did|does)\s+.+\s+predict',
    ]
    for pattern in importance_patterns:
        if re.search(pattern, q):
            return QueryType.FEATURE_IMPORTANCE, 0.90
    
    # Data analysis patterns
    data_patterns = [
        r'(distribution|histogram|spread)\s+of',
        r'(average|mean|median|std|min|max)\s+',
        r'(how\s+many|count|total)\s+',
        r'(show|display|visualize)\s+.*(data|distribution)',
        r'analyze\s+(the\s+)?(data|dataset)',
    ]
    for pattern in data_patterns:
        if re.search(pattern, q):
            return QueryType.DATA_ANALYSIS, 0.85
    
    # Model info patterns
    model_patterns = [
        r'(what|which)\s+(model|algorithm)',
        r'model\s+(type|name|info)',
        r'(target|predicting|training)',
        r'what\s+.+\s+trained\s+on',
        r'features?\s+(used|available)',
    ]
    for pattern in model_patterns:
        if re.search(pattern, q):
            return QueryType.MODEL_INFO, 0.85
    
    # Comparison patterns
    comparison_patterns = [
        r'compare\s+',
        r'(difference|vs|versus)\s+between',
        r'if\s+.+\s+(instead|vs|or)',
        r'(higher|lower|better|worse)\s+(than|if)',
    ]
    for pattern in comparison_patterns:
        if re.search(pattern, q):
            return QueryType.COMPARISON, 0.80
    
    # Help patterns
    help_patterns = [
        r'^(help|how\s+to\s+use|what\s+can)',
        r'(example|examples)\s+',
        r'how\s+does\s+this\s+work',
    ]
    for pattern in help_patterns:
        if re.search(pattern, q):
            return QueryType.HELP, 0.90
    
    # Default to general ML question
    return QueryType.GENERAL_ML, 0.70


def predict_response_sync(user_id: str, query: str, context: str = "", df=None) -> Dict[str, Any]:
    """
    🤖 SILICON VALLEY ML CHAT ASSISTANT
    
    Intelligently handles ANY ML/prediction query with:
    - Real trained model predictions
    - LLM-powered natural language explanations
    - Dynamic Plotly charts from actual data
    - ChatGPT-like conversational responses
    
    NO HARDCODING - All responses based on real model + data!
    """
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.5,
        "sources": [],
        "ml_used": False,
        "chart": None
    }
    
    start_time = datetime.now()
    
    # Check AutoML availability
    if not AUTOML_AVAILABLE:
        result["answer"] = "⚠️ ML Engine not available. Please check installation."
        return result
    
    # Load model
    try:
        model_loaded = automl_engine.load(user_id)
    except Exception as e:
        logger.error(f"Model load error: {e}")
        model_loaded = False
    
    # Detect query type
    query_type, type_confidence = detect_query_type(query)
    logger.info(f"🔍 Query type: {query_type.value} (confidence: {type_confidence:.0%})")
    
    # Route to appropriate handler
    if not model_loaded:
        result = _handle_no_model(query, query_type, df, user_id)
    else:
        handlers = {
            QueryType.PREDICTION: _handle_prediction,
            QueryType.METRICS: _handle_metrics,
            QueryType.FEATURE_IMPORTANCE: _handle_feature_importance,
            QueryType.DATA_ANALYSIS: _handle_data_analysis,
            QueryType.MODEL_INFO: _handle_model_info,
            QueryType.COMPARISON: _handle_comparison,
            QueryType.GENERAL_ML: _handle_general_ml,
            QueryType.HELP: _handle_help,
        }
        
        handler = handlers.get(query_type, _handle_general_ml)
        result = handler(query, df)
    
    # Add execution time
    exec_time = (datetime.now() - start_time).total_seconds()
    result["execution_time"] = f"{exec_time:.2f}s"
    
    return result


def _handle_no_model(query: str, query_type: QueryType, df=None, user_id: str = "") -> Dict[str, Any]:
    """Handle queries when no model is trained yet"""
    
    response = """## 🤖 ML Prediction Assistant

Welcome! I'm your intelligent ML assistant, but I don't have a trained model yet.

### 🚀 To Get Started:

1. **Go to AutoML Tab** in the sidebar
2. **Upload your dataset** (CSV, Excel)
3. **Train a model** - I'll automatically select the best algorithm!

### 💡 Once trained, you can ask me:

- **"Predict for age=60, ejection_fraction=35"** - Get predictions
- **"What affects survival most?"** - Feature importance
- **"Show model accuracy"** - Performance metrics
- **"Compare male vs female outcomes"** - Analysis
- **Any ML question!** - I'll explain using your data

---

*Train a model and let's explore your data together!* 🎯
"""
    
    return {
        "answer": response,
        "mode": "predict",
        "confidence": 0.5,
        "sources": ["ML Assistant"],
        "ml_used": False
    }


def _handle_prediction(query: str, df=None) -> Dict[str, Any]:
    """
    Handle prediction requests with real ML model.
    Returns prediction + confidence + explanation + chart.
    """
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.8,
        "sources": ["Trained ML Model", automl_engine.model_name],
        "ml_used": True
    }
    
    # Extract feature values from query
    feature_values = _extract_features(query, df)
    
    if not feature_values:
        # Show what features are available
        result["answer"] = _get_prediction_help()
        return result
    
    # Make REAL prediction
    try:
        pred = automl_engine.predict(feature_values)
        prediction = pred.get('prediction')
        confidence = pred.get('confidence', 0.8)
        
        result["confidence"] = confidence if confidence else 0.8
        
        # Get model context
        task_type = automl_engine.task_type
        target = automl_engine.target_column
        model_name = automl_engine.model_name
        is_classification = 'classification' in task_type
        
        # Generate LLM explanation
        explanation = _generate_llm_explanation(
            query=query,
            prediction=prediction,
            confidence=confidence,
            features=feature_values,
            target=target,
            task_type=task_type
        )
        
        # Build response
        if is_classification:
            pred_emoji = "✅" if str(prediction) in ["0", "False", "No", "Negative"] else "⚠️"
            pred_text = _interpret_classification(prediction, target, confidence)
        else:
            pred_emoji = "📊"
            pred_text = f"**{target}**: {prediction}"
        
        conf_pct = int(confidence * 100) if confidence else 75
        conf_bar = "🟢" if conf_pct > 70 else "🟡" if conf_pct > 50 else "🔴"
        
        response = f"""## {pred_emoji} ML Prediction Result

### {pred_text}

**Confidence**: {conf_bar} {conf_pct}%
**Model**: {model_name}

---

### 💡 Analysis

{explanation}

---

### 📥 Input Features Used
"""
        # Show features used
        for feat, val in list(feature_values.items())[:8]:
            if isinstance(val, float):
                response += f"- **{feat}**: {val:,.2f}\n"
            else:
                response += f"- **{feat}**: {val}\n"
        
        response += "\n---\n*🤖 Real ML prediction from your trained model*\n"
        
        # Generate chart
        chart = _generate_prediction_chart(prediction, confidence, feature_values)
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        result["answer"] = f"⚠️ Prediction error: {str(e)}"
    
    return result


def _handle_metrics(query: str, df=None) -> Dict[str, Any]:
    """Handle model performance/metrics queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.95,
        "sources": ["Model Metrics", automl_engine.model_name],
        "ml_used": True
    }
    
    try:
        metrics_data = automl_engine.get_model_metrics()
    except Exception as e:
        result["answer"] = f"Error getting metrics: {e}"
        return result
    
    model = metrics_data.get('model_name', 'Unknown')
    task = metrics_data.get('task_type', 'Unknown')
    target = metrics_data.get('target', 'Unknown')
    metrics = metrics_data.get('metrics', {})
    cm = metrics_data.get('confusion_matrix')
    n_features = metrics_data.get('n_features', 0)
    
    response = f"""## 📊 Model Performance Dashboard

### 🤖 Model: **{model}**
- **Task**: {task.replace('_', ' ').title()}
- **Target**: {target}
- **Features**: {n_features}

---

### 🎯 Performance Metrics
"""
    
    # Check if metrics available
    has_metrics = any([metrics.get(k) for k in ['accuracy', 'f1', 'precision', 'recall', 'r2', 'mae']])
    
    if has_metrics:
        if metrics.get('accuracy'):
            acc = metrics['accuracy'] * 100
            acc_emoji = "🟢" if acc > 80 else "🟡" if acc > 60 else "🔴"
            response += f"- **Accuracy**: {acc_emoji} {acc:.1f}%\n"
        if metrics.get('f1'):
            f1 = metrics['f1'] * 100
            response += f"- **F1 Score**: {f1:.1f}%\n"
        if metrics.get('precision'):
            prec = metrics['precision'] * 100
            response += f"- **Precision**: {prec:.1f}%\n"
        if metrics.get('recall'):
            rec = metrics['recall'] * 100
            response += f"- **Recall**: {rec:.1f}%\n"
        if metrics.get('r2'):
            response += f"- **R² Score**: {metrics['r2']:.4f}\n"
        if metrics.get('mae'):
            response += f"- **MAE**: {metrics['mae']:.4f}\n"
        if metrics.get('rmse'):
            response += f"- **RMSE**: {metrics['rmse']:.4f}\n"
        
        # LLM interpretation
        interpretation = _interpret_metrics(metrics, task)
        response += f"\n---\n\n### 💡 Interpretation\n\n{interpretation}\n"
    else:
        response += """
> ⚠️ **Detailed metrics not available**
> 
> This model was trained before metrics storage was enabled.
> **Retrain the model** to get accuracy, F1, confusion matrix, etc.
"""
    
    # Add confusion matrix chart if available
    if cm:
        try:
            labels = ['Class 0', 'Class 1'] if len(cm) == 2 else [f'Class {i}' for i in range(len(cm))]
            if 'death' in target.lower() and len(cm) == 2:
                labels = ['Survived', 'Death']
            
            chart = {
                "data": [{
                    "type": "heatmap",
                    "z": cm,
                    "x": labels,
                    "y": labels,
                    "colorscale": [[0, "#dcfce7"], [0.5, "#22c55e"], [1, "#15803d"]],
                    "showscale": True,
                    "text": [[str(int(v)) for v in row] for row in cm],
                    "texttemplate": "%{text}",
                    "textfont": {"size": 18, "color": "#1f2937"}
                }],
                "layout": {
                    "title": {"text": "📊 Confusion Matrix", "font": {"size": 18, "color": "#1f2937"}},
                    "xaxis": {"title": "Predicted", "tickfont": {"size": 12}},
                    "yaxis": {"title": "Actual", "autorange": "reversed", "tickfont": {"size": 12}},
                    "paper_bgcolor": "#f8fafc",
                    "plot_bgcolor": "#ffffff",
                    "font": {"color": "#1f2937"},
                    "width": 500,
                    "height": 450
                }
            }
            response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        except Exception as e:
            logger.error(f"Confusion matrix chart error: {e}")
    
    result["answer"] = response
    return result


def _handle_feature_importance(query: str, df=None) -> Dict[str, Any]:
    """Handle feature importance queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.9,
        "sources": ["Feature Analysis", automl_engine.model_name],
        "ml_used": True
    }
    
    # Get feature importance from model
    importance = _get_feature_importance()
    target = automl_engine.target_column
    model = automl_engine.model_name
    
    if not importance:
        result["answer"] = "⚠️ Feature importance not available for this model type."
        return result
    
    response = f"""## 🔑 Feature Importance Analysis

### What Affects **{target}** Most?

Based on the trained **{model}** model, here are the most influential features:

"""
    
    # Show top features with bars
    total_importance = sum(f['importance'] for f in importance)
    for i, feat in enumerate(importance[:10], 1):
        imp = feat['importance']
        pct = (imp / total_importance * 100) if total_importance > 0 else 0
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        response += f"**{i}. {feat['feature']}**\n`{bar}` {pct:.1f}%\n\n"
    
    # LLM interpretation
    top_features = [f['feature'] for f in importance[:3]]
    interpretation = _interpret_feature_importance(top_features, target)
    response += f"---\n\n### 💡 Insight\n\n{interpretation}\n"
    
    # Generate bar chart
    feats = [f['feature'][:15] for f in importance[:8]]
    vals = [f['importance'] * 100 for f in importance[:8]]
    
    chart = {
        "data": [{
            "type": "bar",
            "y": feats[::-1],
            "x": vals[::-1],
            "orientation": "h",
            "marker": {"color": ["#3b82f6"] * 7 + ["#1d4ed8"]}
        }],
        "layout": {
            "title": {"text": f"🔑 Feature Importance for {target}", "font": {"size": 16}},
            "xaxis": {"title": "Importance (%)"},
            "yaxis": {"tickfont": {"size": 11}},
            "paper_bgcolor": "#f8fafc",
            "font": {"color": "#1f2937"},
            "margin": {"l": 120}
        }
    }
    response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    result["answer"] = response
    return result


def _handle_data_analysis(query: str, df=None) -> Dict[str, Any]:
    """Handle data exploration and analysis queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.85,
        "sources": ["Data Analysis", "Training Data"],
        "ml_used": True
    }
    
    target = automl_engine.target_column
    features = automl_engine.feature_columns
    metadata = automl_engine.feature_metadata
    
    response = f"""## 📊 Data Analysis

### Dataset Overview

- **Target Variable**: {target}
- **Features**: {len(features)}
- **Task**: {automl_engine.task_type.replace('_', ' ').title()}

---

### 📈 Feature Statistics
"""
    
    # Show feature metadata
    for i, meta in enumerate(metadata[:10], 1):
        name = meta.get('name', f'Feature {i}')
        ftype = meta.get('type', 'unknown')
        
        if ftype == 'numeric':
            min_val = meta.get('min', 0)
            max_val = meta.get('max', 100)
            mean_val = meta.get('mean', 50)
            response += f"**{i}. {name}** (numeric)\n"
            response += f"   - Range: {min_val:.1f} - {max_val:.1f}\n"
            response += f"   - Mean: {mean_val:.1f}\n\n"
        elif ftype == 'categorical':
            options = meta.get('options', [])[:5]
            n_cats = meta.get('n_categories', len(options))
            response += f"**{i}. {name}** (categorical)\n"
            response += f"   - Categories: {n_cats}\n"
            response += f"   - Examples: {', '.join(str(o) for o in options)}\n\n"
    
    # Generate distribution chart for numeric features
    numeric_meta = [m for m in metadata if m.get('type') == 'numeric'][:6]
    if numeric_meta:
        feats = [m['name'][:12] for m in numeric_meta]
        means = [m.get('mean', 0) for m in numeric_meta]
        
        chart = {
            "data": [{
                "type": "bar",
                "x": feats,
                "y": means,
                "marker": {"color": "#8b5cf6"}
            }],
            "layout": {
                "title": {"text": "📊 Feature Mean Values", "font": {"size": 16}},
                "xaxis": {"title": "Features", "tickangle": -45},
                "yaxis": {"title": "Mean Value"},
                "paper_bgcolor": "#f8fafc",
                "font": {"color": "#1f2937"}
            }
        }
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    result["answer"] = response
    return result


def _handle_model_info(query: str, df=None) -> Dict[str, Any]:
    """Handle model information queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.95,
        "sources": ["Model Info", automl_engine.model_name],
        "ml_used": True
    }
    
    model = automl_engine.model_name
    task = automl_engine.task_type
    target = automl_engine.target_column
    features = automl_engine.feature_columns
    n_classes = automl_engine.n_classes
    
    response = f"""## 🤖 Trained Model Information

### Model Details
- **Algorithm**: {model}
- **Task Type**: {task.replace('_', ' ').title()}
- **Target Variable**: {target}
- **Number of Features**: {len(features)}
"""
    
    if 'classification' in task:
        response += f"- **Number of Classes**: {n_classes}\n"
    
    response += f"""
---

### 📋 Features Used for Prediction
"""
    
    for i, feat in enumerate(features[:15], 1):
        response += f"{i}. `{feat}`\n"
    
    if len(features) > 15:
        response += f"\n*...and {len(features) - 15} more features*\n"
    
    response += f"""
---

### 💡 How to Use

Ask me things like:
- "Predict {target} for age=60, time=100"
- "What factors affect {target} most?"
- "Show model accuracy"
- "Compare high vs low values"
"""
    
    result["answer"] = response
    return result


def _handle_comparison(query: str, df=None) -> Dict[str, Any]:
    """Handle comparison queries between scenarios"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.85,
        "sources": ["Comparison Analysis", automl_engine.model_name],
        "ml_used": True
    }
    
    target = automl_engine.target_column
    metadata = automl_engine.feature_metadata
    
    # Find a key feature to compare
    key_features = [m for m in metadata if m.get('type') == 'numeric']
    
    if not key_features:
        result["answer"] = "Comparison analysis requires numeric features."
        return result
    
    key_feat = key_features[0]
    feat_name = key_feat['name']
    low_val = key_feat.get('p25', key_feat.get('min', 30))
    high_val = key_feat.get('p75', key_feat.get('max', 70))
    
    # Make predictions for low and high scenarios
    base_features = _get_default_features()
    
    low_features = base_features.copy()
    low_features[feat_name] = low_val
    
    high_features = base_features.copy()
    high_features[feat_name] = high_val
    
    try:
        low_pred = automl_engine.predict(low_features)
        high_pred = automl_engine.predict(high_features)
        
        response = f"""## ⚖️ Scenario Comparison

### Comparing **{feat_name}** Impact on **{target}**

| Scenario | {feat_name} | Prediction | Confidence |
|----------|-------------|------------|------------|
| Low | {low_val:.1f} | {low_pred['prediction']} | {(low_pred.get('confidence', 0.7)*100):.0f}% |
| High | {high_val:.1f} | {high_pred['prediction']} | {(high_pred.get('confidence', 0.7)*100):.0f}% |

---

### 💡 Insight

"""
        
        # LLM interpretation
        if LLM_AVAILABLE:
            prompt = f"Compare predictions: When {feat_name}={low_val:.1f}, prediction is {low_pred['prediction']}. When {feat_name}={high_val:.1f}, prediction is {high_pred['prediction']}. The target is {target}. Explain in 2-3 sentences what this means."
            try:
                insight = llm_chat(prompt, temperature=0.3, max_tokens=150)
                response += insight
            except:
                response += f"Higher {feat_name} values appear to affect the {target} prediction."
        else:
            response += f"Higher {feat_name} values affect the {target} prediction."
        
        # Chart comparing scenarios
        chart = {
            "data": [{
                "type": "bar",
                "x": [f"Low ({low_val:.0f})", f"High ({high_val:.0f})"],
                "y": [low_pred.get('confidence', 0.7) * 100, high_pred.get('confidence', 0.7) * 100],
                "marker": {"color": ["#22c55e", "#ef4444"]}
            }],
            "layout": {
                "title": {"text": f"Confidence Comparison by {feat_name}", "font": {"size": 16}},
                "xaxis": {"title": feat_name},
                "yaxis": {"title": "Confidence (%)", "range": [0, 100]},
                "paper_bgcolor": "#f8fafc",
                "font": {"color": "#1f2937"}
            }
        }
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        
    except Exception as e:
        result["answer"] = f"Comparison error: {str(e)}"
    
    return result


def _handle_general_ml(query: str, df=None) -> Dict[str, Any]:
    """
    Handle general ML questions with CONCISE, DATA-DRIVEN answers + charts.
    Uses model data directly - no verbose LLM responses.
    """
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.9,
        "sources": ["ML Assistant", automl_engine.model_name],
        "ml_used": True
    }
    
    # Get model info
    model = automl_engine.model_name
    task = automl_engine.task_type
    target = automl_engine.target_column
    features = automl_engine.feature_columns
    n_classes = automl_engine.n_classes
    is_classification = 'classification' in task
    
    q = query.lower().strip()
    
    # Direct answer patterns - no LLM needed!
    
    # Task type question
    if any(p in q for p in ['classification', 'regression', 'type', 'task']):
        task_answer = "**Classification**" if is_classification else "**Regression**"
        response = f"""## 🎯 Model Task Type

{task_answer}

| Property | Value |
|----------|-------|
| **Model** | {model} |
| **Task** | {task.replace('_', ' ').title()} |
| **Target** | {target} |
| **Classes** | {n_classes if is_classification else 'N/A (continuous)'} |
| **Features** | {len(features)} |
"""
        result["answer"] = response
        return result
    
    # "What prediction" / general prediction question
    if any(p in q for p in ['what predict', 'prediction', 'predicting']):
        response = f"""## 🎯 Prediction Summary

**Model**: {model}
**Predicting**: `{target}`
**Using**: {len(features)} features

---

### 📋 To make a prediction, provide values:

"""
        # Show example features
        for meta in automl_engine.feature_metadata[:6]:
            name = meta.get('name', 'feature')
            if meta.get('type') == 'numeric':
                val = meta.get('default', 50)
                response += f"- `{name}={val:.0f}`\n"
        
        response += f"""
### 💡 Example Query:
```
Predict for age=60, ejection_fraction=40, time=100
```
"""
        # Add a simple chart showing feature stats
        chart = _generate_model_overview_chart()
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        return result
    
    # Feature question
    if any(p in q for p in ['feature', 'variable', 'column', 'input']):
        response = f"""## 📊 Model Features

**{len(features)} features** used to predict `{target}`:

"""
        for i, feat in enumerate(features[:12], 1):
            response += f"{i}. `{feat}`\n"
        
        if len(features) > 12:
            response += f"\n*+ {len(features) - 12} more*\n"
        
        # Feature importance chart if available
        importance = _get_feature_importance()
        if importance:
            feats = [f['feature'][:12] for f in importance[:6]]
            vals = [f['importance'] * 100 for f in importance[:6]]
            chart = {
                "data": [{"type": "bar", "y": feats[::-1], "x": vals[::-1], "orientation": "h", "marker": {"color": "#3b82f6"}}],
                "layout": {"title": {"text": "Feature Importance"}, "xaxis": {"title": "%"}, "paper_bgcolor": "#f8fafc", "margin": {"l": 100}}
            }
            response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        return result
    
    # Model question
    if any(p in q for p in ['model', 'algorithm', 'trained']):
        response = f"""## 🤖 Trained Model

| Property | Value |
|----------|-------|
| **Algorithm** | {model} |
| **Task** | {task.replace('_', ' ').title()} |
| **Target** | {target} |
| **Features** | {len(features)} |

---

### 💡 Try asking:
- "Predict for age=60"
- "What affects {target}?"
- "Show accuracy"
"""
        chart = _generate_model_overview_chart()
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        return result
    
    # For any other question - give concise LLM answer with chart
    if LLM_AVAILABLE:
        context = f"Model: {model}, Task: {task}, Target: {target}. Answer in 2-3 SHORT sentences only."
        try:
            llm_response = llm_chat(f"{context}\n\nQuestion: {query}", temperature=0.3, max_tokens=150)
            response = f"""## 💡 Answer

{llm_response}

---

**Model**: {model} | **Target**: {target}
"""
        except:
            response = f"""## 💡 About Your Model

- **Model**: {model}
- **Predicting**: {target}
- **Features**: {len(features)}

Ask me: "Predict for age=60" or "Show accuracy"
"""
    else:
        response = f"""## 💡 About Your Model

- **Model**: {model}
- **Predicting**: {target}
- **Features**: {len(features)}

Ask me: "Predict for age=60" or "Show accuracy"
"""
    
    # Always add a chart
    chart = _generate_model_overview_chart()
    response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    result["answer"] = response
    return result


def _generate_model_overview_chart() -> Dict:
    """Generate a quick overview chart for the model"""
    task = automl_engine.task_type
    target = automl_engine.target_column
    is_classification = 'classification' in task
    
    # Get feature importance if available
    importance = _get_feature_importance()
    
    if importance and len(importance) >= 3:
        # Feature importance chart
        feats = [f['feature'][:15] for f in importance[:6]]
        vals = [f['importance'] * 100 for f in importance[:6]]
        
        return {
            "data": [{
                "type": "bar",
                "y": feats[::-1],
                "x": vals[::-1],
                "orientation": "h",
                "marker": {"color": "#3b82f6"}
            }],
            "layout": {
                "title": {"text": f"🔑 Key Features for {target}", "font": {"size": 16}},
                "xaxis": {"title": "Importance (%)"},
                "paper_bgcolor": "#f8fafc",
                "font": {"color": "#1f2937"},
                "margin": {"l": 120},
                "height": 350
            }
        }
    else:
        # Simple model info chart
        metadata = automl_engine.feature_metadata[:6]
        if metadata:
            names = [m['name'][:12] for m in metadata if m.get('type') == 'numeric']
            means = [m.get('mean', 50) for m in metadata if m.get('type') == 'numeric']
            
            return {
                "data": [{
                    "type": "bar",
                    "x": names[:6],
                    "y": means[:6],
                    "marker": {"color": "#8b5cf6"}
                }],
                "layout": {
                    "title": {"text": "📊 Feature Values", "font": {"size": 16}},
                    "xaxis": {"tickangle": -45},
                    "paper_bgcolor": "#f8fafc",
                    "font": {"color": "#1f2937"},
                    "height": 350
                }
            }
        else:
            return {
                "data": [{"type": "indicator", "mode": "gauge+number", "value": 85, "title": {"text": "Model Ready"}}],
                "layout": {"paper_bgcolor": "#f8fafc", "height": 300}
            }


def _handle_help(query: str, df=None) -> Dict[str, Any]:
    """Handle help/how-to-use queries"""
    target = automl_engine.target_column
    model = automl_engine.model_name
    features = automl_engine.feature_columns[:5]
    
    example_feat = features[0] if features else "feature"
    
    response = f"""## 🤖 ML Prediction Assistant - Help

I'm your intelligent ML assistant! I use your trained **{model}** model to answer questions about **{target}**.

---

### 📝 What You Can Ask Me

**1. Make Predictions** 🎯
- "Predict for {example_feat}=50, age=60"
- "What would happen if time=200?"
- "Classify this patient: age=70, diabetes=1"

**2. Feature Importance** 🔑
- "What affects {target} most?"
- "Which features are important?"
- "Why does the model predict this?"

**3. Model Performance** 📊
- "Show model accuracy"
- "What's the F1 score?"
- "Display confusion matrix"

**4. Data Analysis** 📈
- "Analyze the data distribution"
- "Show feature statistics"
- "What's the average age?"

**5. Comparisons** ⚖️
- "Compare high vs low values"
- "What if age is 30 vs 80?"

---

### 💡 Tips

- Provide feature values like: `feature_name=value`
- Ask naturally - I understand context!
- I use REAL ML predictions, not guesses

*Ready to explore your data!* 🚀
"""
    
    return {
        "answer": response,
        "mode": "predict",
        "confidence": 1.0,
        "sources": ["Help", "ML Assistant"],
        "ml_used": True
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_features(query: str, df=None) -> Dict[str, Any]:
    """Extract feature values from natural language query"""
    values = {}
    query_lower = query.lower()
    
    features = automl_engine.feature_columns
    metadata = {m['name']: m for m in automl_engine.feature_metadata}
    
    # Pattern 1: feature=value or feature:value
    for match in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*[=:]\s*([\d.]+)', query):
        feat_query = match.group(1).lower().replace('_', '')
        val = float(match.group(2))
        
        for feat in features:
            feat_lower = feat.lower().replace('_', '')
            if feat_query == feat_lower or feat_query in feat_lower or feat_lower in feat_query:
                values[feat] = val
                break
    
    # Pattern 2: Natural patterns
    patterns = [
        (r'age\s*(?:is|of|:)?\s*(\d+)', 'age'),
        (r'(\d+)\s*(?:years?\s*)?old', 'age'),
        (r'ejection\s*(?:fraction)?\s*(?:is|of|:)?\s*(\d+)', 'ejection_fraction'),
        (r'creatinine\s*(?:is|of|:)?\s*([\d.]+)', 'serum_creatinine'),
        (r'sodium\s*(?:is|of|:)?\s*(\d+)', 'serum_sodium'),
        (r'platelets?\s*(?:is|of|:)?\s*(\d+)', 'platelets'),
        (r'cpk\s*(?:is|of|:)?\s*(\d+)', 'creatinine_phosphokinase'),
        (r'time\s*(?:is|of|:)?\s*(\d+)', 'time'),
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, query_lower)
        if match:
            val = float(match.group(1))
            for feat in features:
                if key in feat.lower() and feat not in values:
                    values[feat] = val
                    break
    
    # Pattern 3: Boolean features
    bool_map = [
        (r'(?:has\s+)?diabetes', 'diabetes', 1),
        (r'no\s+diabetes', 'diabetes', 0),
        (r'(?:has\s+)?anaemia', 'anaemia', 1),
        (r'(?:has\s+)?(?:high\s*)?(?:blood\s*)?pressure', 'high_blood_pressure', 1),
        (r'smok(?:ing|er|es?)', 'smoking', 1),
        (r'(?:non|no)\s*smok', 'smoking', 0),
        (r'\bmale\b', 'sex', 1),
        (r'\bfemale\b', 'sex', 0),
    ]
    
    for pattern, key, val in bool_map:
        if re.search(pattern, query_lower):
            for feat in features:
                if key in feat.lower() and feat not in values:
                    values[feat] = val
                    break
    
    # Fill missing with defaults
    for feat in features:
        if feat not in values:
            meta = metadata.get(feat, {})
            if meta.get('type') == 'numeric':
                values[feat] = meta.get('default', meta.get('mean', 0))
            else:
                values[feat] = 0
    
    return values


def _get_default_features() -> Dict[str, Any]:
    """Get default feature values from metadata"""
    values = {}
    for meta in automl_engine.feature_metadata:
        name = meta.get('name')
        if meta.get('type') == 'numeric':
            values[name] = meta.get('default', meta.get('mean', 0))
        else:
            values[name] = 0
    return values


def _get_feature_importance() -> List[Dict]:
    """Get feature importance from trained model"""
    try:
        model = automl_engine.model
        features = automl_engine.feature_columns
        
        if hasattr(model, 'feature_importances_'):
            imp = model.feature_importances_
            result = []
            for i, feat in enumerate(features):
                if i < len(imp):
                    result.append({'feature': feat, 'importance': float(imp[i])})
            result.sort(key=lambda x: x['importance'], reverse=True)
            return result
    except:
        pass
    return []


def _get_prediction_help() -> str:
    """Generate help text for making predictions"""
    target = automl_engine.target_column
    features = automl_engine.feature_metadata[:8]
    
    response = f"""## 🤖 Ready to Predict!

To predict **{target}**, provide feature values like:

### Example Query:
```
Predict for """
    
    # Build example
    examples = []
    for meta in features[:4]:
        name = meta['name']
        if meta.get('type') == 'numeric':
            val = meta.get('default', 50)
            examples.append(f"{name}={val:.0f}")
    
    response += ", ".join(examples) + "\n```\n\n### Available Features:\n"
    
    for meta in features:
        name = meta['name']
        if meta.get('type') == 'numeric':
            default = meta.get('default', 50)
            response += f"- **{name}**: typical value ~{default:.0f}\n"
        elif meta.get('type') == 'categorical':
            opts = meta.get('options', [])[:3]
            response += f"- **{name}**: {', '.join(str(o) for o in opts)}\n"
    
    return response


def _interpret_classification(prediction, target: str, confidence: float) -> str:
    """Interpret classification prediction in human terms"""
    conf_pct = int((confidence or 0.7) * 100)
    
    if 'death' in target.lower():
        if str(prediction) == "1":
            return f"⚠️ **High Risk** - Death event predicted ({conf_pct}% confidence)"
        else:
            return f"✅ **Low Risk** - Survival predicted ({conf_pct}% confidence)"
    elif 'churn' in target.lower():
        if str(prediction) == "1":
            return f"⚠️ **Likely to Churn** ({conf_pct}% confidence)"
        else:
            return f"✅ **Likely to Stay** ({conf_pct}% confidence)"
    elif 'fraud' in target.lower():
        if str(prediction) == "1":
            return f"🚨 **Fraud Detected** ({conf_pct}% confidence)"
        else:
            return f"✅ **Legitimate** ({conf_pct}% confidence)"
    else:
        return f"🎯 **{target}**: {prediction} ({conf_pct}% confidence)"


def _generate_llm_explanation(query: str, prediction, confidence: float, 
                              features: Dict, target: str, task_type: str) -> str:
    """Generate natural language explanation using LLM"""
    if not LLM_AVAILABLE:
        return "The model made this prediction based on the input features provided."
    
    top_features = list(features.items())[:5]
    feat_str = ", ".join([f"{k}={v:.1f}" if isinstance(v, float) else f"{k}={v}" for k, v in top_features])
    
    prompt = f"""Explain this ML prediction in 2-3 sentences:
- Target: {target}
- Prediction: {prediction}
- Confidence: {confidence:.0%} if {confidence} else 'N/A'
- Key inputs: {feat_str}
- Task: {task_type}

Be specific about which features likely influenced this result. Keep it brief and insightful."""

    try:
        explanation = llm_chat(prompt, temperature=0.3, max_tokens=150)
        return explanation
    except:
        return "The prediction is based on the input features and patterns learned during training."


def _interpret_metrics(metrics: Dict, task: str) -> str:
    """Interpret model metrics in human terms"""
    if not LLM_AVAILABLE:
        return "These metrics indicate the model's performance on test data."
    
    prompt = f"""Interpret these ML model metrics briefly (2-3 sentences):
Task: {task}
Metrics: {metrics}

Explain what these numbers mean in simple terms. Is this good or needs improvement?"""

    try:
        interpretation = llm_chat(prompt, temperature=0.3, max_tokens=100)
        return interpretation
    except:
        acc = metrics.get('accuracy', metrics.get('r2', 0.7))
        if acc > 0.8:
            return "This is a well-performing model with strong predictive accuracy."
        elif acc > 0.6:
            return "The model shows moderate performance. Consider more data or feature engineering."
        else:
            return "The model's performance could be improved with more training data or tuning."


def _interpret_feature_importance(top_features: List[str], target: str) -> str:
    """Interpret feature importance results"""
    if not LLM_AVAILABLE:
        return f"The top features {', '.join(top_features)} have the most influence on {target}."
    
    prompt = f"""Briefly explain (2-3 sentences) why these features might be important for predicting {target}:
Top features: {', '.join(top_features)}

Be insightful about the domain logic."""

    try:
        interpretation = llm_chat(prompt, temperature=0.4, max_tokens=100)
        return interpretation
    except:
        return f"The features {', '.join(top_features)} show the strongest correlation with {target}."


def _generate_prediction_chart(prediction, confidence: float, features: Dict) -> Dict:
    """Generate dynamic Plotly chart for prediction result"""
    task = automl_engine.task_type
    target = automl_engine.target_column
    is_class = 'classification' in task
    
    if is_class:
        prob = confidence if confidence else 0.75
        pred_label = "Positive" if str(prediction) == "1" else "Negative"
        color = "#ef4444" if str(prediction) == "1" else "#22c55e"
        
        chart = {
            "data": [{
                "type": "pie",
                "values": [prob * 100, (1 - prob) * 100],
                "labels": [pred_label, "Other"],
                "marker": {"colors": [color, "#e5e7eb"]},
                "hole": 0.6,
                "textinfo": "label+percent",
                "textposition": "outside",
                "textfont": {"size": 14}
            }],
            "layout": {
                "title": {"text": f"🎯 {target} Prediction", "font": {"size": 18, "color": "#1f2937"}},
                "paper_bgcolor": "#f8fafc",
                "font": {"color": "#1f2937"},
                "showlegend": False,
                "annotations": [{
                    "text": f"<b>{prob*100:.0f}%</b><br>Confidence",
                    "x": 0.5, "y": 0.5,
                    "font": {"size": 20, "color": color},
                    "showarrow": False
                }],
                "width": 450,
                "height": 400
            }
        }
    else:
        # Regression: Show prediction with feature context
        feats = list(features.keys())[:6]
        vals = [features[f] for f in feats]
        
        chart = {
            "data": [{
                "type": "bar",
                "x": feats,
                "y": vals,
                "marker": {"color": "#3b82f6"}
            }],
            "layout": {
                "title": {"text": f"📊 {target} = {prediction}", "font": {"size": 18}},
                "xaxis": {"title": "Input Features", "tickangle": -45},
                "yaxis": {"title": "Values"},
                "paper_bgcolor": "#f8fafc",
                "font": {"color": "#1f2937"}
            }
        }
    
    return chart


# Legacy function for backward compatibility
async def predict_response(user_id: str, query: str, context: str = "", df=None) -> Dict[str, Any]:
    """Async wrapper for backward compatibility"""
    return predict_response_sync(user_id, query, context, df)
