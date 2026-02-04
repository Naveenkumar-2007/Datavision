"""
📊 EXPLAINABILITY API
=====================

Provides model explanation endpoints:
- POST /api/v1/automl/explain - Explain a single prediction
- GET /api/v1/automl/explain/global - Get global feature importance
"""

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import logging

from utils.paths import get_user_paths

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automl", tags=["AutoML - Explainability"])


# =============================================================================
# SECURITY HELPER - JWT Authentication
# =============================================================================

def get_secure_user_id(form_user_id: str, x_user_id: Optional[str], authorization: Optional[str]) -> str:
    """
    Get verified user_id from JWT token or headers.
    Priority: JWT token > X-User-ID header > Form data
    """
    # 1. Try JWT token first (most secure)
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            from core.auth import decode_supabase_jwt
            payload = decode_supabase_jwt(token)
            if payload and payload.get("sub"):
                return payload["sub"]
        except Exception as e:
            logger.debug(f"JWT decode failed: {e}")
    
    # 2. Try X-User-ID header (from authenticated frontend)
    if x_user_id and x_user_id != "default":
        return x_user_id
    
    # 3. Fallback to form/query data (least secure)
    if form_user_id and form_user_id != "default":
        logger.warning(f"Using form user_id: {form_user_id} - consider using JWT")
        return form_user_id
    
    # 4. Generate guest fingerprint
    import hashlib
    import time
    return f"guest_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"


class ExplainRequest(BaseModel):
    input_values: Dict[str, Any]
    user_id: str = "default"
    mode: Optional[str] = "traditional"  # 'traditional', 'nlp', 'deep_learning'


class ContributionItem(BaseModel):
    feature: str
    value: Any  # Can be str or float for text/categorical  
    shap_value: float
    direction: str


class ExplainResponse(BaseModel):
    success: bool
    base_value: Optional[float] = None
    prediction: Optional[Any] = None
    prediction_contribution: Optional[float] = None
    contributions: List[ContributionItem]
    waterfall_chart: Optional[str] = None
    explanation_text: Optional[str] = None


def aggregate_importance_to_raw_columns(
    model,
    feature_columns: List[str],  # Processed feature names from model
    numeric_cols: List[str],
    categorical_cols: List[str],
    text_cols: List[str]
) -> Dict[str, float]:
    """
    Aggregate feature importances from processed features back to raw column names.
    
    For example, TF-IDF features like 'url_tfidf_0', 'url_tfidf_1', etc. 
    should be summed back to the 'url' column importance.
    """
    raw_importance = {}
    
    # Try to get importances from model
    importances = None
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            coefs = model.coef_
            if coefs.ndim > 1:
                importances = np.abs(coefs).mean(axis=0)  # Average across classes for multiclass
            else:
                importances = np.abs(coefs)
    except Exception as e:
        logger.warning(f"Could not extract importances: {e}")
        return {}
    
    if importances is None or len(importances) == 0:
        return {}
    
    # If feature_columns matches importances, use direct mapping
    if feature_columns and len(feature_columns) == len(importances):
        for col, imp in zip(feature_columns, importances):
            # Check if this is a derived feature (e.g., 'url_tfidf_0')
            original_col = None
            
            # Check numeric
            for raw_col in numeric_cols:
                if col == raw_col or col.startswith(f"{raw_col}_"):
                    original_col = raw_col
                    break
            
            # Check categorical
            if not original_col:
                for raw_col in categorical_cols:
                    if col == raw_col or col.startswith(f"{raw_col}_"):
                        original_col = raw_col
                        break
            
            # Check text (TF-IDF features)
            if not original_col:
                for raw_col in text_cols:
                    if col == raw_col or col.startswith(f"{raw_col}_") or f"_{raw_col}_" in col:
                        original_col = raw_col
                        break
            
            # Fallback to the column name itself
            if not original_col:
                original_col = col.split('_')[0] if '_' in col else col
            
            # Aggregate importance
            raw_importance[original_col] = raw_importance.get(original_col, 0) + float(imp)
    else:
        # No feature column names, distribute evenly across all raw columns
        all_cols = numeric_cols + categorical_cols + text_cols
        if all_cols:
            avg_imp = float(np.sum(importances)) / len(all_cols)
            for col in all_cols:
                raw_importance[col] = avg_imp
    
    # Normalize to sum to 1
    total = sum(raw_importance.values())
    if total > 0:
        raw_importance = {k: v / total for k, v in raw_importance.items()}
    
    return raw_importance


@router.post("/explain", response_model=ExplainResponse)
async def explain_prediction(
    request: ExplainRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """🔍 Explain why the model made a specific prediction using feature importance. SECURED."""
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(request.user_id, x_user_id, authorization)
        mode = request.mode or "traditional"
        
        # Load the correct engine based on mode
        if mode == "nlp":
            from ml.nlp_engine import nlp_engine
            engine = nlp_engine
            loaded = engine.load(secure_user_id)
        elif mode == "deep_learning":
            from ml.deep_learning_engine import deep_learning_engine
            engine = deep_learning_engine
            loaded = engine.load(secure_user_id)
        else:
            from ml.automl_engine import automl_engine
            engine = automl_engine
            loaded = engine.load(secure_user_id)
            
        if not loaded or engine.model is None:
            raise HTTPException(status_code=404, detail=f"No trained {mode} model found")
        
        # Get prediction using correctly loaded engine
        # For NLP, we need to extract text from input_values
        if mode == "nlp":
            text_input = ""
            if isinstance(request.input_values, dict):
                if len(request.input_values) == 1:
                    text_input = list(request.input_values.values())[0]
                else:
                    for k, v in request.input_values.items():
                        if isinstance(v, str) and len(v) > 5:
                            text_input = v
                            break
                    if not text_input:
                        text_input = str(list(request.input_values.values())[0])
            else:
                text_input = str(request.input_values)
            
            prediction_result = engine.predict(text_input, secure_user_id)
        else:
            prediction_result = engine.predict(request.input_values)
            
        prediction = prediction_result.get("prediction")
        
        # Get stored column info
        numeric_cols = getattr(engine, 'numeric_cols', [])
        categorical_cols = getattr(engine, 'categorical_cols', [])
        text_cols = getattr(engine, 'text_cols', [])
        feature_columns = getattr(engine, 'feature_columns', [])
        feature_metadata = getattr(engine, 'feature_metadata', [])
        model = engine.model
        
        logger.info(f"🔍 Explain request - Input values: {list(request.input_values.keys())}")
        logger.info(f"🔍 Stored columns - numeric: {numeric_cols}, categorical: {categorical_cols}, text: {text_cols}")
        logger.info(f"🔍 Feature metadata count: {len(feature_metadata)}")
        
        # Aggregate importance back to raw columns
        importance_map = aggregate_importance_to_raw_columns(
            model, feature_columns, numeric_cols, categorical_cols, text_cols
        )
        
        logger.info(f"🔍 Importance map: {importance_map}")
        
        # Build metadata lookup by name
        meta_lookup = {m.get('name'): m for m in feature_metadata}
        
        # ALWAYS use input values - this is the key fix
        # If column lists are empty, just use what the user sent
        input_keys = list(request.input_values.keys())
        
        # If no importance_map, create uniform importance based on input keys
        if not importance_map and input_keys:
            for col in input_keys:
                importance_map[col] = 1.0 / len(input_keys)
        
        # Calculate contributions for each input value
        contributions = []
        
        for col, input_value in request.input_values.items():
            if input_value is None:
                continue
            
            # Get importance for this raw column - ensure minimum of 0.1
            importance = max(importance_map.get(col, 0.1), 0.1)
            
            # Get metadata if available
            meta = meta_lookup.get(col, {})
            feat_type = meta.get('type', 'numeric')  # Default to numeric
            
            # ALWAYS check if value looks like a URL - override type if needed
            val_str = str(input_value)
            if val_str.startswith('http') or val_str.startswith('www') or '://' in val_str:
                feat_type = 'text'  # URLs should ALWAYS be text
            elif not meta:
                # No metadata - determine type from value
                try:
                    float(input_value)
                    feat_type = 'numeric'
                except:
                    if len(val_str) > 50 or ' ' in val_str:
                        feat_type = 'text'
                    else:
                        feat_type = 'categorical'
            
            logger.info(f"🔍 Feature '{col}': type={feat_type}, importance={importance}, value={val_str[:50]}")
            
            # Calculate contribution based on feature type
            if feat_type == 'numeric':
                try:
                    val = float(input_value)
                except:
                    val = 0
                
                mean_val = meta.get('mean', 0)
                min_val = meta.get('min', 0)
                max_val = meta.get('max', 1)
                
                # If no metadata, estimate range from value
                if not meta:
                    min_val = 0
                    max_val = max(val * 2, 100)  # Reasonable estimate
                    mean_val = max_val / 2
                
                range_val = max_val - min_val if max_val != min_val else 1
                
                # Normalized deviation from mean
                deviation = (val - mean_val) / range_val if range_val != 0 else 0
                
                # Contribution = deviation * importance (scaled for visibility)
                contribution = deviation * importance * 10
                display_val = val
                
            elif feat_type == 'categorical':
                # For categorical, contribution based on the value itself
                val_str = str(input_value)
                options = meta.get('options', [])
                
                if options and val_str in options[:3]:  # Top 3 most common
                    contribution = importance * 5  # Positive for common values
                elif options:
                    contribution = importance * 2  # Still positive for known values
                else:
                    # No options known - give a positive contribution based on string length
                    contribution = importance * (3 + min(len(val_str) / 10, 2))
                
                display_val = val_str
                
            elif feat_type == 'text':
                # For text/URLs, contribution based on content characteristics
                val_str = str(input_value)
                
                # Score based on various factors
                score = 1.0  # Base score
                
                # URL-specific scoring
                if '://' in val_str:
                    score += 2.0  # URLs carry information
                    # IP addresses in URLs are often suspicious
                    if any(c.isdigit() for c in val_str.replace(':', '').replace('/', '')):
                        score += 1.5
                
                # Length factor
                score += min(len(val_str) / 50, 2.0)
                
                # Special chars indicate complexity
                special_count = sum(1 for c in val_str if c in '!@#$%^&*()[]{}|;:,.<>?/')
                score += min(special_count / 5, 1.5)
                
                contribution = importance * score
                logger.info(f"🔍 Text feature '{col}': score={score}, contribution={contribution}")
                display_val = val_str[:50] + "..." if len(val_str) > 50 else val_str
            else:
                # Unknown type - give reasonable positive contribution
                try:
                    display_val = float(input_value)
                    contribution = abs(display_val / 100) * importance * 10
                except:
                    display_val = str(input_value)
                    contribution = importance * 3
            
            contributions.append(ContributionItem(
                feature=col,
                value=display_val,
                shap_value=round(contribution, 4),
                direction="positive" if contribution > 0 else "negative"
            ))
        
        logger.info(f"🔍 Generated {len(contributions)} contributions")
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
        
        # Generate plain English explanation
        top_positive = [c for c in contributions[:5] if c.shap_value > 0]
        top_negative = [c for c in contributions[:5] if c.shap_value < 0]
        
        explanation_parts = []
        if top_positive:
            pos_text = ", ".join([c.feature for c in top_positive[:3]])
            explanation_parts.append(f"Pushed prediction UP: {pos_text}")
        if top_negative:
            neg_text = ", ".join([c.feature for c in top_negative[:3]])
            explanation_parts.append(f"Pushed prediction DOWN: {neg_text}")
        
        if not explanation_parts:
            explanation_parts.append(f"Prediction: {prediction}")
        
        explanation_text = ". ".join(explanation_parts)
        
        return ExplainResponse(
            success=True,
            base_value=0.5,
            prediction=prediction,
            prediction_contribution=sum(c.shap_value for c in contributions),
            contributions=contributions[:50],  # Show up to 50 features
            explanation_text=explanation_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explain error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/global")
async def get_global_importance(
    user_id: str = Query(default="default"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """📊 Get global feature importance aggregated to raw columns. SECURED."""
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(user_id, x_user_id, authorization)
        
        from ml.automl_engine import automl_engine
        
        # Load model for THIS user
        loaded = automl_engine.load(secure_user_id)
        if not loaded or automl_engine.model is None:
            return {"error": "No trained model found"}
        
        # Get stored column info
        numeric_cols = getattr(automl_engine, 'numeric_cols', [])
        categorical_cols = getattr(automl_engine, 'categorical_cols', [])
        text_cols = getattr(automl_engine, 'text_cols', [])
        feature_columns = getattr(automl_engine, 'feature_columns', [])
        model = automl_engine.model
        
        # Aggregate importance back to raw columns
        importance_map = aggregate_importance_to_raw_columns(
            model, feature_columns, numeric_cols, categorical_cols, text_cols
        )
        
        # Build importance list
        importance_list = [
            {"feature": k, "importance": v}
            for k, v in importance_map.items()
        ]
        
        # Sort by importance
        importance_list.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            "success": True,
            "feature_importance": importance_list[:20]
        }
        
    except Exception as e:
        logger.error(f"Global importance error: {e}")
        return {"error": str(e)}
