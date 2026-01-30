"""
🤖 Agentic AutoML API Endpoints

Provides API access to the autonomous multi-agent AutoML system.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import logging
import asyncio
from datetime import datetime

from agents import create_agentic_pipeline, AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agentic-automl", tags=["Agentic AutoML"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AgenticTrainRequest(BaseModel):
    """Request to train using agentic AutoML"""
    file_path: str
    target_column: str
    task_type: Optional[str] = None  # auto-detected if not provided


class AgenticTrainResponse(BaseModel):
    """Response from agentic training"""
    success: bool
    pipeline_id: str
    status: str
    phase: str
    approved: bool
    score: float
    metrics: Dict[str, float]
    duration_seconds: float
    iterations: int
    model_name: Optional[str] = None
    errors: List[str] = []
    execution_log: List[Dict] = []


# =============================================================================
# ACTIVE PIPELINES STORAGE
# =============================================================================

active_pipelines: Dict[str, AgentOrchestrator] = {}


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/train", response_model=AgenticTrainResponse)
async def train_agentic_automl(
    request: AgenticTrainRequest,
    background_tasks: BackgroundTasks
):
    """
    Train a model using the autonomous agentic AutoML system.
    
    This is the main entry point for the multi-agent pipeline:
    1. Data Quality Agent cleans and validates data
    2. Preprocessing Agent transforms features
    3. Feature Engineering Agent creates/selects features
    4. Model Strategy Agent selects algorithms
    5. Hyperparameter Agent optimizes models
    6. Training Validator Agent checks for issues
    7. Evaluation Agent runs final approval tests
    8. Visualization Agent generates explanations
    9. Deployment Agent prepares production pipeline
    """
    try:
        # Load dataset
        df = pd.read_csv(request.file_path)
        logger.info(f"🤖 Agentic AutoML: Loaded {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Create pipeline
        pipeline = create_agentic_pipeline()
        
        # Run pipeline (in executor for non-blocking)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: pipeline.run(
                dataset=df,
                target_column=request.target_column,
                task_type=request.task_type
            )
        )
        
        # Store pipeline for later access
        active_pipelines[result.get("pipeline_id", "unknown")] = pipeline
        
        # Get model name
        model_name = None
        if pipeline.memory.best_model:
            model_name = pipeline.memory.best_model.metadata.get("name", "unknown")
        
        return AgenticTrainResponse(
            success=result.get("success", False),
            pipeline_id=result.get("pipeline_id", "unknown"),
            status=result.get("status", "unknown"),
            phase=result.get("phase", "unknown"),
            approved=result.get("approved", False),
            score=result.get("score", 0),
            metrics=result.get("metrics", {}),
            duration_seconds=result.get("duration_seconds", 0),
            iterations=result.get("iterations", 0),
            model_name=model_name,
            errors=result.get("errors", []),
            execution_log=result.get("execution_log", [])
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Agentic AutoML error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: str):
    """Get status of an agentic pipeline"""
    pipeline = active_pipelines.get(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return {
        "pipeline_id": pipeline_id,
        "status": pipeline.status.value,
        "phase": pipeline.current_phase.value,
        "iteration": pipeline.iteration,
        "state": pipeline.memory.get_state_summary()
    }


@router.get("/pipeline/{pipeline_id}/logs")
async def get_pipeline_logs(pipeline_id: str):
    """Get execution logs for a pipeline"""
    pipeline = active_pipelines.get(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return {
        "pipeline_id": pipeline_id,
        "execution_log": pipeline.execution_log,
        "memory_logs": pipeline.memory.get_logs()
    }


@router.get("/pipeline/{pipeline_id}/charts")
async def get_pipeline_charts(pipeline_id: str):
    """Get generated charts for a pipeline"""
    pipeline = active_pipelines.get(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    charts = {}
    for artifact in pipeline.memory.get_artifacts("chart"):
        charts[artifact.metadata.get("chart_type", artifact.id)] = artifact.data
    
    return {
        "pipeline_id": pipeline_id,
        "charts": charts
    }


@router.post("/pipeline/{pipeline_id}/predict")
async def predict_with_pipeline(pipeline_id: str, data: Dict[str, Any]):
    """Make predictions using a deployed pipeline"""
    pipeline = active_pipelines.get(pipeline_id)
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    deployment = pipeline.memory.get_artifact("deployment_package")
    if not deployment:
        raise HTTPException(status_code=400, detail="Model not deployed")
    
    try:
        model = deployment.data["model"]
        # Convert input to array (simplified - would need full preprocessing in production)
        import numpy as np
        X = np.array([list(data.values())])
        prediction = model.predict(X)
        
        return {
            "pipeline_id": pipeline_id,
            "prediction": prediction.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_agentic_info():
    """Get information about the agentic AutoML system"""
    return {
        "name": "Agentic AutoML",
        "version": "1.0.0",
        "agents": [
            {"name": "Data Quality", "description": "Detects and fixes dataset issues"},
            {"name": "Preprocessing", "description": "Smart encoding and scaling"},
            {"name": "Feature Engineer", "description": "Feature creation and selection"},
            {"name": "Model Strategy", "description": "Algorithm selection based on data"},
            {"name": "Hyperparameter", "description": "Intelligent optimization with Optuna"},
            {"name": "Training Validator", "description": "Catches issues before evaluation"},
            {"name": "Evaluation", "description": "Final approval gate with robustness checks"},
            {"name": "Visualization", "description": "Explainability and charts"},
            {"name": "Deployment", "description": "Production inference pipeline"}
        ],
        "features": [
            "Hybrid communication (shared state + messages)",
            "Two-phase optimization (Fast Discovery + Deep Validation)",
            "Self-correction feedback loops",
            "Traditional ML only (no neural networks)"
        ]
    }
