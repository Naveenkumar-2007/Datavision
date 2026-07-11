"""
Deploy API — ML Model Deployment Endpoints
============================================
POST   /deploy/{model_id}           — Deploy a trained model
GET    /deploy/list                 — List user's deployments
GET    /deploy/{deploy_id}/status   — Health check for a deployment
DELETE /deploy/{deploy_id}          — Undeploy / deactivate
POST   /deploy/predict/{deploy_id}  — Run inference
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import datetime
import logging

from ml.model_deployer import get_model_deployer
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.orm import MLDeployment
from core.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deploy", tags=["Deploy"])


class DeployRequest(BaseModel):
    version: Optional[int] = None


class PredictRequest(BaseModel):
    data: Dict[str, Any]


@router.post("/{model_id}")
async def deploy_model(
    model_id: str,
    request_obj: Request,
    request: DeployRequest = None,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Deploy a trained model to an active endpoint and save to DB"""
    user_id = x_user_id or model_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user context")

    await check_rate_limit(request_obj, "deploy", user_id)

    try:
        deployer = get_model_deployer()
        deployment = deployer.deploy_model(user_id, version=request.version if request else None)

        # Save to PostgreSQL
        new_db_deployment = MLDeployment(
            deploy_id=deployment['deploy_id'],
            user_id=user_id,
            model_name=deployment['model_name'],
            task_type=deployment['task_type'],
            version=deployment['version'],
            api_key=deployment['api_key'],
            status='active'
        )
        db.add(new_db_deployment)
        await db.commit()

        return {"success": True, "deployment": deployment}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Deploy failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_deployments(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """List all active deployments for a user from PostgreSQL"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="Missing user context")

    try:
        stmt = select(MLDeployment).where(MLDeployment.user_id == x_user_id)
        result = await db.execute(stmt)
        deployments = result.scalars().all()

        deployments_list = []
        for d in deployments:
            deployments_list.append({
                "deploy_id": d.deploy_id,
                "model_name": d.model_name,
                "task_type": d.task_type,
                "version": d.version,
                "api_key": d.api_key,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "endpoint": f"/api/v1/deploy/predict/{d.deploy_id}"
            })

        return {"success": True, "deployments": deployments_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{deploy_id}/status")
async def deployment_status(
    deploy_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
):
    """Get health / metadata for a single deployment"""
    try:
        deployer = get_model_deployer()
        status = deployer.get_deployment_status(deploy_id)
        return {"success": True, **status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{deploy_id}")
async def undeploy_model(
    deploy_id: str,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a deployment"""
    user_id = x_user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user context")

    try:
        deployer = get_model_deployer()
        result = deployer.undeploy(deploy_id, user_id=user_id)

        # Update PostgreSQL
        try:
            stmt = select(MLDeployment).where(MLDeployment.deploy_id == deploy_id)
            db_result = await db.execute(stmt)
            db_deployment = db_result.scalars().first()
            if db_deployment:
                db_deployment.status = "inactive"
                await db.commit()
        except Exception as db_err:
            logger.warning(f"DB update for undeploy failed: {db_err}")

        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/{deploy_id}")
async def predict_model(
    deploy_id: str,
    request: PredictRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Run inference against a deployed model"""
    try:
        deployer = get_model_deployer()
        result = deployer.predict(deploy_id, request.data, api_key=x_api_key)
        return {"success": True, "prediction": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
