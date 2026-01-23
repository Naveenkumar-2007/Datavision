"""
📊 EXPLAINABILITY API
=====================

Provides model explanation endpoints using SHAP:
- POST /api/v1/automl/explain - Explain a single prediction
- GET /api/v1/automl/explain/global - Get global feature importance
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import logging

from utils.paths import get_user_paths

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/automl", tags=["AutoML - Explainability"])


class ExplainRequest(BaseModel):
    input_values: Dict[str, Any]
    user_id: str = "default"


class ContributionItem(BaseModel):
    feature: str
    value: float
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


@router.post("/explain", response_model=ExplainResponse)
async def explain_prediction(request: ExplainRequest):
    """🔍 Explain why the model made a specific prediction using SHAP."""
    try:
        from ml.automl_engine import ProductionMLEngine
        from ml.shap_engine import SHAPExplainer, HAS_SHAP
        
        if not HAS_SHAP:
            raise HTTPException(
                status_code=400, 
                detail="SHAP not installed. Run: pip install shap"
            )
        
        engine = ProductionMLEngine()
        engine.load(request.user_id)
        
        if engine.model is None:
            raise HTTPException(status_code=404, detail="No trained model found")
        
        # Get prediction
        prediction_result = engine.predict(request.input_values)
        
        # Prepare input for SHAP
        X_single = engine._preprocess_single(request.input_values)
        
        X_background = getattr(engine, '_X_train', None)
        if X_background is None:
            raise HTTPException(status_code=400, detail="Training data not available for SHAP")
        
        feature_names = getattr(engine, 'feature_columns', None)
        explainer = SHAPExplainer(engine.model, X_background, feature_names)
        
        explanation = explainer.explain_prediction(X_single)
        
        if "error" in explanation:
            raise HTTPException(status_code=500, detail=explanation["error"])
        
        # Generate plain English explanation
        top_features = explanation.get("contributions", [])[:5]
        positive_features = [f for f in top_features if f["shap_value"] > 0]
        negative_features = [f for f in top_features if f["shap_value"] < 0]
        
        explanation_parts = []
        if positive_features:
            pos_text = ", ".join([f['feature'] for f in positive_features[:3]])
            explanation_parts.append(f"Pushed prediction UP: {pos_text}")
        if negative_features:
            neg_text = ", ".join([f['feature'] for f in negative_features[:3]])
            explanation_parts.append(f"Pushed prediction DOWN: {neg_text}")
        
        explanation_text = ". ".join(explanation_parts) if explanation_parts else None
        
        contributions = [
            ContributionItem(
                feature=c["feature"],
                value=c["value"],
                shap_value=c["shap_value"],
                direction=c["direction"]
            )
            for c in explanation.get("contributions", [])
        ]
        
        return ExplainResponse(
            success=True,
            base_value=explanation.get("base_value"),
            prediction=prediction_result.get("prediction"),
            prediction_contribution=explanation.get("prediction_contribution"),
            contributions=contributions,
            waterfall_chart=explanation.get("waterfall_chart"),
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
async def get_global_importance(user_id: str = Query(default="default")):
    """📊 Get global feature importance using SHAP."""
    try:
        from ml.automl_engine import ProductionMLEngine
        from ml.shap_engine import SHAPExplainer, HAS_SHAP
        
        if not HAS_SHAP:
            return {"error": "SHAP not installed. Run: pip install shap"}
        
        engine = ProductionMLEngine()
        engine.load(user_id)
        
        if engine.model is None:
            return {"error": "No trained model found"}
        
        X_train = getattr(engine, '_X_train', None)
        if X_train is None:
            return {"error": "Training data not available"}
        
        feature_names = getattr(engine, 'feature_columns', None)
        explainer = SHAPExplainer(engine.model, X_train, feature_names)
        
        return explainer.get_global_importance()
        
    except Exception as e:
        logger.error(f"Global importance error: {e}")
        return {"error": str(e)}
