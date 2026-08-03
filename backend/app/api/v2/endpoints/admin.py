"""
Admin API Endpoints — /api/v2/admin/*

All endpoints require 'admin' role or higher.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.admin_service import AdminService
from app.core.permissions import require_role, AuthenticatedUser
from app.schemas.admin import (
    AdminDashboardStats,
    AdminUserListItem,
    AdminUserUpdate,
    AuditLogEntry,
    RoleInfo,
)
from app.schemas.common import PaginationParams, PaginatedResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Dashboard ───────────────────────────────────────────────────────

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    user: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get platform-wide dashboard statistics."""
    service = AdminService(db)
    return await service.get_dashboard_stats()


# ── User Management ─────────────────────────────────────────────────

@router.get("/users", response_model=PaginatedResponse[AdminUserListItem])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination, search, and filters."""
    params = PaginationParams(page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    service = AdminService(db)
    items, total = await service.list_users(params, search=search, role_filter=role, is_active=is_active)
    return PaginatedResponse.create(items=items, total=total, params=params)


@router.get("/users/{user_id}", response_model=AdminUserListItem)
async def get_user(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single user's details."""
    service = AdminService(db)
    try:
        return await service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/users/{user_id}", response_model=AdminUserListItem)
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile or roles."""
    service = AdminService(db)
    try:
        return await service.update_user(user_id, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a user."""
    # Prevent self-deletion
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account via admin API",
        )
    service = AdminService(db)
    await service.soft_delete_user(user_id)
    return MessageResponse(message=f"User {user_id} has been deactivated")


@router.post("/users/{user_id}/restore", response_model=MessageResponse)
async def restore_user(
    user_id: str,
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Restore a soft-deleted user."""
    service = AdminService(db)
    await service.restore_user(user_id)
    return MessageResponse(message=f"User {user_id} has been restored")


# ── Roles ───────────────────────────────────────────────────────────

@router.get("/roles", response_model=list[RoleInfo])
async def list_roles(
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all available roles."""
    service = AdminService(db)
    return await service.list_roles()


# ── Audit Logs ──────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogEntry])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    admin: AuthenticatedUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """View audit logs with pagination and filters."""
    params = PaginationParams(page=page, page_size=page_size)
    service = AdminService(db)
    items, total = await service.get_audit_logs(
        params, user_id=user_id, action=action, resource_type=resource_type
    )
    return PaginatedResponse.create(items=items, total=total, params=params)
