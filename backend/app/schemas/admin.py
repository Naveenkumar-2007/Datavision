"""
Admin Schemas — Request/response models for admin operations.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AdminDashboardStats(BaseModel):
    """Dashboard statistics for the admin panel."""
    total_users: int = 0
    active_users: int = 0
    total_projects: int = 0
    total_models: int = 0
    total_datasets: int = 0
    total_experiments: int = 0
    total_training_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    total_api_keys: int = 0
    storage_used_bytes: int = 0


class AdminUserListItem(BaseModel):
    """User summary for admin user list."""
    id: str
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    roles: list[str] = []
    login_count: int = 0
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    """Admin-level user update."""
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    roles: Optional[list[str]] = None


class AuditLogEntry(BaseModel):
    """Audit log entry for admin view."""
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: dict = {}
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleInfo(BaseModel):
    """Role information."""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    hierarchy_level: int
    is_system: bool

    model_config = {"from_attributes": True}
