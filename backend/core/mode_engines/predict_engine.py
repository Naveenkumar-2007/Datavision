"""
🤖 PREDICT ENGINE v6.0 - SENIOR AIML ENGINEER ASSISTANT
=========================================================

A ChatGPT-like intelligent ML assistant designed by a Senior AIML Engineer.

Features:
- 🧠 Senior AIML Engineer level explanations
- 📊 Live integration with trained ML model charts
- 🎯 Real predictions from your trained AutoML model
- 💡 Statistical insights and technical depth
- 🔗 Connects with ML Predictions page for charts
- 🌐 Conversational memory within session

NO HARDCODING - Everything based on real trained model + actual data!

Author: DataVision Team
Version: 6.0.0
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import re
import json
import os

logger = logging.getLogger(__name__)

# =============================================================================
# IMPORTS & DEPENDENCIES
# =============================================================================

# AutoML Engine
try:
    from ml.automl_engine import automl_engine
    AUTOML_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    logger.warning("AutoML engine not available")

# LLM for intelligent explanations
try:
    from core.llm import chat as llm_chat
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM not available")

# Chart Generator
try:
    from ml.chart_generator import generate_ml_charts
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

# Intelligent Query Processor (Claude-style)
try:
    from core.intelligent_processor import IntelligentQueryProcessor, intelligent_process
    INTELLIGENT_PROCESSOR_AVAILABLE = True
except ImportError:
    INTELLIGENT_PROCESSOR_AVAILABLE = False


# =============================================================================
# QUERY TYPES - What the user is asking about
# =============================================================================

class QueryType(Enum):
    """All types of ML queries the assistant can handle"""
    # Core ML Operations
    PREDICTION = "prediction"               # "Predict for age=60"
    BATCH_PREDICTION = "batch_prediction"   # "Predict all rows"
    
    # Model Understanding
    MODEL_INFO = "model_info"               # "What model is trained?"
    METRICS = "metrics"                     # "Show accuracy/F1"
    FEATURE_IMPORTANCE = "importance"       # "What features matter?"
    FEATURE_SPECIFIC = "feature_specific"   # "How does age affect..."
    
    # Data Analysis
    DATA_ANALYSIS = "data_analysis"         # "Analyze the data"
    DATA_DISTRIBUTION = "distribution"      # "Show distribution of X"
    CORRELATION = "correlation"             # "What correlates with..."
    
    # Visualizations - Direct Chart Requests
    SHOW_CHART = "show_chart"               # "Show confusion matrix"
    CONFUSION_MATRIX = "confusion_matrix"   # Direct confusion matrix
    ROC_CURVE = "roc_curve"                 # ROC curve
    PRECISION_RECALL = "precision_recall"   # PR curve
    ACTUAL_VS_PREDICTED = "actual_vs_pred"  # Actual vs Predicted
    
    # Advanced Analysis
    WHAT_IF = "what_if"                     # Scenario analysis
    EXPLAIN = "explain"                     # "Why did model predict X?"
    SHAP = "shap"                           # SHAP explanation
    THRESHOLD = "threshold"                 # Threshold tuning
    
    # Meta
    COMPARISON = "comparison"               # Compare scenarios
    DASHBOARD = "dashboard"                 # Full dashboard
    HELP = "help"                           # How to use
    GENERAL_ML = "general_ml"               # General ML questions


# =============================================================================
# CONVERSATION MEMORY - Remember context within session
# =============================================================================

@dataclass
class ConversationContext:
    """Stores conversation context for multi-turn interactions"""
    last_prediction: Dict = None
    last_features: Dict = None
    last_query_type: QueryType = None
    chart_shown: List[str] = None
    session_start: datetime = None
    
    def __post_init__(self):
        self.chart_shown = []
        self.session_start = datetime.now()


# Session memory - persists during conversation
_session_memory: Dict[str, ConversationContext] = {}

def get_session(user_id: str) -> ConversationContext:
    """Get or create session for user"""
    if user_id not in _session_memory:
        _session_memory[user_id] = ConversationContext()
    return _session_memory[user_id]


# =============================================================================
# SENIOR AIML ENGINEER PROMPTS
# =============================================================================

SENIOR_AIML_SYSTEM_PROMPT = """You are a Senior AI/ML Engineer at a top tech company.
When explaining ML concepts:
- Be precise with technical terminology
- Include statistical context (p-values, confidence intervals when relevant)
- Give actionable recommendations
- Acknowledge model limitations
- Use analogies for complex concepts
- Be concise but thorough

Your explanations should sound like a Staff ML Engineer in a code review, 
not a marketing person. Be real about what the model can and cannot do."""


def generate_senior_explanation(
    topic: str,
    context: Dict[str, Any],
    question: str = ""
) -> str:
    """Generate Senior AIML Engineer quality explanation"""
    if not LLM_AVAILABLE:
        return _fallback_explanation(topic, context)
    
    prompt = f"""{SENIOR_AIML_SYSTEM_PROMPT}

Context:
- Model: {context.get('model_name', 'Unknown')}
- Task: {context.get('task_type', 'Unknown')}
- Target: {context.get('target', 'Unknown')}
- Key Metrics: {context.get('metrics', {})}

Topic to explain: {topic}
User question: {question}

Provide a concise but technically accurate explanation (2-4 sentences).
Focus on what a data scientist would want to know."""

    try:
        return llm_chat(prompt, temperature=0.3, max_tokens=200)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return _fallback_explanation(topic, context)


def _fallback_explanation(topic: str, context: Dict) -> str:
    """Fallback when LLM is unavailable"""
    target = context.get('target', 'the outcome')
    model = context.get('model_name', 'the model')
    
    explanations = {
        'prediction': f"The {model} predicts {target} based on the input features. Higher confidence indicates stronger prediction certainty.",
        'metrics': f"These metrics show how well {model} generalizes to unseen data. F1 balances precision and recall.",
        'importance': f"Feature importance shows which inputs have the most predictive power for {target}.",
        'default': f"This analysis helps understand how {model} makes predictions for {target}."
    }
    return explanations.get(topic, explanations['default'])


# =============================================================================
# QUERY DETECTION - Understand what user is asking
# =============================================================================

def detect_query_type(query: str, user_id: str = "") -> Tuple[QueryType, float, Dict]:
    """
    Intelligently detect query type with confidence and extracted parameters.
    Returns: (QueryType, confidence, extracted_params)
    """
    q = query.lower().strip()
    params = {}
    
    # === CHART REQUESTS (High Priority) ===
    chart_patterns = {
        QueryType.CONFUSION_MATRIX: [
            r'confusion\s*matrix', r'confusion\s+matrix', r'show\s+confusion'
        ],
        QueryType.ROC_CURVE: [
            r'roc\s*curve', r'roc\s+curve', r'receiver\s+operating'
        ],
        QueryType.PRECISION_RECALL: [
            r'precision.+recall', r'pr\s+curve', r'precision\s+recall\s+curve'
        ],
        QueryType.ACTUAL_VS_PREDICTED: [
            r'actual\s*(vs?|versus)\s*predicted', r'predicted\s+vs\s+actual',
            r'scatter\s+plot', r'residual'
        ],
        QueryType.SHOW_CHART: [
            r'show\s+(me\s+)?(the\s+)?(chart|graph|plot|visualization)',
            r'display\s+(the\s+)?(chart|graph)',
            r'(feature\s+)?importance\s+(chart|plot)',
            r'(class\s+)?distribution\s+(chart|plot)',
            r'calibration\s+(curve|plot)',
            r'correlation\s+heatmap'
        ]
    }
    
    for qtype, patterns in chart_patterns.items():
        for pattern in patterns:
            if re.search(pattern, q):
                # Extract specific chart name if present
                chart_keywords = ['confusion', 'roc', 'precision', 'recall', 'feature', 
                                 'importance', 'distribution', 'calibration', 'correlation']
                for kw in chart_keywords:
                    if kw in q:
                        params['chart_name'] = kw
                        break
                return qtype, 0.95, params
    
    # === PREDICTION REQUESTS ===
    prediction_patterns = [
        r'predict\s+(for|if|when|what|with)',
        r'what\s+(is|will|would)\s+.+\s+(be|happen|predict)',
        r'classify\s+',
        r'estimate\s+',
        r'will\s+.+\s+(survive|die|default|churn|happen)',
        r'[a-z_]+\s*[=:]\s*\d+',  # feature=value pattern
    ]
    for pattern in prediction_patterns:
        if re.search(pattern, q):
            params['features'] = _extract_feature_values(q)
            return QueryType.PREDICTION, 0.95, params
    
    # === METRICS/PERFORMANCE ===
    metrics_patterns = [
        r'(accuracy|precision|recall|f1|f2|auc|performance)',
        r'how\s+(good|accurate|well)',
        r'model\s+(metrics|performance|score)',
        r'(show|display)\s+.*(accuracy|metrics|performance)'
    ]
    for pattern in metrics_patterns:
        if re.search(pattern, q):
            return QueryType.METRICS, 0.90, params
    
    # === FEATURE IMPORTANCE ===
    importance_patterns = [
        r'(what|which)\s+(affects?|influences?|matters?|important)',
        r'feature\s+(importance|ranking)',
        r'(most|least)\s+important',
        r'(key|top|main)\s+(factors?|features?)'
    ]
    for pattern in importance_patterns:
        if re.search(pattern, q):
            return QueryType.FEATURE_IMPORTANCE, 0.90, params
    
    # === WHAT-IF SCENARIOS ===
    whatif_patterns = [
        r'what\s+(if|would\s+happen)',
        r'if\s+i\s+(change|increase|decrease)',
        r'scenario',
        r'suppose',
        r'hypothetically'
    ]
    for pattern in whatif_patterns:
        if re.search(pattern, q):
            params['scenario'] = q
            return QueryType.WHAT_IF, 0.88, params
    
    # === EXPLANATION REQUESTS ===
    explain_patterns = [
        r'why\s+(did|does|was|is)',
        r'explain\s+(this|the|why|how)',
        r'interpret',
        r'understand\s+(why|this)',
        r'what\s+does\s+this\s+(mean|show)'
    ]
    for pattern in explain_patterns:
        if re.search(pattern, q):
            return QueryType.EXPLAIN, 0.85, params
    
    # === MODEL INFO ===
    model_patterns = [
        r'(what|which)\s+(model|algorithm)',
        r'model\s+(type|name|info)',
        r'what\s+.+\s+trained',
        r'features?\s+(used|available)'
    ]
    for pattern in model_patterns:
        if re.search(pattern, q):
            return QueryType.MODEL_INFO, 0.85, params
    
    # === DASHBOARD ===
    if any(x in q for x in ['dashboard', 'all charts', 'full report', 'comprehensive']):
        return QueryType.DASHBOARD, 0.88, params
    
    # === HELP ===
    if any(x in q for x in ['help', 'how to use', 'what can you do', 'example']):
        return QueryType.HELP, 0.90, params
    
    # Default to general ML
    return QueryType.GENERAL_ML, 0.70, params


def _extract_feature_values(query: str) -> Dict[str, Any]:
    """Extract feature=value pairs from query"""
    features = {}
    
    # Pattern: feature_name=value or feature_name: value
    pattern = r'([a-z_]+)\s*[=:]\s*([0-9.]+|true|false|yes|no|male|female|[a-z]+)'
    matches = re.findall(pattern, query.lower())
    
    for name, value in matches:
        # Try to convert to appropriate type
        try:
            if '.' in value:
                features[name] = float(value)
            elif value.isdigit():
                features[name] = int(value)
            elif value in ['true', 'yes']:
                features[name] = True
            elif value in ['false', 'no']:
                features[name] = False
            else:
                features[name] = value
        except:
            features[name] = value
    
    return features


# =============================================================================
# CHART RETRIEVAL - Get stored charts from trained model
# =============================================================================

def get_stored_charts(user_id: str) -> Dict[str, Any]:
    """
    Retrieve charts generated during model training.
    These are stored in storage/automl/{user_id}/
    """
    charts = {}
    
    try:
        base_path = f"storage/automl/{user_id}"
        
        # Try to load from automl state
        state_path = f"{base_path}/automl_state.pkl"
        if os.path.exists(state_path):
            import pickle
            with open(state_path, 'rb') as f:
                state = pickle.load(f)
                if 'charts' in state:
                    charts = state['charts']
        
        # Also check for chart JSON files
        chart_dir = f"{base_path}/charts"
        if os.path.exists(chart_dir):
            for fname in os.listdir(chart_dir):
                if fname.endswith('.json'):
                    with open(f"{chart_dir}/{fname}") as f:
                        chart_name = fname.replace('.json', '')
                        charts[chart_name] = json.load(f)
        
        logger.info(f"📊 Retrieved {len(charts)} stored charts for user {user_id}")
        
    except Exception as e:
        logger.error(f"Chart retrieval error: {e}")
    
    return charts


def get_chart_by_name(user_id: str, chart_name: str) -> Optional[Dict]:
    """Get a specific chart by name (fuzzy matching)"""
    charts = get_stored_charts(user_id)
    
    # Direct match
    if chart_name in charts:
        return charts[chart_name]
    
    # Fuzzy match
    chart_name_lower = chart_name.lower().replace(' ', '_')
    for key, value in charts.items():
        if chart_name_lower in key.lower() or key.lower() in chart_name_lower:
            return value
    
    # Partial match
    for key, value in charts.items():
        if any(part in key.lower() for part in chart_name_lower.split('_')):
            return value
    
    return None


# =============================================================================
# MAIN RESPONSE FUNCTION
# =============================================================================

def predict_response_sync(user_id: str, query: str, context: str = "", df=None) -> Dict[str, Any]:
    """
    🤖 SENIOR AIML ENGINEER ML ASSISTANT
    
    Main entry point for all ML queries. Routes to appropriate handler
    and returns ChatGPT-like responses with charts and explanations.
    Uses DYNAMIC routing - ML queries use ML, general queries use AI.
    """
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.5,
        "sources": [],
        "ml_used": False,
        "chart": None,
        "charts": []  # Multiple charts support
    }
    
    start_time = datetime.now()
    session = get_session(user_id)
    
    # =================================================================
    # 🔄 DYNAMIC ROUTING: Check if query relates to ML/predictions
    # =================================================================
    q_lower = query.lower()
    
    # Get column names from data
    column_names = [col.lower() for col in df.columns] if df is not None and hasattr(df, 'columns') else []
    column_names_spaced = [col.replace('_', ' ') for col in column_names]
    
    # ML-related terms
    ml_terms = [
        'predict', 'forecast', 'model', 'train', 'accuracy', 'feature',
        'classification', 'regression', 'ml', 'machine learning',
        'precision', 'recall', 'f1', 'confusion', 'roc', 'auc'
    ]
    
    # Data terms
    data_terms = column_names + column_names_spaced + [
        'my data', 'my ', 'our ', 'the data', 'uploaded', 'dataset',
        'total', 'sum', 'average', 'count', 'revenue', 'sales', 'customer'
    ]
    
    query_is_about_ml = any(term in q_lower for term in ml_terms)
    query_is_about_data = any(term in q_lower for term in data_terms if term)
    
    # If NOT about ML or data, use pure AI Knowledge
    if not query_is_about_ml and not query_is_about_data:
        logger.info("🌐 Predict: Routing to AI KNOWLEDGE (query not about ML/data)")
        
        if LLM_AVAILABLE:
            try:
                ai_prompt = f"""You are an AI with machine learning expertise.

Answer this question using your knowledge:

{query}

Provide a helpful, accurate response. If it's about ML concepts, explain clearly."""

                llm_response = llm_chat(ai_prompt, temperature=0.7, max_tokens=600)
                
                result["answer"] = f"""## 🔮 Predict

🌐 **AI Knowledge**

{llm_response}

---
*💡 This is general AI knowledge. For predictions on YOUR data, train a model first and ask about predictions.*"""
                result["sources"] = ["AI Knowledge"]
                
                exec_time = (datetime.now() - start_time).total_seconds()
                result["execution_time"] = f"{exec_time:.2f}s"
                return result
                
            except Exception as e:
                logger.error(f"AI Knowledge error: {e}")
    
    # =================================================================
    # 📊 ML PATH - Query IS about ML or user's data
    # =================================================================
    logger.info("📊 Predict: Routing to ML ANALYSIS")
    
    # === CHECK AUTOML ===
    if not AUTOML_AVAILABLE:
        result["answer"] = "⚠️ ML Engine not available. Please ensure the backend is properly configured."
        return result
    
    # === LOAD MODEL ===
    try:
        model_loaded = automl_engine.load(user_id)
        if model_loaded:
            logger.info(f"✅ Model loaded: {automl_engine.model_name}")
        else:
            logger.warning(f"⚠️ No model found for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Model load error: {e}")
        model_loaded = False
    
    # === DETECT QUERY TYPE ===
    query_type, type_confidence, params = detect_query_type(query, user_id)
    logger.info(f"🔍 Query: {query_type.value} (confidence: {type_confidence:.0%})")
    
    result["confidence"] = type_confidence
    
    # === ROUTE TO HANDLER ===
    if not model_loaded:
        result = _handle_no_model(query, query_type, df, user_id)
    else:
        handlers = {
            # Core predictions
            QueryType.PREDICTION: _handle_prediction,
            QueryType.BATCH_PREDICTION: _handle_batch_prediction,
            
            # Model understanding
            QueryType.MODEL_INFO: _handle_model_info,
            QueryType.METRICS: _handle_metrics,
            QueryType.FEATURE_IMPORTANCE: _handle_feature_importance,
            QueryType.FEATURE_SPECIFIC: _handle_feature_specific,
            
            # Chart requests
            QueryType.SHOW_CHART: _handle_show_chart,
            QueryType.CONFUSION_MATRIX: lambda q, d: _handle_specific_chart(q, d, user_id, 'confusion_matrix'),
            QueryType.ROC_CURVE: lambda q, d: _handle_specific_chart(q, d, user_id, 'roc_curve'),
            QueryType.PRECISION_RECALL: lambda q, d: _handle_specific_chart(q, d, user_id, 'precision_recall'),
            QueryType.ACTUAL_VS_PREDICTED: lambda q, d: _handle_specific_chart(q, d, user_id, 'actual_vs_predicted'),
            
            # Advanced
            QueryType.WHAT_IF: _handle_what_if,
            QueryType.EXPLAIN: _handle_explain,
            QueryType.DASHBOARD: lambda q, d: _handle_dashboard(q, d, user_id),
            
            # Meta
            QueryType.COMPARISON: _handle_comparison,
            QueryType.HELP: _handle_help,
            QueryType.GENERAL_ML: _handle_general_ml,
        }
        
        handler = handlers.get(query_type, _handle_general_ml)
        
        try:
            if query_type in [QueryType.CONFUSION_MATRIX, QueryType.ROC_CURVE, 
                             QueryType.PRECISION_RECALL, QueryType.ACTUAL_VS_PREDICTED,
                             QueryType.DASHBOARD]:
                result = handler(query, df)
            elif query_type == QueryType.GENERAL_ML:
                result = handler(query, df, context)
            else:
                result = handler(query, df)
        except Exception as e:
            logger.error(f"Handler error: {e}")
            import traceback
            traceback.print_exc()
            result["answer"] = f"⚠️ Error processing your request: {str(e)[:100]}"
    
    # Update session memory
    session.last_query_type = query_type
    
    # Check for custom chart requests (radar, scatter, etc.) using LLM visualizer
    q_lower = query.lower()
    custom_chart_keywords = ['radar', 'spider', 'sunburst', 'treemap', 'bubble', 'scatter', 'heatmap', 'pink', 'blue', 'green']
    wants_custom_chart = any(term in q_lower for term in custom_chart_keywords)
    
    if wants_custom_chart and df is not None and not df.empty and "chart" not in result:
        try:
            from core.llm_visualizer import llm_visualize
            import json
            viz_result = llm_visualize(df, query, user_id)
            if viz_result.get("success") and viz_result.get("chart"):
                chart = viz_result.get("chart")
                if isinstance(chart, dict) and 'data' in chart and 'layout' in chart:
                    chart_json = json.dumps(chart, default=str)
                    result["answer"] += f"\n\n```plotly_chart\n{chart_json}\n```"
                    result["chart"] = chart
                    result["visualization"] = chart
        except Exception as e:
            logger.warning(f"Predict custom chart failed: {e}")
    
    # Add execution time
    exec_time = (datetime.now() - start_time).total_seconds()
    result["execution_time"] = f"{exec_time:.2f}s"
    result["query_type"] = query_type.value
    
    return result


# =============================================================================
# HANDLER: NO MODEL TRAINED
# =============================================================================

def _handle_no_model(query: str, query_type: QueryType, df=None, user_id: str = "") -> Dict[str, Any]:
    """Handle queries when no model is trained yet"""
    
    response = """## 🤖 Senior AIML Engineer Assistant

Welcome! I'm your AI/ML assistant with senior engineer expertise.

### 🚀 Getting Started

To unlock my full capabilities, you need to train a model first:

1. **Go to the AutoML tab** in the sidebar
2. **Upload your dataset** (CSV, Excel, or JSON)
3. **Select your target variable** 
4. **Click Train** - I'll automatically:
   - Clean and preprocess your data
   - Try 15+ algorithms (including neural networks in Ultra mode)
   - Optimize hyperparameters
   - Select the best model

### 💡 Once trained, ask me:

| Query Type | Example |
|------------|---------|
| **Predictions** | "Predict for age=60, income=50000" |
| **Model Info** | "What model was trained?" |
| **Performance** | "Show accuracy and confusion matrix" |
| **Feature Analysis** | "What features matter most?" |
| **Visualizations** | "Show me the ROC curve" |
| **What-If** | "What if age was 30 instead of 60?" |
| **Explanations** | "Why did the model predict this?" |

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


# =============================================================================
# HANDLER: PREDICTIONS
# =============================================================================

def _handle_prediction(query: str, df=None) -> Dict[str, Any]:
    """Handle prediction requests with real ML model"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.85,
        "sources": ["Trained ML Model", automl_engine.model_name],
        "ml_used": True
    }
    
    # Extract features from query
    feature_values = _extract_features_from_query(query, df)
    
    if not feature_values:
        result["answer"] = _get_prediction_help()
        return result
    
    try:
        # Make real prediction
        pred = automl_engine.predict(feature_values)
        prediction = pred.get('prediction')
        confidence = pred.get('confidence', 0.8)
        probabilities = pred.get('probabilities', {})
        
        # Get context
        task_type = automl_engine.task_type
        target = automl_engine.target_column
        model_name = automl_engine.model_name
        is_classification = 'classification' in task_type
        
        # Generate senior-level explanation
        ml_context = {
            'model_name': model_name,
            'task_type': task_type,
            'target': target,
            'prediction': prediction,
            'confidence': confidence,
            'features': feature_values
        }
        explanation = generate_senior_explanation('prediction', ml_context, query)
        
        # Build response
        conf_pct = int(confidence * 100) if confidence else 75
        
        if is_classification:
            pred_emoji = "✅" if str(prediction) in ["0", "False", "No", "Negative", "Survived"] else "⚠️"
            pred_display = _format_classification_prediction(prediction, target, probabilities)
        else:
            pred_emoji = "📊"
            pred_display = f"**{target}**: {prediction:,.2f}" if isinstance(prediction, float) else f"**{target}**: {prediction}"
        
        conf_bar = "🟢" if conf_pct > 80 else "🟡" if conf_pct > 60 else "🔴"
        
        response = f"""## {pred_emoji} ML Prediction Result

### {pred_display}

| Metric | Value |
|--------|-------|
| **Confidence** | {conf_bar} {conf_pct}% |
| **Model** | {model_name} |
| **Task** | {task_type.replace('_', ' ').title()} |

---

### 💡 Senior ML Engineer Analysis

{explanation}

---

### 📥 Input Features

"""
        # Show input features
        for feat, val in list(feature_values.items())[:10]:
            if isinstance(val, float):
                response += f"- `{feat}`: {val:,.2f}\n"
            else:
                response += f"- `{feat}`: {val}\n"
        
        # Add probability breakdown for classification
        if probabilities and is_classification:
            response += "\n### 📊 Class Probabilities\n\n"
            for cls, prob in probabilities.items():
                bar_len = int(prob * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                response += f"- **{cls}**: `{bar}` {prob*100:.1f}%\n"
        
        # Generate prediction chart
        chart = _generate_prediction_confidence_chart(prediction, confidence, probabilities, target)
        if chart:
            response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        result["confidence"] = confidence
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        import traceback
        traceback.print_exc()
        result["answer"] = f"⚠️ Prediction failed: {str(e)}\n\nPlease check that your input features match the training data format."
    
    return result


def _extract_features_from_query(query: str, df=None) -> Dict[str, Any]:
    """Extract feature values from natural language query"""
    features = {}
    
    # Get expected features
    expected_features = automl_engine.feature_columns if hasattr(automl_engine, 'feature_columns') else []
    metadata = automl_engine.feature_metadata if hasattr(automl_engine, 'feature_metadata') else []
    meta_dict = {m.get('name', ''): m for m in metadata} if metadata else {}
    
    q_lower = query.lower()
    
    # Pattern: feature=value, feature:value, feature is value
    patterns = [
        r'([a-z_]+)\s*[=:]\s*([0-9.]+)',
        r'([a-z_]+)\s*[=:]\s*([a-z]+)',
        r'([a-z_]+)\s+is\s+([0-9.]+)',
        r'([a-z_]+)\s+of\s+([0-9.]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, q_lower)
        for name, value in matches:
            # Match to expected feature
            matched_feature = None
            for feat in expected_features:
                if name in feat.lower() or feat.lower() in name:
                    matched_feature = feat
                    break
            
            if matched_feature:
                # Convert value
                meta = meta_dict.get(matched_feature, {})
                if meta.get('type') == 'numeric':
                    try:
                        features[matched_feature] = float(value)
                    except:
                        features[matched_feature] = value
                else:
                    features[matched_feature] = value
    
    # Fill missing features with defaults
    for feat in expected_features:
        if feat not in features:
            meta = meta_dict.get(feat, {})
            if 'default' in meta:
                features[feat] = meta['default']
            elif 'mean' in meta:
                features[feat] = meta['mean']
    
    return features if len(features) >= len(expected_features) * 0.3 else {}


def _get_prediction_help() -> str:
    """Return help message for predictions"""
    features = automl_engine.feature_columns[:8] if hasattr(automl_engine, 'feature_columns') else []
    target = automl_engine.target_column if hasattr(automl_engine, 'target_column') else 'target'
    
    response = f"""## 🎯 Making Predictions

To predict **{target}**, provide values for these features:

"""
    
    for feat in features:
        response += f"- `{feat}`\n"
    
    response += f"""
### Example Queries:

1. **Simple**: "Predict for {features[0] if features else 'age'}=50"
2. **Multiple**: "{features[0] if features else 'age'}=50, {features[1] if len(features) > 1 else 'income'}=60000"
3. **Natural**: "What would happen if {features[0] if features else 'age'} is 30?"

---

*Tip: I'll fill in missing values with defaults from training data.*
"""
    return response


def _format_classification_prediction(prediction, target: str, probabilities: Dict) -> str:
    """Format classification prediction for display"""
    if 'death' in target.lower() or 'survive' in target.lower():
        if str(prediction) in ['0', 'False', 'No']:
            return "🟢 **Predicted: SURVIVED**"
        else:
            return "🔴 **Predicted: DEATH EVENT**"
    elif 'fraud' in target.lower():
        if str(prediction) in ['1', 'True', 'Yes']:
            return "🚨 **Predicted: FRAUD DETECTED**"
        else:
            return "✅ **Predicted: LEGITIMATE**"
    elif 'churn' in target.lower():
        if str(prediction) in ['1', 'True', 'Yes']:
            return "⚠️ **Predicted: WILL CHURN**"
        else:
            return "✅ **Predicted: WILL STAY**"
    else:
        return f"**Predicted {target}**: {prediction}"


def _generate_prediction_confidence_chart(prediction, confidence, probabilities, target) -> Dict:
    """Generate confidence visualization chart"""
    if probabilities and len(probabilities) > 0:
        # Multi-class probability bar chart
        classes = list(probabilities.keys())
        probs = [probabilities[c] * 100 for c in classes]
        
        return {
            "data": [{
                "type": "bar",
                "x": classes,
                "y": probs,
                "marker": {"color": ["#22c55e" if str(prediction) == str(c) else "#94a3b8" for c in classes]}
            }],
            "layout": {
                "title": {"text": f"Class Probabilities for {target}", "font": {"size": 14}},
                "yaxis": {"title": "Probability (%)", "range": [0, 100]},
                "paper_bgcolor": "#f8fafc",
                "height": 300
            }
        }
    else:
        # Simple gauge for confidence
        return {
            "data": [{
                "type": "indicator",
                "mode": "gauge+number",
                "value": confidence * 100,
                "title": {"text": "Prediction Confidence"},
                "gauge": {
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#3b82f6"},
                    "steps": [
                        {"range": [0, 60], "color": "#fee2e2"},
                        {"range": [60, 80], "color": "#fef3c7"},
                        {"range": [80, 100], "color": "#dcfce7"}
                    ]
                }
            }],
            "layout": {"paper_bgcolor": "#f8fafc", "height": 250}
        }


# =============================================================================
# HANDLER: METRICS
# =============================================================================

def _handle_metrics(query: str, df=None) -> Dict[str, Any]:
    """Handle model metrics/performance queries"""
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
        result["answer"] = f"⚠️ Error retrieving metrics: {e}"
        return result
    
    model = metrics_data.get('model_name', 'Unknown')
    task = metrics_data.get('task_type', 'Unknown')
    target = metrics_data.get('target', 'Unknown')
    metrics = metrics_data.get('metrics', {})
    cm = metrics_data.get('confusion_matrix')
    
    response = f"""## 📊 Model Performance Dashboard

### 🤖 Model: **{model}**

| Property | Value |
|----------|-------|
| **Task Type** | {task.replace('_', ' ').title()} |
| **Target** | {target} |
| **Features** | {metrics_data.get('n_features', 'N/A')} |

---

### 🎯 Performance Metrics

"""
    
    # Classification metrics
    if metrics.get('accuracy'):
        acc = metrics['accuracy'] * 100
        acc_emoji = "🟢" if acc > 85 else "🟡" if acc > 70 else "🔴"
        response += f"| **Accuracy** | {acc_emoji} {acc:.1f}% |\n"
    
    if metrics.get('f1'):
        f1 = metrics['f1'] * 100
        response += f"| **F1 Score** | {f1:.1f}% |\n"
    
    if metrics.get('precision'):
        response += f"| **Precision** | {metrics['precision']*100:.1f}% |\n"
    
    if metrics.get('recall'):
        response += f"| **Recall** | {metrics['recall']*100:.1f}% |\n"
    
    if metrics.get('minority_recall'):
        response += f"| **Minority Recall** | {metrics['minority_recall']*100:.1f}% |\n"
    
    if metrics.get('auc_pr'):
        response += f"| **AUC-PR** | {metrics['auc_pr']:.4f} |\n"
    
    # Regression metrics
    if metrics.get('r2'):
        response += f"| **R² Score** | {metrics['r2']:.4f} |\n"
    
    if metrics.get('mae'):
        response += f"| **MAE** | {metrics['mae']:.4f} |\n"
    
    if metrics.get('rmse'):
        response += f"| **RMSE** | {metrics['rmse']:.4f} |\n"
    
    # Senior ML Engineer interpretation
    ml_context = {
        'model_name': model,
        'task_type': task,
        'target': target,
        'metrics': metrics
    }
    interpretation = generate_senior_explanation('metrics', ml_context, query)
    response += f"\n---\n\n### 💡 Senior ML Engineer Analysis\n\n{interpretation}\n"
    
    # Add confusion matrix chart if available
    if cm:
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
                "title": {"text": "📊 Confusion Matrix", "font": {"size": 16}},
                "xaxis": {"title": "Predicted"},
                "yaxis": {"title": "Actual", "autorange": "reversed"},
                "paper_bgcolor": "#f8fafc",
                "height": 400, "width": 450
            }
        }
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    result["answer"] = response
    return result


# =============================================================================
# HANDLER: FEATURE IMPORTANCE
# =============================================================================

def _handle_feature_importance(query: str, df=None) -> Dict[str, Any]:
    """Handle feature importance queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.92,
        "sources": ["Feature Analysis", automl_engine.model_name],
        "ml_used": True
    }
    
    importance = _get_feature_importance_data()
    target = automl_engine.target_column
    model = automl_engine.model_name
    
    if not importance:
        result["answer"] = "⚠️ Feature importance not available for this model type."
        return result
    
    response = f"""## 🔑 Feature Importance Analysis

### What Drives **{target}** Predictions?

Based on the **{model}** model, these features have the highest predictive power:

"""
    
    # Top features with bars
    total_imp = sum(f['importance'] for f in importance)
    for i, feat in enumerate(importance[:10], 1):
        imp = feat['importance']
        pct = (imp / total_imp * 100) if total_imp > 0 else 0
        bar = "█" * int(pct / 3) + "░" * (30 - int(pct / 3))
        response += f"**{i}. {feat['feature']}**\n`{bar}` {pct:.1f}%\n\n"
    
    # Senior interpretation
    top_3 = [f['feature'] for f in importance[:3]]
    ml_context = {
        'model_name': model,
        'target': target,
        'top_features': top_3
    }
    interpretation = generate_senior_explanation('importance', ml_context, query)
    response += f"---\n\n### 💡 Senior ML Engineer Analysis\n\n{interpretation}\n"
    
    # Generate bar chart
    feats = [f['feature'][:20] for f in importance[:8]]
    vals = [f['importance'] * 100 for f in importance[:8]]
    
    chart = {
        "data": [{
            "type": "bar",
            "y": feats[::-1],
            "x": vals[::-1],
            "orientation": "h",
            "marker": {"color": ["#3b82f6"] * (len(feats)-1) + ["#1d4ed8"]}
        }],
        "layout": {
            "title": {"text": f"🔑 Feature Importance", "font": {"size": 16}},
            "xaxis": {"title": "Importance (%)"},
            "paper_bgcolor": "#f8fafc",
            "margin": {"l": 150},
            "height": 400
        }
    }
    response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
    
    result["answer"] = response
    return result


def _get_feature_importance_data() -> List[Dict]:
    """Get feature importance from trained model"""
    try:
        model = automl_engine.model
        feature_names = automl_engine.feature_columns
        
        # Try tree-based importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_).flatten()
        elif hasattr(model, 'estimators_'):
            # Ensemble - average importances
            importances = np.mean([
                getattr(e, 'feature_importances_', np.zeros(len(feature_names)))
                for e in model.estimators_ if hasattr(e, 'feature_importances_')
            ], axis=0) if len(model.estimators_) > 0 else None
        else:
            return []
        
        if importances is None or len(importances) == 0:
            return []
        
        # Normalize
        importances = importances / np.sum(importances) if np.sum(importances) > 0 else importances
        
        # Create list
        result = [
            {'feature': feat, 'importance': float(imp)}
            for feat, imp in zip(feature_names, importances)
        ]
        result.sort(key=lambda x: x['importance'], reverse=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Feature importance error: {e}")
        return []


# =============================================================================
# HANDLER: SPECIFIC CHARTS
# =============================================================================

def _handle_specific_chart(query: str, df, user_id: str, chart_type: str) -> Dict[str, Any]:
    """Handle requests for specific chart types"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.95,
        "sources": ["Chart Generator", automl_engine.model_name],
        "ml_used": True
    }
    
    # Try to get stored chart
    chart = get_chart_by_name(user_id, chart_type)
    
    if chart:
        response = f"""## 📊 {chart_type.replace('_', ' ').title()}

Here is the **{chart_type.replace('_', ' ')}** from your trained model:

"""
        response += f"\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        # Add interpretation
        ml_context = {
            'model_name': automl_engine.model_name,
            'target': automl_engine.target_column,
            'chart_type': chart_type
        }
        interpretation = generate_senior_explanation(chart_type, ml_context, query)
        response += f"\n\n### 💡 Interpretation\n\n{interpretation}"
        
    else:
        response = f"""## 📊 {chart_type.replace('_', ' ').title()}

The **{chart_type.replace('_', ' ')}** chart is being generated...

You can find all available charts on the **ML Predictions** page in the sidebar.

### Available Charts:
- Confusion Matrix
- ROC Curve
- Precision-Recall Curve
- Feature Importance
- Class Distribution
- Calibration Curve
"""
    
    result["answer"] = response
    return result


def _handle_show_chart(query: str, df=None) -> Dict[str, Any]:
    """Handle generic chart show requests"""
    # Detect specific chart from query
    q = query.lower()
    
    chart_mapping = {
        'confusion': 'confusion_matrix',
        'roc': 'roc_curve',
        'precision': 'precision_recall',
        'recall': 'precision_recall',
        'feature': 'feature_importance',
        'importance': 'feature_importance',
        'distribution': 'class_distribution',
        'calibration': 'calibration',
        'correlation': 'correlation_heatmap'
    }
    
    for keyword, chart_name in chart_mapping.items():
        if keyword in q:
            return _handle_feature_importance(query, df) if chart_name == 'feature_importance' else _handle_metrics(query, df)
    
    # Default: show feature importance
    return _handle_feature_importance(query, df)


# =============================================================================
# HANDLER: DASHBOARD
# =============================================================================

def _handle_dashboard(query: str, df, user_id: str) -> Dict[str, Any]:
    """Generate comprehensive dashboard with all charts and metrics"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.98,
        "sources": ["Full Dashboard", automl_engine.model_name],
        "ml_used": True
    }
    
    model = automl_engine.model_name
    target = automl_engine.target_column
    task = automl_engine.task_type
    
    # Get metrics
    try:
        metrics_data = automl_engine.get_model_metrics()
        metrics = metrics_data.get('metrics', {})
    except:
        metrics = {}
    
    response = f"""## 📊 Complete ML Dashboard

### 🤖 Model Overview

| Property | Value |
|----------|-------|
| **Model** | {model} |
| **Target** | {target} |
| **Task** | {task.replace('_', ' ').title()} |
| **Features** | {len(automl_engine.feature_columns)} |

---

### 🎯 Key Metrics

"""
    
    if metrics.get('accuracy'):
        response += f"- **Accuracy**: {metrics['accuracy']*100:.1f}%\n"
    if metrics.get('f1'):
        response += f"- **F1 Score**: {metrics['f1']*100:.1f}%\n"
    if metrics.get('r2'):
        response += f"- **R² Score**: {metrics['r2']:.4f}\n"
    
    response += """
---

### 📈 Available Visualizations

To view specific charts, ask me:
- "Show confusion matrix"
- "Show ROC curve"
- "Show feature importance"
- "Show precision-recall curve"
- "Show class distribution"

Or visit the **ML Predictions** page for the full interactive dashboard!

---

### 💡 Quick Actions

- **Make Prediction**: "Predict for [feature]=value"
- **What-If Analysis**: "What if [feature] was [value]?"
- **Explain**: "Why did the model predict this?"
"""
    
    result["answer"] = response
    return result


# =============================================================================
# HANDLER: MODEL INFO
# =============================================================================

def _handle_model_info(query: str, df=None) -> Dict[str, Any]:
    """Handle model information queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.95,
        "sources": ["Model Info"],
        "ml_used": True
    }
    
    model = automl_engine.model_name
    task = automl_engine.task_type
    target = automl_engine.target_column
    features = automl_engine.feature_columns
    n_classes = getattr(automl_engine, 'n_classes', None)
    
    response = f"""## 🤖 Trained Model Information

### Model Architecture

| Property | Value |
|----------|-------|
| **Algorithm** | {model} |
| **Task Type** | {task.replace('_', ' ').title()} |
| **Target Variable** | `{target}` |
| **Number of Features** | {len(features)} |
"""
    
    if n_classes and 'classification' in task:
        response += f"| **Number of Classes** | {n_classes} |\n"
    
    response += f"""
---

### 📋 Features ({len(features)} total)

"""
    
    for i, feat in enumerate(features[:15], 1):
        response += f"{i}. `{feat}`\n"
    
    if len(features) > 15:
        response += f"\n*...and {len(features) - 15} more features*\n"
    
    response += f"""
---

### 💡 How to Use This Model

| Query Type | Example |
|------------|---------|
| **Predict** | "Predict for {features[0] if features else 'feature'}=50" |
| **Importance** | "What features matter most?" |
| **Metrics** | "Show model accuracy" |
| **What-If** | "What if {features[0] if features else 'feature'} was 100?" |
"""
    
    result["answer"] = response
    return result


# =============================================================================
# HANDLER: WHAT-IF SCENARIOS
# =============================================================================

def _handle_what_if(query: str, df=None) -> Dict[str, Any]:
    """Handle what-if scenario analysis"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.88,
        "sources": ["Scenario Analysis", automl_engine.model_name],
        "ml_used": True
    }
    
    target = automl_engine.target_column
    metadata = automl_engine.feature_metadata
    
    # Find key feature to analyze
    numeric_feats = [m for m in metadata if m.get('type') == 'numeric']
    if not numeric_feats:
        result["answer"] = "What-if analysis requires numeric features."
        return result
    
    # Analyze first numeric feature
    feat = numeric_feats[0]
    feat_name = feat['name']
    low_val = feat.get('p25', feat.get('min', 30))
    high_val = feat.get('p75', feat.get('max', 70))
    
    # Get default features
    base = {m['name']: m.get('mean', m.get('default', 0)) for m in metadata}
    
    # Predict for low and high
    low_input = base.copy()
    low_input[feat_name] = low_val
    
    high_input = base.copy()
    high_input[feat_name] = high_val
    
    try:
        low_pred = automl_engine.predict(low_input)
        high_pred = automl_engine.predict(high_input)
        
        response = f"""## 🔮 What-If Analysis

### Varying **{feat_name}** and its effect on **{target}**

| Scenario | {feat_name} | Prediction | Confidence |
|----------|------------|------------|------------|
| **Low** | {low_val:.1f} | {low_pred['prediction']} | {low_pred.get('confidence', 0.7)*100:.0f}% |
| **High** | {high_val:.1f} | {high_pred['prediction']} | {high_pred.get('confidence', 0.7)*100:.0f}% |

---

### 💡 Insight

"""
        
        # LLM interpretation
        ml_context = {
            'feature': feat_name,
            'target': target,
            'low_val': low_val,
            'high_val': high_val,
            'low_pred': low_pred['prediction'],
            'high_pred': high_pred['prediction']
        }
        interpretation = generate_senior_explanation('what_if', ml_context, query)
        response += interpretation
        
        # Chart
        chart = {
            "data": [{
                "type": "bar",
                "x": [f"Low ({low_val:.0f})", f"High ({high_val:.0f})"],
                "y": [low_pred.get('confidence', 0.7)*100, high_pred.get('confidence', 0.7)*100],
                "marker": {"color": ["#22c55e", "#ef4444"]}
            }],
            "layout": {
                "title": {"text": f"Confidence by {feat_name}", "font": {"size": 14}},
                "yaxis": {"title": "Confidence (%)", "range": [0, 100]},
                "paper_bgcolor": "#f8fafc",
                "height": 300
            }
        }
        response += f"\n\n```plotly_chart\n{json.dumps(chart)}\n```"
        
        result["answer"] = response
        
    except Exception as e:
        result["answer"] = f"⚠️ What-If analysis failed: {e}"
    
    return result


# =============================================================================
# HANDLER: EXPLAIN
# =============================================================================

def _handle_explain(query: str, df=None) -> Dict[str, Any]:
    """Handle explanation requests"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.85,
        "sources": ["Model Explainer", automl_engine.model_name],
        "ml_used": True
    }
    
    model = automl_engine.model_name
    target = automl_engine.target_column
    
    # Get feature importance for context
    importance = _get_feature_importance_data()[:5]
    
    response = f"""## 🔍 Model Explanation

### How does **{model}** predict **{target}**?

"""
    
    if importance:
        response += "### Key Decision Factors\n\n"
        for i, feat in enumerate(importance, 1):
            response += f"{i}. **{feat['feature']}**: {feat['importance']*100:.1f}% influence\n"
    
    response += "\n---\n\n### 💡 Senior ML Engineer Analysis\n\n"
    
    ml_context = {
        'model_name': model,
        'target': target,
        'top_features': [f['feature'] for f in importance] if importance else []
    }
    explanation = generate_senior_explanation('explain', ml_context, query)
    response += explanation
    
    response += """

---

### 🔬 For Deeper Analysis

- Ask: "Show SHAP values" (if available)
- Ask: "Why did the model predict X?"
- View the **ML Predictions** page for interactive explanations
"""
    
    result["answer"] = response
    return result


# =============================================================================
# HANDLER: COMPARISON
# =============================================================================

def _handle_comparison(query: str, df=None) -> Dict[str, Any]:
    """Handle comparison queries between scenarios"""
    # Reuse what-if handler
    return _handle_what_if(query, df)


# =============================================================================
# HANDLER: HELP
# =============================================================================

def _handle_help(query: str, df=None) -> Dict[str, Any]:
    """Handle help queries"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.95,
        "sources": ["Help"],
        "ml_used": False
    }
    
    target = automl_engine.target_column if hasattr(automl_engine, 'target_column') else 'outcome'
    
    response = f"""## 🤖 ML Assistant Help

I'm your Senior AIML Engineer assistant. Here's what I can do:

### 🎯 Make Predictions

```
"Predict for age=60, income=50000"
"What would happen if credit_score is 750?"
```

### 📊 View Model Performance

```
"Show accuracy"
"Show confusion matrix"
"How well does the model perform?"
```

### 🔑 Understand Features

```
"What features are most important?"
"How does age affect {target}?"
```

### 📈 View Charts

```
"Show ROC curve"
"Show precision-recall curve"
"Display feature importance chart"
```

### 🔮 Scenario Analysis

```
"What if age was 30 instead of 60?"
"Compare high vs low income scenarios"
```

### 💡 Get Explanations

```
"Why did the model predict this?"
"Explain how the model works"
```

---

*I provide senior ML engineer level insights with statistical depth!*
"""
    
    result["answer"] = response
    return result


# =============================================================================
# HANDLER: GENERAL ML
# =============================================================================

def _handle_general_ml(query: str, df=None, context: str = "") -> Dict[str, Any]:
    """Handle general ML questions with LLM"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.75,
        "sources": ["ML Knowledge"],
        "ml_used": True
    }
    
    if not LLM_AVAILABLE:
        result["answer"] = "LLM not available for general questions. Try specific queries like 'show accuracy' or 'predict for age=50'."
        return result
    
    # Build context
    model_context = ""
    if hasattr(automl_engine, 'model_name'):
        model_context = f"""
Current trained model: {automl_engine.model_name}
Target: {automl_engine.target_column}
Task: {automl_engine.task_type}
Features: {len(automl_engine.feature_columns)}
"""
    
    prompt = f"""{SENIOR_AIML_SYSTEM_PROMPT}

{model_context}

User question: {query}

Provide a helpful, technically accurate response. If the question relates to the trained model, incorporate that context. Be concise but thorough."""

    try:
        response = llm_chat(prompt, temperature=0.4, max_tokens=400)
        result["answer"] = f"## 💡 ML Insight\n\n{response}"
    except Exception as e:
        result["answer"] = f"⚠️ Error generating response: {e}"
    
    return result


# =============================================================================
# HANDLER: BATCH PREDICTION
# =============================================================================

def _handle_batch_prediction(query: str, df=None) -> Dict[str, Any]:
    """Handle batch prediction requests"""
    result = {
        "answer": "Batch prediction feature coming soon! For now, use the ML Predictions page to make predictions on uploaded data.",
        "mode": "predict",
        "confidence": 0.7,
        "sources": [],
        "ml_used": False
    }
    return result


# =============================================================================
# HANDLER: FEATURE SPECIFIC
# =============================================================================

def _handle_feature_specific(query: str, df=None) -> Dict[str, Any]:
    """Handle specific feature analysis"""
    result = {
        "answer": "",
        "mode": "predict",
        "confidence": 0.90,
        "sources": ["Feature Analysis"],
        "ml_used": True
    }
    
    # Find mentioned feature
    features = automl_engine.feature_columns
    q = query.lower()
    
    target_feat = None
    for feat in features:
        if feat.lower() in q or feat.lower().replace('_', ' ') in q:
            target_feat = feat
            break
    
    if not target_feat:
        result["answer"] = f"Please specify which feature you want to analyze. Available: {', '.join(features[:10])}"
        return result
    
    # Get metadata
    metadata = {m['name']: m for m in automl_engine.feature_metadata}
    meta = metadata.get(target_feat, {})
    target = automl_engine.target_column
    
    response = f"""## 🔍 Feature Analysis: **{target_feat}**

### 📊 Statistics

"""
    
    if meta.get('type') == 'numeric':
        response += f"""| Statistic | Value |
|-----------|-------|
| **Type** | Numeric |
| **Min** | {meta.get('min', 'N/A'):,.1f} |
| **Max** | {meta.get('max', 'N/A'):,.1f} |
| **Mean** | {meta.get('mean', 'N/A'):,.1f} |
"""
    else:
        options = meta.get('options', [])[:5]
        response += f"""| Property | Value |
|----------|-------|
| **Type** | Categorical |
| **Unique Values** | {len(meta.get('options', []))} |
| **Examples** | {', '.join(str(o) for o in options)} |
"""
    
    # Get importance rank
    importance = _get_feature_importance_data()
    rank = next((i+1 for i, f in enumerate(importance) if f['feature'] == target_feat), None)
    
    if rank:
        response += f"\n### 🔑 Importance Rank: #{rank} of {len(features)}\n"
    
    # LLM explanation
    ml_context = {
        'feature': target_feat,
        'target': target,
        'stats': meta
    }
    explanation = generate_senior_explanation('feature_analysis', ml_context, query)
    response += f"\n---\n\n### 💡 Analysis\n\n{explanation}"
    
    result["answer"] = response
    return result


# =============================================================================
# EXPORT - For use by other modules
# =============================================================================

__all__ = [
    'predict_response_sync',
    'detect_query_type',
    'QueryType',
    'get_stored_charts',
    'get_chart_by_name'
]
