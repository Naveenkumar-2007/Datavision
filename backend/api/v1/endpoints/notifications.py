"""
API Endpoints for Notification System
FastAPI routes for settings, push tokens, insights, and agent management
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
import logging
import uuid

# Import agents
from agents.monitoring_agent import MonitoringAgent
from agents.forecast_agent import ForecastAgent
from agents.report_agent import ReportAgent
from agents.memory_agent import MemoryAgent

from database.db import get_db
from database.orm import NotificationSettings as NotificationSettingsModel, PushToken, WorkspaceMember, AIInsight, AgentLog
from database import get_current_user_optional, AuthUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["notifications"])

# ============================================================================
# MODELS
# ============================================================================

class NotificationSettingsReq(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    ai_insights: Optional[bool] = None
    severity_threshold: Optional[str] = None
    dnd_start: Optional[str] = None
    dnd_end: Optional[str] = None

class PushSubscription(BaseModel):
    workspace_id: str
    user_id: str
    token: str
    platform: Optional[str] = "web"

class AgentRunRequest(BaseModel):
    workspace_id: str

# ============================================================================
# AUTH HELPER
# ============================================================================

async def get_current_user_id(
    current_user: Optional[AuthUser] = Depends(get_current_user_optional)
) -> str:
    """Extract and validate user_id from auth"""
    if current_user:
        return current_user.id
    logger.warning("No valid authorization found - using fallback for development")
    return "dev-user-fallback"

async def verify_workspace_membership(user_id: str, workspace_id: str, db: AsyncSession) -> bool:
    if user_id == "dev-user-fallback": return True
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.user_id == uuid.UUID(user_id),
        WorkspaceMember.workspace_id == workspace_id
    )
    result = await db.scalar(stmt)
    return result is not None

# ============================================================================
# NOTIFICATION SETTINGS ENDPOINTS
# ============================================================================

@router.get("/settings/{workspace_id}/{user_id}")
async def get_settings(
    workspace_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if current_user_id != user_id and current_user_id != "dev-user-fallback":
        raise HTTPException(status_code=403, detail="Access denied")
        
    stmt = select(NotificationSettingsModel).where(
        NotificationSettingsModel.workspace_id == workspace_id,
        NotificationSettingsModel.user_id == uuid.UUID(user_id)
    )
    settings = await db.scalar(stmt)
    
    if not settings:
        return {
            'workspace_id': workspace_id,
            'user_id': user_id,
            'email_notifications': True,
            'push_notifications': False,
            'weekly_reports': True,
            'ai_insights': True,
            'severity_threshold': 'medium',
            'dnd_start': None,
            'dnd_end': None
        }
        
    return {
        'workspace_id': settings.workspace_id,
        'user_id': str(settings.user_id),
        'email_notifications': settings.email_notifications,
        'push_notifications': settings.push_notifications,
        'weekly_reports': settings.weekly_reports,
        'ai_insights': settings.ai_insights,
        'severity_threshold': settings.severity_threshold,
        'dnd_start': settings.dnd_start,
        'dnd_end': settings.dnd_end
    }

@router.patch("/settings/{workspace_id}/{user_id}")
async def update_settings(
    workspace_id: str,
    user_id: str,
    settings: NotificationSettingsReq,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if current_user_id != user_id and current_user_id != "dev-user-fallback":
        raise HTTPException(status_code=403, detail="Access denied")
        
    stmt = select(NotificationSettingsModel).where(
        NotificationSettingsModel.workspace_id == workspace_id,
        NotificationSettingsModel.user_id == uuid.UUID(user_id)
    )
    db_settings = await db.scalar(stmt)
    
    if not db_settings:
        db_settings = NotificationSettingsModel(workspace_id=workspace_id, user_id=uuid.UUID(user_id))
        db.add(db_settings)
        
    if settings.email_notifications is not None: db_settings.email_notifications = settings.email_notifications
    if settings.push_notifications is not None: db_settings.push_notifications = settings.push_notifications
    if settings.weekly_reports is not None: db_settings.weekly_reports = settings.weekly_reports
    if settings.ai_insights is not None: db_settings.ai_insights = settings.ai_insights
    if settings.severity_threshold is not None: db_settings.severity_threshold = settings.severity_threshold
    if settings.dnd_start is not None: db_settings.dnd_start = settings.dnd_start
    if settings.dnd_end is not None: db_settings.dnd_end = settings.dnd_end
    
    await db.commit()
    return {
        'workspace_id': db_settings.workspace_id,
        'user_id': str(db_settings.user_id),
        'email_notifications': db_settings.email_notifications,
        'push_notifications': db_settings.push_notifications,
        'weekly_reports': db_settings.weekly_reports,
        'ai_insights': db_settings.ai_insights,
        'severity_threshold': db_settings.severity_threshold,
        'dnd_start': db_settings.dnd_start,
        'dnd_end': db_settings.dnd_end
    }

@router.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if current_user_id != subscription.user_id and current_user_id != "dev-user-fallback":
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not await verify_workspace_membership(current_user_id, subscription.workspace_id, db):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
    token = PushToken(
        workspace_id=subscription.workspace_id,
        user_id=uuid.UUID(subscription.user_id),
        token=subscription.token,
        platform=subscription.platform
    )
    db.add(token)
    await db.commit()
    
    return {"message": "Push subscription successful", "id": str(token.id)}

@router.delete("/push/unsubscribe/{token_id}")
async def unsubscribe_push(
    token_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PushToken).where(PushToken.id == uuid.UUID(token_id))
    token = await db.scalar(stmt)
    
    if not token or (str(token.user_id) != current_user_id and current_user_id != "dev-user-fallback"):
        raise HTTPException(status_code=403, detail="Access denied")
        
    await db.delete(token)
    await db.commit()
    
    return {"message": "Unsubscribed successfully"}

@router.get("/insights/{workspace_id}")
async def get_insights(
    workspace_id: str,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if not await verify_workspace_membership(current_user_id, workspace_id, db):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
        
    stmt = select(AIInsight).where(AIInsight.workspace_id == workspace_id).order_by(AIInsight.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    return [{
        "id": str(i.id),
        "workspace_id": i.workspace_id,
        "title": i.title,
        "description": i.description,
        "insight_type": i.insight_type,
        "created_at": i.created_at
    } for i in insights]

@router.post("/agents/run/{agent_name}")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if current_user_id != "dev-user-fallback":
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == request.workspace_id,
            WorkspaceMember.user_id == uuid.UUID(current_user_id)
        )
        membership = await db.scalar(stmt)
        if not membership or membership.role not in ['admin', 'owner']:
            raise HTTPException(status_code=403, detail="Admin access required")
            
    agent = None
    if agent_name == 'MonitoringAgent':
        agent = MonitoringAgent()
    elif agent_name == 'ForecastAgent':
        agent = ForecastAgent()
    elif agent_name == 'ReportAgent':
        agent = ReportAgent()
    elif agent_name == 'MemoryAgent':
        agent = MemoryAgent()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_name}")
        
    import asyncio
    asyncio.create_task(agent.run(request.workspace_id))
    
    return {"message": f"{agent_name} triggered for workspace {request.workspace_id}"}

@router.get("/agent-logs/{workspace_id}")
async def get_agent_logs(
    workspace_id: str,
    limit: int = 50,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    if current_user_id != "dev-user-fallback":
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == uuid.UUID(current_user_id)
        )
        membership = await db.scalar(stmt)
        if not membership or membership.role not in ['admin', 'owner']:
            raise HTTPException(status_code=403, detail="Admin access required")
            
    stmt = select(AgentLog).where(AgentLog.workspace_id == workspace_id).order_by(AgentLog.executed_at.desc()).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [{
        "id": str(l.id),
        "workspace_id": l.workspace_id,
        "agent_name": l.agent_name,
        "status": l.status,
        "message": l.message,
        "executed_at": l.executed_at
    } for l in logs]

# Export router
__all__ = ['router']
