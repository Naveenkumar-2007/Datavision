from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import base64
import os
import json
import asyncio
import tempfile
import time
import logging
import uuid as _uuid

from core.auth import get_current_user_optional
from core.mode_engines.cv_engine import CVAutoMLEngine
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()
cv_engine = CVAutoMLEngine()

def _is_valid_uuid(val: str) -> bool:
    try:
        _uuid.UUID(str(val))
        return True
    except (ValueError, AttributeError):
        return False


# ─────────────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    image: str  # Base64 string
    model_id: Optional[str] = None

class BatchPredictRequest(BaseModel):
    images: List[str]
    model_id: Optional[str] = None

class TrainRequest(BaseModel):
    dataset_id: str
    mode: str = 'fast'
    config: Dict[str, Any] = {}
    task_type: Optional[str] = None

class ExportRequest(BaseModel):
    formats: List[str] = ["onnx"]

# ─────────────────────────────────────────────────────
# PREDICTION ENDPOINTS
# ─────────────────────────────────────────────────────

@router.post("/predict")
async def predict_image(
    request: PredictRequest,
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Runs real-time prediction on an image — logs to DB for admin visibility."""
    try:
        model_path = None
        model_name = "default"
        task_type = None
        
        # Resolve user ID for model discovery
        user_id_str = None
        if current_user and hasattr(current_user, 'id'):
            user_id_str = str(current_user.id)
        elif current_user and hasattr(current_user, 'user_id'):
            user_id_str = str(current_user.user_id)
        
        if request.model_id:
            # User explicitly selected a model
            progress = cv_engine.get_training_progress(request.model_id)
            if progress:
                model_path = progress.get('model_path')
                model_name = progress.get('config', {}).get('model', 'custom')
                task_type = progress.get('config', {}).get('task_type')
        else:
            # Auto-discover the user's latest trained model
            auto_path, auto_task = cv_engine.find_latest_trained_model(user_id=user_id_str)
            if auto_path:
                model_path = auto_path
                task_type = auto_task
                model_name = f"auto-discovered ({auto_task or 'detection'})"
                logger.info(f"Auto-discovered trained model for prediction: {auto_path} (task: {auto_task})")

        result = cv_engine.predict_image(request.image, model_path, task_type=task_type)
        if "error" in result and not result.get("success"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Persist a ComputerVisionTask record for admin visibility
        try:
            from app.models.dashboard import ComputerVisionTask
            user_id = None
            if current_user and hasattr(current_user, 'id'):
                user_id = current_user.id
            elif current_user and hasattr(current_user, 'user_id'):
                try:
                    user_id = _uuid.UUID(str(current_user.user_id))
                except Exception:
                    pass
            
            if user_id:
                task_type = result.get('task_type', 'object_detection')
                predictions = result.get('predictions', [])
                det_count = len(predictions) if isinstance(predictions, list) else 0
                
                cv_task = ComputerVisionTask(
                    user_id=user_id,
                    task_name=f"Prediction ({task_type.replace('_', ' ').title()})",
                    task_type=task_type,
                    model_name=model_name,
                    status="completed",
                    results_json=result,
                    detected_objects_count=det_count,
                    confidence_threshold=0.25
                )
                db.add(cv_task)
                await db.commit()
        except Exception as db_err:
            logger.warning(f"Could not persist CV prediction to DB: {db_err}")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/batch")
async def predict_batch(request: BatchPredictRequest, current_user=Depends(get_current_user_optional)):
    """Runs prediction on multiple images"""
    try:
        model_path = None
        if request.model_id:
            progress = cv_engine.get_training_progress(request.model_id)
            model_path = progress.get('model_path')

        results = cv_engine.predict_batch(request.images, model_path)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────
# DATASET ENDPOINTS
# ─────────────────────────────────────────────────────

@router.post("/datasets")
async def upload_dataset(file: UploadFile = File(...), current_user=Depends(get_current_user_optional)):
    """Upload a ZIP dataset, auto-detect structure"""
    try:
        user_id = str(current_user.id) if (current_user and hasattr(current_user, 'id')) else "anonymous"

        # Save uploaded file to temp
        suffix = os.path.splitext(file.filename or "dataset.zip")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Process dataset
            result = cv_engine.prepare_dataset(tmp_path, user_id, file.filename)
            
            if result and isinstance(result, dict):
                result['success'] = True
                return result

            raise HTTPException(status_code=400, detail="Upload failed: Invalid dataset structure.")
        finally:
            # Clean up temp file safely
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Could not delete temp dataset file {tmp_path}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset upload endpoint exception: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Dataset upload failed: {str(e)}")


@router.get("/datasets")
async def list_datasets(current_user=Depends(get_current_user_optional)):
    """List user's uploaded CV datasets"""
    user_id = str(current_user.id) if (current_user and hasattr(current_user, 'id')) else "anonymous"
    datasets = cv_engine.list_datasets(user_id)
    return {"datasets": datasets}

@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, current_user=Depends(get_current_user_optional)):
    """Get dataset metadata"""
    dataset = cv_engine.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"dataset": dataset}

@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, current_user=Depends(get_current_user_optional)):
    """Delete a dataset"""
    success = cv_engine.delete_dataset(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found or could not be deleted")
    return {"success": True}

@router.get("/datasets/{dataset_id}/images/{index}")
async def get_dataset_image(dataset_id: str, index: int, current_user=Depends(get_current_user_optional)):
    """Serve a specific image from the dataset by index"""
    img_path = cv_engine.get_dataset_image(dataset_id, index)
    if not img_path or not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    import mimetypes
    mime_type, _ = mimetypes.guess_type(img_path)
    if not mime_type:
        mime_type = "image/jpeg"

    return FileResponse(img_path, media_type=mime_type)

# ─────────────────────────────────────────────────────
# TRAINING ENDPOINTS
# ─────────────────────────────────────────────────────

@router.post("/train")
async def start_training(
    request: TrainRequest,
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Start training in Fast/Ultra/Expert mode (returns job_id) — persists task record to DB."""
    user_id = str(current_user.id) if (current_user and hasattr(current_user, 'id')) else "anonymous"
    
    # Ensure dataset exists
    dataset = cv_engine.get_dataset(request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    job_id = cv_engine.train_model(request.dataset_id, request.config, "ignored_task_id", request.mode, user_id, request.task_type)

    # Persist a ComputerVisionTask record so admin can see it
    try:
        from app.models.dashboard import ComputerVisionTask
        db_user_id = None
        if current_user and hasattr(current_user, 'id'):
            db_user_id = current_user.id
        
        if db_user_id:
            task_type = request.task_type or dataset.get('taskType', 'object_detection')
            model_name = request.config.get('model', 'yolov8n')
            cv_task = ComputerVisionTask(
                id=_uuid.UUID(job_id) if _is_valid_uuid(job_id) else _uuid.uuid4(),
                user_id=db_user_id,
                task_name=f"Training: {model_name} ({request.mode} mode)",
                task_type=task_type,
                model_name=model_name,
                status="running",
                results_json={"job_id": job_id, "dataset_id": request.dataset_id, "mode": request.mode},
                detected_objects_count=len(dataset.get('classes', [])),
                confidence_threshold=0.25
            )
            db.add(cv_task)
            await db.commit()
    except Exception as db_err:
        logger.warning(f"Could not persist CV training task to DB: {db_err}")

    return {
        "success": True,
        "job_id": job_id,
        "message": f"Training started in {request.mode} mode",
        "config": request.config
    }


@router.get("/train/{job_id}/progress")
async def training_progress_sse(job_id: str, current_user=Depends(get_current_user_optional)):
    """Stream training progress via Server-Sent Events"""

    async def event_stream():
        last_epoch = -1
        while True:
            progress = cv_engine.get_training_progress(job_id)

            if progress.get('status') == 'not_found':
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break

            # Send full progress object directly
            yield f"data: {json.dumps(progress)}\n\n"

            if progress.get('status') in ('completed', 'failed', 'cancelled'):
                break

            await asyncio.sleep(1.0) # 1 update per second

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/train/{job_id}/stop")
async def stop_training(job_id: str, current_user=Depends(get_current_user_optional)):
    """Cancel a running training job"""
    success = cv_engine.stop_training(job_id)
    if success:
        return {"success": True, "message": "Training cancelled"}
    raise HTTPException(status_code=404, detail="Training job not found or not running")

@router.post("/train/{job_id}/pause")
async def pause_training(job_id: str, current_user=Depends(get_current_user_optional)):
    """Pause a running training job"""
    success = cv_engine.pause_training(job_id)
    if success:
        return {"success": True, "message": "Training paused"}
    raise HTTPException(status_code=404, detail="Training job not found or not running")
    
@router.post("/train/{job_id}/resume")
async def resume_training(job_id: str, current_user=Depends(get_current_user_optional)):
    """Resume a paused training job"""
    success = cv_engine.resume_training(job_id)
    if success:
        return {"success": True, "message": "Training resumed"}
    raise HTTPException(status_code=404, detail="Training job not found or not paused")

# ─────────────────────────────────────────────────────
# MODEL EXPORT & MANAGEMENT ENDPOINTS
# ─────────────────────────────────────────────────────

@router.get("/models")
async def list_models(current_user=Depends(get_current_user_optional)):
    """List trained models with metrics"""
    models = cv_engine.list_models()
    return {"models": models}

@router.post("/models/{job_id}/export")
async def export_model(job_id: str, request: ExportRequest, current_user=Depends(get_current_user_optional)):
    """Export model to ONNX, Docker, FastAPI, etc. Returns ZIP URL."""
    result = cv_engine.export_model(job_id, request.formats)
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Export failed'))

    return result

@router.get("/export/{job_id}/download")
async def download_export(job_id: str, current_user=Depends(get_current_user_optional)):
    """Download the generated export ZIP"""
    zip_path = os.path.join("cv_exports", f"datavision_model_{job_id}.zip")
    
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Export package not found. Run export first.")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"datavision_cv_{job_id}.zip"
    )

@router.post("/models/{job_id}/deploy")
async def deploy_model(job_id: str, current_user=Depends(get_current_user_optional)):
    """Mock endpoint for model deployment"""
    progress = cv_engine.get_training_progress(job_id)
    model_path = progress.get('model_path')

    if not model_path:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"success": True, "message": "Model deployed successfully"}

@router.get("/models/{job_id}/artifacts/{filename}")
async def get_model_artifact(job_id: str, filename: str, current_user=Depends(get_current_user_optional)):
    """Serves YOLO visualization artifacts (e.g. confusion_matrix.png, results.png)"""
    artifact_path = os.path.join("cv_models", job_id, "train", filename)
    
    if not os.path.exists(artifact_path):
        dir_path = os.path.dirname(artifact_path)
        base_name = os.path.basename(artifact_path)
        
        fallbacks = [
            base_name.replace('.png', '.jpg'),
            base_name.replace('.jpg', '.png'),
            f"Box{base_name}",
            f"Mask{base_name}",
        ]
        
        for f in fallbacks:
            test_path = os.path.join(dir_path, f)
            if os.path.exists(test_path):
                artifact_path = test_path
                break
                
    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found")
        
    import mimetypes
    mime_type, _ = mimetypes.guess_type(artifact_path)
    if not mime_type:
        mime_type = "image/png"
        
    return FileResponse(artifact_path, media_type=mime_type)
