"""
🧠 AUTONOMOUS BRAIN API - DataVision Auto-Analysis Endpoint
============================================================

Drop ANY file → Get complete analysis in seconds.

Endpoints:
- POST /auto-analyze - Analyze uploaded file
- GET /brain/status - Get brain status
- POST /brain/insights - Generate AI insights
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import pandas as pd
import io

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AnalysisRequest(BaseModel):
    """Request for analysis"""
    user_id: str
    file_name: Optional[str] = "data"
    generate_insights: bool = True


class ColumnInfo(BaseModel):
    """Column information"""
    name: str
    type: str
    null_percentage: float
    unique_count: int
    issues: list = []
    fix_suggestions: list = []
    stats: Optional[dict] = None
    top_values: Optional[dict] = None


class RelationshipInfo(BaseModel):
    """Relationship between columns"""
    column1: str
    column2: str
    type: str
    strength: float
    description: str


class InsightInfo(BaseModel):
    """AI-generated insight"""
    title: str
    description: str
    importance: str
    category: str
    visualization: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response from brain analysis"""
    success: bool
    file_name: str
    analysis_time_ms: int
    
    # Overview
    total_rows: int
    total_columns: int
    memory_mb: float
    
    # Quality
    quality_score: float
    quality_level: str
    quality_issues: list
    
    # Details
    columns: list
    relationships: list
    insights: list
    suggested_charts: list
    
    # Summary
    summary: str


class QuickInsightRequest(BaseModel):
    """Request for quick insights"""
    user_id: str
    question: str
    context: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/auto-analyze", response_model=AnalysisResponse)
async def auto_analyze_file(
    file: UploadFile = File(...),
    user_id: str = "default"
):
    """
    🚀 Drop ANY file and get complete autonomous analysis
    
    Supports: CSV, Excel (.xlsx, .xls), JSON
    
    Returns:
    - Complete data profile
    - Quality score with fix suggestions
    - Column relationships
    - AI-generated insights
    - Visualization recommendations
    """
    try:
        # Read file content
        content = await file.read()
        file_name = file.filename or "uploaded_data"
        
        # Detect file type and load DataFrame
        df = await _load_dataframe(content, file_name)
        
        if df is None or len(df) == 0:
            raise HTTPException(status_code=400, detail="Could not parse file or file is empty")
        
        # Import brain and analyze
        from core.autonomous_brain import get_brain
        
        brain = get_brain()
        analysis = await brain.analyze(df, file_name, generate_insights=True)
        result = brain.to_dict(analysis)
        
        return AnalysisResponse(
            success=True,
            file_name=result["file_name"],
            analysis_time_ms=result["analysis_duration_ms"],
            total_rows=result["total_rows"],
            total_columns=result["total_columns"],
            memory_mb=result["memory_usage_mb"],
            quality_score=result["quality_score"],
            quality_level=result["quality_level"],
            quality_issues=result["quality_issues"],
            columns=result["columns"],
            relationships=result["relationships"],
            insights=result["insights"],
            suggested_charts=result["suggested_charts"],
            summary=result["summary"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-dataframe")
async def analyze_existing_data(request: AnalysisRequest):
    """
    Analyze data already uploaded by user
    """
    try:
        from utils.paths import get_user_paths
        import os
        
        paths = get_user_paths(request.user_id)
        
        # Find user's data file
        data_file = None
        for ext in ['.csv', '.xlsx', '.json']:
            potential_file = os.path.join(paths["uploads"], f"data{ext}")
            if os.path.exists(potential_file):
                data_file = potential_file
                break
        
        if not data_file:
            # Look for any file
            if os.path.exists(paths["uploads"]):
                files = os.listdir(paths["uploads"])
                if files:
                    data_file = os.path.join(paths["uploads"], files[0])
        
        if not data_file:
            raise HTTPException(status_code=404, detail="No data found. Please upload a file first.")
        
        # Load DataFrame
        df = await _load_dataframe_from_path(data_file)
        
        if df is None:
            raise HTTPException(status_code=400, detail="Could not load data file")
        
        # Analyze
        from core.autonomous_brain import get_brain
        
        brain = get_brain()
        analysis = await brain.analyze(df, request.file_name, request.generate_insights)
        result = brain.to_dict(analysis)
        
        return {
            "success": True,
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze dataframe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-insight")
async def get_quick_insight(request: QuickInsightRequest):
    """
    Get quick AI insight about a specific question
    """
    try:
        from core.reasoning_engine import reason, ReasoningMode
        
        result = await reason(
            query=request.question,
            context=request.context or "",
            mode=ReasoningMode.CHAIN_OF_THOUGHT
        )
        
        return {
            "success": True,
            "question": request.question,
            "answer": result.final_answer,
            "confidence": result.confidence,
            "reasoning_steps": [
                {"type": step.step_type, "content": step.content}
                for step in result.steps
            ],
            "reasoning_time_ms": result.reasoning_time_ms
        }
        
    except Exception as e:
        logger.error(f"Quick insight error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/root-cause")
async def analyze_root_cause(
    user_id: str,
    target_column: str,
    question: str,
    time_column: Optional[str] = None
):
    """
    Perform root cause analysis on data
    """
    try:
        # Load user's data
        df = await _load_user_data(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        if target_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{target_column}' not found")
        
        from mcp.advanced_mcps import analyze_root_cause
        
        result = await analyze_root_cause(df, target_column, question, time_column)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Root cause error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment")
async def segment_data(
    user_id: str,
    n_segments: Optional[int] = None,
    features: Optional[str] = None  # Comma-separated
):
    """
    Segment data using AI clustering
    """
    try:
        df = await _load_user_data(user_id)
        
        if df is None:
            raise HTTPException(status_code=404, detail="No data found")
        
        feature_list = features.split(",") if features else None
        
        from mcp.advanced_mcps import segment_data
        
        result = await segment_data(df, feature_list, n_segments)
        
        return {"success": True, **result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trends")
async def detect_trends(
    user_id: str,
    time_column: Optional[str] = None
):
    """
    Detect trends and anomalies in data
    """
    try:
        df = await _load_user_data(user_id)
        
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


@router.get("/brain/status")
async def get_brain_status():
    """
    Get the status of the Autonomous Brain
    """
    try:
        from core.autonomous_brain import get_brain
        
        brain = get_brain()
        
        return {
            "status": "active",
            "cached_analyses": len(brain.analysis_cache),
            "version": "1.0.0",
            "capabilities": [
                "auto_profiling",
                "quality_scoring",
                "relationship_discovery",
                "ai_insights",
                "visualization_suggestions",
                "root_cause_analysis",
                "segmentation",
                "trend_detection"
            ]
        }
        
    except Exception as e:
        logger.error(f"Brain status error: {e}")
        return {"status": "error", "error": str(e)}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _load_dataframe(content: bytes, filename: str) -> Optional[pd.DataFrame]:
    """Load DataFrame from file content"""
    try:
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            return pd.read_csv(io.BytesIO(content))
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(content))
        elif filename_lower.endswith('.json'):
            return pd.read_json(io.BytesIO(content))
        else:
            # Try CSV as default
            return pd.read_csv(io.BytesIO(content))
            
    except Exception as e:
        logger.error(f"Error loading DataFrame: {e}")
        return None


async def _load_dataframe_from_path(path: str) -> Optional[pd.DataFrame]:
    """Load DataFrame from file path"""
    try:
        path_lower = path.lower()
        
        if path_lower.endswith('.csv'):
            return pd.read_csv(path)
        elif path_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(path)
        elif path_lower.endswith('.json'):
            return pd.read_json(path)
        else:
            return pd.read_csv(path)
            
    except Exception as e:
        logger.error(f"Error loading DataFrame from path: {e}")
        return None


async def _load_user_data(user_id: str) -> Optional[pd.DataFrame]:
    """Load user's uploaded data"""
    try:
        from utils.paths import get_user_paths
        import os
        
        paths = get_user_paths(user_id)
        uploads_dir = paths.get("uploads", "")
        
        if not os.path.exists(uploads_dir):
            return None
        
        # Find first data file
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            if os.path.isfile(filepath):
                return await _load_dataframe_from_path(filepath)
        
        return None
        
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        return None
