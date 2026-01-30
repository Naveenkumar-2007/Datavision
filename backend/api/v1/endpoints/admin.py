"""
Admin Endpoints
Admin-only operations for user management and platform statistics
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta

from database import (
    get_supabase_admin_client,
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
    current_user: AuthUser = Depends(get_admin_user)
):
    """
    List all users (admin only).
    Supports pagination and filtering.
    """
    client = get_supabase_admin_client()
    
    # Build query
    query = client.table("profiles").select("*", count="exact")
    
    # Apply filters
    if search:
        query = query.or_(f"email.ilike.%{search}%,full_name.ilike.%{search}%")
    
    if role:
        query = query.eq("role", role)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1).order("created_at", desc=True)
    
    result = query.execute()
    
    return {
        "success": True,
        "users": result.data or [],
        "total": result.count or 0,
        "page": page,
        "per_page": per_page
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user)
):
    """
    Get a specific user's details (admin only).
    """
    client = get_supabase_admin_client()
    
    result = client.table("profiles").select("*").eq("id", user_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's stats
    files_result = client.table("user_files").select("id", count="exact").eq("user_id", user_id).execute()
    conversations_result = client.table("conversations").select("id", count="exact").eq("user_id", user_id).execute()
    queries_result = client.table("user_queries").select("id", count="exact").eq("user_id", user_id).execute()
    
    return {
        "success": True,
        "user": result.data,
        "stats": {
            "files_count": files_result.count or 0,
            "conversations_count": conversations_result.count or 0,
            "queries_count": queries_result.count or 0
        }
    }


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: AuthUser = Depends(get_super_admin_user)
):
    """
    Update a user's role (super admin only).
    """
    if request.role not in ["user", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Prevent self-demotion
    if user_id == current_user.id and request.role != "super_admin":
        raise HTTPException(status_code=400, detail="Cannot demote yourself")
    
    client = get_supabase_admin_client()
    
    result = client.table("profiles").update({"role": request.role}).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": f"User role updated to {request.role}",
        "user": result.data[0]
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: AuthUser = Depends(get_super_admin_user)
):
    """
    Delete a user account (super admin only).
    This will cascade delete all user data.
    """
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    client = get_supabase_admin_client()
    
    # Check if user exists
    user_result = client.table("profiles").select("id, role").eq("id", user_id).single().execute()
    
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting other super admins
    if user_result.data.get("role") == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot delete super admin users")
    
    # Delete from auth.users (this will cascade to profiles due to FK)
    try:
        client.auth.admin.delete_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
    
    return {
        "success": True,
        "message": "User deleted successfully"
    }


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user)
):
    """
    Deactivate a user account (admin only).
    User will not be able to login.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    client = get_supabase_admin_client()
    
    result = client.table("profiles").update({"is_active": False}).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User deactivated"
    }


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: AuthUser = Depends(get_admin_user)
):
    """
    Activate a deactivated user account (admin only).
    """
    client = get_supabase_admin_client()
    
    result = client.table("profiles").update({"is_active": True}).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User activated"
    }


@router.get("/stats")
async def get_platform_stats(
    current_user: AuthUser = Depends(get_admin_user)
):
    """
    Get platform-wide statistics (admin only).
    """
    client = get_supabase_admin_client()
    
    # Get counts
    users_result = client.table("profiles").select("id", count="exact").execute()
    files_result = client.table("user_files").select("id", count="exact").execute()
    conversations_result = client.table("conversations").select("id", count="exact").execute()
    queries_result = client.table("user_queries").select("id", count="exact").execute()
    
    # Get recent activity (last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    
    new_users_result = client.table("profiles").select("id", count="exact").gte("created_at", week_ago).execute()
    new_queries_result = client.table("user_queries").select("id", count="exact").gte("created_at", week_ago).execute()
    
    # Get storage usage
    storage_result = client.rpc("get_user_storage_used", {"p_user_id": None}).execute()
    
    # Get user role distribution
    role_dist = client.table("profiles").select("role").execute()
    role_counts = {}
    for row in (role_dist.data or []):
        role = row.get("role", "user")
        role_counts[role] = role_counts.get(role, 0) + 1
    
    return {
        "success": True,
        "stats": {
            "total_users": users_result.count or 0,
            "total_files": files_result.count or 0,
            "total_conversations": conversations_result.count or 0,
            "total_queries": queries_result.count or 0,
            "new_users_last_7_days": new_users_result.count or 0,
            "queries_last_7_days": new_queries_result.count or 0,
            "role_distribution": role_counts
        }
    }


@router.get("/admin-users")
async def list_admin_users(
    current_user: AuthUser = Depends(get_super_admin_user)
):
    """
    List all admin users (super admin only).
    """
    client = get_supabase_admin_client()
    
    result = client.table("admin_users")\
        .select("*, profiles(email, full_name)")\
        .eq("is_active", True)\
        .execute()
    
    return {
        "success": True,
        "admin_users": result.data or []
    }


@router.post("/grant-admin")
async def grant_admin_access(
    request: AdminGrantRequest,
    current_user: AuthUser = Depends(get_super_admin_user)
):
    """
    Grant admin access to a user (super admin only).
    """
    if request.admin_role not in ["moderator", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Invalid admin role")
    
    client = get_supabase_admin_client()
    
    # Check if user exists
    user_result = client.table("profiles").select("id").eq("id", request.user_id).single().execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user role in profiles
    client.table("profiles").update({"role": request.admin_role}).eq("id", request.user_id).execute()
    
    # Create or update admin_users entry
    admin_data = {
        "user_id": request.user_id,
        "admin_role": request.admin_role,
        "permissions": request.permissions or {
            "can_view_users": True,
            "can_edit_users": request.admin_role in ["admin", "super_admin"],
            "can_delete_users": request.admin_role == "super_admin",
            "can_view_analytics": True
        },
        "granted_by": current_user.id,
        "notes": request.notes,
        "is_active": True
    }
    
    result = client.table("admin_users").upsert(admin_data, on_conflict="user_id").execute()
    
    return {
        "success": True,
        "message": f"Admin access granted with role: {request.admin_role}",
        "admin_user": result.data[0] if result.data else None
    }


@router.delete("/revoke-admin/{user_id}")
async def revoke_admin_access(
    user_id: str,
    current_user: AuthUser = Depends(get_super_admin_user)
):
    """
    Revoke admin access from a user (super admin only).
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot revoke your own admin access")
    
    client = get_supabase_admin_client()
    
    # Update user role back to 'user'
    client.table("profiles").update({"role": "user"}).eq("id", user_id).execute()
    
    # Deactivate admin_users entry
    client.table("admin_users").update({"is_active": False}).eq("user_id", user_id).execute()
    
    return {
        "success": True,
        "message": "Admin access revoked"
    }
