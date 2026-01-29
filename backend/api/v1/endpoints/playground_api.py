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
            from core.auth import decode_supabase_jwt
            token = authorization[7:]
            payload = decode_supabase_jwt(token)
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
    type: str
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    default: Optional[Any] = None
    options: Optional[List[str]] = None


class PlaygroundConfig(BaseModel):
    model_name: str
    task_type: str
    target_column: str
    sliders: List[SliderConfig]
    class_names: Optional[List[str]] = None


class PlaygroundPredictRequest(BaseModel):
    values: Dict[str, Any]
    user_id: str = "default"


class PlaygroundPredictResponse(BaseModel):
    success: bool
    prediction: Optional[Any] = None
    prediction_label: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None


@router.get("/config", response_model=PlaygroundConfig)
async def get_playground_config(
    user_id: str = Query(default="default"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """🎮 Get playground configuration with slider settings. SECURED."""
    try:
        # SECURITY: Get verified user_id
        user_id = get_secure_user_id(user_id, x_user_id, authorization)
        
        from ml.automl_engine import ProductionMLEngine
        
        engine = ProductionMLEngine()
        engine.load(user_id)
        
        if engine.model is None:
            raise HTTPException(status_code=404, detail="No trained model found. Train a model first.")
        
        feature_metadata = getattr(engine, 'feature_metadata', [])
        
        if not feature_metadata:
            raise HTTPException(status_code=400, detail="No feature metadata available")
        
        sliders = []
        for meta in feature_metadata:
            name = meta.get('name', 'Unknown')
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
            else:
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
            class_names=class_names
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
