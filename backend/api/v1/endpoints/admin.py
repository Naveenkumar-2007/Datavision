"""
🛡️ ADMIN DASHBOARD — Secure Platform Administration
=====================================================
Password-protected admin panel with user management,
system health, analytics, and platform controls.
Uses a separate admin password (bcrypt hashed in .env),
NOT the normal user auth system.
"""

import os
import sys
import uuid
import logging
import bcrypt
import platform
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from database.db import get_db, AsyncSessionLocal
from database.orm import (
    UserProfile, Conversation, Message, UserFile, UserQuery,
    ActivityLog, WorkspaceMember, DataConnection, Dashboard
)
from core.auth import create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)

# ── Admin Password (bcrypt hash stored in env) ──
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "$2b$12$igNMKjsYUAQsbmJBjYsLPuz7bhJ8HoV9X86W.n3R48LogJ6qLuQ0y"  # DataVision@Admin2026
)


# ── Request/Response Models ──

class AdminLoginRequest(BaseModel):
    password: str

class UpdateUserRoleRequest(BaseModel):
    role: str  # authenticated, admin, banned

class BroadcastRequest(BaseModel):
    title: str
    message: str


# ── Admin Auth Dependency ──

async def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the request has a valid admin JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Not an admin token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")


# ══════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════

@router.post("/login")
async def admin_login(req: AdminLoginRequest):
    """Authenticate with the platform admin password."""
    try:
        is_valid = bcrypt.checkpw(
            req.password.encode("utf-8"),
            ADMIN_PASSWORD_HASH.encode("utf-8")
        )
    except Exception:
        is_valid = False
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    # Issue a super_admin JWT (expires in 4 hours)
    token = create_access_token(
        data={"sub": "admin", "role": "super_admin", "email": "admin@datavision.app"},
        expires_delta=timedelta(hours=4)
    )
    
    return {
        "success": True,
        "token": token,
        "message": "Admin authenticated successfully",
        "expires_in": 240  # minutes
    }


@router.get("/stats")
async def get_platform_stats(
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get platform-wide statistics."""
    try:
        total_users = await db.scalar(select(func.count()).select_from(UserProfile)) or 0
        total_files = await db.scalar(select(func.count()).select_from(UserFile)) or 0
        total_convs = await db.scalar(select(func.count()).select_from(Conversation)) or 0
        total_msgs = await db.scalar(select(func.count()).select_from(Message)) or 0
        total_queries = await db.scalar(select(func.count()).select_from(UserQuery)) or 0
        total_connections = await db.scalar(select(func.count()).select_from(DataConnection)) or 0
        total_dashboards = await db.scalar(select(func.count()).select_from(Dashboard)) or 0
        
        # Active users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_today = await db.scalar(
            select(func.count(func.distinct(UserQuery.user_id))).where(UserQuery.created_at >= today)
        ) or 0
        
        # New users this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = await db.scalar(
            select(func.count()).select_from(UserProfile).where(UserProfile.created_at >= week_ago)
        ) or 0
        
        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_files": total_files,
                "total_conversations": total_convs,
                "total_messages": total_msgs,
                "total_queries": total_queries,
                "active_today": active_today,
                "data_connections": total_connections,
                "dashboards": total_dashboards,
                "new_users_this_week": new_users_week,
            }
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"success": True, "stats": {
            "total_users": 0, "total_files": 0, "total_conversations": 0,
            "total_messages": 0, "total_queries": 0, "active_today": 0,
            "data_connections": 0, "dashboards": 0, "new_users_this_week": 0
        }}


@router.get("/users")
async def list_all_users(
    search: Optional[str] = None,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """List all registered users with their details."""
    try:
        stmt = select(UserProfile)
        if search:
            stmt = stmt.where(or_(
                UserProfile.email.ilike(f"%{search}%"),
                UserProfile.full_name.ilike(f"%{search}%")
            ))
        stmt = stmt.order_by(UserProfile.created_at.desc())
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        user_list = []
        for u in users:
            file_count = await db.scalar(
                select(func.count()).select_from(UserFile).where(UserFile.user_id == u.id)
            ) or 0
            
            conv_count = await db.scalar(
                select(func.count()).select_from(Conversation).where(Conversation.user_id == u.id)
            ) or 0
            
            user_list.append({
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name or "",
                "role": getattr(u, 'role', 'authenticated'),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "file_count": file_count,
                "conversation_count": conv_count,
                "avatar": (u.full_name or u.email or "?")[0].upper(),
            })
        
        return {"success": True, "users": user_list, "total": len(user_list)}
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return {"success": True, "users": [], "total": 0}


@router.get("/users/{target_user_id}")
async def get_user_detail(
    target_user_id: str,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed info about a specific user."""
    try:
        uid = uuid.UUID(target_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    file_count = await db.scalar(select(func.count()).select_from(UserFile).where(UserFile.user_id == uid)) or 0
    conv_count = await db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == uid)) or 0
    query_count = await db.scalar(select(func.count()).select_from(UserQuery).where(UserQuery.user_id == uid)) or 0
    
    return {
        "success": True,
        "user": {
            "id": str(user.id), "email": user.email, "full_name": user.full_name,
            "role": getattr(user, 'role', 'authenticated'),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "stats": {"files": file_count, "conversations": conv_count, "queries": query_count}
    }


@router.delete("/users/{target_user_id}")
async def delete_user(
    target_user_id: str,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user and all their data (CASCADE)."""
    try:
        uid = uuid.UUID(target_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    email = user.email
    await db.delete(user)
    await db.commit()
    
    return {"success": True, "message": f"User {email} and all associated data deleted."}


@router.put("/users/{target_user_id}/role")
async def update_user_role(
    target_user_id: str,
    req: UpdateUserRoleRequest,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Change a user's role."""
    valid_roles = {"authenticated", "admin", "banned"}
    if req.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(valid_roles)}")
    
    try:
        uid = uuid.UUID(target_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if hasattr(user, 'role'):
        user.role = req.role
    await db.commit()
    
    return {"success": True, "message": f"User role updated to {req.role}"}


@router.get("/system")
async def get_system_health(admin: dict = Depends(verify_admin_token)):
    """Get system health information."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_info = {
            "cpu_usage_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
        }
    except ImportError:
        system_info = {
            "cpu_usage_percent": 0, "memory_total_gb": 0, "memory_used_gb": 0,
            "memory_percent": 0, "disk_total_gb": 0, "disk_used_gb": 0, "disk_percent": 0,
        }
    
    db_status = "connected"
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(select(func.count(UserProfile.id)))
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
    
    return {
        "success": True,
        "system": {
            **system_info,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "db_status": db_status,
            "uptime": "Running",
            "environment": "production" if "hf.space" in os.environ.get("APP_URL", "") else "development",
        }
    }


@router.get("/activity")
async def get_global_activity(
    limit: int = 100,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Get global activity feed across all users."""
    try:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ActivityLog).order_by(ActivityLog.timestamp.desc())
            .limit(limit).options(selectinload(ActivityLog.user))
        )
        result = await db.execute(stmt)
        logs = result.scalars().all()
        
        activities = []
        for log in logs:
            name = log.user.full_name if log.user and log.user.full_name else log.user_name or "System"
            activities.append({
                "id": str(log.id),
                "user_name": name,
                "user_email": log.user.email if log.user else "",
                "action": log.action,
                "detail": log.detail,
                "timestamp": log.timestamp.isoformat()
            })
        
        return {"success": True, "activities": activities}
    except Exception as e:
        logger.error(f"Error fetching activity: {e}")
        return {"success": True, "activities": []}


@router.post("/broadcast")
async def broadcast_announcement(
    req: BroadcastRequest,
    admin: dict = Depends(verify_admin_token),
    db: AsyncSession = Depends(get_db)
):
    """Send a system-wide announcement (stored as activity log)."""
    log = ActivityLog(
        user_id=None,
        user_name="System Admin",
        action="broadcast",
        detail=f"📢 {req.title}: {req.message}"
    )
    db.add(log)
    await db.commit()
    
    return {"success": True, "message": "Broadcast sent to activity feed"}
