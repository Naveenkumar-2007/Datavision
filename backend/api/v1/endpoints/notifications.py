"""
API Endpoints for Notification System
FastAPI routes for settings, push tokens, insights, and agent management
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from utils.supabase_admin import get_supabase_admin, verify_workspace_membership
import logging

# Import agents
from agents.monitoring_agent import MonitoringAgent
from agents.forecast_agent import ForecastAgent
from agents.report_agent import ReportAgent
from agents.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["notifications"])
supabase = get_supabase_admin()


# ============================================================================
# MODELS
# ============================================================================

class NotificationSettings(BaseModel):
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

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract and validate JWT token (optional for development)"""
    
    # For development: if no auth header, use fallback
    if not authorization:
        logger.warning("No authorization header - using fallback for development")
        return "dev-user-fallback"
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            logger.warning("Invalid token - using fallback")
            return "dev-user-fallback"
        
        return user.user.id
        
    except Exception as e:
        logger.error(f"Auth error: {e} - using fallback")
        return "dev-user-fallback"


# ============================================================================
# NOTIFICATION SETTINGS ENDPOINTS
# ============================================================================

@router.get("/settings/{workspace_id}/{user_id}")
async def get_settings(
    workspace_id: str,
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get notification settings for a user in a workspace"""
    
    # Verify user can access their own settings
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get settings
    response = supabase.table('notification_settings').select('*').match({
        'workspace_id': workspace_id,
        'user_id': user_id
    }).execute()
    
    if not response.data or len(response.data) == 0:
        # Return defaults if no settings exist
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
    
    return response.data[0]


@router.patch("/settings/{workspace_id}/{user_id}")
async def update_settings(
    workspace_id: str,
    user_id: str,
    settings: NotificationSettings,
    current_user: str = Depends(get_current_user)
):
    """Update notification settings"""
    
    # Verify user can only update their own settings
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prepare update data (only include non-None fields)
    update_data = {
        'workspace_id': workspace_id,
        'user_id': user_id
    }
    
    if settings.email_notifications is not None:
        update_data['email_notifications'] = settings.email_notifications
    if settings.push_notifications is not None:
        update_data['push_notifications'] = settings.push_notifications
    if settings.weekly_reports is not None:
        update_data['weekly_reports'] = settings.weekly_reports
    if settings.ai_insights is not None:
        update_data['ai_insights'] = settings.ai_insights
    if settings.severity_threshold is not None:
        update_data['severity_threshold'] = settings.severity_threshold
    if settings.dnd_start is not None:
        update_data['dnd_start'] = settings.dnd_start
    if settings.dnd_end is not None:
        update_data['dnd_end'] = settings.dnd_end
    
    logger.info(f"Updating settings for user {user_id}: {update_data}")
    
    # Upsert settings
    response = supabase.table('notification_settings').upsert(update_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    logger.info(f"✓ Settings saved successfully: {response.data[0]}")
    
    return response.data[0]


# ============================================================================
# PUSH TOKEN ENDPOINTS
# ============================================================================

@router.post("/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user: str = Depends(get_current_user)
):
    """Register push notification token"""
    
    # Verify access
    if current_user != subscription.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not await verify_workspace_membership(current_user, subscription.workspace_id):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    
    # Insert token
    response = supabase.table('push_tokens').insert({
        'workspace_id': subscription.workspace_id,
        'user_id': subscription.user_id,
        'token': subscription.token,
        'platform': subscription.platform
    }).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save push token")
    
    return {"message": "Push subscription successful", "id": response.data[0]['id']}


@router.delete("/push/unsubscribe/{token_id}")
async def unsubscribe_push(
    token_id: str,
    current_user: str = Depends(get_current_user)
):
    """Remove push notification token"""
    
    # Verify token belongs to user
    token_response = supabase.table('push_tokens').select('user_id').eq('id', token_id).execute()
    
    if not token_response.data or token_response.data[0]['user_id'] != current_user:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete token
    supabase.table('push_tokens').delete().eq('id', token_id).execute()
    
    return {"message": "Unsubscribed successfully"}


# ============================================================================
# INSIGHTS ENDPOINTS
# ============================================================================

@router.get("/insights/{workspace_id}")
async def get_insights(
    workspace_id: str,
    limit: int = 20,
    current_user: str = Depends(get_current_user)
):
    """Get recent insights for a workspace"""
    
    # Verify access
    if not await verify_workspace_membership(current_user, workspace_id):
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    
    # Get insights
    response = supabase.table('ai_insights').select('*').eq(
        'workspace_id', workspace_id
    ).order('created_at', desc=True).limit(limit).execute()
    
    return response.data or []


# ============================================================================
# AGENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/agents/run/{agent_name}")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Manually trigger an agent run (for testing/debugging)
    Requires admin role
    """
    
    # Verify admin access
    membership = supabase.table('workspace_members').select('role').match({
        'workspace_id': request.workspace_id,
        'user_id': current_user
    }).execute()
    
    if not membership.data or membership.data[0]['role'] not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Select and run agent
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
    
    # Run agent asynchronously
    import asyncio
    asyncio.create_task(agent.run(request.workspace_id))
    
    return {"message": f"{agent_name} triggered for workspace {request.workspace_id}"}


@router.get("/agent-logs/{workspace_id}")
async def get_agent_logs(
    workspace_id: str,
    limit: int = 50,
    current_user: str = Depends(get_current_user)
):
    """Get agent execution logs (admin only)"""
    
    # Verify admin access
    membership = supabase.table('workspace_members').select('role').match({
        'workspace_id': workspace_id,
        'user_id': current_user
    }).execute()
    
    if not membership.data or membership.data[0]['role'] not in ['admin', 'owner']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get logs
    response = supabase.table('agent_logs').select('*').eq(
        'workspace_id', workspace_id
    ).order('executed_at', desc=True).limit(limit).execute()
    
    return response.data or []


# Export router
__all__ = ['router']
