"""
🚀 DATAVISION API v2 - Complete Feature Integration
====================================================

Unified API exposing ALL DataVision capabilities:
- Autonomous Brain (auto-analysis)
- Universal Agent (NLU queries)
- Visual Intelligence (knowledge graphs)
- Predictive Intelligence (forecasts)
- Enterprise Features (exports, audit)
- Advanced MCPs

All endpoints in one place.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends, Header
from pydantic import BaseModel, Field
import pandas as pd
import io

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# SECURITY HELPER - JWT Authentication
# =============================================================================

def get_secure_user_id(body_user_id: str, x_user_id: Optional[str], authorization: Optional[str]) -> str:
    """
    Get verified user_id from JWT token or headers.
    Priority: JWT token > X-User-ID header > Body data
    """
    # 1. Try JWT token first (most secure)
    if authorization:
        try:
            token = authorization.replace("Bearer ", "")
            from core.auth import decode_jwt_token
            payload = decode_jwt_token(token)
            if payload and payload.get("sub"):
                return payload["sub"]
        except Exception as e:
            logger.debug(f"JWT decode failed: {e}")
    
    # 2. Try X-User-ID header (from authenticated frontend)
    if x_user_id and x_user_id != "default":
        return x_user_id
    
    # 3. Fallback to body data (least secure)
    if body_user_id and body_user_id != "default":
        logger.warning(f"Using body user_id: {body_user_id} - consider using JWT")
        return body_user_id
    
    # 4. Generate guest fingerprint
    import hashlib
    import time
    return f"guest_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class QueryRequest(BaseModel):
    """Natural language query request"""
    query: str
    user_id: str = "default"
    include_visualizations: bool = True


class PredictionRequest(BaseModel):
    """Prediction request"""
    user_id: str
    target_column: str
    feature_columns: Optional[List[str]] = None
    periods: int = 12


class ExportRequest(BaseModel):
    """Export request"""
    user_id: str
    format: str = "csv"  # csv, excel, pdf
    filename: Optional[str] = None


class SegmentRequest(BaseModel):
    """Segmentation request"""
    user_id: str
    n_segments: Optional[int] = None
    features: Optional[List[str]] = None


class RootCauseRequest(BaseModel):
    """Root cause analysis request"""
    user_id: str
    target_column: str
    question: str
    time_column: Optional[str] = None


class ForecastRequest(BaseModel):
    """Forecast request"""
    user_id: str
    date_column: str
    value_column: str
    periods: int = 12


class ScenarioRequest(BaseModel):
    """What-if scenario request"""
    user_id: str
    target_column: str
    scenarios: List[dict]


# =============================================================================
# DATA LOADING HELPER
# =============================================================================

async def load_user_dataframe(user_id: str) -> Optional[pd.DataFrame]:
    """Load user's uploaded DataFrame"""
    try:
        from utils.paths import get_user_paths
        import os
        
        paths = get_user_paths(user_id)
        uploads_dir = paths.get("uploads", "")
        
        if not os.path.exists(uploads_dir):
            return None
        
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            if os.path.isfile(filepath):
                if filename.endswith('.csv'):
                    return pd.read_csv(filepath)
                elif filename.endswith(('.xlsx', '.xls')):
                    return pd.read_excel(filepath)
                elif filename.endswith('.json'):
                    return pd.read_json(filepath)
        
        return None
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        return None


# =============================================================================
# AUTONOMOUS BRAIN ENDPOINTS
# =============================================================================

@router.post("/analyze")
async def auto_analyze(
    file: UploadFile = File(...),
    user_id: str = "default"
):
    """
    🧠 DROP ANY FILE → GET COMPLETE ANALYSIS
    
    Auto-profiles your data with:
    - Column type detection
    - Quality scoring
    - Relationship discovery
    - AI insights
    - Chart recommendations
    """
    try:
        content = await file.read()
        filename = file.filename or "data"
        
        # Load DataFrame
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
        
        from core.autonomous_brain import get_brain
        
        brain = get_brain()
        analysis = await brain.analyze(df, filename, generate_insights=True)
        result = brain.to_dict(analysis)
        
        # Log action
        from core.enterprise_features import log_action
        log_action(user_id, "auto_analyze", filename, {"rows": len(df)})
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# UNIVERSAL AGENT ENDPOINTS
# =============================================================================

@router.post("/query")
async def process_natural_query(
    request: QueryRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    🤖 ASK ANYTHING ABOUT YOUR DATA - SECURED
    
    Uses advanced NLU to understand:
    - "Why did sales drop in Q3?"
    - "Predict next month's revenue"
    - "Show me customer segments"
    - "What trends should I know about?"
    """
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(request.user_id, x_user_id, authorization)
        
        df = await load_user_dataframe(secure_user_id)
        
        from agents.universal_agent import process_query
        
        result = await process_query(
            query=request.query,
            user_id=secure_user_id,
            df=df
        )
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reason")
async def deep_reasoning(
    query: str,
    user_id: str = "default",
    mode: str = "cot",  # cot, react, sc
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    🧠 DEEP AI REASONING - SECURED
    
    Modes:
    - cot: Chain-of-Thought (step-by-step)
    - react: Reason + Act (multi-step actions)
    - sc: Self-Consistency (multiple attempts)
    """
    try:
        # SECURITY: Get verified user_id from JWT
        secure_user_id = get_secure_user_id(user_id, x_user_id, authorization)
        
        from core.reasoning_engine import reason, ReasoningMode
        
        mode_map = {
            "cot": ReasoningMode.CHAIN_OF_THOUGHT,
            "react": ReasoningMode.REACT,
            "sc": ReasoningMode.SELF_CONSISTENCY,
            "direct": ReasoningMode.DIRECT
        }
        
        result = await reason(
            query=query,
            mode=mode_map.get(mode, ReasoningMode.CHAIN_OF_THOUGHT)
        )
        
        return {
            "success": True,
            "answer": result.final_answer,
            "confidence": result.confidence,
            "steps": [
                {"type": s.step_type, "content": s.content}
                for s in result.steps
            ],
            "processing_time_ms": result.reasoning_time_ms
        }
        
    except Exception as e:
        logger.error(f"Reasoning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VISUAL INTELLIGENCE ENDPOINTS
# =============================================================================

@router.post("/knowledge-graph")
async def build_knowledge_graph(user_id: str = "default"):
    """
    🔗 BUILD KNOWLEDGE GRAPH FROM DATA
    
    Automatically discovers:
    - Column relationships
    - Entity connections
    - Data patterns
    """
    try:
        df = await load_user_dataframe(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from core.visual_intelligence_v2 import build_knowledge_graph
        
        result = await build_knowledge_graph(df)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chart-recommendations")
async def get_chart_recommendations(
    user_id: str = "default",
    max_charts: int = 6
):
    """
    📊 AI CHART RECOMMENDATIONS
    
    Get the best chart types for your data.
    """
    try:
        df = await load_user_dataframe(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from core.visual_intelligence_v2 import get_chart_recommendations
        
        result = await get_chart_recommendations(df, max_charts)
        
        return {"success": True, "recommendations": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PREDICTIVE INTELLIGENCE ENDPOINTS
# =============================================================================

@router.post("/predict")
async def ensemble_prediction(request: PredictionRequest):
    """
    🔮 ENSEMBLE PREDICTIONS WITH CONFIDENCE
    
    Uses 4 ML models for robust predictions:
    - Linear Regression
    - Ridge
    - Random Forest
    - Gradient Boosting
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        if request.target_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.target_column}' not found")
        
        from core.predictive_intelligence import predict_with_confidence
        
        result = await predict_with_confidence(
            df, 
            request.target_column, 
            request.feature_columns
        )
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast")
async def time_series_forecast(request: ForecastRequest):
    """
    📈 TIME SERIES FORECASTING
    
    Predict future values with confidence intervals.
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from core.predictive_intelligence import forecast_time_series
        
        result = await forecast_time_series(
            df,
            request.date_column,
            request.value_column,
            request.periods
        )
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ADVANCED MCP ENDPOINTS
# =============================================================================

@router.post("/root-cause")
async def analyze_root_cause(request: RootCauseRequest):
    """
    🔍 ROOT CAUSE ANALYSIS
    
    Answer "WHY did this happen?" questions.
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.advanced_mcps import analyze_root_cause
        
        result = await analyze_root_cause(
            df, 
            request.target_column, 
            request.question,
            request.time_column
        )
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Root cause error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment")
async def segment_data(request: SegmentRequest):
    """
    🎯 AI-POWERED DATA SEGMENTATION
    
    Uses K-Means clustering to find:
    - Customer segments
    - Product categories
    - Behavior patterns
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.advanced_mcps import segment_data
        
        result = await segment_data(df, request.features, request.n_segments)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends")
async def detect_trends(
    user_id: str = "default",
    time_column: Optional[str] = None
):
    """
    📊 TREND DETECTION & ANOMALY IDENTIFICATION
    """
    try:
        df = await load_user_dataframe(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.advanced_mcps import detect_trends
        
        result = await detect_trends(df, time_column)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trend detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cohorts")
async def analyze_cohorts(
    user_id: str,
    date_column: str,
    user_column: str,
    value_column: Optional[str] = None
):
    """
    📈 COHORT ANALYSIS
    
    Track user retention over time.
    """
    try:
        df = await load_user_dataframe(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.enterprise_mcps import analyze_cohorts
        
        result = await analyze_cohorts(df, date_column, user_column, value_column)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cohort analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/automl")
async def run_automl(
    user_id: str,
    target_column: str,
    features: Optional[str] = None
):
    """
    🤖 AUTOML - AUTOMATIC MODEL SELECTION
    
    Tests multiple models and picks the best one.
    """
    try:
        df = await load_user_dataframe(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.enterprise_mcps import run_automl
        
        feature_list = features.split(",") if features else None
        result = await run_automl(df, target_column, feature_list)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AutoML error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatif")
async def what_if_simulation(request: ScenarioRequest):
    """
    🔮 WHAT-IF SIMULATION
    
    Test scenarios like:
    - "What if we increase price by 10%?"
    - "What if marketing budget goes down 20%?"
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from mcp.enterprise_mcps import simulate_scenarios
        
        result = await simulate_scenarios(df, request.target_column, request.scenarios)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENTERPRISE ENDPOINTS
# =============================================================================

@router.post("/export")
async def export_data(request: ExportRequest):
    """
    📤 EXPORT DATA
    
    Formats: CSV, Excel, PDF
    """
    try:
        df = await load_user_dataframe(request.user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        from core.enterprise_features import export_data
        
        config = {"filename": request.filename} if request.filename else {}
        result = await export_data(df, request.format, request.user_id, config)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limit")
async def check_rate_limit(user_id: str = "default"):
    """
    🚦 CHECK RATE LIMIT STATUS
    """
    from core.enterprise_features import check_rate_limit
    return check_rate_limit(user_id)


@router.get("/status")
async def get_platform_status():
    """
    📊 DATAVISION PLATFORM STATUS
    """
    return {
        "platform": "DataVision",
        "version": "2.0.0",
        "status": "active",
        "capabilities": {
            "autonomous_brain": True,
            "universal_agent": True,
            "knowledge_graphs": True,
            "predictive_intelligence": True,
            "advanced_mcps": [
                "root_cause_analysis",
                "segmentation",
                "trend_detection",
                "cohort_analysis",
                "automl",
                "what_if_simulation"
            ],
            "enterprise_features": [
                "export_csv",
                "export_excel",
                "export_pdf",
                "audit_logging",
                "rate_limiting",
                "session_management"
            ]
        }
    }
