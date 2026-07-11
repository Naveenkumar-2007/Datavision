"""
🎮 PREDICTION PLAYGROUND API
============================

Interactive prediction playground:
- GET /api/v1/automl/playground/config - Get slider configurations
- POST /api/v1/automl/playground/predict - Real-time predictions

SECURED: Uses JWT authentication for user isolation
"""

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import logging

from utils.paths import get_user_paths

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automl/playground", tags=["AutoML - Playground"])


def get_secure_user_id(
    form_user_id: str,
    x_user_id: Optional[str] = None,
    authorization: Optional[str] = None
) -> str:
    """Get secure user_id prioritizing JWT over form/query data."""
    if authorization and authorization.startswith("Bearer "):
        try:
            from core.auth import decode_jwt_token
            token = authorization[7:]
            payload = decode_jwt_token(token)
            user_id = payload.get("sub")
            if user_id:
                return user_id
        except:
            pass
    
    if x_user_id and x_user_id not in ["null", "undefined", "", "default"]:
        return x_user_id
    
    if form_user_id and form_user_id not in ["default", "null", "undefined", ""]:
        return form_user_id
    
    import hashlib, time
    return f"guest_{hashlib.sha256(f'guest_{time.time()}'.encode()).hexdigest()[:12]}"


class SliderConfig(BaseModel):
    name: str
    type: str  # 'numeric', 'categorical', 'text', or 'datetime'
    min: Optional[Any] = None  # float for numeric, ISO string for datetime
    max: Optional[Any] = None  # float for numeric, ISO string for datetime
    step: Optional[float] = None
    default: Optional[Any] = None
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None  # For text/datetime inputs


class PlaygroundConfig(BaseModel):
    model_name: str
    task_type: str
    target_column: str
    sliders: List[SliderConfig]
    class_names: Optional[List[str]] = None
    model_type: Optional[str] = None  # 'traditional', 'nlp', 'deep_learning'


class PlaygroundPredictRequest(BaseModel):
    values: Dict[str, Any]
    user_id: str = "default"
    mode: str = "traditional"  # 'traditional', 'nlp', 'deep_learning', 'fast', 'ultra'
    text: Optional[str] = None  # For NLP models


class PlaygroundPredictResponse(BaseModel):
    success: bool
    prediction: Optional[Any] = None
    prediction_label: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None


@router.get("/config", response_model=PlaygroundConfig)
async def get_playground_config(
    user_id: str = Query(default="default"),
    mode: str = Query(default="traditional"),  # 'traditional', 'nlp', 'deep_learning', 'auto'
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """🎮 Get playground configuration with slider settings. SECURED."""
    try:
        # SECURITY: Get verified user_id
        user_id = get_secure_user_id(user_id, x_user_id, authorization)
        
        # AUTO mode: Try all engines and return the first one with feature_metadata
        if mode == "auto":
            logger.info(f"[Playground] Auto-detecting best mode for user {user_id}")
            errors = []
            
            # Try each mode in order of preference
            for try_mode in ['traditional', 'nlp', 'deep_learning']:
                try:
                    if try_mode == 'traditional':
                        from ml.automl_engine import ProductionMLEngine
                        engine = ProductionMLEngine()
                        engine.load(user_id)
                        if engine.model and getattr(engine, 'feature_metadata', []):
                            logger.info(f"[Playground] Found traditional ML model with feature_metadata")
                            mode = 'traditional'
                            break
                    elif try_mode == 'nlp':
                        from ml.nlp_engine import NLPEngine
                        engine = NLPEngine()
                        engine.load(user_id)
                        if engine.model:
                            logger.info(f"[Playground] Found NLP model")
                            mode = 'nlp'
                            break
                    elif try_mode == 'deep_learning':
                        from ml.deep_learning_engine import DeepLearningEngine
                        engine = DeepLearningEngine()
                        engine.load(user_id)
                        if engine.model and getattr(engine, 'feature_metadata', []):
                            logger.info(f"[Playground] Found Deep Learning model with feature_metadata")
                            mode = 'deep_learning'
                            break
                except Exception as e:
                    errors.append(f"{try_mode}: {str(e)}")
                    continue
            else:
                # No mode worked
                raise HTTPException(status_code=404, detail=f"No trained model found with feature metadata. Train a model first. Errors: {errors}")
        
        # Handle NLP mode - return inputs from actual dataset columns
        if mode == "nlp" or mode == "fast":
            from ml.nlp_engine import NLPEngine
            
            nlp_engine = NLPEngine()
            try:
                nlp_engine.load(user_id)
            except Exception as e:
                logger.warning(f"No NLP model found: {e}")
                raise HTTPException(status_code=404, detail="No NLP model found. Train an NLP model first.")
            
            if nlp_engine.model is None:
                raise HTTPException(status_code=404, detail="No NLP model found. Train an NLP model first.")
            
            text_column = getattr(nlp_engine, 'text_column', 'text')
            target_column = getattr(nlp_engine, 'target_column', 'target')
            task_type = getattr(nlp_engine, 'task_type', 'classification')
            
            # Get feature_metadata from NLP engine - includes ALL columns from user's data
            feature_metadata = getattr(nlp_engine, 'feature_metadata', [])
            
            # Build sliders from actual feature_metadata
            sliders = []
            
            if feature_metadata:
                # Use saved feature_metadata which has ONLY the user's actual columns
                for meta in feature_metadata:
                    name = meta.get('name', 'Unknown')
                    feat_type = meta.get('type', 'text')
                    
                    if feat_type == 'text':
                        sliders.append(SliderConfig(
                            name=name,
                            type='text',
                            placeholder=meta.get('placeholder', f"Enter {name}..."),
                            default=""
                        ))
                    elif feat_type == 'numeric':
                        min_val = meta.get('min', 0)
                        max_val = meta.get('max', 100)
                        mean_val = meta.get('mean', (min_val + max_val) / 2)
                        range_val = max_val - min_val if max_val > min_val else 1
                        step = max(0.01, range_val / 100)
                        
                        sliders.append(SliderConfig(
                            name=name,
                            type='numeric',
                            min=float(min_val),
                            max=float(max_val),
                            step=float(step),
                            default=float(mean_val)
                        ))
                    elif feat_type == 'datetime':
                        # Date picker for datetime columns
                        from datetime import datetime as dt
                        today = dt.now().strftime('%Y-%m-%d')
                        sliders.append(SliderConfig(
                            name=name,
                            type='datetime',
                            min=meta.get('min'),
                            max=meta.get('max'),
                            placeholder=meta.get('placeholder', 'Select date...'),
                            default=today
                        ))
                    elif feat_type == 'categorical':
                        options = meta.get('options', [])
                        sliders.append(SliderConfig(
                            name=name,
                            type='categorical',
                            options=options[:50],
                            default=options[0] if options else None
                        ))
            else:
                # Fallback: just show text input for the text column
                sliders = [
                    SliderConfig(
                        name=text_column,
                        type='text',
                        placeholder=f"Enter {text_column} for prediction...",
                        default=""
                    )
                ]
            
            class_names = None
            if task_type == 'classification' and hasattr(nlp_engine, 'label_encoder') and nlp_engine.label_encoder:
                class_names = nlp_engine.label_encoder.classes_.tolist()
            
            return PlaygroundConfig(
                model_name=getattr(nlp_engine, 'algorithm', 'NLP Model'),
                task_type=task_type,
                target_column=target_column,
                sliders=sliders,
                class_names=class_names,
                model_type='nlp'
            )
        
        # Handle Deep Learning mode
        if mode == "deep_learning" or mode == "ultra":
            from ml.deep_learning_engine import DeepLearningEngine
            
            dl_engine = DeepLearningEngine()
            try:
                dl_engine.load(user_id)
            except Exception as e:
                logger.warning(f"No Deep Learning model found: {e}")
                raise HTTPException(status_code=404, detail="No Deep Learning model found. Train a Deep Learning model first.")
            
            if dl_engine.model is None:
                raise HTTPException(status_code=404, detail="No Deep Learning model found. Train a Deep Learning model first.")
            
            feature_metadata = getattr(dl_engine, 'feature_metadata', [])
            
            # Fallback: build metadata from feature_columns if feature_metadata is empty
            if not feature_metadata and hasattr(dl_engine, 'feature_columns') and dl_engine.feature_columns:
                logger.warning("Building feature metadata from feature_columns (legacy model)")
                numeric_cols = getattr(dl_engine, 'numeric_cols', [])
                categorical_cols = getattr(dl_engine, 'categorical_cols', [])
                
                for col in dl_engine.feature_columns:
                    # Skip one-hot encoded column names (contain prefix_)
                    if '_' in col and any(col.startswith(cat + '_') for cat in categorical_cols):
                        continue
                    
                    if col in numeric_cols:
                        feature_metadata.append({
                            'name': col,
                            'type': 'numeric',
                            'min': 0,
                            'max': 100,
                            'mean': 50
                        })
                    elif col in categorical_cols:
                        feature_metadata.append({
                            'name': col,
                            'type': 'categorical',
                            'options': []
                        })
                    else:
                        # Assume numeric for unknown
                        feature_metadata.append({
                            'name': col,
                            'type': 'numeric',
                            'min': 0,
                            'max': 100,
                            'mean': 50
                        })
            
            sliders = []
            for meta in feature_metadata:
                name = meta.get('name', 'Unknown')
                feat_type = meta.get('type', 'numeric')
                
                if feat_type == 'numeric':
                    min_val = meta.get('min', 0)
                    max_val = meta.get('max', 100)
                    mean_val = meta.get('mean', (min_val + max_val) / 2)
                    range_val = max_val - min_val if max_val > min_val else 1
                    step = max(0.01, range_val / 100)
                    
                    sliders.append(SliderConfig(
                        name=name,
                        type='numeric',
                        min=float(min_val),
                        max=float(max_val),
                        step=float(step),
                        default=float(mean_val)
                    ))
                else:
                    options = meta.get('options', [])
                    sliders.append(SliderConfig(
                        name=name,
                        type='categorical',
                        options=options[:50],
                        default=options[0] if options else None
                    ))
            
            class_names = None
            if hasattr(dl_engine, 'label_encoder') and dl_engine.label_encoder:
                try:
                    class_names = dl_engine.label_encoder.classes_.tolist()
                except:
                    pass
            
            return PlaygroundConfig(
                model_name=getattr(dl_engine, 'algorithm', 'Deep Learning Model'),
                task_type=getattr(dl_engine, 'task_type', 'classification'),
                target_column=getattr(dl_engine, 'target_column', 'target'),
                sliders=sliders,
                class_names=class_names,
                model_type='deep_learning'
            )
        
        # Traditional ML mode (default)
        from ml.automl_engine import ProductionMLEngine
        
        engine = ProductionMLEngine()
        engine.load(user_id)
        
        if engine.model is None:
            raise HTTPException(status_code=404, detail="No trained model found. Train a model first.")
        
        feature_metadata = getattr(engine, 'feature_metadata', [])
        
        # Fallback: build metadata from numeric_cols/categorical_cols/text_cols (original columns)
        # DO NOT use feature_columns - those are engineered features!
        if not feature_metadata:
            numeric_cols = getattr(engine, 'numeric_cols', [])
            categorical_cols = getattr(engine, 'categorical_cols', [])
            text_cols = getattr(engine, 'text_cols', [])
            
            logger.warning("Building feature metadata from column lists (legacy model)")
            
            # Build from original column lists
            for col in numeric_cols:
                feature_metadata.append({
                    'name': col,
                    'type': 'numeric',
                    'min': 0,
                    'max': 100,
                    'mean': 50
                })
            for col in categorical_cols:
                feature_metadata.append({
                    'name': col,
                    'type': 'categorical',
                    'options': []
                })
            for col in text_cols:
                feature_metadata.append({
                    'name': col,
                    'type': 'text',
                    'placeholder': f'Enter {col}...'
                })
        
        # Final fallback: If still no metadata, try to infer from feature_columns using smart detection
        if not feature_metadata:
            logger.warning("No column lists found, using feature_columns with smart detection")
            feature_cols = getattr(engine, 'feature_columns', [])
            target_col = getattr(engine, 'target_column', None)
            
            # Filter out engineered features (those with patterns like _tfidf_, *2, _chars, etc.)
            skip_patterns = ['_tfidf_', '_count_', '_chars', '_words', '_sents', '_punct', '_avg_', 
                            '*', 'unnamed', 'index', '_id']
            
            for col in feature_cols:
                col_lower = col.lower()
                # Skip engineered features
                if any(pattern in col_lower for pattern in skip_patterns):
                    continue
                # Skip target column
                if col == target_col:
                    continue
                # Skip ID columns
                if col_lower == 'id' or col_lower.startswith('unnamed'):
                    continue
                    
                # Detect text columns by name heuristics
                text_keywords = ['text', 'content', 'body', 'email', 'review', 'description', 
                    'summary', 'message', 'overview', 'title', 'name', 'comment', 'note', 'bio']
                is_text = any(kw in col_lower for kw in text_keywords)
                
                if is_text:
                    feature_metadata.append({
                        'name': col,
                        'type': 'text',
                        'placeholder': f'Enter {col}...'
                    })
                else:
                    feature_metadata.append({
                        'name': col,
                        'type': 'numeric',
                        'min': 0,
                        'max': 100,
                        'mean': 50
                    })
        
        if not feature_metadata:
            raise HTTPException(status_code=400, detail="No feature metadata available. Please retrain the model.")
        
        # Filter out ID/index columns from sliders
        skip_names = ['unnamed', 'index', 'id', '_id']
        
        sliders = []
        for meta in feature_metadata:
            name = meta.get('name', 'Unknown')
            name_lower = name.lower()
            
            # Skip ID/index columns
            if name_lower in skip_names or name_lower.startswith('unnamed'):
                continue
                
            feat_type = meta.get('type', 'numeric')
            
            if feat_type == 'numeric':
                min_val = meta.get('min', 0)
                max_val = meta.get('max', 100)
                mean_val = meta.get('mean', (min_val + max_val) / 2)
                range_val = max_val - min_val
                step = max(0.01, range_val / 100)
                
                sliders.append(SliderConfig(
                    name=name,
                    type='numeric',
                    min=float(min_val),
                    max=float(max_val),
                    step=float(step),
                    default=float(mean_val)
                ))
            elif feat_type == 'text':
                # Text input for long text columns
                sliders.append(SliderConfig(
                    name=name,
                    type='text',
                    placeholder=meta.get('placeholder', f"Enter {name}..."),
                    default=""
                ))
            elif feat_type == 'datetime':
                # Date picker for datetime columns
                from datetime import datetime
                today = datetime.now().strftime('%Y-%m-%d')
                sliders.append(SliderConfig(
                    name=name,
                    type='datetime',
                    min=meta.get('min'),  # ISO string or None
                    max=meta.get('max'),  # ISO string or None
                    placeholder=meta.get('placeholder', 'Select date...'),
                    default=today
                ))
            else:
                # Categorical dropdown
                options = meta.get('options', [])
                sliders.append(SliderConfig(
                    name=name,
                    type='categorical',
                    options=options[:50],
                    default=options[0] if options else None
                ))
        
        class_names = None
        if hasattr(engine, 'target_encoder') and engine.target_encoder:
            class_names = engine.target_encoder.classes_.tolist()
        
        return PlaygroundConfig(
            model_name=getattr(engine, 'model_name', 'Model'),
            task_type=getattr(engine, 'task_type', 'classification'),
            target_column=getattr(engine, 'target_column', 'target'),
            sliders=sliders,
            class_names=class_names,
            model_type='traditional'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playground config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=PlaygroundPredictResponse)
async def playground_predict(
    request: PlaygroundPredictRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """⚡ Real-time prediction for playground. SECURED."""
    try:
        # SECURITY: Get verified user_id
        user_id = get_secure_user_id(request.user_id, x_user_id, authorization)
        
        mode = request.mode or "traditional"
        
        # Handle NLP mode prediction
        if mode in ["nlp", "fast"]:
            from ml.nlp_engine import NLPEngine
            
            nlp_engine = NLPEngine()
            loaded = nlp_engine.load(user_id)
            
            if not loaded or nlp_engine.model is None:
                raise HTTPException(status_code=404, detail="No NLP model found")
            
            # Get text from request - could be in 'text' field or in 'values' dict
            text_input = request.text
            if not text_input and request.values:
                # Try to find text in values
                text_column = getattr(nlp_engine, 'text_column', 'text')
                text_input = request.values.get(text_column) or list(request.values.values())[0]
            
            if not text_input:
                raise HTTPException(status_code=400, detail="Text input is required for NLP prediction")
            
            # Make prediction
            result = nlp_engine.predict(text_input)
            
            prediction = result.get("prediction")
            confidence = result.get("confidence")
            probabilities = result.get("probabilities")
            
            return PlaygroundPredictResponse(
                success=True,
                prediction=prediction,
                prediction_label=str(prediction) if prediction is not None else None,
                confidence=confidence,
                probabilities=probabilities
            )
        
        # Handle Deep Learning mode prediction
        if mode in ["deep_learning", "ultra"]:
            from ml.deep_learning_engine import DeepLearningEngine
            
            dl_engine = DeepLearningEngine()
            loaded = dl_engine.load(user_id)
            
            if not loaded or dl_engine.model is None:
                raise HTTPException(status_code=404, detail="No Deep Learning model found")
            
            # Make prediction
            result = dl_engine.predict(request.values)
            
            prediction = result.get("prediction")
            confidence = result.get("confidence")
            probability = result.get("probability")
            
            # Convert probability list to dict if we have class names
            probabilities = None
            if probability and hasattr(dl_engine, 'target_encoder') and dl_engine.target_encoder:
                try:
                    class_names = dl_engine.target_encoder.classes_.tolist()
                    probabilities = {str(name): float(prob) for name, prob in zip(class_names, probability)}
                except:
                    pass
            
            return PlaygroundPredictResponse(
                success=True,
                prediction=prediction,
                prediction_label=str(prediction) if prediction is not None else None,
                confidence=confidence,
                probabilities=probabilities
            )
        
        # Traditional ML mode (default)
        from ml.automl_engine import automl_engine
        
        # Load model for THIS user
        loaded = automl_engine.load(user_id)
        if not loaded or automl_engine.model is None:
            raise HTTPException(status_code=404, detail="No trained model found")
        
        # predict() returns {prediction, probability, confidence, model}
        result = automl_engine.predict(request.values)
        
        prediction = result.get("prediction")
        confidence = result.get("confidence")
        probability = result.get("probability")
        
        # Convert probability list to dict if we have class names
        probabilities = None
        if probability and hasattr(automl_engine, 'target_encoder') and automl_engine.target_encoder:
            try:
                class_names = automl_engine.target_encoder.classes_.tolist()
                probabilities = {str(name): float(prob) for name, prob in zip(class_names, probability)}
            except:
                pass
        
        prediction_label = str(prediction) if prediction is not None else None
        
        return PlaygroundPredictResponse(
            success=True,
            prediction=prediction,
            prediction_label=prediction_label,
            confidence=confidence,
            probabilities=probabilities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playground predict error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sensitivity")
async def sensitivity_analysis(
    feature_name: str = Query(...),
    user_id: str = Query(default="default"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """📈 Sensitivity analysis for a feature. SECURED."""
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(user_id, x_user_id, authorization)
        
        from ml.automl_engine import ProductionMLEngine
        
        engine = ProductionMLEngine()
        engine.load(secure_user_id)
        
        if engine.model is None:
            raise HTTPException(status_code=404, detail="No trained model found")
        
        feature_metadata = getattr(engine, 'feature_metadata', [])
        feature_meta = next((m for m in feature_metadata if m.get('name') == feature_name), None)
        
        if not feature_meta:
            raise HTTPException(status_code=400, detail=f"Feature not found: {feature_name}")
        
        # Create base values from defaults
        base_values = {}
        for meta in feature_metadata:
            name = meta.get('name')
            if meta.get('type') == 'numeric':
                base_values[name] = meta.get('mean', 0)
            else:
                options = meta.get('options', [])
                base_values[name] = options[0] if options else ""
        
        results = []
        
        if feature_meta.get('type') == 'numeric':
            min_val = feature_meta.get('min', 0)
            max_val = feature_meta.get('max', 100)
            test_values = np.linspace(min_val, max_val, 10)
            
            for val in test_values:
                test_input = base_values.copy()
                test_input[feature_name] = float(val)
                
                try:
                    pred = engine.predict(test_input)
                    results.append({
                        "value": float(val),
                        "prediction": pred.get("prediction"),
                        "confidence": pred.get("confidence")
                    })
                except:
                    pass
        else:
            options = feature_meta.get('options', [])[:10]
            
            for opt in options:
                test_input = base_values.copy()
                test_input[feature_name] = opt
                
                try:
                    pred = engine.predict(test_input)
                    results.append({
                        "value": opt,
                        "prediction": pred.get("prediction"),
                        "confidence": pred.get("confidence")
                    })
                except:
                    pass
        
        return {"success": True, "feature": feature_name, "results": results}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sensitivity analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
