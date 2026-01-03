"""
🚀 AUTOML API - Production ML Endpoints
========================================

Upload ANY dataset → Get complete ML pipeline results.

Endpoints:
- POST /automl/train - Full AutoML pipeline
- POST /automl/predict - Use trained model
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class PredictRequest(BaseModel):
    """Request for prediction"""
    user_id: str
    model_name: str
    data: dict  # Feature values


# =============================================================================
# AUTOML ENDPOINTS
# =============================================================================

@router.post("/train")
async def train_automl(
    file: UploadFile = File(...),
    target_column: Optional[str] = Form(None),
    user_id: str = Form("default")
):
    """
    🚀 FULL AUTOML PIPELINE
    
    Upload a dataset → Get trained models, metrics, and charts.
    
    Returns:
    - Best model with metrics
    - Leaderboard of all models
    - Feature importance
    - Task-specific charts (classification or regression)
    - Feature metadata for prediction form
    """
    try:
        print("🚀 [AUTOML] Received training request")
        
        # 1. Load file
        content = await file.read()
        filename = file.filename or "data"
        print(f"📂 [AUTOML] Loading: {filename}")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
        
        print(f"📊 [AUTOML] Data: {df.shape[0]} rows, {df.shape[1]} columns")
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Empty dataset")
        
        # 2. Run AutoML
        from ml.automl_engine import automl_engine
        
        result = await automl_engine.run(df, target_column, user_id)
        
        # 3. Generate Charts (task-specific)
        charts = {}
        try:
            from ml.chart_generator import chart_generator
            
            charts = chart_generator.generate_all_charts(
                task_type=result.task_type,
                y_test=result.y_test,
                y_pred=result.y_pred,
                y_proba=result.y_proba,
                feature_importance=result.feature_importance,
                leaderboard=result.leaderboard
            )
            print(f"📊 [AUTOML] Generated {len(charts)} charts")
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            print(f"⚠️ Chart error: {e}")
        
        # 4. Save model for persistence
        try:
            automl_engine.save_model(user_id)
        except Exception as e:
            print(f"⚠️ Model save error: {e}")
        
        # 4. Return response
        return {
            "success": True,
            "task_type": result.task_type,
            "target_column": result.target_column,
            
            # Data summary
            "data_summary": result.data_profile,
            
            # Best model
            "best_model": result.best_model,
            
            # Leaderboard (all models sorted by performance)
            "all_models": result.leaderboard,
            
            # Feature importance
            "feature_importance": result.feature_importance,
            
            # Feature metadata for prediction form
            "feature_metadata": result.feature_metadata,
            
            # Charts (base64 images)
            "charts": charts,
            
            # Processing time
            "processing_time_seconds": result.processing_time,
            
            # Legacy fields (for compatibility)
            "bias_reports": [],
            "insights": [
                f"Best model: {result.best_model['name']} with {list(result.best_model['metrics'].keys())[0]}={list(result.best_model['metrics'].values())[0]:.3f}",
                f"Trained {len(result.leaderboard)} models in {result.processing_time:.1f}s"
            ],
            "recommendations": [
                f"Consider using {result.best_model['name']} for production",
                "Monitor feature drift for top features"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AutoML error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict")
async def predict(request: PredictRequest):
    """
    🔮 Make prediction using trained model
    
    Input: Feature values
    Output: Prediction + confidence
    """
    try:
        from ml.automl_engine import automl_engine
        
        if automl_engine.trainer.best_model is None:
            raise HTTPException(
                status_code=400, 
                detail="No model trained yet. Please train a model first."
            )
        
        result = automl_engine.predict(request.data)
        
        return {
            "success": True,
            "prediction": result['prediction'],
            "probability": result.get('probability'),
            "model": result.get('model'),
            "message": f"Predicted using {result.get('model')}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get AutoML engine status"""
    try:
        from ml.automl_engine import automl_engine
        
        return {
            "ready": True,
            "model_trained": automl_engine.trainer.best_model is not None,
            "best_model": automl_engine.trainer.best_model_name,
            "task_type": automl_engine.profile.task_type.value if automl_engine.profile else None
        }
    except:
        return {"ready": True, "model_trained": False}
