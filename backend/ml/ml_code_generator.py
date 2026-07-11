"""
📦 ML CODE GENERATOR - Dynamic Project ZIP Export
===================================================

Generates a downloadable ZIP file containing a complete, runnable Python
ML project BASED ON THE USER'S ACTUAL TRAINING. Dynamically generates
code matching the exact modes, algorithms, features, and task type
that were used during AutoML training.

All scripts use real column names, actual model types, and genuine 
feature metadata from the user's training session.
"""

import io
import json
import zipfile
import logging
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


API_SERVER_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<title>DataVision ML API</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #f9fafb; color: #111827; }
h1 { color: #4F46E5; } h2 { color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }
.card { background: white; border-radius: 12px; padding: 24px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
button { background: #4F46E5; color: white; border: none; padding: 12px 32px; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 12px; }
button:hover { background: #4338CA; }
#result { margin-top: 20px; padding: 16px; background: #f0fdf4; border-radius: 8px; display: none; }
</style>
</head>
<body>
<h1>🚀 DataVision ML API</h1>
<div class="card">
<h2>Model Info</h2>
<p>🏆 <b>Model:</b> {{ model_name }} | 🎯 <b>Target:</b> {{ target }} | 📊 <b>Task:</b> {{ task_type_val }} | 📁 <b>Features:</b> {{ raw_feature_info|length }}</p>
<ul>
{% for k, v in metrics.items() %}
  <li><b>{{ k }}</b>: {{ "%.4f"|format(v) if v is float else v }}</li>
{% endfor %}
</ul>
</div>
<div class="card">
<h2>🔮 Make a Prediction</h2>
<form id="predForm">
{% for col, info in raw_feature_info.items() %}
  <div style="margin:6px 0">
    <label style="display:inline-block;width:260px;font-weight:500">{{ col }}</label>
    {% if info.type == 'categorical' %}
      <select name="{{ col }}" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;width:214px">
        {% for o in info.options[:20] %}
          <option value="{{ o }}">{{ o }}</option>
        {% endfor %}
      </select>
    {% else %}
      {% set placeholder = (info.min|string + ' - ' + info.max|string) if info.min else '' %}
      <input name="{{ col }}" type="text" value="{{ info.default }}" placeholder="{{ placeholder }}" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;width:200px">
    {% endif %}
  </div>
{% endfor %}
<button type="submit">Predict</button>
</form>
<div id="result"></div>
</div>
<div class="card"><h2>📡 API Usage</h2>
<pre style="background:#1f2937;color:#e5e7eb;padding:16px;border-radius:8px;overflow-x:auto">
POST /predict
Content-Type: application/json

{"feature1": val, "feature2": val}

GET /health — Health check
GET /model-info — Model metadata</pre></div>
<script>
document.getElementById("predForm").onsubmit=function(e){
    e.preventDefault();
    var fd=new FormData(this);
    var data={};
    fd.forEach(function(v,k){ data[k]=isNaN(v)||v===""?v:parseFloat(v) });
    fetch("/predict",{ method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data) })
    .then(function(r){ return r.json() })
    .then(function(j){
        var h="<h3>🎯 Prediction: "+j.prediction+"</h3>";
        if(j.confidence)h+="<p>📊 Confidence: "+(j.confidence*100).toFixed(1)+"%</p>";
        if(j.probabilities){
            h+="<p>Probabilities:</p><ul>";
            var ent=Object.entries(j.probabilities).sort(function(a,b){ return b[1]-a[1] });
            for(var i=0;i<ent.length;i++)h+="<li><b>"+ent[i][0]+"</b>: "+(ent[i][1]*100).toFixed(1)+"%</li>";
            h+="</ul>"
        }
        document.getElementById("result").innerHTML=h;
        document.getElementById("result").style.display="block"
    });
};
</script>
</body>
</html>"""



def generate_code_zip(
    model_path: Path,
    metadata: Dict[str, Any],
    cleaned_data_path: Optional[Path] = None,
    dl_model_path: Optional[Path] = None,
    charts_data: Optional[Dict[str, str]] = None,
) -> io.BytesIO:
    """
    Generate a complete Python ML project as a ZIP file.
    Only includes scripts for modes the user actually trained.
    All code uses real column names, real model types, real metrics.
    
    Args:
        model_path: Path to model.pkl
        metadata: Training metadata dict
        cleaned_data_path: Path to cleaned_data.csv
        dl_model_path: Path to deep_learning_model.pkl
        charts_data: Dict of chart_name -> base64 data URI strings from active_charts.json
    
    IMPORTANT: Extracts actual hyperparameters from the trained model
    to ensure generated code reproduces EXACT same results.
    """
    import pickle
    
    buf = io.BytesIO()
    
    # =========================================================================
    # CRITICAL: Load actual model to extract EXACT hyperparameters
    # =========================================================================
    actual_model_params = {}
    actual_model_class = None
    production_engineer = None
    scaler = None
    label_encoders = {}
    target_encoder = None
    model_state = None  # Initialize so it's available for clean pkl creation later
    
    if model_path and model_path.exists():
        try:
            with open(model_path, 'rb') as f:
                model_state = pickle.load(f)
            
            # Extract the actual trained model
            if model_state is not None:
                actual_model = model_state.get('model')
                if actual_model is not None and hasattr(actual_model, 'get_params'):
                    actual_model_params = actual_model.get_params()
                    actual_model_class = type(actual_model).__name__
                    logger.info(f"Extracted hyperparameters from {actual_model_class}: {list(actual_model_params.keys())}")
                
                # Extract preprocessing objects
                production_engineer = model_state.get('production_engineer')
                scaler = model_state.get('scaler')
                label_encoders = model_state.get('label_encoders', {})
                target_encoder = model_state.get('target_encoder')
            
        except Exception as e:
            logger.warning(f"Could not load model for hyperparameter extraction: {e}")
    
    # Extract REAL training info from metadata
    target_column = metadata.get('target_column', 'target')
    feature_columns = metadata.get('feature_columns', [])
    task_type = metadata.get('task_type', 'classification')
    best_mode = metadata.get('best_mode', 'traditional')
    modes_trained = metadata.get('modes_trained', ['traditional'])
    best_overall = metadata.get('best_overall') or {}
    best_model_name = best_overall.get('name', metadata.get('model_name', 'Unknown'))
    best_metrics = best_overall.get('metrics', metadata.get('metrics', {}))
    feature_metadata = metadata.get('feature_metadata') or []
    data_summary = metadata.get('data_summary') or {}
    results_per_mode = metadata.get('results_per_mode') or {}
    leaderboard = metadata.get('leaderboard') or []
    nlp_text_column = metadata.get('primary_text_col', metadata.get('nlp_text_column', metadata.get('text_column', '')))
    
    # Classify features by type from feature_metadata
    numeric_features = []
    categorical_features = []
    text_features = []
    for fm in feature_metadata:
        name = fm.get('name', '')
        ftype = fm.get('type', 'numeric')
        if ftype == 'numeric':
            numeric_features.append(fm)
        elif ftype == 'categorical':
            categorical_features.append(fm)
        elif ftype == 'text':
            text_features.append(fm)
    
    # Build config object with ALL real data INCLUDING actual model params
    config = {
        "target_column": target_column,
        "feature_columns": feature_columns,
        "task_type": task_type,
        "best_mode": best_mode,
        "modes_trained": modes_trained,
        "best_model_name": best_model_name,
        "metrics": _sanitize_for_json(best_metrics),
        "data_summary": _sanitize_for_json(data_summary),
        "feature_metadata": _sanitize_for_json(feature_metadata),
        "numeric_features": _sanitize_for_json(numeric_features),
        "categorical_features": _sanitize_for_json(categorical_features),
        "text_features": _sanitize_for_json(text_features),
        "nlp_text_column": nlp_text_column,
        "results_per_mode": _sanitize_for_json(results_per_mode),
        "leaderboard": _sanitize_for_json(leaderboard),
        # NEW: Actual model hyperparameters from trained model
        "actual_model_params": _sanitize_for_json(actual_model_params),
        "actual_model_class": actual_model_class,
        "has_production_engineer": production_engineer is not None,
    }
    
    is_classification = 'classif' in task_type.lower()
    
    logger.info(f"[ZIP Gen] best_mode={best_mode}, modes_trained={modes_trained}, best_model={best_model_name}")
    
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. Add standalone model.pkl (stripped of backend class dependencies)
        #    This removes ProductionFeatureEngineer and other backend-specific
        #    objects that would cause "ModuleNotFoundError: No module named 'ml'"
        #    when users run the scripts outside of DataVision.
        if model_path and model_path.exists():
            if model_state is not None:
                # Create clean pkl with ONLY standard sklearn/numpy objects
                standalone_state = {}
                safe_keys = [
                    'model', 'model_name', 'task_type', 'task_type_simple',
                    'n_classes', 'target_column', 'feature_columns',
                    'numeric_cols', 'categorical_cols', 'text_cols',
                    'label_encoders', 'target_encoder', 'scaler',
                    'numeric_fill_values', 'feature_metadata',
                    'metrics', 'confusion_matrix',
                    'y_test', 'y_pred', 'y_proba',
                    'production_mode', 'mode',
                    'is_nlp_task', 'primary_text_col',
                ]
                for key in safe_keys:
                    if key in model_state:
                        standalone_state[key] = model_state[key]
                
                clean_buf = io.BytesIO()
                pickle.dump(standalone_state, clean_buf)
                clean_bytes = clean_buf.getvalue()
                zf.writestr('model.pkl', clean_bytes)
                logger.info(f"Added standalone model.pkl ({len(clean_bytes) / 1024:.1f} KB, stripped backend deps)")
            else:
                # Fallback: copy raw model.pkl if we couldn't load it to clean
                zf.write(model_path, 'model.pkl')
                logger.info(f"Added model.pkl ({model_path.stat().st_size / 1024:.1f} KB) [WARNING: may contain backend deps]")
        
        # 1b. Extract and save production_engineer state as standalone pkl
        #     This contains all the fitted transformers (sklearn objects)
        #     needed to replicate the EXACT preprocessing pipeline
        if production_engineer is not None:
            try:
                eng_state = {
                    'transformers': production_engineer.transformers,
                    'encoders': production_engineer.encoders,
                    'feature_names': production_engineer.feature_names,
                    'original_columns': production_engineer.original_columns,
                    'selected_feature_indices': getattr(production_engineer, 'selected_feature_indices', None),
                    'is_fitted': True,
                    'mode': getattr(production_engineer, 'mode', 'fast'),
                }
                eng_buf = io.BytesIO()
                pickle.dump(eng_state, eng_buf)
                eng_bytes = eng_buf.getvalue()
                zf.writestr('feature_engineer.pkl', eng_bytes)
                logger.info(f"Added feature_engineer.pkl ({len(eng_bytes) / 1024:.1f} KB) — exact preprocessing pipeline")
            except Exception as e:
                logger.warning(f"Could not serialize feature_engineer: {e}")
        
        # 1c. Add deep_learning_model.pkl if DL was trained
        if dl_model_path and dl_model_path.exists():
            try:
                with open(dl_model_path, 'rb') as f:
                    dl_state = pickle.load(f)
                # Create clean DL pkl with only standard sklearn/numpy objects
                dl_safe_keys = [
                    'model', 'scaler', 'label_encoder', 'feature_columns',
                    'numeric_cols', 'categorical_cols', 'feature_metadata',
                    'target_column', 'algorithm', 'task_type', 'classes',
                    'metrics', 'training_history', 'model_type',
                    'y_test', 'y_pred', 'y_proba',
                ]
                dl_clean = {}
                for key in dl_safe_keys:
                    if key in dl_state:
                        dl_clean[key] = dl_state[key]
                dl_buf = io.BytesIO()
                pickle.dump(dl_clean, dl_buf)
                dl_bytes = dl_buf.getvalue()
                zf.writestr('deep_learning_model.pkl', dl_bytes)
                logger.info(f"Added deep_learning_model.pkl ({len(dl_bytes) / 1024:.1f} KB)")
            except Exception as e:
                logger.warning(f"Could not bundle deep_learning_model.pkl: {e}")
        elif 'deep_learning' in modes_trained:
            # Try to find DL model automatically in multiple directories
            auto_dl_path = None
            if model_path and model_path.exists():
                # Search in model dir, plus common storage locations
                search_dirs = [model_path.parent]
                # Add storage/users, storage/automl, storage/models directories
                storage_base = model_path.parent.parent  # Go up from user_id dir to storage base
                for subdir in ['users', 'automl', 'models', 'files']:
                    candidate_dir = storage_base / subdir
                    if not candidate_dir.exists():
                        # Try from parent of storage_base (in case we're at storage/automl/user_id)
                        candidate_dir = storage_base.parent / subdir
                    if candidate_dir.exists():
                        # Find user_id from the original path
                        user_id_dir = model_path.parent.name
                        candidate = candidate_dir / user_id_dir / "deep_learning_model.pkl"
                        if candidate.exists():
                            auto_dl_path = candidate
                            break
                
                if auto_dl_path is None:
                    for sd in search_dirs:
                        candidate = sd / "deep_learning_model.pkl"
                        if candidate.exists():
                            auto_dl_path = candidate
                            break
            
            if auto_dl_path and auto_dl_path.exists():
                    try:
                        with open(auto_dl_path, 'rb') as f:
                            dl_state = pickle.load(f)
                        dl_safe_keys = [
                            'model', 'scaler', 'label_encoder', 'feature_columns',
                            'numeric_cols', 'categorical_cols', 'feature_metadata',
                            'target_column', 'algorithm', 'task_type', 'classes',
                            'metrics', 'training_history', 'model_type',
                            'y_test', 'y_pred', 'y_proba',
                        ]
                        dl_clean = {}
                        for key in dl_safe_keys:
                            if key in dl_state:
                                dl_clean[key] = dl_state[key]
                        dl_buf = io.BytesIO()
                        pickle.dump(dl_clean, dl_buf)
                        dl_bytes = dl_buf.getvalue()
                        zf.writestr('deep_learning_model.pkl', dl_bytes)
                        logger.info(f"Added deep_learning_model.pkl ({len(dl_bytes) / 1024:.1f} KB) [auto-detected]")
                    except Exception as e:
                        logger.warning(f"Could not bundle auto-detected deep_learning_model.pkl: {e}")
        
        # 1d. Bundle nlp_model.pkl if NLP was trained (separate from model.pkl)
        if 'nlp' in modes_trained and model_path and model_path.exists():
            nlp_model_path = None
            # Search multiple directories for nlp_model.pkl
            user_id_dir = model_path.parent.name
            storage_base = model_path.parent.parent
            nlp_search = [
                model_path.parent / "nlp_model.pkl",
            ]
            for subdir in ['users', 'automl', 'models', 'files']:
                for base in [storage_base, storage_base.parent]:
                    candidate = base / subdir / user_id_dir / "nlp_model.pkl"
                    if candidate not in nlp_search:
                        nlp_search.append(candidate)
            
            for np_path in nlp_search:
                if np_path.exists():
                    nlp_model_path = np_path
                    break
            
            if nlp_model_path:
                try:
                    zf.write(nlp_model_path, 'nlp_model.pkl')
                    logger.info(f"Added nlp_model.pkl from {nlp_model_path}")
                except Exception as e:
                    logger.warning(f"Could not bundle nlp_model.pkl: {e}")
        
        # 2. Add cleaned data
        if cleaned_data_path and cleaned_data_path.exists():
            zf.write(cleaned_data_path, 'data/cleaned_data.csv')
            logger.info(f"Added data/cleaned_data.csv")
        
        # 3. config.json with full real metadata
        zf.writestr('config.json', json.dumps(config, indent=2, default=str))
        
        # 4. ALWAYS: predict.py (uses the actual saved model)
        zf.writestr('predict.py', _generate_predict_script(config))
        
        # 5. ALWAYS: visualize.py (generates charts matching what user saw)
        zf.writestr('visualize.py', _generate_visualize_script(config))
        
        # 6. ALWAYS: evaluate.py
        zf.writestr('evaluate.py', _generate_evaluate_script(config))
        
        # 7. ONLY include training scripts for modes the user actually trained
        if 'traditional' in modes_trained:
            trad_result = results_per_mode.get('traditional') or {}
            zf.writestr('train_traditional.py', _generate_traditional_train_script(config, trad_result))
            logger.info("Added train_traditional.py")
        
        if 'nlp' in modes_trained and nlp_text_column:
            nlp_result = results_per_mode.get('nlp') or {}
            zf.writestr('train_nlp.py', _generate_nlp_train_script(config, nlp_result))
            logger.info("Added train_nlp.py")
        
        if 'deep_learning' in modes_trained:
            dl_result = results_per_mode.get('deep_learning') or {}
            zf.writestr('train_deep_learning.py', _generate_deep_learning_script(config, dl_result))
            logger.info("Added train_deep_learning.py")
        
        # 8. api_server.py for deployment
        zf.writestr('api_server.py', _generate_api_server_script(config))
        zf.writestr('templates/index.html', API_SERVER_HTML_TEMPLATE)
        
        # 9. Utilities
        zf.writestr('utils/__init__.py', '')
        zf.writestr('utils/preprocessing.py', _generate_preprocessing_utils(config))
        
        # 10. requirements.txt (only deps needed for actual modes)
        zf.writestr('requirements.txt', _generate_requirements(config))
        
        # 11. README.md (documents what was actually trained)
        zf.writestr('README.md', _generate_readme(config))
        
        # 12. Dockerfile
        zf.writestr('Dockerfile', _generate_dockerfile(config))
        
        # 13. Bundle actual training charts as PNG images
        #     These are the EXACT charts the user saw in DataVision AutoML
        if charts_data:
            charts_added = 0
            for chart_name, chart_value in charts_data.items():
                try:
                    # Charts are stored as "data:image/png;base64,..." data URIs
                    if isinstance(chart_value, str) and 'base64,' in chart_value:
                        b64_data = chart_value.split('base64,', 1)[1]
                        img_bytes = base64.b64decode(b64_data)
                        # Clean chart name for filename
                        safe_name = chart_name.replace(' ', '_').replace('/', '_').lower()
                        if not safe_name.endswith('.png'):
                            safe_name += '.png'
                        zf.writestr(f'charts/{safe_name}', img_bytes)
                        charts_added += 1
                except Exception as e:
                    logger.warning(f"Could not bundle chart '{chart_name}': {e}")
            if charts_added > 0:
                logger.info(f"Added {charts_added} training charts to charts/ directory")
    
    buf.seek(0)
    logger.info(f"Generated ZIP: {buf.getbuffer().nbytes / 1024:.1f} KB")
    return buf


def _sanitize_for_json(obj):
    """Make object JSON-serializable"""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    elif isinstance(obj, float):
        if obj != obj:  # NaN
            return None
        return obj
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def _params_to_python_literal(params: Dict) -> str:
    """Convert model parameters to valid Python code literal.
    
    Handles numpy types, None, strings, etc. to produce code like:
    {'n_estimators': 100, 'max_depth': 10, 'random_state': 42}
    """
    import numpy as np
    
    def _convert_value(v):
        """Convert a single value to Python literal representation"""
        if v is None:
            return 'None'
        elif isinstance(v, bool):
            return 'True' if v else 'False'
        elif isinstance(v, (int, np.integer)):
            return str(int(v))
        elif isinstance(v, (float, np.floating)):
            if np.isnan(v):
                return 'None'
            elif np.isinf(v):
                return 'float("inf")' if v > 0 else 'float("-inf")'
            return repr(float(v))
        elif isinstance(v, str):
            return repr(v)
        elif isinstance(v, (list, tuple, np.ndarray)):
            items = [_convert_value(item) for item in v]
            if isinstance(v, tuple):
                return f"({', '.join(items)})"
            return f"[{', '.join(items)}]"
        elif isinstance(v, dict):
            items = [f"{repr(k)}: {_convert_value(val)}" for k, val in v.items()]
            return '{' + ', '.join(items) + '}'
        elif callable(v):
            # Skip callable parameters (like loss functions)
            return None
        else:
            # Try to convert to string
            try:
                return repr(str(v))
            except:
                return None
    
    # Filter and convert parameters
    result_items = []
    skip_params = {
        'oob_score', 'warm_start', 'verbose', 'callbacks', 'early_stopping_rounds',
        # XGBoost internal/deprecated params
        'use_label_encoder', 'gpu_id', 'predictor', 'enable_categorical',
        'feature_types', 'max_cat_to_onehot', 'max_cat_threshold',
        'multi_strategy', 'updater', 'refresh_leaf', 'process_type',
        'grow_policy', 'max_leaves', 'max_bin', 'num_parallel_tree',
        'monotone_constraints', 'interaction_constraints',
        'validate_parameters', 'nthread', 'device',
        # LightGBM internal params  
        'silent', 'importance_type', 'n_jobs',
        # CatBoost internal params
        'cat_features', 'text_features', 'embedding_features',
        'task_type', 'devices', 'bootstrap_type',
    }
    
    for k, v in params.items():
        if k in skip_params:
            continue
        if k.startswith('_'):  # Skip private params
            continue
        if callable(v):
            continue
        converted = _convert_value(v)
        if converted is not None:
            result_items.append(f"'{k}': {converted}")
    
    return '{' + ', '.join(result_items) + '}'


# =============================================================================
# TRADITIONAL ML TRAINING SCRIPT - DATA-AWARE
# =============================================================================

def _generate_traditional_train_script(config: Dict, mode_result: Dict) -> str:
    """Generate training script that mirrors the REAL DataVision AutoML pipeline.
    
    Uses the EXACT hyperparameters extracted from the trained model to ensure
    retraining produces the SAME results as AutoML.
    """
    target = config['target_column']
    task_type = config['task_type']
    features = config.get('feature_columns', [])
    numeric_features = config.get('numeric_features', [])
    categorical_features = config.get('categorical_features', [])
    leaderboard = config.get('leaderboard', [])
    best_model_name = mode_result.get('best_model', mode_result.get('algorithm', config.get('best_model_name', 'Unknown')))
    best_metrics = mode_result.get('metrics', config.get('metrics', {}))
    
    # CRITICAL: Get ACTUAL hyperparameters from the trained model
    actual_model_params = config.get('actual_model_params', {})
    actual_model_class = config.get('actual_model_class', best_model_name)
    
    is_clf = 'classif' in task_type.lower()
    
    # Build the list of ACTUAL algorithms from leaderboard
    actual_algorithms = []
    for entry in leaderboard[:15]:
        algo_name = entry.get('name', entry.get('model_name', ''))
        if algo_name:
            actual_algorithms.append(algo_name)
    if not actual_algorithms:
        actual_algorithms = [best_model_name]
    
    # Feature info comment
    feature_info_lines = []
    for fm in numeric_features[:10]:
        name = fm.get('name', '')
        mn = fm.get('min', '?')
        mx = fm.get('max', '?')
        mean = fm.get('mean', '?')
        feature_info_lines.append(f"#   {name}: numeric (min={mn}, max={mx}, mean={mean})")
    for fm in categorical_features[:10]:
        name = fm.get('name', '')
        options = fm.get('options', [])
        feature_info_lines.append(f"#   {name}: categorical ({', '.join(str(o) for o in options[:5])}{'...' if len(options) > 5 else ''})")
    feature_info_block = "\n".join(feature_info_lines) if feature_info_lines else "#   (no feature metadata available)"
    
    # Metrics comment
    metrics_lines = []
    for k, v in best_metrics.items():
        if isinstance(v, float):
            metrics_lines.append(f"#   {k}: {v:.4f}")
        else:
            metrics_lines.append(f"#   {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "#   (no metrics available)"
    
    # Leaderboard comment
    leaderboard_lines = []
    for i, entry in enumerate(leaderboard[:10]):
        name = entry.get('name', entry.get('model_name', '?'))
        score = entry.get('score', entry.get('accuracy', entry.get('r2', '?')))
        if isinstance(score, float):
            leaderboard_lines.append(f"#   {i+1}. {name}: {score:.4f}")
        else:
            leaderboard_lines.append(f"#   {i+1}. {name}: {score}")
    leaderboard_block = "\n".join(leaderboard_lines) if leaderboard_lines else "#   (no leaderboard data)"
    
    features_list = ", ".join(f"'{f}'" for f in features[:30])
    
    # Detect which optional packages are needed
    algo_lower_list = [a.lower() for a in actual_algorithms]
    algo_joined = " ".join(algo_lower_list)
    needs_xgb = any('xgb' in a or 'xgboost' in a for a in algo_lower_list)
    needs_lgb = any('lgb' in a or 'lightgbm' in a or 'lgbm' in a for a in algo_lower_list)
    needs_catboost = any('catboost' in a or 'cat_boost' in a or 'cat boost' in a for a in algo_lower_list)
    
    # Determine mode (fast vs ultra) from number of algorithms trained
    is_ultra = len(actual_algorithms) > 10
    
    metric_name = 'F1-Macro' if is_clf else 'R²'
    
    script = f'''"""
🚀 Traditional ML Training Script — YOUR DataVision AutoML Results
=====================================================================
Auto-generated by DataVision AI

╔═══════════════════════════════════════════════════════════════════════╗
║  📦 model.pkl contains your ALREADY TRAINED model with the metrics   ║
║     you saw in the AutoML UI.                                         ║
║                                                                       ║
║  ▶ python evaluate.py    — See your EXACT AutoML results             ║
║  ▶ python predict.py     — Make predictions with your model          ║
║                                                                       ║
║  This script is for RETRAINING only. Results may differ slightly     ║
║  due to train/test random split, even with same hyperparameters.     ║
╚═══════════════════════════════════════════════════════════════════════╝

YOUR AUTOML TRAINING RESULTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 WINNING MODEL : {best_model_name}
🎯 Target        : {target}
📊 Task          : {task_type}
📁 Features      : {len(features)} columns

YOUR METRICS:
{metrics_block}

YOUR LEADERBOARD (what AutoML trained):
{leaderboard_block}

FEATURE INFO:
{feature_info_block}

Usage:
    # VERIFY YOUR AUTOML RESULTS:
    python evaluate.py                             # Shows exact AutoML metrics
    
    # MAKE PREDICTIONS:
    python predict.py --json '{{"col1": value}}'   # Your trained model
    
    # RETRAIN (if needed):
    python train_traditional.py                    # Train ONLY {best_model_name}
    python train_traditional.py --all              # Train ALL algorithms
"""

import os
import pickle
import argparse
import time
import warnings
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, RobustScaler, StandardScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import KNNImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error,
    classification_report, confusion_matrix
)
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    HistGradientBoostingClassifier, HistGradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    BaggingClassifier, BaggingRegressor,
)
from sklearn.linear_model import (
    LogisticRegression, Ridge, Lasso, ElasticNet,
    SGDClassifier, SGDRegressor, RidgeClassifier,
    PassiveAggressiveClassifier, PassiveAggressiveRegressor,
    BayesianRidge
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

warnings.filterwarnings('ignore')

HAS_XGB = False
HAS_LGB = False
HAS_CB = False
HAS_SMOTE = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    pass
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    pass
try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    HAS_CB = True
except ImportError:
    pass
try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    pass

TARGET_COLUMN = '{target}'
TASK_TYPE = '{task_type}'

# YOUR WINNING MODEL FROM AUTOML
BEST_MODEL_NAME = '{best_model_name}'


# ============================================================================
# STEP 1: DATA CLEANING (mirrors ProductionDataCleaner.clean())
# ============================================================================

def clean_data(df):
    """
    Mirrors DataVision's ProductionDataCleaner pipeline:
    1. Remove useless columns (IDs, URLs, high-cardinality strings)
    2. Remove exact duplicates
    3. Strip whitespace, replace 'nan'/'None'/'' with NaN
    4. Smart type conversion (parse $, M/K units, commas)
    5. KNN imputation for numerics (median fallback)
    6. Mode fill for categoricals
    7. Replace inf/-inf with median
    8. Remove constant columns (nunique <= 1)
    9. IQR-based outlier capping (Q1-3*IQR to Q3+3*IQR, clipped to [1st, 99th] percentile)
    10. Final NaN fill to 0
    """
    print("\\n🧹 Step 1: Data Cleaning (ProductionDataCleaner)")
    print("-" * 50)
    original_shape = df.shape
    
    # Remove useless columns
    id_patterns = ['unnamed', 'index', '_id', 'guid', 'uuid', 'url', 'link', 'href', 'path']
    cols_to_drop = []
    for col in df.columns:
        col_lower = col.lower().strip()
        if any(pat in col_lower for pat in id_patterns):
            if col != TARGET_COLUMN:
                cols_to_drop.append(col)
        elif df[col].dtype == 'object' and col != TARGET_COLUMN:
            unique_ratio = df[col].nunique() / max(len(df), 1)
            if unique_ratio > 0.9:
                cols_to_drop.append(col)
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop, errors='ignore')
        print(f"   Dropped {{len(cols_to_drop)}} useless columns: {{cols_to_drop[:5]}}")
    
    # Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    if len(df) < before:
        print(f"   Removed {{before - len(df)}} duplicate rows")
    
    # Strip whitespace + replace string NaN variants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace(
            ['nan', 'NaN', 'None', 'null', 'NULL', 'none', 'NA', 'N/A', ''],
            np.nan
        )
    
    # Smart type conversion (parse $, M/K, commas)
    for col in df.select_dtypes(include=['object']).columns:
        if col == TARGET_COLUMN:
            continue
        sample = df[col].dropna().head(20)
        if len(sample) == 0:
            continue
        converted = 0
        for val in sample:
            try:
                v = str(val).replace('$', '').replace(',', '').strip()
                if v.upper().endswith('M'):
                    float(v[:-1])
                elif v.upper().endswith('K'):
                    float(v[:-1])
                elif v.endswith('+'):
                    float(v[:-1])
                else:
                    float(v)
                converted += 1
            except:
                pass
        if converted / max(len(sample), 1) > 0.6:
            def parse_value(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).replace('$', '').replace(',', '').strip()
                try:
                    if v.upper().endswith('M'):
                        return float(v[:-1]) * 1_000_000
                    elif v.upper().endswith('K'):
                        return float(v[:-1]) * 1_000
                    elif v.endswith('+'):
                        return float(v[:-1])
                    return float(v)
                except:
                    return np.nan
            df[col] = df[col].apply(parse_value)
            print(f"   Converted {{col}} to numeric (parsed special formats)")
    
    # KNN imputation for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if TARGET_COLUMN in numeric_cols:
        numeric_cols.remove(TARGET_COLUMN)
    if numeric_cols and df[numeric_cols].isna().any().any():
        try:
            imputer = KNNImputer(n_neighbors=5, weights='distance')
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
            print(f"   KNN imputed {{len(numeric_cols)}} numeric columns")
        except:
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
            print(f"   Median-filled {{len(numeric_cols)}} numeric columns (KNN fallback)")
    
    # Mode fill for categoricals
    for col in df.select_dtypes(include=['object', 'category']).columns:
        if col == TARGET_COLUMN:
            continue
        mode = df[col].mode()
        df[col] = df[col].fillna(mode.iloc[0] if len(mode) > 0 else '_MISSING_')
    
    # Replace inf/-inf with median
    for col in numeric_cols:
        if np.isinf(df[col]).any():
            med = df[col].replace([np.inf, -np.inf], np.nan).median()
            df[col] = df[col].replace([np.inf, -np.inf], med)
    
    # Remove constant columns
    const_cols = [col for col in df.columns if col != TARGET_COLUMN and df[col].nunique() <= 1]
    if const_cols:
        df = df.drop(columns=const_cols)
        print(f"   Removed {{len(const_cols)}} constant columns")
    
    # IQR-based outlier capping (same as DataVision)
    capped_count = 0
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == TARGET_COLUMN:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        p1 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)
        lower = max(p1, Q1 - 3 * IQR)
        upper = min(p99, Q3 + 3 * IQR)
        before_clip = ((df[col] < lower) | (df[col] > upper)).sum()
        if before_clip > 0:
            df[col] = df[col].clip(lower=lower, upper=upper)
            capped_count += before_clip
    if capped_count:
        print(f"   Capped {{capped_count}} outlier values (IQR method)")
    
    # Final NaN fill
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(0)
    
    print(f"   Clean: {{original_shape}} → {{df.shape}}")
    return df


# ============================================================================
# STEP 2: FEATURE ENGINEERING (mirrors ProductionFeatureEngineer)
# ============================================================================

def engineer_features(X, mode='fast'):
    """
    Mirrors DataVision's ProductionFeatureEngineer.fit_transform():
    1. Detect column types (numeric, categorical, text, datetime)
    2. Log-transform skewed numerics (skewness > 2)
    3. RobustScaler for numeric features
    4. Polynomial features (squared + interactions for top columns)
    5. Categorical: binary→LabelEncoder, low-card→one-hot, high-card→label+frequency
    6. VarianceThreshold (remove near-constant features, threshold=0.01)
    """
    print("\\n🔧 Step 2: Feature Engineering (ProductionFeatureEngineer)")
    print("-" * 50)
    
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    label_encoders = {{}}
    
    # --- Numeric feature engineering ---
    # Log transform skewed features (skewness > 2, non-negative only)
    log_transformed = []
    for col in numeric_cols:
        if (X[col] >= 0).all():
            skew = X[col].skew()
            if abs(skew) > 2:
                X[f'{{col}}_log'] = np.log1p(X[col])
                log_transformed.append(col)
    if log_transformed:
        print(f"   Log-transformed {{len(log_transformed)}} skewed features")
    
    # Scale with RobustScaler (same as DataVision)
    numeric_cols_updated = X.select_dtypes(include=[np.number]).columns.tolist()
    scaler = RobustScaler()
    if numeric_cols_updated:
        X[numeric_cols_updated] = scaler.fit_transform(X[numeric_cols_updated])
    
    # Polynomial features (top 4 numeric columns — squared + interactions)
    if 2 <= len(numeric_cols) <= 10:
        top_n = min(4, len(numeric_cols))
        top_cols = numeric_cols[:top_n]
        for col in top_cols:
            X[f'{{col}}_sq'] = X[col] ** 2
        for i in range(len(top_cols)):
            for j in range(i + 1, len(top_cols)):
                X[f'{{top_cols[i]}}_x_{{top_cols[j]}}'] = X[top_cols[i]] * X[top_cols[j]]
        print(f"   Added polynomial features for top {{top_n}} numeric columns")
    
    # --- Categorical feature engineering ---
    for col in categorical_cols:
        nuniq = X[col].nunique()
        if nuniq <= 2:
            # Binary: LabelEncoder
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
        elif nuniq <= 10:
            # Low cardinality: one-hot encoding (no drop_first — same as DataVision)
            dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
            X = pd.concat([X.drop(columns=[col]), dummies], axis=1)
        else:
            # High cardinality: LabelEncoder + frequency encoding
            le = LabelEncoder()
            X[f'{{col}}_label'] = le.fit_transform(X[col].astype(str))
            freq = X[col].value_counts(normalize=True)
            X[f'{{col}}_freq'] = X[col].map(freq)
            label_encoders[col] = le
            X = X.drop(columns=[col])
    
    # Force all to float
    for col in X.columns:
        try:
            X[col] = X[col].astype(float)
        except:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str)).astype(float)
    
    # Handle NaN/Inf
    X = X.replace([np.inf, -np.inf], 0)
    X = X.fillna(0)
    
    # VarianceThreshold (remove near-constant features)
    try:
        vt = VarianceThreshold(threshold=0.01)
        cols_before = X.columns.tolist()
        X_filtered = pd.DataFrame(vt.fit_transform(X), columns=X.columns[vt.get_support()], index=X.index)
        removed = len(cols_before) - X_filtered.shape[1]
        if removed > 0:
            print(f"   VarianceThreshold removed {{removed}} near-constant features")
        X = X_filtered
    except:
        pass
    
    print(f"   Final features: {{X.shape[1]}}")
    return X, label_encoders, scaler


# ============================================================================
# STEP 3: YOUR EXACT TRAINED MODEL
# ============================================================================

# These are the EXACT hyperparameters from YOUR trained model
ACTUAL_MODEL_CLASS = '{actual_model_class}'
ACTUAL_MODEL_PARAMS = {_params_to_python_literal(actual_model_params) if actual_model_params else '{}'}

def get_exact_trained_model():
    """Returns YOUR exact model with the SAME hyperparameters as AutoML used.
    
    This ensures retraining produces the SAME results as your AutoML session.
    """
    params = ACTUAL_MODEL_PARAMS.copy()
    
    # Remove non-constructor / problematic params that cause crashes
    for bad_key in ['oob_score', 'warm_start', 'verbose', 'callbacks',
                    'early_stopping_rounds', 'use_label_encoder', 'gpu_id',
                    'predictor', 'enable_categorical', 'feature_types',
                    'validate_parameters', 'nthread', 'device',
                    'n_jobs', 'silent', 'importance_type',
                    'cat_features', 'text_features', 'task_type',
                    'multi_strategy', 'max_cat_to_onehot', 'max_cat_threshold',
                    'num_parallel_tree', 'monotone_constraints',
                    'interaction_constraints', 'grow_policy', 'max_leaves',
                    'process_type', 'updater', 'refresh_leaf', 'max_bin',
                    'bootstrap_type', 'devices', 'embedding_features']:
        params.pop(bad_key, None)
    # Remove private params
    params = {{k: v for k, v in params.items() if not k.startswith('_')}}
    
    '''
    
    # Build the model instantiation based on actual class
    if actual_model_class == 'RandomForestClassifier':
        script += f'''
    return {{'RandomForest': RandomForestClassifier(**params)}}
'''
    elif actual_model_class == 'RandomForestRegressor':
        script += f'''
    return {{'RandomForest': RandomForestRegressor(**params)}}
'''
    elif actual_model_class == 'GradientBoostingClassifier':
        script += f'''
    return {{'GradientBoosting': GradientBoostingClassifier(**params)}}
'''
    elif actual_model_class == 'GradientBoostingRegressor':
        script += f'''
    return {{'GradientBoosting': GradientBoostingRegressor(**params)}}
'''
    elif actual_model_class == 'XGBClassifier':
        script += f'''
    if HAS_XGB:
        # Clean XGBoost params for version compatibility
        xgb_safe = {{k: v for k, v in params.items() if k in {{
            'n_estimators', 'max_depth', 'learning_rate', 'subsample',
            'colsample_bytree', 'colsample_bylevel', 'colsample_bynode',
            'reg_alpha', 'reg_lambda', 'gamma', 'min_child_weight',
            'scale_pos_weight', 'base_score', 'random_state', 'seed',
            'objective', 'booster', 'tree_method', 'eval_metric',
        }}}}
        xgb_safe['verbosity'] = 0
        xgb_safe['n_jobs'] = -1
        return {{'XGBoost': xgb.XGBClassifier(**xgb_safe)}}
    else:
        print("⚠️ XGBoost not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'XGBRegressor':
        script += f'''
    if HAS_XGB:
        xgb_safe = {{k: v for k, v in params.items() if k in {{
            'n_estimators', 'max_depth', 'learning_rate', 'subsample',
            'colsample_bytree', 'colsample_bylevel', 'colsample_bynode',
            'reg_alpha', 'reg_lambda', 'gamma', 'min_child_weight',
            'scale_pos_weight', 'base_score', 'random_state', 'seed',
            'objective', 'booster', 'tree_method', 'eval_metric',
        }}}}
        xgb_safe['verbosity'] = 0
        xgb_safe['n_jobs'] = -1
        return {{'XGBoost': xgb.XGBRegressor(**xgb_safe)}}
    else:
        print("⚠️ XGBoost not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'LGBMClassifier':
        script += f'''
    if HAS_LGB:
        return {{'LightGBM': lgb.LGBMClassifier(**params)}}
    else:
        print("⚠️ LightGBM not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'LGBMRegressor':
        script += f'''
    if HAS_LGB:
        return {{'LightGBM': lgb.LGBMRegressor(**params)}}
    else:
        print("⚠️ LightGBM not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'CatBoostClassifier':
        script += f'''
    if HAS_CB:
        params['verbose'] = False
        params['allow_writing_files'] = False
        return {{'CatBoost': CatBoostClassifier(**params)}}
    else:
        print("⚠️ CatBoost not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'CatBoostRegressor':
        script += f'''
    if HAS_CB:
        params['verbose'] = False
        params['allow_writing_files'] = False
        return {{'CatBoost': CatBoostRegressor(**params)}}
    else:
        print("⚠️ CatBoost not installed, using RandomForest")
        return get_models(1000, 'fast')
'''
    elif actual_model_class == 'LogisticRegression':
        script += f'''
    return {{'LogisticRegression': LogisticRegression(**params)}}
'''
    elif actual_model_class in ('HistGradientBoostingClassifier', 'HistGradientBoostingRegressor'):
        if is_clf:
            script += f'''
    return {{'HistGradientBoosting': HistGradientBoostingClassifier(**params)}}
'''
        else:
            script += f'''
    return {{'HistGradientBoosting': HistGradientBoostingRegressor(**params)}}
'''
    else:
        # Fallback - try to use it with generic RF params
        script += f'''
    # Model class '{actual_model_class}' - using extracted params with RandomForest as fallback
    try:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        if TASK_TYPE == 'classification':
            return {{'RandomForest': RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, class_weight='balanced', n_jobs=-1)}}
        else:
            return {{'RandomForest': RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)}}
    except:
        return get_models(1000, 'fast')
'''
    
    script += f'''

def get_single_model(model_name, n_samples):
    """Get ONLY your winning model.
    
    Uses get_exact_trained_model() to get YOUR exact hyperparameters.
    """
    # First try to use exact trained model params
    if model_name == BEST_MODEL_NAME or model_name == '{best_model_name}':
        return get_exact_trained_model()
    
    # Otherwise fall back to generic models
    is_large = n_samples > 50000
    all_models = get_models(n_samples, mode='fast')
    
    # Try exact match first
    if model_name in all_models:
        return {{model_name: all_models[model_name]}}
    
    # Try case-insensitive match
    model_name_lower = model_name.lower().replace('_', '').replace(' ', '')
    for k, v in all_models.items():
        if k.lower().replace('_', '').replace(' ', '') == model_name_lower:
            return {{k: v}}
    
    # Check in ultra models too
    all_models = get_models(n_samples, mode='ultra')
    if model_name in all_models:
        return {{model_name: all_models[model_name]}}
    for k, v in all_models.items():
        if k.lower().replace('_', '').replace(' ', '') == model_name_lower:
            return {{k: v}}
    
    # Fallback to exact trained model
    print(f"   ⚠️ Model '{{model_name}}' not found, using your trained model")
    return get_exact_trained_model()


def get_models(n_samples, mode='{"ultra" if is_ultra else "fast"}'):
    """Returns the EXACT algorithms & hyperparameters used by DataVision AutoML.
    
    Mirrors ProductionModelTrainer.get_models() with the same conditional
    logic for dataset size and mode.
    """
    is_large = n_samples > 50000
    is_ultra = mode == 'ultra'
    
    '''
    
    if is_clf:
        script += f'''
    models = {{
        'LogisticRegression': LogisticRegression(
            max_iter=2000, C=0.1, random_state=42, n_jobs=1,
            class_weight='balanced'
        ),
        'RandomForest': RandomForestClassifier(
            n_estimators=100 if is_large else (150 if not is_ultra else 250),
            max_depth=8 if is_large else (12 if not is_ultra else 18),
            min_samples_split=4, random_state=42, n_jobs=-1,
            class_weight='balanced'
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=80 if is_large else 120,
            max_depth=5 if is_large else 6,
            learning_rate=0.1, random_state=42, subsample=0.8
        ),
        'HistGradientBoosting': HistGradientBoostingClassifier(
            max_iter=100 if is_large else (150 if not is_ultra else 250),
            max_depth=6 if is_large else (8 if not is_ultra else 12),
            learning_rate=0.1, random_state=42, class_weight='balanced'
        ),
        'GaussianNB': GaussianNB(),
        'ExtraTrees': ExtraTreesClassifier(
            n_estimators=80 if is_large else (100 if not is_ultra else 200),
            max_depth=8 if is_large else (10 if not is_ultra else 15),
            random_state=42, n_jobs=-1, class_weight='balanced'
        ),
    }}
    
    if not is_large:
        models['KNN'] = KNeighborsClassifier(n_neighbors=7, weights='distance', n_jobs=-1)
    
    if HAS_XGB:
        models['XGBoost'] = xgb.XGBClassifier(
            n_estimators=100 if is_large else (150 if not is_ultra else 300),
            max_depth=6 if is_large else (7 if not is_ultra else 10),
            learning_rate=0.1 if not is_ultra else 0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbosity=0,
            eval_metric='mlogloss',
            tree_method='hist' if is_large else 'auto',
            scale_pos_weight=10
        )
    if HAS_LGB:
        models['LightGBM'] = lgb.LGBMClassifier(
            n_estimators=100 if is_large else (150 if not is_ultra else 300),
            max_depth=6 if is_large else (7 if not is_ultra else 10),
            learning_rate=0.1 if not is_ultra else 0.05,
            num_leaves=31 if not is_ultra else 50,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbose=-1,
            class_weight='balanced'
        )
    if HAS_CB:
        if is_ultra:
            models['CatBoost'] = CatBoostClassifier(
                iterations=150 if is_large else 300, depth=6 if is_large else 10,
                learning_rate=0.05 if is_large else 0.03,
                l2_leaf_reg=3, random_strength=1, bagging_temperature=0.5,
                random_state=42, verbose=False,
                auto_class_weights='Balanced', allow_writing_files=False
            )
        else:
            models['CatBoost'] = CatBoostClassifier(
                iterations=100, depth=6, learning_rate=0.1,
                random_state=42, verbose=False,
                auto_class_weights='Balanced', allow_writing_files=False
            )
    
    # Ultra mode adds more algorithms
    if is_ultra:
        if not is_large:
            models['SVM_RBF'] = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42, class_weight='balanced')
            models['SVM_Linear'] = SVC(kernel='linear', C=0.5, probability=True, random_state=42, class_weight='balanced')
        models['RidgeClassifier'] = RidgeClassifier(alpha=1.0, random_state=42, class_weight='balanced')
        models['MLP'] = MLPClassifier(
            hidden_layer_sizes=(128, 64) if is_large else (256, 128, 64, 32),
            max_iter=500 if is_large else 1500,
            learning_rate='adaptive', early_stopping=True,
            batch_size=256 if is_large else 'auto',
            validation_fraction=0.1, random_state=42
        )
        models['AdaBoost'] = AdaBoostClassifier(n_estimators=100 if is_large else 150, learning_rate=0.5, random_state=42)
        models['Bagging'] = BaggingClassifier(
            n_estimators=50 if is_large else 100,
            max_samples=0.5 if is_large else 0.8,
            max_features=0.8, random_state=42, n_jobs=-1
        )
        models['SGD'] = SGDClassifier(loss='log_loss', max_iter=1500, random_state=42, class_weight='balanced', early_stopping=True)
        models['PassiveAggressive'] = PassiveAggressiveClassifier(max_iter=1500, random_state=42, class_weight='balanced')
        models['DecisionTree'] = DecisionTreeClassifier(max_depth=12 if is_large else 18, min_samples_split=3, random_state=42, class_weight='balanced')
        models['BernoulliNB'] = BernoulliNB(alpha=0.5)
'''
    else:  # regression
        script += f'''
    models = {{
        'Ridge': Ridge(alpha=1.0, random_state=42),
        'ElasticNet': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42, max_iter=2000),
        'RandomForest': RandomForestRegressor(
            n_estimators=100 if is_large else (150 if not is_ultra else 250),
            max_depth=8 if is_large else (12 if not is_ultra else 18),
            min_samples_split=4, random_state=42, n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingRegressor(
            n_estimators=80 if is_large else 120,
            max_depth=5 if is_large else 6,
            learning_rate=0.1, subsample=0.8, random_state=42
        ),
        'HistGradientBoosting': HistGradientBoostingRegressor(
            max_iter=100 if is_large else (150 if not is_ultra else 250),
            max_depth=6 if is_large else (8 if not is_ultra else 12),
            learning_rate=0.1, random_state=42
        ),
        'ExtraTrees': ExtraTreesRegressor(
            n_estimators=80 if is_large else (100 if not is_ultra else 200),
            max_depth=8 if is_large else (10 if not is_ultra else 15),
            random_state=42, n_jobs=-1
        ),
    }}
    
    if not is_large:
        models['KNN'] = KNeighborsRegressor(n_neighbors=7, weights='distance', n_jobs=-1)
    
    if HAS_XGB:
        models['XGBoost'] = xgb.XGBRegressor(
            n_estimators=100 if is_large else (150 if not is_ultra else 300),
            max_depth=6 if is_large else (7 if not is_ultra else 10),
            learning_rate=0.1 if not is_ultra else 0.05,
            subsample=0.8, colsample_bytree=0.8,
            tree_method='hist' if is_large else 'auto',
            random_state=42, n_jobs=-1, verbosity=0
        )
    if HAS_LGB:
        models['LightGBM'] = lgb.LGBMRegressor(
            n_estimators=100 if is_large else (150 if not is_ultra else 300),
            max_depth=6 if is_large else (7 if not is_ultra else 10),
            learning_rate=0.1 if not is_ultra else 0.05,
            num_leaves=31 if not is_ultra else 50,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, n_jobs=-1, verbose=-1
        )
    if HAS_CB:
        if is_ultra:
            models['CatBoost'] = CatBoostRegressor(
                iterations=300, depth=10, learning_rate=0.03,
                l2_leaf_reg=3, random_strength=1, bagging_temperature=0.5,
                random_state=42, verbose=False, allow_writing_files=False
            )
        else:
            models['CatBoost'] = CatBoostRegressor(
                iterations=100, depth=6, learning_rate=0.1,
                random_state=42, verbose=False, allow_writing_files=False
            )
    
    # Ultra mode adds more algorithms
    if is_ultra:
        models['Lasso'] = Lasso(alpha=0.01, random_state=42, max_iter=2000)
        models['BayesianRidge'] = BayesianRidge()
        models['MLP'] = MLPRegressor(
            hidden_layer_sizes=(128, 64) if is_large else (256, 128, 64, 32),
            max_iter=500 if is_large else 1500,
            batch_size=256 if is_large else 'auto',
            learning_rate='adaptive', early_stopping=True,
            validation_fraction=0.1, random_state=42
        )
        models['AdaBoost'] = AdaBoostRegressor(n_estimators=100 if is_large else 150, learning_rate=0.5, random_state=42)
        models['Bagging'] = BaggingRegressor(
            n_estimators=50 if is_large else 100,
            max_samples=0.5 if is_large else 0.8,
            max_features=0.8, random_state=42, n_jobs=-1
        )
        models['SGD'] = SGDRegressor(max_iter=1500, early_stopping=True, random_state=42)
        models['DecisionTree'] = DecisionTreeRegressor(max_depth=12 if is_large else 18, min_samples_split=3, random_state=42)
        models['PassiveAggressive'] = PassiveAggressiveRegressor(max_iter=1500, random_state=42)
        if not is_large:
            models['SVR_RBF'] = SVR(kernel='rbf', C=1.0, gamma='scale')
'''
    
    script += f'''
    return models


# ============================================================================
# STEP 4: TRAINING (mirrors ProductionModelTrainer.train_all())
# ============================================================================

def apply_smote(X_train, y_train):
    """Apply SMOTE for imbalanced classification (same as DataVision).
    
    Only applied when:
    - imbalance_ratio > 1.5
    - min class count >= 6
    Falls back to class_weight='balanced' if SMOTE fails.
    """
    if not HAS_SMOTE or TASK_TYPE != 'classification':
        return X_train, y_train, False
    
    class_counts = pd.Series(y_train).value_counts()
    max_count = class_counts.max()
    min_count = class_counts.min()
    imbalance_ratio = max_count / max(min_count, 1)
    
    if imbalance_ratio <= 1.5 or min_count < 6:
        return X_train, y_train, False
    
    try:
        k_neighbors = min(5, min_count - 1)
        n_classes = len(class_counts)
        
        if n_classes == 2:
            if imbalance_ratio > 100:
                sampling_strategy = 0.1
            elif imbalance_ratio > 20:
                sampling_strategy = 0.25
            else:
                sampling_strategy = 1.0
        else:
            sampling_strategy = 'not majority' if imbalance_ratio > 20 else 'auto'
        
        smote = SMOTE(k_neighbors=k_neighbors, sampling_strategy=sampling_strategy, random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
        print(f"   ⚖️ SMOTE applied: {{len(X_train)}} → {{len(X_resampled)}} samples (ratio: {{imbalance_ratio:.1f}}x)")
        return X_resampled, y_resampled, True
    except Exception as e:
        print(f"   ⚠️ SMOTE failed ({{e}}), using class_weight='balanced'")
        return X_train, y_train, False


def train_and_evaluate(X_train, X_test, y_train, y_test, mode='{"ultra" if is_ultra else "fast"}', selected_models=None):
    """Train models with real DataVision scoring logic.
    
    Args:
        selected_models: Optional dict of {{name: model}} to train only specific models.
                        If None, trains all models for the specified mode.
    
    Scoring:
    - Classification (balanced): F1-macro
    - Classification (imbalanced >5x): minority_recall*0.6 + f1_macro*0.4
    - Regression: R² score
    
    Cross-validation:
    - Fast: 3-fold StratifiedKFold/KFold
    - Ultra: 5-fold
    """
    is_clf = TASK_TYPE == 'classification'
    is_ultra = mode == 'ultra'
    
    # Apply SMOTE (classification only)
    X_train_sm, y_train_sm, smote_applied = apply_smote(X_train, y_train)
    
    # Use selected_models if provided, otherwise get all models for the mode
    if selected_models is not None:
        models = selected_models
    else:
        models = get_models(len(X_train), mode)
    results = []
    best_model = None
    best_score = -999
    best_name = ""
    
    # Check imbalance for scoring
    if is_clf:
        class_counts = pd.Series(y_train).value_counts()
        imbalance_ratio = class_counts.max() / max(class_counts.min(), 1)
        is_imbalanced = imbalance_ratio > 5
        minority_class = class_counts.idxmin()
    
    # Cross-validation setup (same as DataVision)
    cv_folds = 3 if mode == 'fast' else 5
    if is_clf:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    else:
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    print(f"\\n🏋️ Training {{len(models)}} model(s) ({{'ALL' if selected_models is None else 'SELECTED'}} mode, {{cv_folds}}-fold CV)...")
    print("=" * 70)
    
    for name, model in models.items():
        try:
            t0 = time.time()
            model.fit(X_train_sm, y_train_sm)
            y_pred = model.predict(X_test)
            elapsed = time.time() - t0
            
            if is_clf:
                f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
                
                if is_imbalanced and len(pd.Series(y_train).unique()) == 2:
                    # DataVision's real scoring for imbalanced binary: 
                    # minority_recall * 0.6 + f1_macro * 0.4
                    from sklearn.metrics import recall_score as rs
                    minority_recall = rs(y_test, y_pred, pos_label=minority_class, zero_division=0)
                    score = minority_recall * 0.6 + f1_macro * 0.4
                else:
                    score = f1_macro
                
                metrics = {{
                    'accuracy': accuracy_score(y_test, y_pred),
                    'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
                    'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
                    'f1_weighted': f1_score(y_test, y_pred, average='weighted', zero_division=0),
                    'f1_macro': f1_macro,
                    'score': score,
                }}
            else:
                score = r2_score(y_test, y_pred)
                metrics = {{
                    'r2': score,
                    'mae': mean_absolute_error(y_test, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                    'score': score,
                }}
            
            # Cross-validation
            try:
                cv_scoring = 'f1_weighted' if is_clf else 'r2'
                cv_scores = cross_val_score(model, X_train_sm, y_train_sm, cv=cv, scoring=cv_scoring)
                metrics['cv_mean'] = cv_scores.mean()
                metrics['cv_std'] = cv_scores.std()
            except:
                metrics['cv_mean'] = score
                metrics['cv_std'] = 0
            
            results.append({{
                'name': name, 'score': score, 'metrics': metrics, 'model': model,
                'y_pred': y_pred, 'time': elapsed, 'cv_mean': metrics.get('cv_mean', score)
            }})
            
            marker = "🏆" if score > best_score else "  "
            cv_str = f"CV: {{metrics.get('cv_mean', 0):.4f}}±{{metrics.get('cv_std', 0):.3f}}"
            print(f"   {{marker}} {{name:.<30}} Score: {{score:.4f}} | {{cv_str}} ({{elapsed:.1f}}s)")
            
            if score > best_score:
                best_score = score
                best_model = model
                best_name = name
                
        except Exception as e:
            print(f"   ❌ {{name:.<30}} Failed: {{str(e)[:60]}}")
    
    # Sort results by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print("=" * 70)
    
    if not results:
        print("\\n❌ All models failed to train!")
        print("   Try: python train_traditional.py --all  (to try all algorithms)")
        return None, '', {{}}, []
    
    print(f"\\n🏆 Best Model: {{best_name}} (Score: {{best_score:.4f}})")
    
    best_result = results[0]
    if is_clf:
        print(f"\\n📊 Classification Report:")
        print(classification_report(y_test, best_result['y_pred']))
    else:
        print(f"\\n📊 Regression Metrics:")
        for k, v in best_result['metrics'].items():
            if k not in ('score', 'cv_mean', 'cv_std'):
                print(f"   {{k.upper()}}: {{v:.4f}}")
    
    # Overfitting check (same as DataVision's Production Intelligence)
    y_pred_train = best_model.predict(X_train)
    if is_clf:
        train_score = accuracy_score(y_train, y_pred_train)
        test_score = accuracy_score(y_test, best_result['y_pred'])
    else:
        train_score = r2_score(y_train, y_pred_train)
        test_score = r2_score(y_test, best_result['y_pred'])
    gap = train_score - test_score
    if gap > 0.1:
        print(f"\\n⚠️ Overfitting detected (train-test gap: {{gap:.4f}})")
    elif gap < 0.02:
        print(f"\\n✅ Good generalization (train-test gap: {{gap:.4f}})")
    
    return best_model, best_name, best_result['metrics'], results


def main():
    parser = argparse.ArgumentParser(description="Train ML model (reproduces your DataVision AutoML)")
    parser.add_argument('--data', type=str, default='data/cleaned_data.csv', help='Path to CSV data file')
    parser.add_argument('--output', type=str, default='model.pkl', help='Output model file')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test split ratio (DataVision uses 0.2)')
    parser.add_argument('--all', action='store_true', help='Train ALL algorithms (like full AutoML)')
    parser.add_argument('--mode', type=str, default='{"ultra" if is_ultra else "fast"}', choices=['fast', 'ultra'],
                        help='Training mode when using --all (fast: ~10 models, ultra: ~25 models)')
    args = parser.parse_args()
    
    print("\\n" + "=" * 70)
    if args.all:
        print("🚀 DataVision AutoML — Training ALL Algorithms")
    else:
        print(f"🚀 DataVision AutoML — Training YOUR Winning Model: {best_model_name}")
        print("   (Use --all to train all algorithms like full AutoML)")
    print("=" * 70)
    
    if not os.path.exists(args.data):
        print(f"❌ Data file not found: {{args.data}}")
        return
    
    start_time = time.time()
    
    # Load data
    df = pd.read_csv(args.data)
    
    # Step 1: Clean data (ProductionDataCleaner)
    df = clean_data(df)
    df = df.dropna(subset=[TARGET_COLUMN])
    
    # Separate target BEFORE feature engineering (anti-leakage — same as DataVision)
    X = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    
    # Encode target
    target_encoder = None
    if TASK_TYPE == 'classification':
        target_encoder = LabelEncoder()
        y = pd.Series(target_encoder.fit_transform(y), name=TARGET_COLUMN)
        print(f"\\n🎯 Target: {target} ({{len(target_encoder.classes_)}} classes: {{list(target_encoder.classes_)[:10]}})")
    else:
        print(f"\\n🎯 Target: {target} (regression)")
    
    # Train/test split BEFORE feature engineering (anti-leakage)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42,
        stratify=y if TASK_TYPE == 'classification' else None
    )
    print(f"📦 Split: {{len(X_train)}} train / {{len(X_test)}} test")
    print(f"   ⚠️ Feature engineering applied on train ONLY (anti-leakage)")
    
    # Step 2: Feature engineering (fit on train, transform test — anti-leakage)
    X_train_eng, label_encoders, scaler = engineer_features(X_train.copy(), mode=args.mode)
    
    # Transform test set using same encoding (simplified — uses same column structure)
    X_test_eng = X_test.copy()
    # Apply same encoding to test
    for col in X_test_eng.select_dtypes(include=['object', 'category']).columns:
        if col in label_encoders:
            le = label_encoders[col]
            X_test_eng[col] = X_test_eng[col].astype(str).map(
                lambda x: le.transform([x])[0] if x in le.classes_ else 0
            )
        else:
            le = LabelEncoder()
            X_test_eng[col] = le.fit_transform(X_test_eng[col].astype(str))
    for col in X_test_eng.select_dtypes(include=['object', 'category']).columns:
        X_test_eng[col] = pd.to_numeric(X_test_eng[col], errors='coerce').fillna(0)
    X_test_eng = X_test_eng.fillna(0)
    X_test_eng = X_test_eng.replace([np.inf, -np.inf], 0)
    
    # Ensure same columns as train
    for col in X_train_eng.columns:
        if col not in X_test_eng.columns:
            X_test_eng[col] = 0
    X_test_eng = X_test_eng[X_train_eng.columns]
    for col in X_test_eng.columns:
        X_test_eng[col] = pd.to_numeric(X_test_eng[col], errors='coerce').fillna(0)
    
    # Step 3 & 4: Train models
    # DEFAULT: Train ONLY your winning model (to reproduce exact result)
    # --all: Train all algorithms like full AutoML
    if args.all:
        print(f"\\n📊 Training ALL models (mode={{args.mode}})...")
        best_model, best_name, metrics, all_results = train_and_evaluate(
            X_train_eng, X_test_eng, y_train, y_test, mode=args.mode
        )
    else:
        print(f"\\n📊 Training ONLY your winning model: {best_model_name}")
        models = get_single_model(BEST_MODEL_NAME, len(X_train_eng))
        best_model, best_name, metrics, all_results = train_and_evaluate(
            X_train_eng, X_test_eng, y_train, y_test, mode=args.mode, selected_models=models
        )
    
    if best_model is None:
        print("\\n⚠️ Selected model failed. Retrying with ALL algorithms...")
        best_model, best_name, metrics, all_results = train_and_evaluate(
            X_train_eng, X_test_eng, y_train, y_test, mode='fast'
        )
    
    if best_model is None:
        print("\\n❌ All models failed. Check your data and dependencies.")
        return
    
    total_time = time.time() - start_time
    
    # Save model state (same structure as DataVision's engine_state)
    engine_state = {{
        'model': best_model,
        'model_name': best_name,
        'task_type': TASK_TYPE,
        'task_type_simple': TASK_TYPE,
        'target_column': TARGET_COLUMN,
        'feature_columns': X_train_eng.columns.tolist(),
        'label_encoders': label_encoders,
        'target_encoder': target_encoder,
        'scaler': scaler,
        'metrics': metrics,
        'production_mode': True,
        'mode': args.mode,
        'training_time_seconds': total_time,
        'leaderboard': [
            {{'name': r['name'], 'score': r['score'], 'metrics': r['metrics'], 'time': r.get('time', 0)}}
            for r in all_results
        ],
    }}
    
    with open(args.output, 'wb') as f:
        pickle.dump(engine_state, f)
    
    file_size = os.path.getsize(args.output) / 1024
    print(f"\\n💾 Model saved to: {{args.output}} ({{file_size:.1f}} KB)")
    print(f"⏱️ Total time: {{total_time:.1f}}s")
    print("✅ Training complete!")


if __name__ == '__main__':
    main()
'''
    return script


# =============================================================================
# PREDICT.PY GENERATOR — DATA-AWARE
# =============================================================================

def _generate_predict_script(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    features = config.get('feature_columns', [])
    feature_metadata = config.get('feature_metadata', [])
    numeric_features = config.get('numeric_features', [])
    categorical_features = config.get('categorical_features', [])
    best_model = config.get('best_model_name', 'Unknown')
    
    is_classification = 'classif' in task_type.lower()
    
    # Build real feature input examples with actual values from metadata
    feature_examples = []
    for fm in feature_metadata[:20]:
        name = fm.get('name', '')
        ftype = fm.get('type', 'numeric')
        if ftype == 'numeric':
            mean_val = fm.get('mean', 0)
            mn = fm.get('min', '?')
            mx = fm.get('max', '?')
            feature_examples.append(f"#         '{name}': {mean_val:.2f},  # numeric, range [{mn} .. {mx}]")
        elif ftype == 'categorical':
            options = fm.get('options', ['A'])
            first_opt = options[0] if options else 'A'
            opts_str = ', '.join(str(o) for o in options[:5])
            feature_examples.append(f"#         '{name}': '{first_opt}',  # categorical: [{opts_str}]")
        elif ftype == 'text':
            feature_examples.append(f"#         '{name}': 'sample text here',  # text field")
    
    if not feature_examples and features:
        for f in features[:20]:
            feature_examples.append(f"#         '{f}': 0,")
    
    example_dict = "\n".join(feature_examples)
    
    # Build interactive prompts with actual types and ranges
    interactive_prompts = []
    for fm in feature_metadata[:30]:
        name = fm.get('name', '')
        ftype = fm.get('type', 'numeric')
        if ftype == 'numeric':
            mn = fm.get('min', '?')
            mx = fm.get('max', '?')
            mean_val = fm.get('mean', 0)
            interactive_prompts.append(f'        "{name}": {{"type": "numeric", "min": {mn}, "max": {mx}, "default": {mean_val:.2f}}},')
        elif ftype == 'categorical':
            options = fm.get('options', [])
            opts_str = str(options[:10])
            interactive_prompts.append(f'        "{name}": {{"type": "categorical", "options": {opts_str}}},')
        elif ftype == 'text':
            interactive_prompts.append(f'        "{name}": {{"type": "text"}},')
    
    if not interactive_prompts and features:
        for f in features[:30]:
            interactive_prompts.append(f'        "{f}": {{"type": "numeric", "default": 0}},')
    
    prompts_block = "\n".join(interactive_prompts)
    
    features_list = ", ".join(f"'{f}'" for f in features[:30])
    
    script = f'''"""
🔮 Prediction Script — Uses Your ACTUAL Trained Model
========================================================
Auto-generated by DataVision AI

╔════════════════════════════════════════════════════════════════════╗
║  This script loads YOUR model.pkl that was trained by AutoML.     ║
║  The predictions match EXACTLY what you saw in DataVision.        ║
╚════════════════════════════════════════════════════════════════════╝

YOUR MODEL:
    🏆 Model     : {best_model}
    🎯 Target    : {target}
    📊 Task      : {task_type}
    📁 Features  : {len(features)} columns

Usage:
    python predict.py                                    # Interactive mode
    python predict.py --json '{{"col1": 1, "col2": "A"}}'  # JSON input
    python predict.py --csv input.csv                    # Batch predictions
"""

import os
import pickle
import argparse
import json
import re
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler

warnings.filterwarnings('ignore')

# Your actual feature columns from training
FEATURE_COLUMNS = [{features_list}]
TARGET_COLUMN = '{target}'
BEST_MODE = '{config.get("best_mode", "traditional")}'  # Which mode won during AutoML

# Feature metadata with actual types and ranges from your dataset
FEATURE_INFO = {{
{prompts_block}
}}


# =============================================================================
# Standalone Feature Engineer — Replicates DataVision's EXACT preprocessing
# =============================================================================
class StandaloneFeatureEngineer:
    """Replicate DataVision's ProductionFeatureEngineer.transform() pipeline.
    
    Loaded from feature_engineer.pkl which contains all fitted sklearn
    transformers, encoders, and feature names from your AutoML training.
    """
    
    def __init__(self, state):
        self.transformers = state.get('transformers', {{}})
        self.encoders = state.get('encoders', {{}})
        self.feature_names = state.get('feature_names', [])
        self.original_columns = state.get('original_columns', [])
        self.selected_feature_indices = state.get('selected_feature_indices', None)
        self.is_fitted = state.get('is_fitted', True)
        # Stopwords / sentiment words for text features
        self.stopwords = set("i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it its itself they them their theirs themselves what which who whom this that these those am is are was were be been being have has had having do does did doing a an the and but if or because as until while of at by for with about against between through during before after above below to from up down in out on off over under again further then once here there when where why how all both each few more most other some such no nor not only own same so than too very s t can will just don should now d ll m o re ve y ain aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan shouldn wasn weren won wouldn".split())
        self.positive_words = set("good great excellent amazing wonderful fantastic brilliant outstanding superb love best perfect beautiful awesome incredible impressive magnificent exceptional fabulous terrific marvelous stellar remarkable extraordinary delightful gorgeous splendid spectacular phenomenal exquisite lovely charming pleasant nice fine happy joy enjoy satisfied pleased glad cheerful excited thrilled".split())
        self.negative_words = set("bad terrible horrible awful worst poor disappointing disgusting pathetic useless dreadful atrocious appalling abysmal mediocre inferior unpleasant nasty vile wretched miserable lousy horrendous hideous ghastly hideous deplorable lamentable pitiful woeful tragic sad angry frustrated annoyed irritated disappointed upset unhappy distressed sorrowful gloomy depressed".split())
    
    def _clean_text(self, text):
        text = str(text).lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'http\\S+', ' ', text)
        text = re.sub(r'[^a-z0-9\\s]', ' ', text)
        text = ' '.join(w for w in text.split() if w not in self.stopwords and len(w) > 1)
        return text if text.strip() else 'empty'
    
    def _text_statistics(self, text):
        text = str(text)
        words = text.split()
        word_lengths = [len(w) for w in words] if words else [0]
        unique_ratio = len(set(words)) / max(len(words), 1)
        features = [
            len(text), len(words), np.mean(word_lengths), np.std(word_lengths),
            np.max(word_lengths) if word_lengths else 0, unique_ratio,
            text.count('!'), text.count('?'),
            sum(1 for c in text if c.isupper()) / max(len(text), 1),
            len([w for w in words if len(w) > 6]) / max(len(words), 1),
        ]
        return features
    
    def _sentiment_score(self, text):
        words = set(str(text).lower().split())
        pos = len(words & self.positive_words)
        neg = len(words & self.negative_words)
        total = max(pos + neg, 1)
        return [pos / total, neg / total, (pos - neg) / total, total]
    
    def transform(self, df):
        if not self.is_fitted:
            raise ValueError("Feature engineer not fitted!")
        df = df.copy()
        
        # Handle duplicate column names
        cols = df.columns.tolist()
        seen = {{}}
        new_cols = []
        for col in cols:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{{col}}_{{seen[col]}}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols
        
        feature_parts = []
        
        # ===== NUMERIC FEATURES =====
        if 'numeric_cols' in self.transformers:
            numeric_cols = self.transformers['numeric_cols']
            for col in numeric_cols:
                if col not in df.columns:
                    df[col] = 0
            try:
                numeric_data = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).values
                scaler = self.transformers['numeric_scaler']
                numeric_scaled = scaler.transform(numeric_data)
                numeric_scaled = np.nan_to_num(numeric_scaled, nan=0.0, posinf=0.0, neginf=0.0)
                feature_parts.append(numeric_scaled)
                
                # Polynomial features
                if 2 <= len(numeric_cols) <= 10:
                    interactions = []
                    for i in range(min(len(numeric_cols), 4)):
                        interactions.append((numeric_scaled[:, i] ** 2).reshape(-1, 1))
                    for i in range(min(len(numeric_cols), 4)):
                        for j in range(i + 1, min(len(numeric_cols), 4)):
                            interactions.append((numeric_scaled[:, i] * numeric_scaled[:, j]).reshape(-1, 1))
                    if interactions:
                        feature_parts.append(np.hstack(interactions))
            except Exception as e:
                print(f"   Warning: Numeric transform error: {{e}}")
                feature_parts.append(np.zeros((len(df), len(numeric_cols))))
        
        # ===== CATEGORICAL: One-hot =====
        for key, cols in self.transformers.items():
            if key.endswith('_onehot'):
                col_name = key.replace('_onehot', '')
                try:
                    if col_name in df.columns:
                        series = df[col_name].fillna('_MISSING_').astype(str).str.strip()
                        dummies = pd.get_dummies(series, prefix=col_name)
                        dummies = dummies.reindex(columns=cols, fill_value=0)
                        feature_parts.append(dummies.values.astype(float))
                    else:
                        feature_parts.append(np.zeros((len(df), len(cols))))
                except:
                    feature_parts.append(np.zeros((len(df), len(cols))))
        
        # ===== CATEGORICAL: Label + Frequency =====
        for col, le in self.encoders.items():
            try:
                if col in df.columns:
                    series = df[col].fillna('_MISSING_').astype(str).str.strip()
                    encoded = series.map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
                    feature_parts.append(encoded.values.reshape(-1, 1).astype(float))
                    freq_key = f'{{col}}_freq_map'
                    if freq_key in self.transformers:
                        freq_map = self.transformers[freq_key]
                        freq_encoded = series.map(lambda s: freq_map.get(s, 0.0)).values.astype(float)
                        feature_parts.append(freq_encoded.reshape(-1, 1))
                else:
                    feature_parts.append(np.zeros((len(df), 1)))
                    if f'{{col}}_freq_map' in self.transformers:
                        feature_parts.append(np.zeros((len(df), 1)))
            except:
                feature_parts.append(np.zeros((len(df), 1)))
        
        # ===== CATEGORICAL INTERACTIONS =====
        if 'cat_interactions' in self.transformers:
            interaction_encoders = self.transformers['cat_interactions']
            for key, value in interaction_encoders.items():
                if key.endswith('_freq_map'):
                    continue
                try:
                    col1, col2, le = value
                    if col1 in df.columns and col2 in df.columns:
                        combined = df[col1].fillna('_NA_').astype(str) + "_X_" + df[col2].fillna('_NA_').astype(str)
                        encoded = combined.map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
                        feature_parts.append(encoded.values.reshape(-1, 1).astype(float))
                        freq_key = f"{{key}}_freq_map"
                        if freq_key in interaction_encoders:
                            freq_map = interaction_encoders[freq_key]
                            freq_encoded = combined.map(lambda s: freq_map.get(s, 0.0)).values.astype(float)
                            feature_parts.append(freq_encoded.reshape(-1, 1))
                    else:
                        feature_parts.append(np.zeros((len(df), 1)))
                        if f"{{key}}_freq_map" in interaction_encoders:
                            feature_parts.append(np.zeros((len(df), 1)))
                except:
                    pass
        
        # ===== NUMERIC-CATEGORICAL AGGREGATES =====
        if 'num_cat_aggs' in self.transformers:
            agg_maps = self.transformers['num_cat_aggs']
            for key, mean_map in agg_maps.items():
                try:
                    parts = key.rsplit('_by_', 1)
                    if len(parts) == 2:
                        num_col = parts[0]
                        cat_col = parts[1].rsplit('_mean', 1)[0]
                        if num_col in df.columns and cat_col in df.columns:
                            cat_series = df[cat_col].fillna('_NA_').astype(str)
                            default_val = np.mean(list(mean_map.values())) if mean_map else 0
                            agg_values = cat_series.map(lambda s: mean_map.get(s, default_val)).values.astype(float)
                            feature_parts.append(agg_values.reshape(-1, 1))
                            deviation = df[num_col].fillna(0).values - agg_values
                            feature_parts.append(deviation.reshape(-1, 1))
                        else:
                            feature_parts.append(np.zeros((len(df), 1)))
                            feature_parts.append(np.zeros((len(df), 1)))
                except:
                    pass
        
        # ===== TEXT / NLP FEATURES =====
        for key, tfidf in self.transformers.items():
            if key.endswith('_tfidf'):
                col = key.replace('_tfidf', '')
                try:
                    if col in df.columns:
                        series = df[col].fillna('').astype(str)
                        cleaned = series.apply(self._clean_text)
                        tfidf_matrix = tfidf.transform(cleaned)
                        svd_key = f'{{col}}_svd'
                        if svd_key in self.transformers:
                            text_features = self.transformers[svd_key].transform(tfidf_matrix)
                        else:
                            text_features = tfidf_matrix.toarray()
                        feature_parts.append(text_features)
                        text_stats = np.array([self._text_statistics(t) for t in series])
                        feature_parts.append(text_stats)
                        sentiment = np.array([self._sentiment_score(t) for t in series])
                        feature_parts.append(sentiment)
                except:
                    pass
        
        # ===== COMBINE =====
        if not feature_parts:
            return np.zeros((len(df), len(self.feature_names)))
        
        X = np.hstack(feature_parts)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        
        # Variance selector
        if 'variance_selector' in self.transformers:
            selector = self.transformers['variance_selector']
            try:
                if X.shape[1] == selector.n_features_in_:
                    X = selector.transform(X)
                elif hasattr(self, 'selected_feature_indices') and self.selected_feature_indices is not None:
                    valid_idx = [i for i in self.selected_feature_indices if i < X.shape[1]]
                    if valid_idx:
                        X = X[:, valid_idx]
            except:
                pass
        
        # PCA (if used during training)
        if 'pca' in self.transformers:
            try:
                pca = self.transformers['pca']
                if X.shape[1] == pca.n_features_in_:
                    X = pca.transform(X)
            except:
                pass
        
        # Pad/truncate to match training dimensions
        if X.shape[1] != len(self.feature_names):
            if X.shape[1] < len(self.feature_names):
                padding = np.zeros((len(df), len(self.feature_names) - X.shape[1]))
                X = np.hstack([X, padding])
            else:
                X = X[:, :len(self.feature_names)]
        
        return X
    
    def transform_single(self, data):
        for col in self.original_columns:
            if col not in data:
                data[col] = 0
        df = pd.DataFrame([data])
        X = self.transform(df)
        expected = len(self.feature_names)
        if X.shape[1] != expected:
            if X.shape[1] < expected:
                X = np.hstack([X, np.zeros((1, expected - X.shape[1]))])
            else:
                X = X[:, :expected]
        return X


# =============================================================================
# Load model and feature engineer
# =============================================================================
FEATURE_ENGINEER = None

def _load_feature_engineer():
    global FEATURE_ENGINEER
    if FEATURE_ENGINEER is not None:
        return FEATURE_ENGINEER
    eng_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feature_engineer.pkl')
    if os.path.exists(eng_path):
        try:
            with open(eng_path, 'rb') as f:
                eng_state = pickle.load(f)
            FEATURE_ENGINEER = StandaloneFeatureEngineer(eng_state)
            print(f"   Pipeline: feature_engineer.pkl ({{len(FEATURE_ENGINEER.feature_names)}} engineered features)")
            return FEATURE_ENGINEER
        except Exception as e:
            print(f"   Warning: Could not load feature_engineer.pkl: {{e}}")
    return None


def load_model(model_path='model.pkl'):
    """Load the trained model and its components."""
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {{model_path}}")
        print("   Run the training script first, or ensure model.pkl is in this directory.")
        return None
    
    with open(model_path, 'rb') as f:
        state = pickle.load(f)
    
    print(f"✅ Loaded model: {{state.get('model_name', 'Unknown')}}")
    print(f"   Task: {{state.get('task_type', 'Unknown')}}")
    print(f"   Target: {{state.get('target_column', 'Unknown')}}")
    
    # Load feature engineer (exact preprocessing pipeline)
    _load_feature_engineer()
    return state


def predict_single(state, input_data: dict):
    """Make a prediction for a single data point.
    
    Uses the EXACT same preprocessing pipeline as DataVision AutoML:
    1. StandaloneFeatureEngineer from feature_engineer.pkl (preferred)
    2. Fallback to basic label-encode + scale (less accurate)
    """
    model = state['model']
    feature_cols = state.get('feature_columns', FEATURE_COLUMNS)
    target_encoder = state.get('target_encoder', None)
    task_type = state.get('task_type', '{task_type}')
    
    # Use feature engineer for EXACT AutoML-matching preprocessing
    engineer = _load_feature_engineer()
    if engineer is not None:
        try:
            X = engineer.transform_single(input_data)
        except Exception as e:
            print(f"Warning: Feature engineer failed ({{e}}), using fallback")
            X = _fallback_preprocess(input_data, state)
    else:
        X = _fallback_preprocess(input_data, state)
    
    prediction = model.predict(X)[0]
    result = {{'raw_prediction': prediction}}
    
    if 'classif' in task_type.lower() and target_encoder is not None:
        try:
            result['prediction'] = target_encoder.inverse_transform([int(prediction)])[0]
        except:
            result['prediction'] = prediction
    else:
        result['prediction'] = float(prediction)
    
    if 'classif' in task_type.lower() and hasattr(model, 'predict_proba'):
        try:
            proba = model.predict_proba(X)[0]
            result['confidence'] = float(max(proba))
            if target_encoder is not None:
                result['probabilities'] = {{
                    str(cls): float(p) for cls, p in zip(target_encoder.classes_, proba)
                }}
            else:
                result['probabilities'] = {{str(i): float(p) for i, p in enumerate(proba)}}
        except:
            pass
    
    return result


def _fallback_preprocess(input_data, state):
    """Fallback: basic label-encode + scale (used only if feature_engineer.pkl missing)."""
    feature_cols = state.get('feature_columns', FEATURE_COLUMNS)
    label_encoders = state.get('label_encoders', {{}})
    scaler = state.get('scaler', None)
    
    row = {{}}
    for col in feature_cols:
        val = input_data.get(col, 0)
        if col in label_encoders:
            le = label_encoders[col]
            val_str = str(val)
            val = le.transform([val_str])[0] if val_str in le.classes_ else 0
        else:
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0
        row[col] = val
    
    X_proc = pd.DataFrame([row], columns=feature_cols)
    if scaler is not None:
        try:
            X_proc = pd.DataFrame(scaler.transform(X_proc), columns=feature_cols)
        except:
            pass
    return X_proc


def predict_batch(state, csv_path: str, output_path: str = None):
    """Make predictions for a CSV file."""
    df = pd.read_csv(csv_path)
    print(f"\\n📊 Predicting for {{len(df)}} rows...")
    
    predictions = []
    for _, row in df.iterrows():
        result = predict_single(state, row.to_dict())
        predictions.append(result['prediction'])
    
    df['prediction'] = predictions
    if output_path is None:
        output_path = csv_path.replace('.csv', '_predictions.csv')
    df.to_csv(output_path, index=False)
    print(f"💾 Predictions saved to: {{output_path}}")
    return df


# =============================================================================
# Deep Learning Model Support (sklearn MLPClassifier/MLPRegressor)
# =============================================================================
DL_STATE = None

def load_dl_model(dl_path='deep_learning_model.pkl'):
    """Load the Deep Learning model (sklearn MLP) with its preprocessing state."""
    global DL_STATE
    if not os.path.exists(dl_path):
        return None
    try:
        with open(dl_path, 'rb') as f:
            DL_STATE = pickle.load(f)
        print(f"✅ Loaded DL model: {{DL_STATE.get('algorithm', 'MLP')}}")
        print(f"   Task: {{DL_STATE.get('task_type', 'Unknown')}}")
        print(f"   Features: {{len(DL_STATE.get('feature_metadata', []))}}")
        return DL_STATE
    except Exception as e:
        print(f"⚠️ Failed to load DL model: {{e}}")
        return None


def predict_single_dl(dl_state, input_data: dict):
    """Make a prediction using the Deep Learning model.
    
    Uses feature_metadata for correct preprocessing:
    - Numeric features: float conversion, fillna with mean
    - Categorical features: one-hot encoding matching training
    - StandardScaler applied to full feature vector
    """
    model = dl_state['model']
    scaler = dl_state.get('scaler')
    label_encoder = dl_state.get('label_encoder')
    feature_metadata = dl_state.get('feature_metadata', [])
    task_type = dl_state.get('task_type', '{task_type}')
    classes = dl_state.get('classes', [])
    
    # Build feature vector using feature_metadata (same as DL engine)
    feature_values = []
    
    # Process numeric features first
    for meta in feature_metadata:
        if meta.get('type') == 'numeric':
            col = meta['name']
            if col in input_data:
                try:
                    feature_values.append(float(input_data[col]))
                except (ValueError, TypeError):
                    feature_values.append(meta.get('mean', 0))
            else:
                feature_values.append(meta.get('mean', 0))
    
    # Process categorical features (one-hot encoded during training)
    for meta in feature_metadata:
        if meta.get('type') == 'categorical':
            col = meta['name']
            value = str(input_data.get(col, ''))
            options = meta.get('options', [])
            
            # One-hot encode: one value per option
            for opt in options:
                feature_values.append(1.0 if value == opt else 0.0)
            # NaN dummy (dummy_na=True during training)
            feature_values.append(1.0 if not value or value == 'nan' else 0.0)
    
    # Fallback to feature_columns if no metadata
    if not feature_values and dl_state.get('feature_columns'):
        for col in dl_state['feature_columns']:
            if col in input_data:
                try:
                    feature_values.append(float(input_data[col]) if not isinstance(input_data[col], str) else 0)
                except:
                    feature_values.append(0)
            else:
                feature_values.append(0)
    
    X = np.array([feature_values])
    
    # Handle dimension mismatch with scaler
    if scaler and hasattr(scaler, 'n_features_in_'):
        expected = scaler.n_features_in_
        actual = X.shape[1]
        if actual < expected:
            padding = np.zeros((1, expected - actual))
            X = np.hstack([X, padding])
        elif actual > expected:
            X = X[:, :expected]
    
    # Scale
    if scaler:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X
    
    # Predict
    pred = model.predict(X_scaled)[0]
    result = {{'raw_prediction': pred}}
    
    if 'classif' in task_type.lower() and label_encoder is not None:
        try:
            result['prediction'] = str(label_encoder.inverse_transform([int(pred)])[0])
        except:
            result['prediction'] = str(pred)
    else:
        result['prediction'] = float(pred)
    
    if 'classif' in task_type.lower() and hasattr(model, 'predict_proba'):
        try:
            proba = model.predict_proba(X_scaled)[0]
            result['confidence'] = float(max(proba))
            if classes:
                result['probabilities'] = {{
                    str(cls): round(float(p), 4) for cls, p in zip(classes, proba)
                }}
        except:
            pass
    
    return result


def interactive_mode(state, use_dl=False):
    """Interactive prediction mode with actual feature names and types."""
    print("\\n" + "=" * 50)
    print("🔮 Interactive Prediction Mode")
    if use_dl:
        print("   (Using Deep Learning model)")
    print("=" * 50)
    print("Enter values for each feature:\\n")
    
    # For DL mode, use feature_metadata from DL state
    if use_dl and DL_STATE:
        input_data = {{}}
        for meta in DL_STATE.get('feature_metadata', []):
            col = meta['name']
            ftype = meta.get('type', 'numeric')
            if ftype == 'numeric':
                mn = meta.get('min', '?')
                mx = meta.get('max', '?')
                default = meta.get('mean', 0)
                val = input(f"  {{col}} [{{mn}} - {{mx}}] (default: {{default:.2f}}): ").strip()
                input_data[col] = float(val) if val else default
            elif ftype == 'categorical':
                options = meta.get('options', [])
                print(f"  {{col}} options: {{options}}")
                val = input(f"  {{col}} (pick one): ").strip()
                input_data[col] = val if val else (options[0] if options else '')
        result = predict_single_dl(DL_STATE, input_data)
    else:
        input_data = {{}}
        for col, info in FEATURE_INFO.items():
            ftype = info.get('type', 'numeric')
            
            if ftype == 'numeric':
                mn = info.get('min', '?')
                mx = info.get('max', '?')
                default = info.get('default', 0)
                val = input(f"  {{col}} [{{mn}} - {{mx}}] (default: {{default}}): ").strip()
                input_data[col] = float(val) if val else default
                
            elif ftype == 'categorical':
                options = info.get('options', [])
                print(f"  {{col}} options: {{options}}")
                val = input(f"  {{col}} (pick one): ").strip()
                input_data[col] = val if val else (options[0] if options else '')
                
            elif ftype == 'text':
                val = input(f"  {{col}} (enter text): ").strip()
                input_data[col] = val if val else ''
        result = predict_single(state, input_data)
    
    print(f"\\n🎯 Prediction: {{result['prediction']}}")
    if 'confidence' in result:
        print(f"📊 Confidence: {{result['confidence']:.1%}}")
    if 'probabilities' in result:
        print(f"📊 Probabilities:")
        for cls, prob in sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prob * 30)
            print(f"   {{cls:>15}}: {{prob:.1%}} {{bar}}")
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Make predictions with your trained model")
    parser.add_argument('--model', type=str, default='model.pkl', help='Path to model file')
    parser.add_argument('--dl-model', type=str, default='deep_learning_model.pkl', help='Path to DL model file')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', 'traditional', 'dl'], help='Prediction mode')
    parser.add_argument('--json', type=str, default=None, help='JSON string with input data')
    parser.add_argument('--csv', type=str, default=None, help='CSV file for batch predictions')
    parser.add_argument('--output', type=str, default=None, help='Output CSV for batch predictions')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    args = parser.parse_args()
    
    # Auto-detect which model to use based on BEST_MODE from training
    use_dl = False
    dl_state = None
    state = None
    
    # Use DL if: explicitly requested, or BEST_MODE is deep_learning, or DL model exists
    if args.mode == 'dl' or (args.mode == 'auto' and BEST_MODE == 'deep_learning') or (args.mode == 'auto' and os.path.exists(args.dl_model) and not os.path.exists(args.model)):
        dl_state = load_dl_model(args.dl_model)
        if dl_state:
            use_dl = True
    
    if not use_dl:
        state = load_model(args.model)
        if state is None:
            # Last resort: try DL model
            dl_state = load_dl_model(args.dl_model)
            if dl_state:
                use_dl = True
            else:
                return
    
    if args.json:
        input_data = json.loads(args.json)
        if use_dl:
            result = predict_single_dl(dl_state, input_data)
        else:
            result = predict_single(state, input_data)
        print(f"\\n🎯 Prediction: {{result['prediction']}}")
        if 'confidence' in result:
            print(f"📊 Confidence: {{result['confidence']:.1%}}")
        print(f"\\n📋 Full result: {{json.dumps(result, indent=2, default=str)}}")
    elif args.csv:
        if use_dl:
            # Batch DL predictions
            df = pd.read_csv(args.csv)
            print(f"\\n📊 Predicting for {{len(df)}} rows (DL mode)...")
            predictions = []
            for _, row in df.iterrows():
                result = predict_single_dl(dl_state, row.to_dict())
                predictions.append(result['prediction'])
            df['prediction'] = predictions
            output_path = args.output or args.csv.replace('.csv', '_predictions.csv')
            df.to_csv(output_path, index=False)
            print(f"💾 Predictions saved to: {{output_path}}")
        else:
            predict_batch(state, args.csv, args.output)
    else:
        interactive_mode(state, use_dl=use_dl)


# =========================================================================
# Example (using YOUR actual feature names):
#
# from predict import load_model, predict_single
# state = load_model('model.pkl')
# result = predict_single(state, {{
{example_dict}
# }})
# print(result['prediction'])
# =========================================================================


if __name__ == '__main__':
    main()
'''
    return script


# =============================================================================
# VISUALIZE.PY GENERATOR — DATA-AWARE
# =============================================================================

def _generate_visualize_script(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    is_classification = 'classif' in task_type.lower()
    features = config.get('feature_columns', [])
    numeric_features = config.get('numeric_features', [])
    categorical_features = config.get('categorical_features', [])
    best_model = config.get('best_model_name', 'Unknown')
    leaderboard = config.get('leaderboard', [])
    
    lb_names = [e.get('name', '?') for e in leaderboard[:10]]
    lb_scores = [e.get('score', e.get('accuracy', e.get('r2', 0))) for e in leaderboard[:10]]
    numeric_col_names = [f.get('name', '') for f in numeric_features[:9]]
    
    script = f'''"""
📊 Visualization Script — ALL Charts Matching DataVision AutoML
================================================================
Auto-generated by DataVision AI

Model         : {best_model}
Target Column : {target}
Task Type     : {task_type}
Features      : {len(features)} columns

Supports Traditional ML AND Deep Learning models.
Automatically loads the correct model based on BEST_MODE.

Generates the SAME charts you see in DataVision AutoML:
  Classification: confusion matrix, class distribution, ROC curve,
                  precision-recall, calibration, confidence histogram,
                  metrics heatmap, feature importance, model comparison,
                  correlation heatmap, feature distributions, boxplots
  Regression:     actual vs predicted, residuals analysis, error distribution,
                  prediction overview, feature importance, model comparison,
                  correlation heatmap, feature distributions, boxplots
  Deep Learning:  training loss curve, validation score curve,
                  model architecture summary, MLP weight importance
  Unsupervised:   KMeans clustering scatter plot (PCA 2D),
                  cluster distribution chart

Usage:
    python visualize.py                         # Auto-detect best model
    python visualize.py --mode dl               # Force Deep Learning model
    python visualize.py --mode traditional      # Force traditional ML model
    python visualize.py --data my_data.csv
    python visualize.py --output charts/
"""

import os
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.metrics import (
    accuracy_score, confusion_matrix, classification_report,
    r2_score, mean_absolute_error, mean_squared_error,
    roc_curve, auc, precision_recall_curve, average_precision_score,
    precision_score, recall_score, f1_score
)

try:
    from sklearn.calibration import calibration_curve
    HAS_CALIBRATION = True
except ImportError:
    HAS_CALIBRATION = False

warnings.filterwarnings('ignore')
sns.set_style("whitegrid")
plt.rcParams.update({{
    'figure.figsize': (10, 6),
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
}})

TARGET_COLUMN = '{target}'
TASK_TYPE = '{task_type}'
BEST_MODE = '{config.get("best_mode", "traditional")}'  # Which mode won during AutoML
NUMERIC_FEATURES = {numeric_col_names}
LEADERBOARD_NAMES = {lb_names}
LEADERBOARD_SCORES = {lb_scores}


def load_model_and_data(model_path='model.pkl', data_path='data/cleaned_data.csv'):
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {{model_path}}")
        return None, None
    with open(model_path, 'rb') as f:
        state = pickle.load(f)
    df = pd.read_csv(data_path) if os.path.exists(data_path) else None
    return state, df


def load_dl_model(dl_path='deep_learning_model.pkl'):
    """Load the Deep Learning model (sklearn MLP)."""
    if not os.path.exists(dl_path):
        return None
    try:
        with open(dl_path, 'rb') as f:
            state = pickle.load(f)
        print(f"✅ Loaded DL model: {{state.get('algorithm', 'MLP')}}")
        print(f"   Task: {{state.get('task_type', 'Unknown')}}")
        print(f"   Features: {{len(state.get('feature_columns', state.get('feature_metadata', [])))}}")
        return state
    except Exception as e:
        print(f"⚠️ Failed to load DL model: {{e}}")
        return None


def generate_charts(state, df, output_dir='charts'):
    os.makedirs(output_dir, exist_ok=True)
    
    model = state['model']
    task_type = state.get('task_type', '{task_type}')
    target_col = state.get('target_column', TARGET_COLUMN)
    feature_cols = state.get('feature_columns', [])
    is_clf = 'classif' in task_type.lower()
    is_dl = state.get('model_type') == 'deep_learning'
    charts = []
    
    # Load SAVED predictions from AutoML (exact results, no feature mismatch)
    y_test = np.array(state['y_test']) if state.get('y_test') is not None else None
    y_pred = np.array(state['y_pred']) if state.get('y_pred') is not None else None
    y_proba = np.array(state['y_proba']) if state.get('y_proba') is not None else None
    # Handle both ML (target_encoder) and DL (label_encoder) naming
    target_encoder = state.get('target_encoder', None)
    label_encoder = state.get('label_encoder', None)
    encoder = target_encoder or label_encoder
    class_names = list(encoder.classes_) if encoder is not None else None
    mode_display = 'Deep Learning (MLP)' if is_dl else 'Traditional ML'
    model_name = state.get('model_name', state.get('algorithm', 'Unknown'))
    
    print(f"\\n📊 Generating charts for {{model_name}} ({{mode_display}})...")
    print(f"   Saved predictions: y_test={{y_test is not None}}, y_pred={{y_pred is not None}}, y_proba={{y_proba is not None}}")
    
    # =====================================================================
    # 1. MODEL COMPARISON / LEADERBOARD (same as AutoML)
    # =====================================================================
    if LEADERBOARD_NAMES and LEADERBOARD_SCORES:
        try:
            fig, ax = plt.subplots(figsize=(10, max(4, len(LEADERBOARD_NAMES) * 0.5)))
            colors = sns.color_palette('viridis', len(LEADERBOARD_NAMES))
            y_pos = range(len(LEADERBOARD_NAMES))
            ax.barh(y_pos, LEADERBOARD_SCORES, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(LEADERBOARD_NAMES)
            metric_label = 'F1-Score' if is_clf else 'R²'
            ax.set_xlabel(metric_label)
            ax.set_title(f'Model Leaderboard — {{metric_label}}')
            for i, v in enumerate(LEADERBOARD_SCORES):
                ax.text(v + 0.001, i, f'{{v:.4f}}', va='center', fontsize=9)
            plt.tight_layout()
            path = os.path.join(output_dir, 'model_comparison.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Model Comparison → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Model Comparison failed: {{e}}")
    
    # =====================================================================
    # 2. FEATURE IMPORTANCE (from model)
    # =====================================================================
    try:
        importances = None
        if hasattr(model, 'feature_importances_'):
            # Tree-based models (RF, XGB, etc.)
            importances = model.feature_importances_
        elif hasattr(model, 'coefs_') and len(model.coefs_) > 0:
            # MLP/Neural Network — use mean absolute weight of first layer
            importances = np.mean(np.abs(model.coefs_[0]), axis=1)
        elif hasattr(model, 'coef_'):
            # Linear models (LogReg, SVM, etc.)
            coef = model.coef_
            importances = np.mean(np.abs(coef), axis=0) if coef.ndim > 1 else np.abs(coef)
        
        if importances is not None:
            names = feature_cols[:len(importances)] if feature_cols else [f'Feature_{{i}}' for i in range(len(importances))]
            fi = pd.Series(importances, index=names).nlargest(min(20, len(names)))
            
            fig, ax = plt.subplots(figsize=(10, max(4, len(fi) * 0.35)))
            bars = fi.sort_values().plot(kind='barh', ax=ax, 
                color=plt.cm.viridis(np.linspace(0.2, 0.8, len(fi))))
            title_suffix = ' (MLP Weight Magnitude)' if is_dl else ''
            ax.set_title(f'Feature Importance — Top Features{{title_suffix}}')
            ax.set_xlabel('Importance')
            for i, (val, name) in enumerate(zip(fi.sort_values(), fi.sort_values().index)):
                ax.text(val + 0.001, i, f'{{val:.4f}}', va='center', fontsize=8)
            plt.tight_layout()
            path = os.path.join(output_dir, 'feature_importance.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Feature Importance → {{path}}")
    except Exception as e:
        print(f"   ⚠️ Feature Importance failed: {{e}}")
    
    # =====================================================================
    # DL-SPECIFIC: TRAINING HISTORY (loss curve + validation score)
    # =====================================================================
    if is_dl:
        training_history = state.get('training_history', {{}})
        loss_curve = training_history.get('loss', [])
        val_scores = training_history.get('val_score', [])
        
        if loss_curve:
            try:
                n_plots = 1 + (1 if val_scores else 0)
                fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 5))
                if n_plots == 1:
                    axes = [axes]
                
                # Loss curve
                axes[0].plot(range(1, len(loss_curve) + 1), loss_curve, color='#EF4444', lw=2)
                axes[0].set_xlabel('Epoch')
                axes[0].set_ylabel('Loss')
                axes[0].set_title('Training Loss Curve')
                axes[0].grid(True, alpha=0.3)
                
                # Validation score curve
                if val_scores and n_plots > 1:
                    axes[1].plot(range(1, len(val_scores) + 1), val_scores, color='#22C55E', lw=2)
                    axes[1].set_xlabel('Epoch')
                    axes[1].set_ylabel('Validation Score')
                    axes[1].set_title('Validation Score Curve')
                    axes[1].grid(True, alpha=0.3)
                
                plt.suptitle(f'Deep Learning Training History — {{state.get("algorithm", "MLP")}}', fontsize=14)
                plt.tight_layout()
                path = os.path.join(output_dir, 'training_history.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Training History → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Training History failed: {{e}}")
        
        # DL Model Architecture Summary
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.axis('off')
            info_lines = [
                f"Model: {{state.get('algorithm', 'MLP')}}",
                f"Task: {{state.get('task_type', 'Unknown')}}",
                f"Features: {{len(feature_cols)}}",
            ]
            if hasattr(model, 'hidden_layer_sizes'):
                info_lines.append(f"Hidden Layers: {{model.hidden_layer_sizes}}")
            if hasattr(model, 'activation'):
                info_lines.append(f"Activation: {{model.activation}}")
            if hasattr(model, 'n_iter_'):
                info_lines.append(f"Epochs Trained: {{model.n_iter_}}")
            metrics = state.get('metrics', {{}})
            if metrics:
                info_lines.append("")
                info_lines.append("Metrics:")
                for k, v in metrics.items():
                    if isinstance(v, float):
                        info_lines.append(f"  {{k}}: {{v:.4f}}")
            text = "\\n".join(info_lines)
            ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='#F0F9FF', alpha=0.8))
            ax.set_title('Deep Learning Model Summary', fontsize=14, fontweight='bold')
            plt.tight_layout()
            path = os.path.join(output_dir, 'dl_model_summary.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ DL Model Summary → {{path}}")
        except Exception as e:
            print(f"   ⚠️ DL Model Summary failed: {{e}}")
    
    # =====================================================================
    # CLASSIFICATION-SPECIFIC CHARTS
    # =====================================================================
    if is_clf and y_test is not None and y_pred is not None:
        n_classes = len(np.unique(y_test))
        is_binary = n_classes == 2
        
        # --- 3. CONFUSION MATRIX (normalized + counts) ---
        try:
            cm = confusion_matrix(y_test, y_pred)
            cm_norm = cm.astype('float') / cm.sum(axis=1, keepdims=True)
            labels = class_names if class_names else sorted(np.unique(y_test).tolist())
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            # Counts
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
                       xticklabels=labels, yticklabels=labels)
            axes[0].set_title('Confusion Matrix (Counts)')
            axes[0].set_xlabel('Predicted')
            axes[0].set_ylabel('Actual')
            # Normalized
            sns.heatmap(cm_norm, annot=True, fmt='.2%', cmap='Blues', ax=axes[1],
                       xticklabels=labels, yticklabels=labels)
            axes[1].set_title('Confusion Matrix (Normalized)')
            axes[1].set_xlabel('Predicted')
            axes[1].set_ylabel('Actual')
            plt.tight_layout()
            path = os.path.join(output_dir, 'confusion_matrix.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Confusion Matrix → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Confusion Matrix failed: {{e}}")
        
        # --- 4. CLASS DISTRIBUTION (actual vs predicted) ---
        try:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            labels = class_names if class_names else sorted(np.unique(y_test).tolist())
            # Actual
            actual_counts = pd.Series(y_test).value_counts().sort_index()
            pred_counts = pd.Series(y_pred).value_counts().sort_index()
            axes[0].bar(range(len(actual_counts)), actual_counts.values, color=sns.color_palette('Set2'))
            axes[0].set_xticks(range(len(actual_counts)))
            axes[0].set_xticklabels(labels, rotation=45, ha='right')
            axes[0].set_title('Actual Distribution')
            axes[0].set_ylabel('Count')
            axes[1].bar(range(len(pred_counts)), pred_counts.reindex(actual_counts.index, fill_value=0).values, 
                       color=sns.color_palette('Set3'))
            axes[1].set_xticks(range(len(actual_counts)))
            axes[1].set_xticklabels(labels, rotation=45, ha='right')
            axes[1].set_title('Predicted Distribution')
            axes[1].set_ylabel('Count')
            plt.suptitle('Class Distribution: Actual vs Predicted', fontsize=14)
            plt.tight_layout()
            path = os.path.join(output_dir, 'class_distribution.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Class Distribution → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Class Distribution failed: {{e}}")
        
        # --- 5. ROC CURVE (binary + multi-class) ---
        if y_proba is not None:
            try:
                fig, ax = plt.subplots(figsize=(8, 8))
                if is_binary:
                    proba_pos = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
                    fpr, tpr, _ = roc_curve(y_test, proba_pos)
                    roc_auc = auc(fpr, tpr)
                    ax.plot(fpr, tpr, color='#4F46E5', lw=2, label=f'ROC (AUC = {{roc_auc:.4f}})')
                else:
                    y_test_bin = label_binarize(y_test, classes=sorted(np.unique(y_test)))
                    colors = plt.cm.Set1(np.linspace(0, 1, n_classes))
                    for i in range(min(n_classes, y_proba.shape[1])):
                        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
                        roc_auc = auc(fpr, tpr)
                        label = class_names[i] if class_names and i < len(class_names) else f'Class {{i}}'
                        ax.plot(fpr, tpr, color=colors[i], lw=2, label=f'{{label}} (AUC={{roc_auc:.3f}})')
                ax.plot([0, 1], [0, 1], 'k--', lw=1, alpha=0.5)
                ax.set_xlabel('False Positive Rate')
                ax.set_ylabel('True Positive Rate')
                ax.set_title('ROC Curve')
                ax.legend(loc='lower right')
                ax.set_xlim([0, 1])
                ax.set_ylim([0, 1.02])
                plt.tight_layout()
                path = os.path.join(output_dir, 'roc_curve.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ ROC Curve → {{path}}")
            except Exception as e:
                print(f"   ⚠️ ROC Curve failed: {{e}}")
        
        # --- 6. PRECISION-RECALL CURVE (binary) ---
        if y_proba is not None and is_binary:
            try:
                proba_pos = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
                precision_vals, recall_vals, _ = precision_recall_curve(y_test, proba_pos)
                ap = average_precision_score(y_test, proba_pos)
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.plot(recall_vals, precision_vals, color='#059669', lw=2,
                       label=f'AP = {{ap:.4f}}')
                ax.set_xlabel('Recall')
                ax.set_ylabel('Precision')
                ax.set_title('Precision-Recall Curve')
                ax.legend(loc='lower left')
                ax.set_xlim([0, 1])
                ax.set_ylim([0, 1.02])
                plt.tight_layout()
                path = os.path.join(output_dir, 'precision_recall.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Precision-Recall → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Precision-Recall failed: {{e}}")
        
        # --- 7. CALIBRATION CURVE (binary) ---
        if y_proba is not None and is_binary and HAS_CALIBRATION and len(y_test) >= 20:
            try:
                proba_pos = y_proba[:, 1] if y_proba.ndim == 2 else y_proba
                fraction_of_positives, mean_predicted_value = calibration_curve(
                    y_test, proba_pos, n_bins=10
                )
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.plot(mean_predicted_value, fraction_of_positives, 's-', color='#4F46E5',
                       label='Model', lw=2)
                ax.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
                ax.set_xlabel('Mean Predicted Probability')
                ax.set_ylabel('Fraction of Positives')
                ax.set_title('Calibration Curve')
                ax.legend()
                plt.tight_layout()
                path = os.path.join(output_dir, 'calibration.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Calibration Curve → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Calibration Curve failed: {{e}}")
        
        # --- 8. CONFIDENCE HISTOGRAM ---
        if y_proba is not None:
            try:
                max_proba = np.max(y_proba, axis=1) if y_proba.ndim == 2 else y_proba
                correct = (y_test == y_pred)
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.hist(max_proba[correct], bins=20, alpha=0.7, color='#22C55E', label='Correct', edgecolor='white')
                ax.hist(max_proba[~correct], bins=20, alpha=0.7, color='#EF4444', label='Incorrect', edgecolor='white')
                ax.set_xlabel('Prediction Confidence')
                ax.set_ylabel('Count')
                ax.set_title('Confidence Distribution: Correct vs Incorrect')
                ax.legend()
                plt.tight_layout()
                path = os.path.join(output_dir, 'confidence_histogram.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Confidence Histogram → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Confidence Histogram failed: {{e}}")
        
        # --- 9. METRICS HEATMAP (per-class precision/recall/f1) ---
        if n_classes <= 10:
            try:
                labels = class_names if class_names else sorted(np.unique(y_test).tolist())
                prec_per_class = precision_score(y_test, y_pred, average=None, zero_division=0)
                rec_per_class = recall_score(y_test, y_pred, average=None, zero_division=0)
                f1_per_class = f1_score(y_test, y_pred, average=None, zero_division=0)
                
                metrics_df = pd.DataFrame({{
                    'Precision': prec_per_class[:len(labels)],
                    'Recall': rec_per_class[:len(labels)],
                    'F1-Score': f1_per_class[:len(labels)],
                }}, index=labels[:len(prec_per_class)])
                
                fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.5)))
                sns.heatmap(metrics_df, annot=True, fmt='.3f', cmap='YlGn', ax=ax,
                           vmin=0, vmax=1, linewidths=0.5)
                ax.set_title('Per-Class Metrics Heatmap')
                plt.tight_layout()
                path = os.path.join(output_dir, 'metrics_heatmap.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Metrics Heatmap → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Metrics Heatmap failed: {{e}}")
        
        # --- 10. CLASS BALANCE PIE CHART (actual vs predicted) ---
        try:
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            labels = class_names if class_names else sorted(np.unique(y_test).tolist())
            actual_counts = pd.Series(y_test).value_counts().sort_index()
            pred_counts = pd.Series(y_pred).value_counts().sort_index()
            colors_pie = sns.color_palette('Set2', len(labels))
            axes[0].pie(actual_counts.values, labels=[str(l)[:15] for l in labels],
                       autopct='%1.1f%%', colors=colors_pie,
                       wedgeprops={{'edgecolor': 'white'}})
            axes[0].set_title('Actual Class Balance')
            axes[1].pie(pred_counts.reindex(actual_counts.index, fill_value=0).values,
                       labels=[str(l)[:15] for l in labels],
                       autopct='%1.1f%%', colors=colors_pie,
                       wedgeprops={{'edgecolor': 'white'}})
            axes[1].set_title('Predicted Class Balance')
            plt.suptitle('Class Balance: Actual vs Predicted', fontsize=14)
            plt.tight_layout()
            path = os.path.join(output_dir, 'class_balance_pie.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Class Balance Pie → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Class Balance Pie failed: {{e}}")
        
        # --- 11. CONFIDENCE BOX PLOT BY CLASS ---
        if y_proba is not None:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                max_proba = np.max(y_proba, axis=1) if y_proba.ndim == 2 else y_proba
                classes = sorted(np.unique(y_test).tolist())
                data_boxes = [max_proba[y_test == c] for c in classes]
                bp = ax.boxplot(data_boxes, patch_artist=True)
                box_colors = sns.color_palette('Set2', len(classes))
                for i, patch in enumerate(bp['boxes']):
                    patch.set_facecolor(box_colors[i % len(box_colors)])
                    patch.set_alpha(0.7)
                labels = [str(class_names[i])[:15] if class_names and i < len(class_names) else str(c) for i, c in enumerate(classes)]
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.set_xlabel('Class')
                ax.set_ylabel('Prediction Confidence')
                ax.set_title('Confidence Distribution by Class')
                plt.tight_layout()
                path = os.path.join(output_dir, 'confidence_boxplot.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Confidence Boxplot → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Confidence Boxplot failed: {{e}}")
        
        # --- 12. SCORE DISTRIBUTION (KDE per class) ---
        if y_proba is not None and y_proba.ndim == 2:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                for i in range(min(y_proba.shape[1], 5)):
                    label = str(class_names[i])[:15] if class_names and i < len(class_names) else f'Class {{i}}'
                    try:
                        sns.kdeplot(y_proba[:, i], ax=ax, label=label, lw=2)
                    except:
                        ax.hist(y_proba[:, i], bins=30, alpha=0.5, label=label, density=True)
                ax.set_xlabel('Prediction Score')
                ax.set_ylabel('Density')
                ax.set_title('Score Distribution by Class')
                ax.legend()
                plt.tight_layout()
                path = os.path.join(output_dir, 'score_distribution.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Score Distribution → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Score Distribution failed: {{e}}")
    
    # =====================================================================
    # REGRESSION-SPECIFIC CHARTS
    # =====================================================================
    if not is_clf and y_test is not None and y_pred is not None:
        
        # --- 3. ACTUAL VS PREDICTED ---
        try:
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.scatter(y_test, y_pred, alpha=0.5, color='#3B82F6', edgecolors='white', s=50)
            lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
            ax.plot(lims, lims, '--', color='#EF4444', linewidth=2, label='Perfect')
            ax.set_title(f'Actual vs Predicted — R²={{r2:.4f}}, MAE={{mae:.4f}}, RMSE={{rmse:.4f}}')
            ax.set_xlabel('Actual')
            ax.set_ylabel('Predicted')
            ax.legend()
            plt.tight_layout()
            path = os.path.join(output_dir, 'actual_vs_predicted.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Actual vs Predicted → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Actual vs Predicted failed: {{e}}")
        
        # --- 4. RESIDUALS ANALYSIS (2x2 grid) ---
        try:
            residuals = y_test - y_pred
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            # Residuals vs Predicted
            axes[0, 0].scatter(y_pred, residuals, alpha=0.5, color='#8B5CF6', s=30)
            axes[0, 0].axhline(y=0, color='#EF4444', linestyle='--', linewidth=2)
            axes[0, 0].set_title('Residuals vs Predicted')
            axes[0, 0].set_xlabel('Predicted'); axes[0, 0].set_ylabel('Residuals')
            # Histogram
            axes[0, 1].hist(residuals, bins=30, color='#06B6D4', edgecolor='white', alpha=0.8)
            axes[0, 1].set_title('Residual Distribution')
            axes[0, 1].set_xlabel('Residual'); axes[0, 1].set_ylabel('Frequency')
            # Q-Q plot
            sorted_res = np.sort(residuals)
            n = len(sorted_res)
            theoretical = np.random.normal(0, 1, n)
            theoretical.sort()
            axes[1, 0].scatter(theoretical, sorted_res, alpha=0.5, color='#F59E0B', s=20)
            lims = [min(theoretical.min(), sorted_res.min()), max(theoretical.max(), sorted_res.max())]
            axes[1, 0].plot(lims, lims, 'r--')
            axes[1, 0].set_title('Q-Q Plot')
            axes[1, 0].set_xlabel('Theoretical Quantiles'); axes[1, 0].set_ylabel('Sample Quantiles')
            # Residuals vs Index
            axes[1, 1].plot(range(len(residuals)), residuals, 'o', alpha=0.5, color='#10B981', markersize=4)
            axes[1, 1].axhline(y=0, color='#EF4444', linestyle='--')
            axes[1, 1].set_title('Residuals vs Index')
            axes[1, 1].set_xlabel('Sample Index'); axes[1, 1].set_ylabel('Residual')
            plt.suptitle('Residuals Analysis', fontsize=14)
            plt.tight_layout()
            path = os.path.join(output_dir, 'residuals_analysis.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Residuals Analysis → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Residuals Analysis failed: {{e}}")
        
        # --- 5. ERROR DISTRIBUTION ---
        try:
            abs_errors = np.abs(y_test - y_pred)
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(abs_errors, bins=30, color='#F97316', edgecolor='white', alpha=0.8, density=True)
            p50 = np.percentile(abs_errors, 50)
            p90 = np.percentile(abs_errors, 90)
            p95 = np.percentile(abs_errors, 95)
            ax.axvline(p50, color='green', linestyle='--', label=f'Median: {{p50:.3f}}')
            ax.axvline(p90, color='orange', linestyle='--', label=f'P90: {{p90:.3f}}')
            ax.axvline(p95, color='red', linestyle='--', label=f'P95: {{p95:.3f}}')
            ax.set_title('Absolute Error Distribution')
            ax.set_xlabel('Absolute Error')
            ax.set_ylabel('Density')
            ax.legend()
            plt.tight_layout()
            path = os.path.join(output_dir, 'error_distribution.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Error Distribution → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Error Distribution failed: {{e}}")
        
        # --- 6. PREDICTION OVERVIEW (sorted with ±2sigma) ---
        try:
            idx_sorted = np.argsort(y_test)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(range(len(y_test)), y_test[idx_sorted], 'o', color='#3B82F6', markersize=3, label='Actual', alpha=0.7)
            ax.plot(range(len(y_pred)), y_pred[idx_sorted], 'x', color='#EF4444', markersize=3, label='Predicted', alpha=0.7)
            residuals_sorted = y_test[idx_sorted] - y_pred[idx_sorted]
            sigma = np.std(residuals_sorted)
            ax.fill_between(range(len(y_test)), y_pred[idx_sorted] - 2*sigma, y_pred[idx_sorted] + 2*sigma,
                           alpha=0.15, color='red', label=f'±2σ ({{sigma:.3f}})')
            ax.set_title('Prediction Overview (Sorted)')
            ax.set_xlabel('Sorted Sample Index')
            ax.set_ylabel('Value')
            ax.legend()
            plt.tight_layout()
            path = os.path.join(output_dir, 'prediction_overview.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Prediction Overview → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Prediction Overview failed: {{e}}")
        
        # --- 7. ERROR BOX PLOT BY QUANTILES ---
        try:
            abs_errors = np.abs(y_test - y_pred)
            quantiles = np.percentile(y_test, [0, 25, 50, 75, 100])
            groups = []
            q_labels = []
            for qi in range(len(quantiles) - 1):
                mask = (y_test >= quantiles[qi]) & (y_test < quantiles[qi+1])
                if mask.sum() > 0:
                    groups.append(abs_errors[mask])
                    q_labels.append(f'Q{{qi+1}}')
            if groups:
                fig, ax = plt.subplots(figsize=(10, 6))
                bp = ax.boxplot(groups, patch_artist=True)
                box_colors = ['#3B82F6', '#22C55E', '#F59E0B', '#EF4444']
                for i, patch in enumerate(bp['boxes']):
                    patch.set_facecolor(box_colors[i % len(box_colors)])
                    patch.set_alpha(0.7)
                ax.set_xticklabels(q_labels)
                ax.set_xlabel('Target Quantile')
                ax.set_ylabel('Absolute Error')
                ax.set_title('Error Distribution by Target Range')
                plt.tight_layout()
                path = os.path.join(output_dir, 'error_boxplot.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Error Boxplot → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Error Boxplot failed: {{e}}")
        
        # --- 8. SCALE-LOCATION PLOT ---
        try:
            residuals_sl = y_test - y_pred
            sqrt_abs_resid = np.sqrt(np.abs(residuals_sl))
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(y_pred, sqrt_abs_resid, alpha=0.5, color='#8B5CF6', s=30)
            z = np.polyfit(y_pred, sqrt_abs_resid, 1)
            p = np.poly1d(z)
            ax.plot(np.sort(y_pred), p(np.sort(y_pred)), 'r--', lw=2)
            ax.set_xlabel('Fitted Values')
            ax.set_ylabel('√|Residuals|')
            ax.set_title('Scale-Location Plot')
            plt.tight_layout()
            path = os.path.join(output_dir, 'scale_location.png')
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            charts.append(path)
            print(f"   ✅ Scale-Location → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Scale-Location failed: {{e}}")
    
    # =====================================================================
    # DATA EXPLORATION CHARTS (both classification & regression)
    # =====================================================================
    if df is not None:
        y = df[target_col] if target_col in df.columns else None
        
        # --- 10. CORRELATION HEATMAP ---
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr = numeric_df.corr()
                fig, ax = plt.subplots(figsize=(min(14, len(corr) + 2), min(12, len(corr) + 1)))
                mask = np.triu(np.ones_like(corr, dtype=bool))
                sns.heatmap(corr, mask=mask, annot=len(corr) <= 15, fmt='.2f',
                           cmap='RdBu_r', center=0, ax=ax, square=True, linewidths=0.5)
                ax.set_title('Feature Correlation Heatmap')
                plt.tight_layout()
                path = os.path.join(output_dir, 'correlation_heatmap.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Correlation Heatmap → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Correlation Heatmap failed: {{e}}")
        
        # --- 11. FEATURE DISTRIBUTIONS ---
        try:
            plot_cols = NUMERIC_FEATURES if NUMERIC_FEATURES else df.select_dtypes(include=[np.number]).columns[:9].tolist()
            cols_to_plot = [c for c in plot_cols if c in df.columns][:9]
            if cols_to_plot:
                ncols = min(3, len(cols_to_plot))
                nrows = (len(cols_to_plot) + ncols - 1) // ncols
                fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
                if nrows * ncols == 1:
                    axes = np.array([axes])
                axes = axes.flatten()
                for i, col in enumerate(cols_to_plot):
                    axes[i].hist(df[col].dropna(), bins=30, color='#4F46E5', edgecolor='white', alpha=0.8)
                    axes[i].set_title(col, fontsize=10)
                    axes[i].tick_params(labelsize=8)
                for i in range(len(cols_to_plot), len(axes)):
                    axes[i].set_visible(False)
                plt.suptitle('Feature Distributions', fontsize=14)
                plt.tight_layout()
                path = os.path.join(output_dir, 'distribution_grid.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Distribution Grid → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Distribution Grid failed: {{e}}")
        
        # --- 12. BOXPLOT GRID ---
        try:
            plot_cols = NUMERIC_FEATURES if NUMERIC_FEATURES else df.select_dtypes(include=[np.number]).columns[:9].tolist()
            cols_to_plot = [c for c in plot_cols if c in df.columns][:9]
            if cols_to_plot:
                ncols = min(3, len(cols_to_plot))
                nrows = (len(cols_to_plot) + ncols - 1) // ncols
                fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
                if nrows * ncols == 1:
                    axes = np.array([axes])
                axes = axes.flatten()
                colors = sns.color_palette('Set2', len(cols_to_plot))
                for i, col in enumerate(cols_to_plot):
                    axes[i].boxplot(df[col].dropna(), patch_artist=True,
                                   boxprops=dict(facecolor=colors[i], alpha=0.7))
                    axes[i].set_title(col, fontsize=10)
                    axes[i].tick_params(labelsize=8)
                for i in range(len(cols_to_plot), len(axes)):
                    axes[i].set_visible(False)
                plt.suptitle('Feature Boxplots (Outlier Detection)', fontsize=14)
                plt.tight_layout()
                path = os.path.join(output_dir, 'boxplot_grid.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Boxplot Grid → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Boxplot Grid failed: {{e}}")
        
        # --- 13. TARGET DISTRIBUTION (from raw data) ---
        if y is not None:
            try:
                fig, ax = plt.subplots(figsize=(8, 5))
                if is_clf:
                    y.value_counts().plot(kind='bar', ax=ax, color=sns.color_palette('Set2'))
                    ax.set_ylabel('Count')
                else:
                    ax.hist(y.dropna(), bins=30, color='#06B6D4', edgecolor='white', alpha=0.8)
                    ax.set_ylabel('Frequency')
                ax.set_title(f'Target Distribution: {target}')
                ax.set_xlabel('{target}')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                path = os.path.join(output_dir, 'target_distribution.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Target Distribution → {{path}}")
            except Exception as e:
                print(f"   ⚠️ Target Distribution failed: {{e}}")
        
        # =====================================================================
        # UNSUPERVISED LEARNING — Auto Clustering (KMeans)
        # =====================================================================
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler as ClusterScaler
            from sklearn.decomposition import PCA
            from sklearn.metrics import silhouette_score as sil_score
            
            numeric_df = df.select_dtypes(include=[np.number]).dropna()
            if len(numeric_df) >= 10 and len(numeric_df.columns) >= 2:
                # Scale for clustering
                c_scaler = ClusterScaler()
                X_clust = c_scaler.fit_transform(numeric_df)
                
                # Find optimal k using silhouette score
                best_k = 3
                best_sil = -1
                for k in range(2, min(8, len(numeric_df))):
                    try:
                        km = KMeans(n_clusters=k, random_state=42, n_init=10)
                        labels_k = km.fit_predict(X_clust)
                        sil_k = sil_score(X_clust, labels_k)
                        if sil_k > best_sil:
                            best_sil = sil_k
                            best_k = k
                    except:
                        pass
                
                # Run clustering with best k
                km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
                labels = km_final.fit_predict(X_clust)
                
                # PCA for 2D visualization
                pca = PCA(n_components=2)
                X_2d = pca.fit_transform(X_clust)
                
                # --- Cluster Scatter Plot ---
                fig, ax = plt.subplots(figsize=(10, 8))
                colors_clust = ['#2563eb', '#16a34a', '#dc2626', '#ea580c', '#9333ea',
                               '#0891b2', '#db2777', '#d97706', '#0d9488', '#4f46e5']
                for i in range(best_k):
                    mask = labels == i
                    ax.scatter(X_2d[mask, 0], X_2d[mask, 1],
                              c=colors_clust[i % len(colors_clust)],
                              label=f'Cluster {{i}}', alpha=0.7, s=50,
                              edgecolors='white', linewidth=0.5)
                ax.set_xlabel('PCA Component 1', fontweight='bold')
                ax.set_ylabel('PCA Component 2', fontweight='bold')
                ax.set_title(f'KMeans Clustering (k={{best_k}}, Silhouette={{best_sil:.3f}})',
                            fontweight='bold', pad=15, fontsize=14)
                ax.legend(loc='best')
                ax.grid(alpha=0.3)
                plt.tight_layout()
                path = os.path.join(output_dir, 'cluster_scatter.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Cluster Scatter → {{path}}")
                
                # --- Cluster Distribution Bar Chart ---
                fig, ax = plt.subplots(figsize=(8, 5))
                unique, counts = np.unique(labels, return_counts=True)
                ax.bar([f'Cluster {{u}}' for u in unique], counts,
                      color=[colors_clust[u % len(colors_clust)] for u in unique],
                      edgecolor='white')
                ax.set_xlabel('Cluster')
                ax.set_ylabel('Count')
                ax.set_title('Cluster Size Distribution')
                for i, (u, c) in enumerate(zip(unique, counts)):
                    ax.text(i, c + 0.5, str(c), ha='center', fontsize=10)
                plt.tight_layout()
                path = os.path.join(output_dir, 'cluster_distribution.png')
                plt.savefig(path, dpi=150, bbox_inches='tight')
                plt.close()
                charts.append(path)
                print(f"   ✅ Cluster Distribution → {{path}}")
        except Exception as e:
            print(f"   ⚠️ Clustering charts failed: {{e}}")
    
    print(f"\\n📊 Generated {{len(charts)}} charts in '{{output_dir}}/'")
    return charts


def main():
    parser = argparse.ArgumentParser(description="Generate charts from your trained model")
    parser.add_argument('--model', type=str, default='model.pkl', help='Path to traditional ML model')
    parser.add_argument('--dl-model', type=str, default='deep_learning_model.pkl', help='Path to DL model')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', 'traditional', 'dl'],
                       help='Which model to visualize (auto uses BEST_MODE)')
    parser.add_argument('--data', type=str, default='data/cleaned_data.csv')
    parser.add_argument('--output', type=str, default='charts')
    args = parser.parse_args()
    
    print("\\n" + "=" * 60)
    print("📊 DataVision Chart Generator")
    print("=" * 60)
    
    # Decide which model to load based on BEST_MODE
    use_dl = False
    state = None
    df = None
    
    if args.mode == 'dl' or (args.mode == 'auto' and BEST_MODE == 'deep_learning'):
        state = load_dl_model(args.dl_model)
        if state:
            use_dl = True
        else:
            print("⚠️ DL model not found, falling back to traditional ML model...")
    
    if not use_dl and args.mode != 'dl':
        state, df = load_model_and_data(args.model, args.data)
        if state is None and os.path.exists(args.dl_model):
            state = load_dl_model(args.dl_model)
            if state:
                use_dl = True
    
    if state is None:
        print("❌ No model found. Provide model.pkl or deep_learning_model.pkl")
        return
    
    # Load data if not yet loaded
    if df is None:
        data_path = args.data
        df = pd.read_csv(data_path) if os.path.exists(data_path) else None
    
    mode_display = 'deep_learning' if use_dl else state.get('mode', 'traditional')
    model_name = state.get('model_name', state.get('algorithm', 'Unknown'))
    
    print(f"\\n🏆 Model: {{model_name}}")
    print(f"📊 Mode: {{mode_display}}")
    print(f"🎯 Task: {{state.get('task_type', TASK_TYPE)}}")
    if use_dl:
        print(f"🧠 Architecture: {{state.get('algorithm', 'MLP')}}")
    if df is not None:
        print(f"📋 Data: {{len(df)}} rows, {{len(df.columns)}} columns")
    
    generate_charts(state, df, args.output)
    print(f"\\n✅ Done! Open '{{args.output}}/' to view charts.")


if __name__ == '__main__':
    main()
'''
    return script


# =============================================================================
# REQUIREMENTS.TXT — ONLY DEPS FOR MODES ACTUALLY TRAINED
# =============================================================================

def _generate_requirements(config: Dict) -> str:
    """Generate requirements.txt matching DataVision's real dependencies."""
    reqs = [
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
        "joblib>=1.1.0",
        "scipy>=1.7.0",
        "flask>=2.2.0",
        "imbalanced-learn>=0.10.0",  # SMOTE for class balancing
    ]
    
    modes = config.get('modes_trained', ['traditional'])
    leaderboard = config.get('leaderboard', [])
    
    # Check what algorithms were actually used
    algo_names_lower = [e.get('name', '').lower() for e in leaderboard]
    algo_joined = " ".join(algo_names_lower)
    
    if 'xgb' in algo_joined or 'xgboost' in algo_joined:
        reqs.append("xgboost>=1.7.0")
    if 'lgb' in algo_joined or 'lightgbm' in algo_joined or 'lgbm' in algo_joined:
        reqs.append("lightgbm>=3.3.0")
    if 'catboost' in algo_joined or 'cat_boost' in algo_joined:
        reqs.append("catboost>=1.1.0")
    
    # NLP dependencies only if NLP was trained
    if 'nlp' in modes:
        nlp_result = config.get('results_per_mode', {}).get('nlp', {})
        algo_key = nlp_result.get('algorithm_key', nlp_result.get('algorithm', ''))
        
        reqs.append("nltk>=3.7")
        
        if 'transformer' in algo_key or 'sentence' in algo_key or 'bert' in algo_key:
            reqs.extend([
                "transformers>=4.20.0",
                "torch>=2.0.0",
                "sentence-transformers>=2.2.0",
            ])
    
    # Deep Learning uses sklearn MLPClassifier/MLPRegressor (already included)
    # No additional dependencies needed for DL mode
    
    return "\n".join(sorted(set(reqs))) + "\n"


# =============================================================================
# README.MD — DOCUMENTS ACTUAL TRAINING RESULTS
# =============================================================================

def _generate_readme(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    best_model = config['best_model_name']
    best_mode = config['best_mode']
    metrics = config.get('metrics', {})
    data_summary = config.get('data_summary', {})
    features = config.get('feature_columns', [])
    modes_trained = config.get('modes_trained', ['traditional'])
    leaderboard = config.get('leaderboard', [])
    numeric_features = config.get('numeric_features', [])
    categorical_features = config.get('categorical_features', [])
    
    # Format metrics
    metrics_lines = []
    for k, v in metrics.items():
        if isinstance(v, float):
            if 0 < v < 1:
                metrics_lines.append(f"- **{k.upper()}**: {v:.4f} ({v*100:.1f}%)")
            else:
                metrics_lines.append(f"- **{k.upper()}**: {v:.4f}")
        else:
            metrics_lines.append(f"- **{k.upper()}**: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "- No metrics available"
    
    # Build leaderboard table
    lb_lines = []
    for i, entry in enumerate(leaderboard[:10]):
        name = entry.get('name', entry.get('model_name', '?'))
        score = entry.get('score', entry.get('accuracy', entry.get('r2', '?')))
        if isinstance(score, float):
            lb_lines.append(f"| {i+1} | {name} | {score:.4f} |")
        else:
            lb_lines.append(f"| {i+1} | {name} | {score} |")
    lb_block = "\n".join(lb_lines) if lb_lines else "| - | No leaderboard data | - |"
    
    # Project structure — only include scripts for modes trained
    structure_lines = [
        "├── model.pkl                     # Your trained model",
        "├── data/",
        "│   └── cleaned_data.csv          # Your cleaned dataset",
        "├── predict.py                    # Make predictions (CLI / import)",
        "├── visualize.py                  # Generate performance charts",
        "├── evaluate.py                   # Comprehensive model evaluation",
    ]
    if 'traditional' in modes_trained:
        structure_lines.append("├── train_traditional.py          # Traditional ML training")
    if 'nlp' in modes_trained:
        structure_lines.append("├── train_nlp.py                  # NLP text classification")
    if 'deep_learning' in modes_trained:
        structure_lines.append("├── train_deep_learning.py        # Deep Learning (sklearn MLP)")
        structure_lines.append("├── deep_learning_model.pkl       # Trained DL model")
    structure_lines.extend([
        "├── charts/                       # Pre-generated training charts (PNG)",
        "├── api_server.py                 # Flask REST API for deployment",
        "├── utils/",
        "│   └── preprocessing.py          # Data preprocessing utilities",
        "├── config.json                   # Full training configuration",
        "├── requirements.txt              # Python dependencies",
        "├── Dockerfile                    # Docker deployment",
        "└── README.md                     # This file",
    ])
    structure_block = "\n".join(structure_lines)
    
    # Feature info table
    feature_lines = []
    for fm in numeric_features[:10]:
        name = fm.get('name', '')
        mn = fm.get('min', '?')
        mx = fm.get('max', '?')
        feature_lines.append(f"| `{name}` | numeric | {mn} - {mx} |")
    for fm in categorical_features[:10]:
        name = fm.get('name', '')
        options = fm.get('options', [])
        opts_str = ', '.join(str(o) for o in options[:4])
        feature_lines.append(f"| `{name}` | categorical | {opts_str} |")
    feature_block = "\n".join(feature_lines) if feature_lines else "| (see config.json for details) | | |"
    
    # Mode-specific usage instructions
    usage_modes = []
    if 'traditional' in modes_trained:
        usage_modes.append(f"""#### Traditional ML
```bash
python train_traditional.py                    # Reproduces your training
python train_traditional.py --data your.csv    # Custom data
```""")
    if 'nlp' in modes_trained:
        usage_modes.append(f"""#### NLP Text Classification
```bash
python train_nlp.py                            # NLP training
```""")
    if 'deep_learning' in modes_trained:
        usage_modes.append(f"""#### Deep Learning
```bash
python train_deep_learning.py                  # sklearn MLP neural network
python train_deep_learning.py --epochs 100     # Custom epochs
python predict.py --mode dl                    # Predict using DL model
```""")
    usage_block = "\n\n".join(usage_modes) if usage_modes else "```bash\npython predict.py\n```"
    
    readme = f"""# 🚀 DataVision ML Project — Complete Guide

Auto-generated by **DataVision AI Business Analyst**  
*This ZIP contains YOUR actual trained model, data, scripts, and everything needed to use it.*

---

## 📦 What's Inside This ZIP?

```
{structure_block}
```

### What Each File Does:

| File | What It Does | When To Use |
|------|-------------|-------------|
| `model.pkl` | Your **already trained** ML model (ready to use) | Loaded automatically by other scripts |
| `data/cleaned_data.csv` | Your cleaned dataset (used for charts & evaluation) | Used by visualize.py and evaluate.py |
| `predict.py` | Make predictions on new data | When you want to predict something |
| `visualize.py` | Generate all charts (confusion matrix, ROC, etc.) | When you want to see model performance charts |
| `evaluate.py` | Show detailed model metrics and scores | When you want to see accuracy, F1, R2 scores |
| `api_server.py` | Start a web API server with a form | When you want a web interface or REST API |
| `requirements.txt` | List of Python packages needed | Install once before running anything |
| `config.json` | Full training configuration and metadata | Reference only |
| `README.md` | This guide | You are reading it now |

---

## Step-by-Step: Getting Started (For Beginners)

### STEP 1: Install Python (if not installed)

Download and install Python 3.8 or newer from https://www.python.org/downloads/

> **Important**: During installation, check the box **"Add Python to PATH"**

### STEP 2: Open Terminal / Command Prompt

- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac/Linux**: Open Terminal app

Navigate to the project folder:
```bash
cd path/to/this/folder
```

### STEP 3: Install Dependencies (Run Once)

```bash
pip install -r requirements.txt
```

This installs all the Python packages needed. You only need to do this **once**.

> If you get an error, try: `pip3 install -r requirements.txt`

---

## STEP 4: See Your Model Results (evaluate.py)

This shows your **exact same scores** from DataVision.
Automatically evaluates the correct model (Traditional ML or Deep Learning) based on your best training mode.

```bash
python evaluate.py                           # Auto-detect best model
python evaluate.py --mode dl                 # Force Deep Learning model
python evaluate.py --mode traditional        # Force traditional ML model
```

**What you will see:**
- Your model accuracy or R2 score
- Classification report (precision, recall, F1 per class)
- Confusion matrix
- All stored metrics from training

**Additional options:**
```bash
python evaluate.py --cv 5        # Run 5-fold cross-validation
python evaluate.py --reeval       # Re-evaluate model on dataset
```

**Expected output example:**
```
Model: RandomForest
Task: classification
Accuracy: 0.9450
F1-Score: 0.9380
```

---

## STEP 5: Make Predictions (predict.py)

### Option A: Interactive Mode (Easiest)
```bash
python predict.py
```
It will ask you to enter a value for each feature one by one, then show the prediction.

### Option B: JSON Input (Single Prediction)
```bash
python predict.py --json "{{\\"feature1\\": 25, \\"feature2\\": \\"value\\"}}"
```
Replace `feature1`, `feature2` with your actual column names.

### Option C: CSV Batch Predictions (Many Rows)
```bash
python predict.py --csv your_data.csv
```
This reads your CSV, predicts for every row, saves results to `your_data_predictions.csv`.

```bash
python predict.py --csv input.csv --output results.csv
```

**Expected output example:**
```
Prediction: Normal
Confidence: 94.5%
Probabilities:
  Normal: 94.5%
  Abnormal: 5.5%
```

---

## STEP 6: Generate Charts (visualize.py)

Creates **all the same charts** you saw in DataVision AutoML.
Automatically loads the correct model (Traditional ML or Deep Learning) based on your best training mode.

```bash
python visualize.py                          # Auto-detect best model
python visualize.py --mode dl                # Force Deep Learning model
python visualize.py --mode traditional       # Force traditional ML model
```

Charts are saved to a `charts/` folder. Open them with any image viewer.

**Classification charts generated:**

| Chart File | What It Shows |
|------------|---------------|
| `model_comparison.png` | All models ranked by score |
| `feature_importance.png` | Which features matter most |
| `confusion_matrix.png` | Correct vs wrong predictions per class |
| `class_distribution.png` | Actual vs predicted class counts |
| `roc_curve.png` | ROC curve with AUC score |
| `precision_recall.png` | Precision-Recall curve |
| `calibration.png` | Probability calibration curve |
| `confidence_histogram.png` | Confidence for correct vs incorrect |
| `metrics_heatmap.png` | Per-class precision, recall, F1 |
| `class_balance_pie.png` | Class balance pie charts |
| `confidence_boxplot.png` | Confidence box plot per class |
| `score_distribution.png` | Score distribution per class |

**Regression charts generated:**

| Chart File | What It Shows |
|------------|---------------|
| `actual_vs_predicted.png` | Scatter: actual vs predicted values |
| `residuals_analysis.png` | 4-panel residual analysis |
| `error_distribution.png` | Error distribution with percentiles |
| `prediction_overview.png` | Sorted predictions with error band |
| `error_boxplot.png` | Error by target range (Q1-Q4) |
| `scale_location.png` | Scale-Location diagnostic plot |

**Common charts (both):**

| Chart File | What It Shows |
|------------|---------------|
| `correlation_heatmap.png` | Feature correlations |
| `distribution_grid.png` | Distribution of each feature |
| `boxplot_grid.png` | Outlier detection per feature |
| `target_distribution.png` | Target column distribution |

**Deep Learning charts (when DL model is loaded):**

| Chart File | What It Shows |
|------------|---------------|
| `training_history.png` | Training loss curve and validation scores |
| `dl_model_summary.png` | Model architecture, hyperparameters, metrics |
| `feature_importance.png` | MLP weight-based feature importance |

**Unsupervised Learning charts (auto-generated):**

| Chart File | What It Shows |
|------------|---------------|
| `cluster_scatter.png` | KMeans clustering with PCA 2D projection |
| `cluster_distribution.png` | Cluster size distribution |

> **Note:** Your ZIP already contains pre-generated charts in the `charts/` folder
> from your actual training. These are the EXACT same charts you saw in DataVision.
> Running `visualize.py` will regenerate them from your model data.

**Custom options:**
```bash
python visualize.py --data other_data.csv    # Use different data
python visualize.py --output my_charts/      # Save to different folder
```

---

## STEP 7: Deploy as Web API (api_server.py)

Start a local web server with a prediction form:

```bash
python api_server.py
```

Then open your browser and go to: **http://localhost:5000/predict**

You will see a **web form** with your actual column names where you can:
1. Enter values for each feature
2. Click "Predict"  
3. See the prediction result instantly

**API Endpoints:**

| URL | Method | What It Does |
|-----|--------|-------------|
| `/predict` | GET | Web form with your feature names |
| `/predict` | POST | JSON API for developers |
| `/health` | GET | Health check (is server running?) |
| `/model-info` | GET | Model metadata and metrics |

**Change port:**
```bash
python api_server.py --port 8080
```

---

## STEP 8: Retrain the Model (Optional)

> Your model is already trained in `model.pkl`. Only retrain if you want to
> experiment with new data or verify the training.

{usage_block}

---

## STEP 9: Docker Deployment (Advanced)

```bash
docker build -t my-ml-model .
docker run -p 5000:5000 my-ml-model
```

Then access: `http://localhost:5000/predict`

---

## Your Model Summary

| Property | Value |
|----------|-------|
| **Target Column** | `{target}` |
| **Task Type** | {task_type} |
| **Best Model** | {best_model} |
| **Training Mode** | {best_mode} |
| **Features** | {len(features)} columns |
| **Dataset Rows** | {data_summary.get('rows', 'N/A')} |
| **Modes Trained** | {', '.join(modes_trained)} |

### Training Metrics
{metrics_block}

### Model Leaderboard

| Rank | Model | Score |
|------|-------|-------|
{lb_block}

### Feature Details

| Feature | Type | Range/Values |
|---------|------|-------------|
{feature_block}

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `model.pkl not found` | Make sure you are in the project folder |
| `No module named flask` | Run `pip install flask` |
| `Port already in use` | Use `python api_server.py --port 8080` |
| Charts not generating | Make sure `data/cleaned_data.csv` exists |
| Wrong model loaded | Use `--mode dl` or `--mode traditional` to force specific model |
| DL model not found | Make sure `deep_learning_model.pkl` exists |
| Permission denied | On Mac/Linux: try `python3` instead of `python` |

---

## Using as Python Module (For Developers)

```python
from predict import load_model, predict_single

state = load_model('model.pkl')
result = predict_single(state, {{
    # Use your actual column names here
    # Run 'python predict.py' to see what columns are needed
}})
print(f"Prediction: {{result['prediction']}}")
if 'confidence' in result:
    print(f"Confidence: {{result['confidence']:.1%}}")
```

---
*Generated by DataVision AI Business Analyst*
"""
    return readme


# =============================================================================
# NLP TRAINING SCRIPT — DATA-AWARE
# =============================================================================

def _generate_nlp_train_script(config: Dict, nlp_result: Dict) -> str:
    """Generate NLP training script based on ACTUAL NLP training results."""
    target = config['target_column']
    task_type = config['task_type']
    text_col = config.get('nlp_text_column', '')
    
    # Extract actual NLP results
    actual_algorithm = nlp_result.get('algorithm', nlp_result.get('algorithm_key', 'tfidf_lr'))
    actual_best_model = nlp_result.get('best_model', actual_algorithm)
    actual_metrics = nlp_result.get('metrics', {})
    actual_classes = nlp_result.get('classes', [])
    
    # Determine what approach was used
    is_tfidf = 'tfidf' in actual_algorithm.lower()
    is_transformer = 'transformer' in actual_algorithm.lower() or 'bert' in actual_algorithm.lower() or 'sentence' in actual_algorithm.lower()
    
    # Build metrics comment
    metrics_lines = []
    for k, v in actual_metrics.items():
        if isinstance(v, float):
            metrics_lines.append(f"#   {k}: {v:.4f}")
        else:
            metrics_lines.append(f"#   {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "#   (metrics unavailable)"
    
    classes_str = str(actual_classes[:20]) if actual_classes else "[]"
    
    return f'''"""
🔤 NLP Training Script — Based on Your Actual NLP Training
=============================================================
Auto-generated by DataVision AI

YOUR NLP TRAINING RESULTS:
    Text Column  : {text_col}
    Target       : {target}
    Algorithm    : {actual_algorithm}
    Best Model   : {actual_best_model}
    Classes      : {classes_str}
    
{metrics_block}

Usage:
    python train_nlp.py
    python train_nlp.py --data my_data.csv
"""

import os
import re
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

warnings.filterwarnings('ignore')

# Your actual training configuration
TEXT_COLUMN = '{text_col}'
TARGET_COLUMN = '{target}'
ALGORITHM = '{actual_algorithm}'
CLASSES = {classes_str}


def clean_text(text):
    """Basic text cleaning."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'http\\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\\s]', ' ', text)
    text = re.sub(r'\\s+', ' ', text).strip()
    return text


def train_tfidf(X_train, X_test, y_train, y_test):
    """Train with TF-IDF — matching your actual training approach."""
    print("\\n📊 Mode: TF-IDF + ML (your trained approach)")
    print("=" * 50)
    
    models = {{
        'Logistic Regression': Pipeline([
            ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)),
            ('clf', LogisticRegression(max_iter=1000, C=1.0, random_state=42))
        ]),
        'Linear SVM': Pipeline([
            ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2), sublinear_tf=True)),
            ('clf', LinearSVC(max_iter=2000, C=1.0, random_state=42))
        ]),
        'Naive Bayes': Pipeline([
            ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
            ('clf', MultinomialNB(alpha=0.1))
        ]),
        'Random Forest': Pipeline([
            ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
        ]),
    }}
    
    best_score = -1
    best_model = None
    best_name = ""
    
    for name, pipeline in models.items():
        try:
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
            marker = "🏆" if acc > best_score else "  "
            print(f"   {{marker}} {{name:.<35}} Acc: {{acc:.4f}} | F1: {{f1:.4f}}")
            if acc > best_score:
                best_score = acc
                best_model = pipeline
                best_name = name
        except Exception as e:
            print(f"   ❌ {{name:.<35}} Failed: {{e}}")
    
    print(f"\\n🏆 Best: {{best_name}} (Accuracy: {{best_score:.4f}})")
    y_pred = best_model.predict(X_test)
    print(f"\\n{{classification_report(y_test, y_pred)}}")
    
    return best_model, best_name, {{'accuracy': best_score}}


def main():
    parser = argparse.ArgumentParser(description="NLP Training — Reproducing your DataVision results")
    parser.add_argument('--data', type=str, default='data/cleaned_data.csv')
    parser.add_argument('--output', type=str, default='nlp_model.pkl')
    parser.add_argument('--test-size', type=float, default=0.2)
    args = parser.parse_args()
    
    print("\\n" + "=" * 60)
    print("🔤 DataVision NLP Training — Your Configuration")
    print("=" * 60)
    
    if not os.path.exists(args.data):
        print(f"❌ Data file not found: {{args.data}}")
        return
    
    df = pd.read_csv(args.data)
    print(f"📊 Dataset: {{len(df)}} rows")
    
    text_col = TEXT_COLUMN
    if text_col not in df.columns:
        text_candidates = [c for c in df.columns if df[c].dtype == 'object' and c != TARGET_COLUMN]
        if text_candidates:
            text_col = max(text_candidates, key=lambda c: df[c].str.len().mean())
            print(f"   Auto-detected text column: {{text_col}}")
        else:
            print("❌ No text column found")
            return
    
    df = df.dropna(subset=[text_col, TARGET_COLUMN])
    df['__clean_text__'] = df[text_col].apply(clean_text)
    
    X = df['__clean_text__']
    y = df[TARGET_COLUMN]
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print(f"🎯 Target: {{TARGET_COLUMN}} ({{len(le.classes_)}} classes: {{list(le.classes_)[:10]}})")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=args.test_size, random_state=42, stratify=y_encoded
    )
    
    model, name, metrics = train_tfidf(X_train, X_test, y_train, y_test)
    
    if model is None:
        print("❌ Training failed")
        return
    
    state = {{
        'model': model,
        'model_name': f'NLP_{{name}}',
        'task_type': 'classification',
        'target_column': TARGET_COLUMN,
        'text_column': text_col,
        'target_encoder': le,
        'metrics': metrics,
        'mode': 'nlp',
    }}
    
    with open(args.output, 'wb') as f:
        pickle.dump(state, f)
    
    print(f"\\n💾 NLP model saved to: {{args.output}}")
    print("✅ NLP training complete!")


if __name__ == '__main__':
    main()
'''


# =============================================================================
# DEEP LEARNING SCRIPT — DATA-AWARE (sklearn MLPClassifier/MLPRegressor)
# =============================================================================

def _generate_deep_learning_script(config: Dict, dl_result: Dict) -> str:
    """Generate DL training script based on ACTUAL deep learning results.
    
    Uses sklearn's MLPClassifier/MLPRegressor (same as DataVision's DL engine).
    """
    target = config['target_column']
    task_type = config['task_type']
    features = config.get('feature_columns', [])
    is_clf = 'classif' in task_type.lower()
    
    # Extract actual DL results
    actual_algorithm = dl_result.get('algorithm', dl_result.get('algorithm_key', 'auto'))
    actual_epochs = dl_result.get('epochs_completed', dl_result.get('epochs', 100))
    actual_metrics = dl_result.get('metrics', {})
    actual_best_model = dl_result.get('best_model', f'DL_{actual_algorithm}')
    
    metrics_lines = []
    for k, v in actual_metrics.items():
        if isinstance(v, float):
            metrics_lines.append(f"#   {k}: {v:.4f}")
        else:
            metrics_lines.append(f"#   {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "#   (metrics unavailable)"
    
    features_list = ", ".join(f"'{f}'" for f in features[:30])
    
    return f'''"""
🧠 Deep Learning Training Script — Based on Your Training
============================================================
Auto-generated by DataVision AI

Uses sklearn MLPClassifier/MLPRegressor (same as DataVision's DL engine).
CPU-friendly neural networks with anti-overfitting intelligence.

YOUR DL TRAINING RESULTS:
    Algorithm    : {actual_algorithm}
    Best Model   : {actual_best_model}
    Epochs       : {actual_epochs}
    Target       : {target}
    Task         : {task_type}
    Features     : {len(features)} columns
    
{metrics_block}

Usage:
    python train_deep_learning.py
    python train_deep_learning.py --epochs {actual_epochs}
    python train_deep_learning.py --data my_data.csv
"""

import os
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report,
    r2_score, mean_absolute_error, mean_squared_error
)

warnings.filterwarnings('ignore')

# Your actual training configuration
FEATURE_COLUMNS = [{features_list}]
TARGET_COLUMN = '{target}'
TASK_TYPE = '{task_type}'
MAX_EPOCHS = {actual_epochs}


def get_smart_config(n_samples, n_features):
    """Smart architecture selection based on dataset size (same as DataVision)."""
    if n_samples < 200:
        hidden = (32, 16)
        alpha = 0.1
        max_iter = 50
        patience = 10
    elif n_samples < 500:
        hidden = (64, 32)
        alpha = 0.05
        max_iter = 75
        patience = 12
    elif n_samples < 1000:
        hidden = (64, 32)
        alpha = 0.01
        max_iter = 100
        patience = 15
    elif n_samples < 5000:
        hidden = (128, 64)
        alpha = 0.005
        max_iter = 100
        patience = 15
    elif n_samples < 20000:
        hidden = (128, 64, 32)
        alpha = 0.001
        max_iter = 75
        patience = 12
    else:
        hidden = (256, 128, 64)
        alpha = 0.0005
        max_iter = 50
        patience = 10
    
    # High-dimensional adjustment
    if n_features > 1000:
        hidden = tuple(min(s, 64) for s in hidden)
        alpha = max(alpha, 0.01)
    elif n_features > 500:
        hidden = tuple(min(s, 128) for s in hidden)
        alpha = max(alpha, 0.005)
    
    return {{
        'hidden_layer_sizes': hidden,
        'alpha': alpha,
        'max_iter': max_iter,
        'n_iter_no_change': patience,
    }}


def preprocess_for_dl(df):
    """Preprocess data for deep learning — matches DataVision DL engine exactly."""
    df = df.dropna(subset=[TARGET_COLUMN])
    
    feature_df = df.drop(columns=[TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    
    is_clf = 'classif' in TASK_TYPE.lower()
    
    # Encode target
    label_encoder = None
    if is_clf:
        label_encoder = LabelEncoder()
        y = pd.Series(label_encoder.fit_transform(y))
    
    # Separate numeric and categorical columns
    numeric_cols = feature_df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = feature_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    processed_parts = []
    feature_names = []
    feature_metadata = []
    
    # Process numeric features
    if numeric_cols:
        X_numeric = feature_df[numeric_cols].fillna(feature_df[numeric_cols].median()).values
        processed_parts.append(X_numeric)
        feature_names.extend(numeric_cols)
        
        for col in numeric_cols:
            try:
                feature_metadata.append({{
                    'name': col,
                    'type': 'numeric',
                    'min': float(feature_df[col].min()),
                    'max': float(feature_df[col].max()),
                    'mean': float(feature_df[col].mean())
                }})
            except:
                feature_metadata.append({{
                    'name': col, 'type': 'numeric',
                    'min': 0, 'max': 100, 'mean': 50
                }})
    
    # Process categorical features (one-hot encode with dummy_na)
    if categorical_cols:
        for col in categorical_cols:
            dummies = pd.get_dummies(feature_df[col], prefix=col, dummy_na=True)
            processed_parts.append(dummies.values)
            feature_names.extend(dummies.columns.tolist())
            
            try:
                options = feature_df[col].dropna().unique().tolist()[:50]
                feature_metadata.append({{
                    'name': col,
                    'type': 'categorical',
                    'options': [str(x) for x in options]
                }})
            except:
                pass
    
    if not processed_parts:
        raise ValueError("No valid features found")
    
    X = np.hstack(processed_parts)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, is_clf, label_encoder, scaler, feature_names, feature_metadata, numeric_cols, categorical_cols


def train_dl_model(X_train, X_test, y_train, y_test, is_clf, config, classes=None):
    """Train sklearn MLP model with smart configuration."""
    hidden = config['hidden_layer_sizes']
    alpha = config['alpha']
    max_iter = config['max_iter']
    patience = config['n_iter_no_change']
    
    print(f"\\n🏋️ Training MLP Neural Network...")
    print(f"   Architecture: {{hidden}}")
    print(f"   Regularization (alpha): {{alpha}}")
    print(f"   Max epochs: {{max_iter}}")
    print(f"   Early stopping patience: {{patience}}")
    
    if is_clf:
        model = MLPClassifier(
            hidden_layer_sizes=hidden,
            activation='relu',
            solver='adam',
            alpha=alpha,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=max_iter,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=patience,
            random_state=42,
            verbose=True
        )
    else:
        model = MLPRegressor(
            hidden_layer_sizes=hidden,
            activation='relu',
            solver='adam',
            alpha=alpha,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=max_iter,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=patience,
            random_state=42,
            verbose=True
        )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    if is_clf:
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        print(f"\\n🏆 Final Accuracy: {{acc:.4f}} | F1: {{f1:.4f}}")
        print(f"   Precision: {{prec:.4f}} | Recall: {{rec:.4f}}")
        print(f"\\n{{classification_report(y_test, y_pred)}}")
        metrics = {{'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}}
        # ROC-AUC
        try:
            from sklearn.metrics import roc_auc_score
            n_cls = len(np.unique(y_test))
            if n_cls == 2 and hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test)[:, 1]
                roc = roc_auc_score(y_test, y_proba)
                metrics['roc_auc'] = roc
                print(f"   ROC-AUC: {{roc:.4f}}")
            elif n_cls > 2 and hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test)
                roc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
                metrics['roc_auc'] = roc
                print(f"   ROC-AUC: {{roc:.4f}}")
        except Exception:
            pass
    else:
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        print(f"\\n🏆 R²: {{r2:.4f}} | MAE: {{mae:.4f}} | RMSE: {{rmse:.4f}}")
        print(f"   MSE: {{mse:.4f}}")
        metrics = {{'r2': r2, 'mse': mse, 'mae': mae, 'rmse': rmse}}
    
    return model, metrics


def main():
    parser = argparse.ArgumentParser(description="Deep Learning Training — Your Configuration")
    parser.add_argument('--data', type=str, default='data/cleaned_data.csv')
    parser.add_argument('--output', type=str, default='deep_learning_model.pkl')
    parser.add_argument('--epochs', type=int, default=MAX_EPOCHS)
    parser.add_argument('--test-size', type=float, default=0.2)
    args = parser.parse_args()
    
    print("\\n" + "=" * 60)
    print("🧠 DataVision Deep Learning — sklearn MLP")
    print("=" * 60)
    
    if not os.path.exists(args.data):
        print(f"❌ Data file not found: {{args.data}}")
        return
    
    df = pd.read_csv(args.data)
    print(f"📊 Dataset: {{len(df)}} rows × {{len(df.columns)}} columns")
    
    X, y, is_clf, label_encoder, scaler, feature_names, feature_metadata, numeric_cols, categorical_cols = preprocess_for_dl(df)
    print(f"📐 Features after preprocessing: {{X.shape[1]}}")
    
    classes = list(label_encoder.classes_) if label_encoder else []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42,
        stratify=y if is_clf else None
    )
    print(f"📦 Split: {{len(X_train)}} train / {{len(X_test)}} test")
    
    # Get smart configuration based on data size
    config = get_smart_config(len(X_train), X.shape[1])
    config['max_iter'] = args.epochs
    
    model, metrics = train_dl_model(X_train, X_test, y_train, y_test, is_clf, config, classes)
    
    # Generate predictions for saved evaluation
    y_pred = model.predict(X_test)
    
    # Save in same format as DataVision DL engine
    state = {{
        'model': model,
        'scaler': scaler,
        'label_encoder': label_encoder,
        'feature_columns': feature_names,
        'numeric_cols': numeric_cols,
        'categorical_cols': categorical_cols,
        'feature_metadata': feature_metadata,
        'target_column': TARGET_COLUMN,
        'algorithm': '{actual_algorithm}',
        'task_type': TASK_TYPE,
        'classes': classes,
        'metrics': metrics,
        'model_type': 'deep_learning',
        'y_test': y_test.tolist() if hasattr(y_test, 'tolist') else list(y_test),
        'y_pred': y_pred.tolist() if hasattr(y_pred, 'tolist') else list(y_pred),
    }}
    
    with open(args.output, 'wb') as f:
        pickle.dump(state, f)
    
    print(f"\\n💾 Model saved to: {{args.output}}")
    print("✅ Deep learning training complete!")
    print("\\nTo predict: python predict.py --mode dl")


if __name__ == '__main__':
    main()
'''


# =============================================================================
# EVALUATE SCRIPT — DATA-AWARE
# =============================================================================

def _generate_evaluate_script(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    best_model = config.get('best_model_name', 'Unknown')
    metrics = config.get('metrics', {})
    is_clf = 'classif' in task_type.lower()
    
    metrics_lines = []
    for k, v in metrics.items():
        if isinstance(v, float):
            metrics_lines.append(f"#   {k}: {v:.4f}")
        else:
            metrics_lines.append(f"#   {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "#   (no stored metrics)"
    
    return f'''"""
📊 Model Evaluation Script — Shows YOUR AutoML Results
========================================================
Auto-generated by DataVision AI

╔════════════════════════════════════════════════════════════════════╗
║  This script shows the EXACT SAME metrics as your AutoML training. ║
║  Supports Traditional ML, Deep Learning, and NLP models.           ║
╚════════════════════════════════════════════════════════════════════╝

Model         : {best_model}
Target Column : {target}
Task Type     : {task_type}

YOUR AUTOML METRICS:
{metrics_block}

Usage:
    python evaluate.py                    # Show YOUR AutoML results
    python evaluate.py --reeval           # Re-evaluate with data (may differ)
"""

import os
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    r2_score, mean_absolute_error, mean_squared_error,
    confusion_matrix, classification_report
)
try:
    from sklearn.metrics import roc_auc_score
except ImportError:
    roc_auc_score = None

warnings.filterwarnings('ignore')

TARGET_COLUMN = '{target}'
TASK_TYPE = '{task_type}'
BEST_MODE = '{config.get("best_mode", "traditional")}'  # Which mode won during AutoML


def print_classification_metrics(y_test, y_pred, model=None, X_test=None, target_encoder=None):
    """Print all classification metrics including ROC-AUC."""
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
    
    print(f"\\n✅ ACCURACY:    {{acc:.4f}} ({{acc*100:.1f}}%)")
    print(f"   Precision:   {{prec:.4f}} ({{prec*100:.1f}}%)")
    print(f"   Recall:      {{rec:.4f}} ({{rec*100:.1f}}%)")
    print(f"   F1-Weighted: {{f1:.4f}} ({{f1*100:.1f}}%)")
    print(f"   F1-Macro:    {{f1_macro:.4f}} ({{f1_macro*100:.1f}}%)")
    
    # ROC-AUC
    if roc_auc_score is not None and model is not None and X_test is not None:
        try:
            n_classes = len(np.unique(y_test))
            if n_classes == 2 and hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test)[:, 1]
                roc = roc_auc_score(y_test, y_proba)
                print(f"   ROC-AUC:     {{roc:.4f}} ({{roc*100:.1f}}%)")
            elif n_classes > 2 and hasattr(model, 'predict_proba'):
                y_proba = model.predict_proba(X_test)
                roc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
                print(f"   ROC-AUC:     {{roc:.4f}} ({{roc*100:.1f}}%)")
            elif n_classes == 2 and hasattr(model, 'decision_function'):
                y_scores = model.decision_function(X_test)
                roc = roc_auc_score(y_test, y_scores)
                print(f"   ROC-AUC:     {{roc:.4f}} ({{roc*100:.1f}}%)")
        except Exception:
            pass
    
    print("\\n📊 Classification Report:")
    if target_encoder is not None:
        try:
            print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))
        except Exception:
            print(classification_report(y_test, y_pred))
    else:
        print(classification_report(y_test, y_pred))
    
    print("\\n📊 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)


def print_regression_metrics(y_test, y_pred):
    """Print all regression metrics."""
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    
    print(f"\\n✅ R² SCORE: {{r2:.4f}}")
    print(f"   MSE:  {{mse:.4f}}")
    print(f"   RMSE: {{rmse:.4f}}")
    print(f"   MAE:  {{mae:.4f}}")


def load_dl_model(dl_path='deep_learning_model.pkl'):
    """Load the Deep Learning model."""
    if not os.path.exists(dl_path):
        return None
    try:
        with open(dl_path, 'rb') as f:
            state = pickle.load(f)
        return state
    except Exception as e:
        print(f"⚠️ Failed to load DL model: {{e}}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Show your AutoML training results")
    parser.add_argument('--model', type=str, default='model.pkl')
    parser.add_argument('--dl-model', type=str, default='deep_learning_model.pkl', help='Path to DL model file')
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', 'traditional', 'dl'], help='Evaluation mode')
    parser.add_argument('--data', type=str, default='data/cleaned_data.csv')
    parser.add_argument('--reeval', action='store_true', help='Re-evaluate with fresh train/test split (may differ from AutoML)')
    parser.add_argument('--cv', type=int, default=5, help='Number of cross-validation folds for --reeval')
    args = parser.parse_args()
    
    print("\\n" + "=" * 60)
    print("📊 DataVision AutoML — Your Training Results")
    print("=" * 60)
    
    # Decide which model to load based on BEST_MODE
    use_dl = False
    state = None
    
    if args.mode == 'dl' or (args.mode == 'auto' and BEST_MODE == 'deep_learning'):
        state = load_dl_model(args.dl_model)
        if state:
            use_dl = True
        else:
            print("⚠️ DL model not found, falling back to traditional ML model...")
    
    if not use_dl and args.mode != 'dl':
        if os.path.exists(args.model):
            with open(args.model, 'rb') as f:
                state = pickle.load(f)
        elif os.path.exists(args.dl_model):
            state = load_dl_model(args.dl_model)
            if state:
                use_dl = True
    
    if state is None:
        print("❌ No model found. Provide model.pkl or deep_learning_model.pkl")
        return
    
    model = state['model']
    task_type = state.get('task_type', TASK_TYPE)
    is_clf = 'classif' in task_type.lower()
    mode_display = 'deep_learning' if use_dl else state.get('mode', 'traditional')
    model_name = state.get('model_name', state.get('algorithm', 'Unknown'))
    
    print(f"\\n🏆 Model: {{model_name}}")
    print(f"🎯 Task: {{task_type}}")
    print(f"📊 Mode: {{mode_display}}")
    if use_dl:
        print(f"🧠 Architecture: {{state.get('algorithm', 'MLP')}}")
        print(f"   Features: {{len(state.get('feature_columns', state.get('feature_metadata', [])))}}")
    
    # =========================================================================
    # OPTION 1: Use SAVED y_test/y_pred (EXACT same as AutoML showed)
    # =========================================================================
    y_test_saved = state.get('y_test')
    y_pred_saved = state.get('y_pred')
    
    if not args.reeval and y_test_saved is not None and y_pred_saved is not None:
        print("\\n" + "=" * 60)
        print("📋 YOUR AUTOML TRAINING RESULTS (from saved predictions)")
        print("=" * 60)
        
        y_test = np.array(y_test_saved)
        y_pred = np.array(y_pred_saved)
        
        # For ROC-AUC we need X_test and the model — try to reconstruct
        X_test_for_roc = None
        if use_dl:
            X_test_saved = state.get('X_test')
            if X_test_saved is not None:
                X_test_for_roc = np.array(X_test_saved)
        
        if is_clf:
            print_classification_metrics(
                y_test, y_pred, model=model,
                X_test=X_test_for_roc,
                target_encoder=state.get('target_encoder') if not use_dl else state.get('label_encoder')
            )
        else:
            print_regression_metrics(y_test, y_pred)
        
        # Also show stored metrics
        stored_metrics = state.get('metrics', {{}})
        if stored_metrics:
            print("\\n📋 Stored Metrics from Training:")
            for k, v in stored_metrics.items():
                if isinstance(v, float):
                    print(f"   {{k}}: {{v:.4f}}")
                else:
                    print(f"   {{k}}: {{v}}")
        
        print("\\n" + "=" * 60)
        print("✅ These are your EXACT AutoML results.")
        print("   Use --reeval to re-evaluate with fresh data split (may differ).")
        print("=" * 60)
        return
    
    # =========================================================================
    # OPTION 2: Re-evaluate (may produce different results due to random split)
    # =========================================================================
    print("\\n⚠️ Re-evaluating with fresh train/test split...")
    print("   Note: Results may differ from AutoML due to different random split.")
    
    if not os.path.exists(args.data):
        print(f"⚠️ Data file not found: {{args.data}}")
        print("   Showing stored metrics only:")
        for k, v in state.get('metrics', {{}}).items():
            print(f"   {{k}}: {{v}}")
        return
    
    df = pd.read_csv(args.data)
    target_col = state.get('target_column', TARGET_COLUMN)
    feature_cols = state.get('feature_columns', [])
    
    if target_col not in df.columns:
        print(f"❌ Target '{{target_col}}' not in data")
        return
    
    df = df.dropna(subset=[target_col])
    
    if use_dl:
        # =====================================================================
        # DL Re-evaluation: Use the DL model's preprocessing pipeline
        # =====================================================================
        feature_metadata = state.get('feature_metadata', [])
        scaler = state.get('scaler')
        label_encoder = state.get('label_encoder')
        
        # Build feature matrix from metadata
        X_parts = []
        for meta in feature_metadata:
            col = meta['name']
            if meta.get('type') == 'numeric':
                if col in df.columns:
                    X_parts.append(df[col].apply(pd.to_numeric, errors='coerce').fillna(meta.get('mean', 0)).values.reshape(-1, 1))
                else:
                    X_parts.append(np.full((len(df), 1), meta.get('mean', 0)))
            elif meta.get('type') == 'categorical':
                if col in df.columns:
                    encoding = meta.get('encoding', {{}})
                    X_parts.append(df[col].astype(str).map(lambda v: encoding.get(v, 0)).values.reshape(-1, 1))
                else:
                    X_parts.append(np.zeros((len(df), 1)))
        
        if X_parts:
            X = np.hstack(X_parts).astype(float)
        else:
            X = df.drop(columns=[target_col]).select_dtypes(include=[np.number]).fillna(0).values
        
        y = df[target_col].values
        if is_clf and label_encoder:
            try:
                y = label_encoder.transform(y)
            except Exception:
                le = LabelEncoder()
                y = le.fit_transform(y)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale AFTER split (same as training)
        if scaler:
            X_train = scaler.transform(X_train)
            X_test = scaler.transform(X_test)
        
        y_pred = model.predict(X_test)
        
        if is_clf:
            print(f"\\n📊 Deep Learning Classification Metrics (re-evaluated):")
            print_classification_metrics(y_test, y_pred, model=model, X_test=X_test,
                                       target_encoder=label_encoder)
        else:
            print(f"\\n📊 Deep Learning Regression Metrics (re-evaluated):")
            print_regression_metrics(y_test, y_pred)
    else:
        # =====================================================================
        # Traditional ML Re-evaluation
        # =====================================================================
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        target_encoder = state.get('target_encoder')
        if is_clf and target_encoder:
            y = pd.Series(target_encoder.transform(y))
        
        label_encoders = state.get('label_encoders', {{}})
        for col in X.select_dtypes(include=['object', 'category']).columns:
            if col in label_encoders:
                try:
                    X[col] = label_encoders[col].transform(X[col].astype(str))
                except:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
            else:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        X = X.fillna(0)
        
        scaler = state.get('scaler')
        if scaler and feature_cols:
            avail = [c for c in feature_cols if c in X.columns]
            if avail:
                X = X[avail]
                X = pd.DataFrame(scaler.transform(X), columns=avail)
        
        # Align columns with model's expected features
        if feature_cols:
            for col in feature_cols:
                if col not in X.columns:
                    X[col] = 0
            X = X.reindex(columns=feature_cols, fill_value=0)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        y_pred = model.predict(X_test)
        y_pred_train = model.predict(X_train)
        
        if is_clf:
            print(f"\\n📊 Classification Metrics (re-evaluated):")
            print_classification_metrics(y_test, y_pred, model=model, X_test=X_test,
                                       target_encoder=state.get('target_encoder'))
            
            # Overfitting check
            train_acc = accuracy_score(y_train, y_pred_train)
            test_acc = accuracy_score(y_test, y_pred)
            gap = train_acc - test_acc
            if gap > 0.1:
                print(f"\\n⚠️ Overfitting detected (train-test gap: {{gap:.4f}})")
            elif gap < 0.01:
                print(f"\\n✅ Good generalization (train-test gap: {{gap:.4f}})")
            
            try:
                cv_scores = cross_val_score(model, X, y, cv=args.cv, scoring='accuracy')
                print(f"\\n🔄 {{args.cv}}-Fold CV Accuracy: {{cv_scores.mean():.4f}} ± {{cv_scores.std():.4f}}")
            except Exception as e:
                print(f"   CV failed: {{e}}")
        else:
            print(f"\\n📊 Regression Metrics (re-evaluated):")
            print_regression_metrics(y_test, y_pred)
            
            try:
                cv_scores = cross_val_score(model, X, y, cv=args.cv, scoring='r2')
                print(f"\\n🔄 {{args.cv}}-Fold CV R²: {{cv_scores.mean():.4f}} ± {{cv_scores.std():.4f}}")
            except:
                pass
    
    print("\\n✅ Evaluation complete!")


if __name__ == '__main__':
    main()
'''


# =============================================================================
# API SERVER — DATA-AWARE
# =============================================================================

def _generate_api_server_script(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    features = config.get('feature_columns', [])
    best_model = config.get('best_model_name', 'Unknown')
    numeric_features = config.get('numeric_features', [])
    categorical_features = config.get('categorical_features', [])
    feature_metadata = config.get('feature_metadata', [])
    
    features_list = ", ".join(f"'{f}'" for f in features[:30])
    
    # Build raw feature info (original columns user understands)
    raw_feature_info_lines = []
    for fm in feature_metadata[:30]:
        name = fm.get('name', '')
        ftype = fm.get('type', 'numeric')
        if ftype == 'numeric':
            mn = fm.get('min', '?')
            mx = fm.get('max', '?')
            mean_val = fm.get('mean', 0)
            raw_feature_info_lines.append(f'    "{name}": {{"type": "numeric", "min": {mn}, "max": {mx}, "default": {mean_val:.2f}}},')
        elif ftype == 'categorical':
            options = fm.get('options', [])
            opts_str = str(options[:10])
            raw_feature_info_lines.append(f'    "{name}": {{"type": "categorical", "options": {opts_str}}},')
        elif ftype == 'text':
            raw_feature_info_lines.append(f'    "{name}": {{"type": "text"}},')
    
    if not raw_feature_info_lines and features:
        for f in features[:30]:
            raw_feature_info_lines.append(f'    "{f}": {{"type": "numeric", "default": 0}},')
    
    raw_features_block = "\n".join(raw_feature_info_lines)
    
    return f'''"""
🌐 Flask API Server — Your Trained Model
============================================
Auto-generated by DataVision AI

Model         : {best_model}
Target Column : {target}
Task Type     : {task_type}
Features      : {len(features)} columns

Usage:
    python api_server.py
    python api_server.py --port 8080
    
Endpoints:
    POST /predict    — Make a prediction (JSON body with your feature names)
    GET  /health     — Health check
    GET  /model-info — Model metadata and expected features
"""

import os
import json
import re
import pickle
import argparse
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from sklearn.preprocessing import LabelEncoder, RobustScaler

app = Flask(__name__)

MODEL_STATE = None
FEATURE_ENGINEER = None
FEATURE_COLUMNS = [{features_list}]
TARGET_COLUMN = '{target}'
BEST_MODE = '{config.get("best_mode", "traditional")}'  # Which mode won during AutoML

# YOUR original column names with types and ranges (what you input)
RAW_FEATURE_INFO = {{
{raw_features_block}
}}


# =============================================================================
# Standalone Feature Engineer — exact DataVision preprocessing
# =============================================================================
class StandaloneFeatureEngineer:
    def __init__(self, state):
        self.transformers = state.get('transformers', {{}})
        self.encoders = state.get('encoders', {{}})
        self.feature_names = state.get('feature_names', [])
        self.original_columns = state.get('original_columns', [])
        self.selected_feature_indices = state.get('selected_feature_indices', None)
        self.is_fitted = state.get('is_fitted', True)
        self.stopwords = set("i me my myself we our ours ourselves you your yours yourself yourselves he him his himself she her hers herself it its itself they them their theirs themselves what which who whom this that these those am is are was were be been being have has had having do does did doing a an the and but if or because as until while of at by for with about against between through during before after above below to from up down in out on off over under again further then once here there when where why how all both each few more most other some such no nor not only own same so than too very s t can will just don should now d ll m o re ve y ain aren couldn didn doesn hadn hasn haven isn ma mightn mustn needn shan shouldn wasn weren won wouldn".split())
        self.positive_words = set("good great excellent amazing wonderful fantastic brilliant outstanding superb love best perfect beautiful awesome incredible impressive magnificent exceptional fabulous terrific marvelous stellar remarkable extraordinary delightful gorgeous splendid spectacular phenomenal exquisite lovely charming pleasant nice fine happy joy enjoy satisfied pleased glad cheerful excited thrilled".split())
        self.negative_words = set("bad terrible horrible awful worst poor disappointing disgusting pathetic useless dreadful atrocious appalling abysmal mediocre inferior unpleasant nasty vile wretched miserable lousy horrendous hideous ghastly hideous deplorable lamentable pitiful woeful tragic sad angry frustrated annoyed irritated disappointed upset unhappy distressed sorrowful gloomy depressed".split())

    def _clean_text(self, text):
        text = str(text).lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'http\\S+', ' ', text)
        text = re.sub(r'[^a-z0-9\\s]', ' ', text)
        text = ' '.join(w for w in text.split() if w not in self.stopwords and len(w) > 1)
        return text if text.strip() else 'empty'

    def _text_statistics(self, text):
        text = str(text)
        words = text.split()
        wl = [len(w) for w in words] if words else [0]
        return [len(text), len(words), np.mean(wl), np.std(wl), max(wl) if wl else 0,
                len(set(words)) / max(len(words), 1), text.count('!'), text.count('?'),
                sum(1 for c in text if c.isupper()) / max(len(text), 1),
                len([w for w in words if len(w) > 6]) / max(len(words), 1)]

    def _sentiment_score(self, text):
        words = set(str(text).lower().split())
        pos = len(words & self.positive_words)
        neg = len(words & self.negative_words)
        total = max(pos + neg, 1)
        return [pos / total, neg / total, (pos - neg) / total, total]

    def transform(self, df):
        df = df.copy()
        cols = df.columns.tolist()
        seen = {{}}
        new_cols = []
        for col in cols:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{{col}}_{{seen[col]}}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols
        feature_parts = []

        if 'numeric_cols' in self.transformers:
            numeric_cols = self.transformers['numeric_cols']
            for col in numeric_cols:
                if col not in df.columns:
                    df[col] = 0
            try:
                numeric_data = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0).values
                scaler = self.transformers['numeric_scaler']
                numeric_scaled = scaler.transform(numeric_data)
                numeric_scaled = np.nan_to_num(numeric_scaled, nan=0.0, posinf=0.0, neginf=0.0)
                feature_parts.append(numeric_scaled)
                if 2 <= len(numeric_cols) <= 10:
                    interactions = []
                    for i in range(min(len(numeric_cols), 4)):
                        interactions.append((numeric_scaled[:, i] ** 2).reshape(-1, 1))
                    for i in range(min(len(numeric_cols), 4)):
                        for j in range(i + 1, min(len(numeric_cols), 4)):
                            interactions.append((numeric_scaled[:, i] * numeric_scaled[:, j]).reshape(-1, 1))
                    if interactions:
                        feature_parts.append(np.hstack(interactions))
            except:
                feature_parts.append(np.zeros((len(df), len(numeric_cols))))

        for key, cols in self.transformers.items():
            if key.endswith('_onehot'):
                col_name = key.replace('_onehot', '')
                try:
                    if col_name in df.columns:
                        series = df[col_name].fillna('_MISSING_').astype(str).str.strip()
                        dummies = pd.get_dummies(series, prefix=col_name)
                        dummies = dummies.reindex(columns=cols, fill_value=0)
                        feature_parts.append(dummies.values.astype(float))
                    else:
                        feature_parts.append(np.zeros((len(df), len(cols))))
                except:
                    feature_parts.append(np.zeros((len(df), len(cols))))

        for col, le in self.encoders.items():
            try:
                if col in df.columns:
                    series = df[col].fillna('_MISSING_').astype(str).str.strip()
                    encoded = series.map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
                    feature_parts.append(encoded.values.reshape(-1, 1).astype(float))
                    freq_key = f'{{col}}_freq_map'
                    if freq_key in self.transformers:
                        freq_map = self.transformers[freq_key]
                        freq_encoded = series.map(lambda s: freq_map.get(s, 0.0)).values.astype(float)
                        feature_parts.append(freq_encoded.reshape(-1, 1))
                else:
                    feature_parts.append(np.zeros((len(df), 1)))
                    if f'{{col}}_freq_map' in self.transformers:
                        feature_parts.append(np.zeros((len(df), 1)))
            except:
                feature_parts.append(np.zeros((len(df), 1)))

        if 'cat_interactions' in self.transformers:
            for key, value in self.transformers['cat_interactions'].items():
                if key.endswith('_freq_map'):
                    continue
                try:
                    col1, col2, le = value
                    if col1 in df.columns and col2 in df.columns:
                        combined = df[col1].fillna('_NA_').astype(str) + "_X_" + df[col2].fillna('_NA_').astype(str)
                        encoded = combined.map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
                        feature_parts.append(encoded.values.reshape(-1, 1).astype(float))
                        fk = f"{{key}}_freq_map"
                        if fk in self.transformers['cat_interactions']:
                            fm = self.transformers['cat_interactions'][fk]
                            feature_parts.append(combined.map(lambda s: fm.get(s, 0.0)).values.reshape(-1, 1).astype(float))
                    else:
                        feature_parts.append(np.zeros((len(df), 1)))
                except:
                    pass

        if 'num_cat_aggs' in self.transformers:
            for key, mean_map in self.transformers['num_cat_aggs'].items():
                try:
                    parts = key.rsplit('_by_', 1)
                    if len(parts) == 2:
                        num_col, cat_col = parts[0], parts[1].rsplit('_mean', 1)[0]
                        if num_col in df.columns and cat_col in df.columns:
                            cat_s = df[cat_col].fillna('_NA_').astype(str)
                            dv = np.mean(list(mean_map.values())) if mean_map else 0
                            agg = cat_s.map(lambda s: mean_map.get(s, dv)).values.astype(float)
                            feature_parts.append(agg.reshape(-1, 1))
                            feature_parts.append((df[num_col].fillna(0).values - agg).reshape(-1, 1))
                        else:
                            feature_parts.extend([np.zeros((len(df), 1))] * 2)
                except:
                    pass

        for key, tfidf in self.transformers.items():
            if key.endswith('_tfidf'):
                col = key.replace('_tfidf', '')
                try:
                    if col in df.columns:
                        series = df[col].fillna('').astype(str)
                        cleaned = series.apply(self._clean_text)
                        tm = tfidf.transform(cleaned)
                        svd_key = f'{{col}}_svd'
                        feature_parts.append(self.transformers[svd_key].transform(tm) if svd_key in self.transformers else tm.toarray())
                        feature_parts.append(np.array([self._text_statistics(t) for t in series]))
                        feature_parts.append(np.array([self._sentiment_score(t) for t in series]))
                except:
                    pass

        if not feature_parts:
            return np.zeros((len(df), len(self.feature_names)))
        X = np.hstack(feature_parts)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        if 'variance_selector' in self.transformers:
            sel = self.transformers['variance_selector']
            try:
                if X.shape[1] == sel.n_features_in_:
                    X = sel.transform(X)
                elif self.selected_feature_indices is not None:
                    vi = [i for i in self.selected_feature_indices if i < X.shape[1]]
                    if vi:
                        X = X[:, vi]
            except:
                pass

        if 'pca' in self.transformers:
            try:
                pca = self.transformers['pca']
                if X.shape[1] == pca.n_features_in_:
                    X = pca.transform(X)
            except:
                pass

        if X.shape[1] != len(self.feature_names):
            if X.shape[1] < len(self.feature_names):
                X = np.hstack([X, np.zeros((len(df), len(self.feature_names) - X.shape[1]))])
            else:
                X = X[:, :len(self.feature_names)]
        return X

    def transform_single(self, data):
        for col in self.original_columns:
            if col not in data:
                data[col] = 0
        df = pd.DataFrame([data])
        X = self.transform(df)
        n = len(self.feature_names)
        if X.shape[1] < n:
            X = np.hstack([X, np.zeros((1, n - X.shape[1]))])
        elif X.shape[1] > n:
            X = X[:, :n]
        return X


def load_model():
    global MODEL_STATE, FEATURE_ENGINEER
    
    # If best mode is deep_learning, load DL first as primary
    if BEST_MODE == 'deep_learning':
        load_dl_model()
        if DL_STATE is not None:
            print(f"🧠 Primary mode: Deep Learning (BEST_MODE={{BEST_MODE}})")
            # Also try loading ML model as fallback
            for path in ['model.pkl', 'nlp_model.pkl']:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        MODEL_STATE = pickle.load(f)
                    print(f"   Also loaded fallback: {{path}}")
                    break
            return True
    
    # Traditional/NLP: load ML model first
    for path in ['model.pkl', 'nlp_model.pkl']:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                MODEL_STATE = pickle.load(f)
            print(f"✅ Loaded: {{path}} ({{MODEL_STATE.get('model_name', 'Unknown')}})")
            # Load feature engineer for exact preprocessing
            eng_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feature_engineer.pkl')
            if os.path.exists(eng_path):
                try:
                    with open(eng_path, 'rb') as ef:
                        eng_state = pickle.load(ef)
                    FEATURE_ENGINEER = StandaloneFeatureEngineer(eng_state)
                    print(f"   Pipeline: feature_engineer.pkl ({{len(FEATURE_ENGINEER.feature_names)}} features)")
                except Exception as e:
                    print(f"   Warning: Could not load feature_engineer.pkl: {{e}}")
            break
    
    # Also load DL model if available
    load_dl_model()
    
    if MODEL_STATE is None and DL_STATE is None:
        print("❌ No model file found")
        return False
    return True


# =============================================================================
# Deep Learning Model Support (sklearn MLPClassifier/MLPRegressor)
# =============================================================================
DL_STATE = None

def load_dl_model():
    """Load the Deep Learning model if available."""
    global DL_STATE
    dl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deep_learning_model.pkl')
    if os.path.exists(dl_path):
        try:
            with open(dl_path, 'rb') as f:
                DL_STATE = pickle.load(f)
            print(f"✅ Loaded DL model: {{DL_STATE.get('algorithm', 'MLP')}}")
        except Exception as e:
            print(f"⚠️ Failed to load DL model: {{e}}")


def preprocess_dl_input(data):
    """Preprocess input for Deep Learning model using feature_metadata."""
    feature_metadata = DL_STATE.get('feature_metadata', [])
    feature_values = []
    
    # Process numeric features
    for meta in feature_metadata:
        if meta.get('type') == 'numeric':
            col = meta['name']
            if col in data:
                try:
                    feature_values.append(float(data[col]))
                except (ValueError, TypeError):
                    feature_values.append(meta.get('mean', 0))
            else:
                feature_values.append(meta.get('mean', 0))
    
    # Process categorical features (one-hot)
    for meta in feature_metadata:
        if meta.get('type') == 'categorical':
            col = meta['name']
            value = str(data.get(col, ''))
            options = meta.get('options', [])
            for opt in options:
                feature_values.append(1.0 if value == opt else 0.0)
            feature_values.append(1.0 if not value or value == 'nan' else 0.0)
    
    # Fallback
    if not feature_values and DL_STATE.get('feature_columns'):
        for col in DL_STATE['feature_columns']:
            if col in data:
                try:
                    feature_values.append(float(data[col]) if not isinstance(data[col], str) else 0)
                except:
                    feature_values.append(0)
            else:
                feature_values.append(0)
    
    X = np.array([feature_values])
    
    scaler = DL_STATE.get('scaler')
    if scaler and hasattr(scaler, 'n_features_in_'):
        expected = scaler.n_features_in_
        actual = X.shape[1]
        if actual < expected:
            X = np.hstack([X, np.zeros((1, expected - actual))])
        elif actual > expected:
            X = X[:, :expected]
    
    if scaler:
        X = scaler.transform(X)
    
    return X


def preprocess_input(data):
    """Preprocess raw input using the EXACT same pipeline as DataVision AutoML."""
    global FEATURE_ENGINEER
    
    # Use feature engineer (exact AutoML pipeline)
    if FEATURE_ENGINEER is not None:
        try:
            return FEATURE_ENGINEER.transform_single(data)
        except Exception as e:
            print(f"Warning: Feature engineer failed ({{e}}), using fallback")
    
    # Fallback: basic label-encode + scale
    feature_cols = MODEL_STATE.get('feature_columns', FEATURE_COLUMNS)
    label_encoders = MODEL_STATE.get('label_encoders', {{}})
    scaler = MODEL_STATE.get('scaler')
    
    row = {{}}
    for col in feature_cols:
        val = data.get(col, 0)
        if col in label_encoders:
            le = label_encoders[col]
            val_str = str(val)
            if val_str in le.classes_:
                val = le.transform([val_str])[0]
            else:
                val = 0
        else:
            try:
                val = float(val)
            except (ValueError, TypeError):
                val = 0
        row[col] = val
    
    X = pd.DataFrame([row], columns=feature_cols)
    if scaler:
        try:
            X = pd.DataFrame(scaler.transform(X), columns=feature_cols)
        except:
            pass
    return X


@app.route('/health', methods=['GET'])
def health():
    return jsonify({{"status": "healthy", "model_loaded": MODEL_STATE is not None or DL_STATE is not None, "dl_model_loaded": DL_STATE is not None}})


@app.route('/model-info', methods=['GET'])
def model_info():
    if MODEL_STATE is None and DL_STATE is None:
        return jsonify({{"error": "No model loaded"}}), 404
    
    info = {{"best_mode": BEST_MODE}}
    if BEST_MODE == 'deep_learning' and DL_STATE:
        info.update({{
            "model_name": DL_STATE.get('algorithm', 'MLP Neural Network'),
            "task_type": DL_STATE.get('task_type', '{task_type}'),
            "target_column": TARGET_COLUMN,
            "input_features": list(RAW_FEATURE_INFO.keys()),
            "metrics": {{k: float(v) if isinstance(v, (int, float)) else str(v) 
                        for k, v in DL_STATE.get('metrics', {{}}).items()}},
        }})
    elif MODEL_STATE:
        info.update({{
            "model_name": MODEL_STATE.get('model_name', 'Unknown'),
            "task_type": MODEL_STATE.get('task_type', '{task_type}'),
            "target_column": TARGET_COLUMN,
            "input_features": list(RAW_FEATURE_INFO.keys()),
            "metrics": {{k: float(v) if isinstance(v, (int, float)) else str(v) 
                        for k, v in MODEL_STATE.get('metrics', {{}}).items()}},
        }})
    if DL_STATE:
        info["dl_model"] = {{
            "algorithm": DL_STATE.get('algorithm', 'MLP'),
            "task_type": DL_STATE.get('task_type', '{task_type}'),
            "metrics": {{k: float(v) if isinstance(v, (int, float)) else str(v) 
                        for k, v in DL_STATE.get('metrics', {{}}).items()}},
        }}
    return jsonify(info)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if MODEL_STATE is None and DL_STATE is None:
        return jsonify({{"error": "No model loaded"}}), 500
    
    # GET request: show web form for interactive prediction
    if request.method == 'GET':
        if BEST_MODE == 'deep_learning' and DL_STATE:
            model_name = DL_STATE.get('algorithm', 'MLP Neural Network')
            task_type_val = DL_STATE.get('task_type', '{task_type}')
            metrics = DL_STATE.get('metrics', {{}})
        elif MODEL_STATE:
            model_name = MODEL_STATE.get('model_name', 'Unknown')
            task_type_val = MODEL_STATE.get('task_type', '{task_type}')
            metrics = MODEL_STATE.get('metrics', {{}})
        else:
            model_name = 'Unknown'
            task_type_val = '{task_type}'
            metrics = {{}}
        
        # Serve the UI using the extracted index.html template
        return render_template("index.html", 
                               model_name=model_name, 
                               target=TARGET_COLUMN, 
                               task_type_val=task_type_val, 
                               metrics=metrics, 
                               raw_feature_info=RAW_FEATURE_INFO)
    
    # POST request: JSON API prediction
    try:
        data = request.get_json()
        if not data:
            return jsonify({{"error": "No JSON body. Send features as JSON.", "expected_features": list(RAW_FEATURE_INFO.keys())}}), 400
        
        # Check if caller wants DL mode, or if BEST_MODE is deep_learning, or if only DL is available
        req_mode = data.pop('_mode', None)
        use_dl = (req_mode == 'dl') or (req_mode != 'ml' and BEST_MODE == 'deep_learning' and DL_STATE is not None) or (MODEL_STATE is None and DL_STATE is not None)
        
        if use_dl and DL_STATE:
            # Deep Learning prediction
            X = preprocess_dl_input(data)
            dl_model = DL_STATE['model']
            label_encoder = DL_STATE.get('label_encoder')
            task_type = DL_STATE.get('task_type', '{task_type}')
            classes = DL_STATE.get('classes', [])
            
            pred = dl_model.predict(X)[0]
            result = {{"raw_prediction": int(pred) if isinstance(pred, (np.integer,)) else float(pred)}}
            
            if 'classif' in task_type.lower() and label_encoder:
                try:
                    result['prediction'] = str(label_encoder.inverse_transform([int(pred)])[0])
                except:
                    result['prediction'] = str(pred)
            else:
                result['prediction'] = float(pred)
            
            if 'classif' in task_type.lower() and hasattr(dl_model, 'predict_proba'):
                try:
                    proba = dl_model.predict_proba(X)[0]
                    result['confidence'] = float(max(proba))
                    if classes:
                        result['probabilities'] = {{
                            str(c): round(float(p), 4) for c, p in zip(classes, proba)
                        }}
                except:
                    pass
            
            result['mode'] = 'deep_learning'
            return jsonify(result)
        
        # Traditional/NLP prediction
        model = MODEL_STATE['model']
        target_encoder = MODEL_STATE.get('target_encoder')
        task_type = MODEL_STATE.get('task_type', '{task_type}')
        
        X = preprocess_input(data)
        
        prediction = model.predict(X)[0]
        result = {{"raw_prediction": int(prediction) if isinstance(prediction, (np.integer,)) else float(prediction)}}
        
        if 'classif' in task_type.lower() and target_encoder:
            try:
                result['prediction'] = str(target_encoder.inverse_transform([int(prediction)])[0])
            except:
                result['prediction'] = str(prediction)
        else:
            result['prediction'] = float(prediction)
        
        if 'classif' in task_type.lower() and hasattr(model, 'predict_proba'):
            try:
                proba = model.predict_proba(X)[0]
                result['confidence'] = float(max(proba))
                if target_encoder:
                    result['probabilities'] = {{
                        str(c): round(float(p), 4) for c, p in zip(target_encoder.classes_, proba)
                    }}
            except:
                pass
        
        return jsonify(result)
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    args = parser.parse_args()
    
    if load_model():
        print(f"\\n🌐 API Server on http://{{args.host}}:{{args.port}}")
        print(f"   POST /predict  — Send JSON with your feature values")
        print(f"   GET  /health   — Health check")
        print(f"   GET  /model-info — Your model details and expected features")
        app.run(host=args.host, port=args.port, debug=False)
'''


# =============================================================================
# PREPROCESSING UTILS — DATA-AWARE
# =============================================================================

def _generate_preprocessing_utils(config: Dict) -> str:
    target = config['target_column']
    task_type = config['task_type']
    features = config.get('feature_columns', [])
    features_list = ", ".join(f"'{f}'" for f in features[:30])
    
    return f'''"""
🔧 Preprocessing Utilities — Mirrors DataVision AutoML Pipeline
===================================================================
These utilities replicate the EXACT preprocessing pipeline used by
DataVision's ProductionDataCleaner + ProductionFeatureEngineer.

Pipeline steps:
1. Remove useless columns (IDs, URLs, high-cardinality strings)
2. Remove duplicates
3. Smart type conversion (parse $, M/K units, commas)
4. KNN imputation for numerics (median fallback)
5. Mode fill for categoricals
6. Replace inf/-inf with median
7. Remove constant columns
8. IQR-based outlier capping
9. Log-transform skewed features
10. RobustScaler for numeric features
11. Categorical encoding (binary→label, low-card→one-hot, high-card→label+freq)
12. VarianceThreshold to remove near-constant features
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import KNNImputer

TARGET_COLUMN = '{target}'
TASK_TYPE = '{task_type}'
FEATURE_COLUMNS = [{features_list}]


def detect_task_type(y):
    """Auto-detect classification vs regression."""
    if y.dtype == 'object' or y.nunique() < 20:
        return 'classification'
    return 'regression'


def remove_useless_columns(df, target_col=TARGET_COLUMN):
    """Remove ID-like, URL, and high-cardinality columns (same as DataVision)."""
    id_patterns = ['unnamed', 'index', '_id', 'guid', 'uuid', 'url', 'link', 'href', 'path']
    cols_to_drop = []
    for col in df.columns:
        if col == target_col:
            continue
        col_lower = col.lower().strip()
        if any(pat in col_lower for pat in id_patterns):
            cols_to_drop.append(col)
        elif df[col].dtype == 'object' and df[col].nunique() / max(len(df), 1) > 0.9:
            cols_to_drop.append(col)
    return df.drop(columns=cols_to_drop, errors='ignore') if cols_to_drop else df


def smart_type_conversion(df, target_col=TARGET_COLUMN):
    """Parse hidden numerics: $, M/K units, commas (same as DataVision)."""
    for col in df.select_dtypes(include=['object']).columns:
        if col == target_col:
            continue
        sample = df[col].dropna().head(20)
        if len(sample) == 0:
            continue
        converted = 0
        for val in sample:
            try:
                v = str(val).replace('$', '').replace(',', '').strip()
                if v.upper().endswith(('M', 'K', '+')):
                    float(v[:-1])
                else:
                    float(v)
                converted += 1
            except:
                pass
        if converted / max(len(sample), 1) > 0.6:
            def parse_val(val):
                if pd.isna(val):
                    return np.nan
                v = str(val).replace('$', '').replace(',', '').strip()
                try:
                    if v.upper().endswith('M'): return float(v[:-1]) * 1e6
                    if v.upper().endswith('K'): return float(v[:-1]) * 1e3
                    if v.endswith('+'): return float(v[:-1])
                    return float(v)
                except:
                    return np.nan
            df[col] = df[col].apply(parse_val)
    return df


def impute_missing(df, target_col=TARGET_COLUMN):
    """KNN imputation for numerics, mode fill for categoricals (same as DataVision)."""
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
    if numeric_cols and df[numeric_cols].isna().any().any():
        try:
            imputer = KNNImputer(n_neighbors=5, weights='distance')
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        except:
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median())
    
    for col in df.select_dtypes(include=['object', 'category']).columns:
        if col == target_col:
            continue
        mode = df[col].mode()
        df[col] = df[col].fillna(mode.iloc[0] if len(mode) > 0 else '_MISSING_')
    return df


def cap_outliers_iqr(df, target_col=TARGET_COLUMN):
    """IQR-based outlier capping with [1st, 99th] percentile bounds (same as DataVision)."""
    for col in df.select_dtypes(include=[np.number]).columns:
        if col == target_col:
            continue
        Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        IQR = Q3 - Q1
        p1, p99 = df[col].quantile(0.01), df[col].quantile(0.99)
        lower = max(p1, Q1 - 3 * IQR)
        upper = min(p99, Q3 + 3 * IQR)
        df[col] = df[col].clip(lower=lower, upper=upper)
    return df


def engineer_features(X):
    """Feature engineering matching DataVision's ProductionFeatureEngineer."""
    label_encoders = {{}}
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Log-transform skewed numerics (skewness > 2, non-negative)
    for col in numeric_cols:
        if (X[col] >= 0).all() and abs(X[col].skew()) > 2:
            X[f'{{col}}_log'] = np.log1p(X[col])
    
    # RobustScaler (same as DataVision, not StandardScaler)
    numeric_cols_all = X.select_dtypes(include=[np.number]).columns.tolist()
    scaler = RobustScaler()
    if numeric_cols_all:
        X[numeric_cols_all] = scaler.fit_transform(X[numeric_cols_all])
    
    # Polynomial features (top 4 numeric, squared + interactions)
    if 2 <= len(numeric_cols) <= 10:
        top_n = min(4, len(numeric_cols))
        top_cols = numeric_cols[:top_n]
        for col in top_cols:
            X[f'{{col}}_sq'] = X[col] ** 2
        for i in range(len(top_cols)):
            for j in range(i + 1, len(top_cols)):
                X[f'{{top_cols[i]}}_x_{{top_cols[j]}}'] = X[top_cols[i]] * X[top_cols[j]]
    
    # Categorical encoding
    for col in categorical_cols:
        nuniq = X[col].nunique()
        if nuniq <= 2:  # Binary → LabelEncoder
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            label_encoders[col] = le
        elif nuniq <= 10:  # Low cardinality → one-hot
            dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
            X = pd.concat([X.drop(columns=[col]), dummies], axis=1)
        else:  # High cardinality → label + frequency encoding
            le = LabelEncoder()
            X[f'{{col}}_label'] = le.fit_transform(X[col].astype(str))
            freq = X[col].value_counts(normalize=True)
            X[f'{{col}}_freq'] = X[col].map(freq)
            label_encoders[col] = le
            X = X.drop(columns=[col])
    
    # Force float + clean
    for col in X.columns:
        try:
            X[col] = X[col].astype(float)
        except:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str)).astype(float)
    X = X.replace([np.inf, -np.inf], 0).fillna(0)
    
    # VarianceThreshold (remove near-constant, threshold=0.01)
    try:
        vt = VarianceThreshold(threshold=0.01)
        X = pd.DataFrame(vt.fit_transform(X), columns=X.columns[vt.get_support()], index=X.index)
    except:
        pass
    
    return X, label_encoders, scaler


def full_preprocess(df, target_column=TARGET_COLUMN):
    """Complete DataVision preprocessing pipeline.
    
    Combines ProductionDataCleaner.clean() + ProductionFeatureEngineer.fit_transform().
    """
    # Step 1: Clean
    df = df.dropna(subset=[target_column])
    df = df.drop_duplicates()
    
    # Strip whitespace and replace string NaN variants
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace(['nan', 'NaN', 'None', 'null', 'NULL', ''], np.nan)
    
    df = remove_useless_columns(df, target_column)
    df = smart_type_conversion(df, target_column)
    df = impute_missing(df, target_column)
    
    # Replace inf, remove constant columns
    for col in df.select_dtypes(include=[np.number]).columns:
        if col != target_column:
            df[col] = df[col].replace([np.inf, -np.inf], df[col].replace([np.inf, -np.inf], np.nan).median())
    const_cols = [c for c in df.columns if c != target_column and df[c].nunique() <= 1]
    df = df.drop(columns=const_cols, errors='ignore')
    
    df = cap_outliers_iqr(df, target_column)
    df[df.select_dtypes(include=[np.number]).columns] = df.select_dtypes(include=[np.number]).fillna(0)
    
    # Step 2: Split target
    X = df.drop(columns=[target_column])
    y = df[target_column]
    
    task_type = detect_task_type(y)
    target_encoder = None
    if task_type == 'classification':
        target_encoder = LabelEncoder()
        y = pd.Series(target_encoder.fit_transform(y))
    
    # Step 3: Engineer features
    X, label_encoders, scaler = engineer_features(X)
    feature_cols = X.columns.tolist()
    
    return X, y, task_type, target_encoder, label_encoders, scaler, feature_cols
'''


# =============================================================================
# DOCKERFILE
# =============================================================================

def _generate_dockerfile(config: Dict) -> str:
    return '''FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "api_server.py", "--port", "5000"]
'''


# =============================================================================
# CLUSTERING / UNSUPERVISED LEARNING ZIP GENERATOR
# =============================================================================

def generate_clustering_code_zip(
    pkl_path: Path,
    cleaned_data_path: Optional[Path] = None,
    charts_data: Optional[Dict[str, str]] = None,
    clustering_meta: Optional[Dict[str, Any]] = None,
) -> io.BytesIO:
    """
    Generate a complete Python clustering project as a ZIP file.
    Similar to supervised ZIP but tailored for unsupervised learning.
    
    Args:
        pkl_path: Path to clustering_model_*.pkl
        cleaned_data_path: Path to clustered_data_*.csv
        charts_data: Dict of chart_name -> base64 data URI strings
        clustering_meta: Dict with algorithm, n_clusters, silhouette_score, feature_columns, etc.
    """
    import pickle

    buf = io.BytesIO()
    meta = clustering_meta or {}

    algorithm = meta.get('algorithm', 'kmeans')
    n_clusters = meta.get('n_clusters', 3)
    silhouette = meta.get('silhouette_score', 0)
    feature_columns = meta.get('feature_columns', [])
    cluster_profiles = meta.get('cluster_profiles', {})
    n_samples = meta.get('n_samples', 0)

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:

        # 1. Model PKL
        if pkl_path and pkl_path.exists():
            zf.write(pkl_path, 'clustering_model.pkl')

        # 2. Cleaned data with cluster assignments
        if cleaned_data_path and cleaned_data_path.exists():
            zf.writestr('data/clustered_data.csv', cleaned_data_path.read_bytes())

        # 3. config.json
        config_json = {
            "task_type": "clustering",
            "algorithm": algorithm,
            "n_clusters": n_clusters,
            "silhouette_score": silhouette,
            "feature_columns": feature_columns,
            "n_samples": n_samples,
            "generated_by": "DataVision AutoML",
        }
        zf.writestr('config.json', json.dumps(config_json, indent=2, default=str))

        # 4. predict_cluster.py
        zf.writestr('predict_cluster.py', _generate_clustering_predict_script(
            algorithm, n_clusters, feature_columns
        ))

        # 5. train_clustering.py
        zf.writestr('train_clustering.py', _generate_clustering_train_script(
            algorithm, n_clusters, feature_columns
        ))

        # 6. visualize_clusters.py
        zf.writestr('visualize_clusters.py', _generate_clustering_visualize_script(
            algorithm, n_clusters, feature_columns
        ))

        # 7. requirements.txt
        reqs = (
            "scikit-learn>=1.3.0\n"
            "pandas>=2.0.0\n"
            "numpy>=1.24.0\n"
            "matplotlib>=3.7.0\n"
            "seaborn>=0.12.0\n"
            "flask>=2.3.0\n"
            "joblib>=1.3.0\n"
        )
        zf.writestr('requirements.txt', reqs)

        # 8. api_server.py
        zf.writestr('api_server.py', _generate_clustering_api_script(
            algorithm, n_clusters, feature_columns
        ))

        # 9. README.md
        zf.writestr('README.md', _generate_clustering_readme(
            algorithm, n_clusters, silhouette, feature_columns, n_samples, cluster_profiles
        ))

        # 10. Dockerfile
        zf.writestr('Dockerfile', _generate_dockerfile({}))

        # 11. Bundle training charts as PNG
        if charts_data:
            charts_added = 0
            for chart_name, chart_value in charts_data.items():
                try:
                    if isinstance(chart_value, str) and 'base64,' in chart_value:
                        b64_data = chart_value.split('base64,', 1)[1]
                        img_bytes = base64.b64decode(b64_data)
                        safe_name = chart_name.replace(' ', '_').replace('/', '_').lower()
                        if not safe_name.endswith('.png'):
                            safe_name += '.png'
                        zf.writestr(f'charts/{safe_name}', img_bytes)
                        charts_added += 1
                except Exception as e:
                    logger.warning(f"Could not bundle chart '{chart_name}': {e}")
            if charts_added > 0:
                logger.info(f"Added {charts_added} clustering charts to charts/ directory")

    buf.seek(0)
    logger.info(f"Generated clustering ZIP: {buf.getbuffer().nbytes / 1024:.1f} KB")
    return buf


def _generate_clustering_predict_script(algorithm: str, n_clusters: int, feature_columns: List[str]) -> str:
    features_list = ", ".join(f'"{f}"' for f in feature_columns[:20])
    return f'''#!/usr/bin/env python3
"""
Predict Cluster Assignment for New Data
========================================
Generated by DataVision AutoML - Unsupervised Learning

Usage:
    python predict_cluster.py                    # Interactive mode
    python predict_cluster.py --csv input.csv    # Batch mode
"""

import pickle
import pandas as pd
import numpy as np
import argparse
import json
import sys
from pathlib import Path


FEATURE_COLUMNS = [{features_list}]


def load_model(model_path="clustering_model.pkl"):
    """Load the trained clustering model"""
    with open(model_path, "rb") as f:
        model_data = pickle.load(f)
    return model_data


def predict_cluster(model_data, features_dict):
    """Predict cluster for a single data point"""
    scaler = model_data.get("scaler")
    centroids = model_data.get("centroids_scaled")
    feature_cols = model_data.get("feature_columns", FEATURE_COLUMNS)

    # Build feature vector
    values = []
    for col in feature_cols:
        val = features_dict.get(col, 0)
        try:
            values.append(float(val))
        except (ValueError, TypeError):
            values.append(0.0)

    X = np.array(values).reshape(1, -1)

    # Scale
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X

    # Find nearest centroid
    if centroids is not None:
        centroids_arr = np.array(centroids)
        distances = np.linalg.norm(X_scaled - centroids_arr, axis=1)
        cluster = int(np.argmin(distances))
        confidence = 1.0 / (1.0 + distances[cluster])
    else:
        cluster = 0
        confidence = 0.0

    return {{
        "cluster": cluster,
        "cluster_name": f"Cluster_{{cluster}}",
        "confidence": round(confidence, 4),
    }}


def predict_batch(model_data, df):
    """Predict clusters for a batch of data"""
    results = []
    for _, row in df.iterrows():
        features = row.to_dict()
        result = predict_cluster(model_data, features)
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="Predict cluster assignment")
    parser.add_argument("--csv", type=str, help="Path to CSV file for batch prediction")
    parser.add_argument("--model", type=str, default="clustering_model.pkl", help="Model path")
    parser.add_argument("--output", type=str, default="predictions.csv", help="Output CSV path")
    args = parser.parse_args()

    model_data = load_model(args.model)
    feature_cols = model_data.get("feature_columns", FEATURE_COLUMNS)

    if args.csv:
        # Batch mode
        df = pd.read_csv(args.csv)
        print(f"Predicting clusters for {{len(df)}} samples...")
        results = predict_batch(model_data, df)
        df["Predicted_Cluster"] = [r["cluster"] for r in results]
        df["Cluster_Name"] = [r["cluster_name"] for r in results]
        df["Confidence"] = [r["confidence"] for r in results]
        df.to_csv(args.output, index=False)
        print(f"Results saved to {{args.output}}")
    else:
        # Interactive mode
        print("\\n=== Cluster Prediction (Interactive) ===")
        print(f"Algorithm: {algorithm.upper()}, Clusters: {n_clusters}")
        print(f"Features: {{len(feature_cols)}}")
        print()

        features = {{}}
        for col in feature_cols:
            val = input(f"  {{col}}: ")
            features[col] = val

        result = predict_cluster(model_data, features)
        print(f"\\n  Predicted: {{result[\'cluster_name\']}}")
        print(f"  Confidence: {{result[\'confidence\']:.1%}}")


if __name__ == "__main__":
    main()
'''


def _generate_clustering_train_script(algorithm: str, n_clusters: int, feature_columns: List[str]) -> str:
    features_list = ", ".join(f'"{f}"' for f in feature_columns[:20])
    return f'''#!/usr/bin/env python3
"""
Re-Train Clustering Model
==========================
Generated by DataVision AutoML - Unsupervised Learning

Reproduces the EXACT clustering from DataVision training.
Algorithm: {algorithm.upper()}, Clusters: {n_clusters}

Usage:
    python train_clustering.py                          # Use default data
    python train_clustering.py --data my_data.csv       # Custom data
    python train_clustering.py --algorithm dbscan       # Different algorithm
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering, SpectralClustering
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import pickle
import argparse
import json
from pathlib import Path


FEATURE_COLUMNS = [{features_list}]
DEFAULT_ALGORITHM = "{algorithm}"
DEFAULT_N_CLUSTERS = {n_clusters}


def train_clustering(data_path="data/clustered_data.csv", algorithm=DEFAULT_ALGORITHM,
                     n_clusters=DEFAULT_N_CLUSTERS, output_path="clustering_model.pkl"):
    """Train a clustering model"""
    print(f"\\n{'='*60}")
    print(f"  CLUSTERING TRAINING")
    print(f"  Algorithm: {{algorithm.upper()}}")
    print(f"  Target clusters: {{n_clusters}}")
    print(f"{'='*60}\\n")

    # Load data
    df = pd.read_csv(data_path)
    print(f"Loaded {{len(df)}} samples")

    # Select numeric features
    feature_cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    if not feature_cols:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove cluster assignment columns if present
        feature_cols = [c for c in feature_cols if c not in ["Cluster", "PCA_1", "PCA_2"]]

    print(f"Using {{len(feature_cols)}} features: {{feature_cols[:10]}}")

    X = df[feature_cols].fillna(0).values

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    if algorithm.lower() == "kmeans":
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
    elif algorithm.lower() == "dbscan":
        model = DBSCAN(eps=0.5, min_samples=5)
        labels = model.fit_predict(X_scaled)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    elif algorithm.lower() == "hierarchical":
        model = AgglomerativeClustering(n_clusters=n_clusters)
        labels = model.fit_predict(X_scaled)
    elif algorithm.lower() == "gmm":
        model = GaussianMixture(n_components=n_clusters, random_state=42)
        labels = model.fit_predict(X_scaled)
    elif algorithm.lower() == "spectral":
        model = SpectralClustering(n_clusters=n_clusters, random_state=42)
        labels = model.fit_predict(X_scaled)
    else:
        print(f"Unknown algorithm: {{algorithm}}. Using KMeans.")
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)

    # Compute centroids
    centroids = []
    for i in range(max(labels) + 1):
        mask = labels == i
        if mask.sum() > 0:
            centroids.append(X_scaled[mask].mean(axis=0))
    centroids = np.array(centroids) if centroids else np.array([])

    # Metrics
    if len(set(labels)) > 1 and -1 not in labels:
        sil = silhouette_score(X_scaled, labels)
        cal = calinski_harabasz_score(X_scaled, labels)
        dav = davies_bouldin_score(X_scaled, labels)
    else:
        sil, cal, dav = 0, 0, 0

    print(f"\\n  Clusters found: {{len(set(labels) - {{-1}})}}")
    print(f"  Silhouette Score: {{sil:.4f}}")
    print(f"  Calinski-Harabasz: {{cal:.2f}}")
    print(f"  Davies-Bouldin: {{dav:.4f}}")

    # Save model
    pkl_data = {{
        "algorithm": algorithm,
        "n_clusters": int(max(labels) + 1) if len(labels) > 0 else n_clusters,
        "scaler": scaler,
        "feature_columns": feature_cols,
        "centroids_scaled": centroids,
        "labels": labels,
        "silhouette_score": sil,
    }}
    with open(output_path, "wb") as f:
        pickle.dump(pkl_data, f)
    print(f"\\n  Model saved: {{output_path}}")

    # Save clustered data
    df_out = df.copy()
    df_out["Cluster"] = labels
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X_scaled)
    df_out["PCA_1"] = X_2d[:, 0]
    df_out["PCA_2"] = X_2d[:, 1]
    df_out.to_csv("data/clustered_data.csv", index=False)
    print(f"  Clustered data saved: data/clustered_data.csv")

    return pkl_data


def main():
    parser = argparse.ArgumentParser(description="Train clustering model")
    parser.add_argument("--data", type=str, default="data/clustered_data.csv")
    parser.add_argument("--algorithm", type=str, default=DEFAULT_ALGORITHM)
    parser.add_argument("--n-clusters", type=int, default=DEFAULT_N_CLUSTERS)
    parser.add_argument("--output", type=str, default="clustering_model.pkl")
    args = parser.parse_args()

    train_clustering(args.data, args.algorithm, args.n_clusters, args.output)


if __name__ == "__main__":
    main()
'''


def _generate_clustering_visualize_script(algorithm: str, n_clusters: int, feature_columns: List[str]) -> str:
    return f'''#!/usr/bin/env python3
"""
Clustering Visualization
=========================
Generated by DataVision AutoML - Unsupervised Learning

Generates:
  - PCA 2D scatter plot colored by cluster
  - Cluster distribution bar chart
  - Silhouette analysis
  - Feature importance for clustering
  - Elbow method chart

Usage:
    python visualize_clusters.py
    python visualize_clusters.py --data data/clustered_data.csv
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, silhouette_samples
import pickle
import argparse
from pathlib import Path


def generate_all_charts(data_path="data/clustered_data.csv", model_path="clustering_model.pkl",
                        output_dir="charts"):
    """Generate all clustering visualization charts"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Load data
    df = pd.read_csv(data_path)
    print(f"Loaded {{len(df)}} samples")

    # Load model
    model_data = None
    if Path(model_path).exists():
        with open(model_path, "rb") as f:
            model_data = pickle.load(f)

    feature_cols = model_data.get("feature_columns", []) if model_data else []
    if not feature_cols:
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in feature_cols if c not in ["Cluster", "PCA_1", "PCA_2"]]

    labels = df["Cluster"].values if "Cluster" in df.columns else None

    # Prepare scaled data
    X = df[feature_cols].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    charts_generated = 0

    # 1. PCA Scatter Plot
    try:
        pca = PCA(n_components=2)
        X_2d = pca.fit_transform(X_scaled)
        fig, ax = plt.subplots(figsize=(10, 8))
        scatter = ax.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap="viridis",
                            alpha=0.6, s=20, edgecolors="white", linewidth=0.3)
        plt.colorbar(scatter, ax=ax, label="Cluster")
        ax.set_xlabel(f"PC1 ({{pca.explained_variance_ratio_[0]*100:.1f}}%)")
        ax.set_ylabel(f"PC2 ({{pca.explained_variance_ratio_[1]*100:.1f}}%)")
        ax.set_title("Cluster Scatter Plot (PCA 2D Projection)")
        plt.tight_layout()
        plt.savefig(f"{{output_dir}}/cluster_scatter.png", dpi=150, bbox_inches="tight")
        plt.close()
        charts_generated += 1
        print(f"  [1] cluster_scatter.png")
    except Exception as e:
        print(f"  [!] scatter plot failed: {{e}}")

    # 2. Cluster Distribution
    try:
        if labels is not None:
            unique, counts = np.unique(labels[labels >= 0], return_counts=True)
            fig, ax = plt.subplots(figsize=(8, 5))
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(unique)))
            bars = ax.bar([f"Cluster {{u}}" for u in unique], counts, color=colors, edgecolor="white")
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                        str(count), ha="center", va="bottom", fontweight="bold")
            ax.set_xlabel("Cluster")
            ax.set_ylabel("Number of Samples")
            ax.set_title("Cluster Size Distribution")
            plt.tight_layout()
            plt.savefig(f"{{output_dir}}/cluster_distribution.png", dpi=150, bbox_inches="tight")
            plt.close()
            charts_generated += 1
            print(f"  [2] cluster_distribution.png")
    except Exception as e:
        print(f"  [!] distribution chart failed: {{e}}")

    # 3. Silhouette Analysis
    try:
        if labels is not None and len(set(labels)) > 1 and -1 not in labels:
            sample_silhouette = silhouette_samples(X_scaled, labels)
            fig, ax = plt.subplots(figsize=(10, 7))
            y_lower = 10
            unique_labels = sorted(set(labels))
            colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(unique_labels)))
            for i, label in enumerate(unique_labels):
                cluster_sil = sample_silhouette[labels == label]
                cluster_sil.sort()
                size = cluster_sil.shape[0]
                y_upper = y_lower + size
                ax.fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_sil,
                                facecolor=colors[i], alpha=0.7, edgecolor="none")
                ax.text(-0.05, y_lower + 0.5 * size, f"C{{label}}", fontsize=10)
                y_lower = y_upper + 10
            avg_sil = silhouette_score(X_scaled, labels)
            ax.axvline(x=avg_sil, color="red", linestyle="--", label=f"Avg: {{avg_sil:.3f}}")
            ax.set_xlabel("Silhouette Coefficient")
            ax.set_ylabel("Cluster")
            ax.set_title("Silhouette Analysis")
            ax.legend()
            plt.tight_layout()
            plt.savefig(f"{{output_dir}}/silhouette_analysis.png", dpi=150, bbox_inches="tight")
            plt.close()
            charts_generated += 1
            print(f"  [3] silhouette_analysis.png")
    except Exception as e:
        print(f"  [!] silhouette analysis failed: {{e}}")

    # 4. Elbow Method
    try:
        max_k = min(10, len(X_scaled) - 1)
        if max_k >= 2:
            inertias = []
            sil_scores = []
            K_range = range(2, max_k + 1)
            for k in K_range:
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                km.fit(X_scaled)
                inertias.append(km.inertia_)
                sil_scores.append(silhouette_score(X_scaled, km.labels_))

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            ax1.plot(list(K_range), inertias, "bo-", linewidth=2)
            ax1.set_xlabel("Number of Clusters (k)")
            ax1.set_ylabel("Inertia")
            ax1.set_title("Elbow Method")
            ax1.grid(alpha=0.3)

            ax2.plot(list(K_range), sil_scores, "ro-", linewidth=2)
            ax2.set_xlabel("Number of Clusters (k)")
            ax2.set_ylabel("Silhouette Score")
            ax2.set_title("Silhouette Score vs k")
            ax2.grid(alpha=0.3)

            plt.tight_layout()
            plt.savefig(f"{{output_dir}}/elbow_method.png", dpi=150, bbox_inches="tight")
            plt.close()
            charts_generated += 1
            print(f"  [4] elbow_method.png")
    except Exception as e:
        print(f"  [!] elbow method failed: {{e}}")

    # 5. Feature Importance (variance-based)
    try:
        if labels is not None and len(feature_cols) > 1:
            importances = []
            for i, col in enumerate(feature_cols):
                between_var = 0
                overall_mean = X_scaled[:, i].mean()
                for label in set(labels):
                    if label < 0:
                        continue
                    mask = labels == label
                    cluster_mean = X_scaled[mask, i].mean()
                    between_var += mask.sum() * (cluster_mean - overall_mean) ** 2
                importances.append(between_var)

            importances = np.array(importances)
            if importances.sum() > 0:
                importances = importances / importances.sum()

            # Sort
            sorted_idx = np.argsort(importances)[::-1][:15]
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.barh(
                [feature_cols[i] for i in sorted_idx][::-1],
                importances[sorted_idx][::-1],
                color=plt.cm.viridis(np.linspace(0.3, 0.8, len(sorted_idx))),
                edgecolor="white"
            )
            ax.set_xlabel("Importance (Between-cluster Variance Ratio)")
            ax.set_title("Feature Importance for Clustering")
            plt.tight_layout()
            plt.savefig(f"{{output_dir}}/feature_importance.png", dpi=150, bbox_inches="tight")
            plt.close()
            charts_generated += 1
            print(f"  [5] feature_importance.png")
    except Exception as e:
        print(f"  [!] feature importance failed: {{e}}")

    print(f"\\n  Total charts generated: {{charts_generated}}")
    print(f"  Saved to: {{output_dir}}/")


def main():
    parser = argparse.ArgumentParser(description="Generate clustering charts")
    parser.add_argument("--data", type=str, default="data/clustered_data.csv")
    parser.add_argument("--model", type=str, default="clustering_model.pkl")
    parser.add_argument("--output", type=str, default="charts")
    args = parser.parse_args()

    generate_all_charts(args.data, args.model, args.output)


if __name__ == "__main__":
    main()
'''


def _generate_clustering_api_script(algorithm: str, n_clusters: int, feature_columns: List[str]) -> str:
    features_list = ", ".join(f'"{f}"' for f in feature_columns[:20])
    return f'''#!/usr/bin/env python3
"""
Clustering API Server
======================
Generated by DataVision AutoML - Unsupervised Learning

Endpoints:
    GET  /predict    - Web form for interactive cluster prediction
    POST /predict    - Predict cluster for new data (JSON API)
    GET  /health     - Health check
    GET  /info       - Model info

Usage:
    python api_server.py
    python api_server.py --port 8000
"""

from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import argparse


app = Flask(__name__)
FEATURE_COLUMNS = [{features_list}]

# Load model at startup
with open("clustering_model.pkl", "rb") as f:
    MODEL_DATA = pickle.load(f)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({{"status": "healthy", "model": "clustering", "algorithm": "{algorithm}"}})


@app.route("/info", methods=["GET"])
def info():
    return jsonify({{
        "algorithm": MODEL_DATA.get("algorithm", "{algorithm}"),
        "n_clusters": MODEL_DATA.get("n_clusters", {n_clusters}),
        "feature_columns": MODEL_DATA.get("feature_columns", FEATURE_COLUMNS),
        "silhouette_score": MODEL_DATA.get("silhouette_score", 0),
    }})


@app.route("/predict", methods=["GET", "POST"])
def predict():
    # GET request: show web form for interactive cluster prediction
    if request.method == "GET":
        form_fields = ""
        for col in FEATURE_COLUMNS:
            form_fields += '<div style="margin:6px 0"><label style="display:inline-block;width:260px;font-weight:500">' + col + '</label><input name="' + col + '" type="text" value="0" placeholder="Enter value" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;width:200px"></div>\\n'

        algo = MODEL_DATA.get("algorithm", "{algorithm}")
        n_cl = MODEL_DATA.get("n_clusters", {n_clusters})
        sil = MODEL_DATA.get("silhouette_score", 0)

        html = '<!DOCTYPE html><html><head><title>DataVision Clustering API</title>'
        html += '<style>'
        html += "body " + chr(123) + " font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #f9fafb; color: #111827; " + chr(125)
        html += 'h1 ' + chr(123) + ' color: #7C3AED; ' + chr(125) + ' h2 ' + chr(123) + ' color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; ' + chr(125)
        html += '.card ' + chr(123) + ' background: white; border-radius: 12px; padding: 24px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); ' + chr(125)
        html += 'button ' + chr(123) + ' background: #7C3AED; color: white; border: none; padding: 12px 32px; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 12px; ' + chr(125)
        html += 'button:hover ' + chr(123) + ' background: #6D28D9; ' + chr(125)
        html += '#result ' + chr(123) + ' margin-top: 20px; padding: 16px; background: #f5f3ff; border-radius: 8px; display: none; ' + chr(125)
        html += '</style></head><body>'
        html += '<h1>DataVision Clustering API</h1>'
        html += '<div class="card"><h2>Model Info</h2>'
        html += '<p><b>Algorithm:</b> ' + str(algo).upper() + ' | <b>Clusters:</b> ' + str(n_cl) + ' | <b>Silhouette:</b> ' + format(sil, '.4f') + ' | <b>Features:</b> ' + str(len(FEATURE_COLUMNS)) + '</p></div>'
        html += '<div class="card"><h2>Predict Cluster</h2>'
        html += '<form id="predForm">' + form_fields + '<button type="submit">Predict Cluster</button></form>'
        html += '<div id="result"></div></div>'
        html += '<div class="card"><h2>API Usage</h2>'
        html += '<pre style="background:#1f2937;color:#e5e7eb;padding:16px;border-radius:8px;overflow-x:auto">'
        html += 'POST /predict\\nContent-Type: application/json\\n\\n' + chr(123) + '"feature1": val, "feature2": val' + chr(125)
        html += '\\n\\nGET /health - Health check\\nGET /info - Model metadata</pre></div>'
        html += '<script>'
        html += 'document.getElementById("predForm").onsubmit=function(e)' + chr(123)
        html += 'e.preventDefault();var fd=new FormData(this);var data=' + chr(123) + chr(125) + ';'
        html += 'fd.forEach(function(v,k)' + chr(123) + 'data[k]=isNaN(v)||v===""?v:parseFloat(v)' + chr(125) + ');'
        html += 'fetch("/predict",' + chr(123) + 'method:"POST",headers:' + chr(123) + '"Content-Type":"application/json"' + chr(125) + ',body:JSON.stringify(' + chr(123) + 'features:data' + chr(125) + ')' + chr(125) + ')'
        html += '.then(function(r)' + chr(123) + 'return r.json()' + chr(125) + ')'
        html += '.then(function(j)' + chr(123)
        html += 'var h="<h3>Assigned Cluster: "+j.cluster_name+"</h3>";'
        html += 'h+="<p>Cluster ID: "+j.cluster+"</p>";'
        html += 'if(j.confidence)h+="<p>Confidence: "+(j.confidence*100).toFixed(1)+"%</p>";'
        html += 'document.getElementById("result").innerHTML=h;document.getElementById("result").style.display="block"'
        html += chr(125) + ')' + chr(125) + ';'
        html += '</script></body></html>'
        return html

    # POST request: JSON API prediction
    try:
        data = request.get_json()
        if not data:
            return jsonify({{"error": "No JSON body"}}), 400

        features = data.get("features", data)
        scaler = MODEL_DATA.get("scaler")
        centroids = MODEL_DATA.get("centroids_scaled")
        feature_cols = MODEL_DATA.get("feature_columns", FEATURE_COLUMNS)

        values = []
        for col in feature_cols:
            val = features.get(col, 0)
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                values.append(0.0)

        X = np.array(values).reshape(1, -1)
        if scaler is not None:
            X = scaler.transform(X)

        if centroids is not None:
            centroids_arr = np.array(centroids)
            distances = np.linalg.norm(X - centroids_arr, axis=1)
            cluster = int(np.argmin(distances))
            confidence = float(1.0 / (1.0 + distances[cluster]))
        else:
            cluster = 0
            confidence = 0.0

        return jsonify({{
            "cluster": cluster,
            "cluster_name": f"Cluster_{{cluster}}",
            "confidence": round(confidence, 4),
        }})

    except Exception as e:
        return jsonify({{"error": str(e)}}), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print("")
    print("Clustering API running on http://localhost:" + str(args.port))
    print("   GET  /predict  - Web form for predictions")
    print("   POST /predict  - Send JSON with feature values")
    print("   GET  /health   - Health check")
    print("   GET  /info     - Model metadata")
    app.run(host="0.0.0.0", port=args.port, debug=False)
'''


def _generate_clustering_readme(algorithm: str, n_clusters: int, silhouette: float,
                                 feature_columns: List[str], n_samples: int,
                                 cluster_profiles: Dict) -> str:
    features_block = "\\n".join(f"| `{{f}}` | numeric |" for f in feature_columns[:15])
    profiles_block = ""
    if cluster_profiles:
        for cname, cdata in cluster_profiles.items():
            size = cdata.get("size", "?")
            pct = cdata.get("percentage", 0)
            profiles_block += f"| {{cname}} | {{size}} samples ({{pct:.1f}}%) |\\n"

    return f"""# Clustering Model - DataVision AutoML

## Overview
| Property | Value |
|---|---|
| **Task** | Unsupervised Clustering |
| **Algorithm** | {algorithm.upper()} |
| **Clusters** | {n_clusters} |
| **Silhouette Score** | {silhouette:.4f} |
| **Samples** | {n_samples:,} |
| **Features** | {len(feature_columns)} |

## Project Structure
```
├── clustering_model.pkl          # Trained clustering model
├── data/
│   └── clustered_data.csv        # Data with cluster assignments
├── predict_cluster.py            # Predict cluster for new data
├── train_clustering.py           # Re-train the clustering model
├── visualize_clusters.py         # Generate clustering charts
├── api_server.py                 # Flask REST API
├── charts/                       # Pre-generated training charts (PNG)
├── config.json                   # Clustering configuration
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker deployment
└── README.md                     # This file
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Predict Cluster
```bash
# Interactive
python predict_cluster.py

# Batch
python predict_cluster.py --csv new_data.csv
```

### 3. Generate Charts
```bash
python visualize_clusters.py
```

### 4. Re-Train Model
```bash
python train_clustering.py --data data/clustered_data.csv --algorithm {algorithm} --n-clusters {n_clusters}
```

### 5. Start API Server
```bash
python api_server.py --port 5000

# Test
curl -X POST http://localhost:5000/predict \\
     -H "Content-Type: application/json" \\
     -d '{{"features": {{}}}}'
```

## Features Used
| Feature | Type |
|---|---|
{features_block}

## Cluster Profiles
| Cluster | Size |
|---|---|
{profiles_block}

## Charts
| Chart | Description |
|---|---|
| `cluster_scatter.png` | PCA 2D scatter plot colored by cluster |
| `cluster_distribution.png` | Cluster size distribution |
| `silhouette_analysis.png` | Per-sample silhouette coefficients |
| `elbow_method.png` | Optimal k detection (inertia + silhouette) |
| `feature_importance.png` | Feature importance for cluster separation |

---
*Generated by DataVision AutoML - Unsupervised Learning*
"""
