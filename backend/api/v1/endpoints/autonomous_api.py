"""
🤖 AUTONOMOUS API - Model Management & Auto-Fix Endpoints
==========================================================

Provides API endpoints for:
1. Model persistence (list, load, delete, rollback)
2. Autonomous data operations (auto-fix, detect issues)
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import pandas as pd
import io

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AutoFixRequest(BaseModel):
    user_id: str
    fix_missing: bool = True
    fix_outliers: bool = True
    fix_duplicates: bool = True
    fix_types: bool = True
    enrich_dates: bool = True
    aggressive: bool = False


class ModelRollbackRequest(BaseModel):
    user_id: str
    version: int


# =============================================================================
# MODEL MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/models/{user_id}")
async def list_user_models(user_id: str):
    """
    List all trained models for a user.
    Returns active model and version history with metrics.
    """
    try:
        from ml.model_persistence import model_persistence
        
        models = model_persistence.list_models(user_id)
        
        if not models:
            return {
                "success": True,
                "user_id": user_id,
                "has_models": False,
                "models": [],
                "message": "No trained models found. Train a model first."
            }
        
        return {
            "success": True,
            "user_id": user_id,
            "has_models": True,
            "active_model": models[0].to_dict() if models else None,
            "total_versions": len(models),
            "models": [m.to_dict() for m in models]
        }
        
    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{user_id}/active")
async def get_active_model(user_id: str):
    """Get the currently active model for a user."""
    try:
        from ml.model_persistence import model_persistence
        
        metadata = model_persistence.get_metadata(user_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="No active model found")
        
        return {
            "success": True,
            "model": metadata.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get active model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/rollback")
async def rollback_model(request: ModelRollbackRequest):
    """Rollback to a previous model version."""
    try:
        from ml.model_persistence import model_persistence
        
        success = model_persistence.rollback_to_version(request.user_id, request.version)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Version {request.version} not found"
            )
        
        return {
            "success": True,
            "message": f"Rolled back to version {request.version}",
            "active_version": request.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{user_id}")
async def delete_all_models(user_id: str):
    """Delete all models for a user."""
    try:
        from ml.model_persistence import model_persistence
        
        success = model_persistence.delete_model(user_id)
        
        return {
            "success": success,
            "message": f"All models deleted for user {user_id}" if success else "No models found"
        }
        
    except Exception as e:
        logger.error(f"Delete models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/models/{user_id}/version/{version}")
async def delete_model_version(user_id: str, version: int):
    """Delete a specific model version."""
    try:
        from ml.model_persistence import model_persistence
        
        success = model_persistence.delete_model(user_id, version)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")
        
        return {
            "success": True,
            "message": f"Deleted version {version}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUTONOMOUS DATA OPERATIONS ENDPOINTS
# =============================================================================

@router.post("/auto-fix")
async def auto_fix_data(
    file: UploadFile = File(...),
    user_id: str = Form("default"),
    fix_missing: bool = Form(True),
    fix_outliers: bool = Form(True),
    fix_duplicates: bool = Form(True),
    fix_types: bool = Form(True),
    enrich_dates: bool = Form(True),
    aggressive: bool = Form(False)
):
    """
    🤖 Automatically fix data quality issues.
    
    Fixes applied:
    - Missing value imputation (median/mode)
    - Outlier capping (IQR method)
    - Duplicate removal
    - Data type corrections
    - Date feature enrichment
    
    Returns the fixed data and a detailed report.
    """
    try:
        from core.autonomous_data_ops import autonomous_data_ops
        
        # Load file
        content = await file.read()
        filename = file.filename or "data.csv"
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        logger.info(f"🤖 Auto-fix request: {filename} ({df.shape[0]} rows, {df.shape[1]} cols)")
        
        # Apply autonomous fixes
        df_fixed, report = autonomous_data_ops.auto_fix(
            df,
            fix_missing=fix_missing,
            fix_outliers=fix_outliers,
            fix_duplicates=fix_duplicates,
            fix_types=fix_types,
            enrich_dates=enrich_dates,
            aggressive=aggressive
        )
        
        # Save fixed data to user storage
        from pathlib import Path
        save_dir = Path(f"./storage/users/{user_id}/fixed_data")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        fixed_filename = f"fixed_{filename}"
        save_path = save_dir / fixed_filename
        df_fixed.to_csv(save_path, index=False)
        
        return {
            "success": True,
            "original_file": filename,
            "fixed_file": fixed_filename,
            "report": report.to_dict(),
            "preview": {
                "columns": list(df_fixed.columns),
                "rows": df_fixed.head(10).to_dict(orient="records")
            },
            "message": f"Applied {len(report.fixes_applied)} fixes, quality improved from {report.quality_score_before:.0%} to {report.quality_score_after:.0%}"
        }
        
    except Exception as e:
        logger.error(f"Auto-fix error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-issues")
async def detect_data_issues(
    file: UploadFile = File(...)
):
    """
    Detect data quality issues without fixing them.
    Returns a report of issues and recommendations.
    """
    try:
        from core.autonomous_data_ops import autonomous_data_ops
        
        # Load file
        content = await file.read()
        filename = file.filename or "data.csv"
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        
        # Detect issues
        issues = autonomous_data_ops.detect_issues(df)
        recommendation = autonomous_data_ops.get_fix_recommendation(df)
        
        return {
            "success": True,
            "filename": filename,
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "issues": issues,
            "recommendation": recommendation,
            "issue_summary": {
                "missing_value_columns": len(issues["missing_values"]),
                "duplicate_rows": len(issues["duplicates"]) > 0,
                "outlier_columns": len(issues["outliers"]),
                "type_issues": len(issues["type_issues"])
            }
        }
        
    except Exception as e:
        logger.error(f"Detect issues error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-users-with-models")
async def get_all_users_with_models():
    """Get list of all users who have trained models."""
    try:
        from ml.model_persistence import model_persistence
        
        users = model_persistence.get_all_users_with_models()
        
        return {
            "success": True,
            "total_users": len(users),
            "users": users
        }
        
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
