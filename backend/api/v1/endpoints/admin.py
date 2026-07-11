"""
Admin Endpoints
Admin-only operations for user management and platform statistics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from database.db import get_db
from database.orm import UserProfile, UserFile, Conversation, UserQuery, AdminUser

from database import (
    get_admin_user,
    get_super_admin_user,
    AuthUser,
    UserRole
)

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UpdateRoleRequest(BaseModel):
    role: str  # 'user', 'admin', 'super_admin'


class AdminGrantRequest(BaseModel):
    user_id: str
    admin_role: str = "moderator"  # 'moderator', 'admin', 'super_admin'
    permissions: Optional[dict] = None
    notes: Optional[str] = None


class UserListResponse(BaseModel):
    users: List[dict]
    total: int
    page: int
    per_page: int


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get("/users")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserProfile)
    
    if search:
        stmt = stmt.where(or_(UserProfile.email.ilike(f"%{search}%"), UserProfile.full_name.ilike(f"%{search}%")))
    if role:
        stmt = stmt.where(UserProfile.role == role)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0
    
    stmt = stmt.order_by(UserProfile.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return {
        "success": True,
        "users": [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "role": u.role, "created_at": u.created_at} for u in users],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserProfile).where(UserProfile.id == uuid.UUID(user_id))
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    files_count = await db.scalar(select(func.count()).select_from(UserFile).where(UserFile.user_id == user.id))
    conv_count = await db.scalar(select(func.count()).select_from(Conversation).where(Conversation.user_id == user.id))
    queries_count = await db.scalar(select(func.count()).select_from(UserQuery).where(UserQuery.user_id == user.id))
    
    return {
        "success": True,
        "user": {"id": str(user.id), "email": user.email, "full_name": user.full_name, "role": user.role},
        "stats": {
            "files_count": files_count or 0,
            "conversations_count": conv_count or 0,
            "queries_count": queries_count or 0
        }
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: AuthUser = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if request.role not in ["user", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    if user_id == current_user.id and request.role != "super_admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
        
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = request.role
    await db.commit()
    
    return {
        "success": True,
        "message": f"User role updated to {request.role}",
        "user": {"id": str(user.id), "email": user.email, "role": user.role}
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: AuthUser = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot delete super admin users")
        
    await db.delete(user)
    await db.commit()
    
    return {"success": True, "message": "User deleted successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"success": True, "message": "User deactivated"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    return {"success": True, "message": "User activated"}


@router.get("/stats")
async def get_platform_stats(
    current_user: AuthUser = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    total_users = await db.scalar(select(func.count()).select_from(UserProfile))
    total_files = await db.scalar(select(func.count()).select_from(UserFile))
    total_convs = await db.scalar(select(func.count()).select_from(Conversation))
    total_queries = await db.scalar(select(func.count()).select_from(UserQuery))
    
    week_ago = datetime.now() - timedelta(days=7)
    new_users = await db.scalar(select(func.count()).select_from(UserProfile).where(UserProfile.created_at >= week_ago))
    new_queries = await db.scalar(select(func.count()).select_from(UserQuery).where(UserQuery.created_at >= week_ago))
    
    roles = (await db.execute(select(UserProfile.role))).scalars().all()
    role_counts = {}
    for r in roles:
        role_counts[r] = role_counts.get(r, 0) + 1
        
    return {
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_files": total_files,
            "total_conversations": total_convs,
            "total_queries": total_queries,
            "new_users_last_7_days": new_users,
            "queries_last_7_days": new_queries,
            "role_distribution": role_counts
        }
    }


@router.get("/admin-users")
async def list_admin_users(
    current_user: AuthUser = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    stmt = select(AdminUser).options(selectinload(AdminUser.user)).where(AdminUser.is_active == True)
    admins = (await db.execute(stmt)).scalars().all()
    
    return {
        "success": True,
        "admin_users": [{
            "id": str(a.id), 
            "user_id": str(a.user_id),
            "admin_role": a.admin_role,
            "profiles": {"email": a.user.email if a.user else None, "full_name": a.user.full_name if a.user else None}
        } for a in admins]
    }


@router.post("/grant-admin")
async def grant_admin_access(
    request: AdminGrantRequest,
    current_user: AuthUser = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if request.admin_role not in ["moderator", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid admin role")
        
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(request.user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.role = request.admin_role
    
    admin_user = (await db.execute(select(AdminUser).where(AdminUser.user_id == user.id))).scalar_one_or_none()
    if not admin_user:
        admin_user = AdminUser(user_id=user.id)
        db.add(admin_user)
        
    admin_user.admin_role = request.admin_role
    admin_user.permissions = request.permissions or {
        "can_view_users": True,
        "can_edit_users": request.admin_role in ["admin", "super_admin"],
        "can_delete_users": request.admin_role == "super_admin",
        "can_view_analytics": True
    }
    admin_user.granted_by = uuid.UUID(current_user.id)
    admin_user.notes = request.notes
    admin_user.is_active = True
    
    await db.commit()
    
    return {"success": True, "message": f"Admin access granted with role: {request.admin_role}"}


@router.delete("/revoke-admin/{user_id}")
async def revoke_admin_access(
    user_id: str,
    current_user: AuthUser = Depends(get_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot revoke your own admin access")
        
    user = (await db.execute(select(UserProfile).where(UserProfile.id == uuid.UUID(user_id)))).scalar_one_or_none()
    if user:
        user.role = "user"
        
    admin_user = (await db.execute(select(AdminUser).where(AdminUser.user_id == uuid.UUID(user_id)))).scalar_one_or_none()
    if admin_user:
        admin_user.is_active = False
        
    await db.commit()
    return {"success": True, "message": "Admin access revoked"}
