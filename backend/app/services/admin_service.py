"""
Admin Service — Business logic for admin operations.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.auth import UserSession
from app.models.rbac import Role, UserRole
from app.models.ml import Project, Dataset, Experiment, MLModel, TrainingJob
from app.models.platform import AuditLog, APIKey, FileUpload
from app.schemas.admin import (
    AdminDashboardStats,
    AdminUserListItem,
    AdminUserUpdate,
    AuditLogEntry,
    RoleInfo,
)
from app.schemas.common import PaginationParams

logger = logging.getLogger(__name__)


class AdminService:
    """Admin operations — user management, stats, audit logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Dashboard ───────────────────────────────────────────────────

    async def get_dashboard_stats(self) -> AdminDashboardStats:
        """Get platform-wide statistics for the admin dashboard."""
        stats = AdminDashboardStats()

        # User counts
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.is_deleted == False)
        )
        stats.total_users = result.scalar() or 0

        result = await self.db.execute(
            select(func.count()).select_from(User)
            .where(User.is_deleted == False, User.is_active == True)
        )
        stats.active_users = result.scalar() or 0

        # ML counts (wrapped in try/except for tables that may not exist yet)
        for model_cls, attr_name in [
            (Project, "total_projects"),
            (MLModel, "total_models"),
            (Dataset, "total_datasets"),
            (Experiment, "total_experiments"),
        ]:
            try:
                result = await self.db.execute(
                    select(func.count()).select_from(model_cls)
                )
                setattr(stats, attr_name, result.scalar() or 0)
            except Exception:
                pass

        # Training job counts
        try:
            result = await self.db.execute(
                select(func.count()).select_from(TrainingJob)
            )
            stats.total_training_jobs = result.scalar() or 0

            result = await self.db.execute(
                select(func.count()).select_from(TrainingJob)
                .where(TrainingJob.status == "pending")
            )
            stats.pending_jobs = result.scalar() or 0

            result = await self.db.execute(
                select(func.count()).select_from(TrainingJob)
                .where(TrainingJob.status == "running")
            )
            stats.running_jobs = result.scalar() or 0
        except Exception:
            pass

        # API keys
        try:
            result = await self.db.execute(
                select(func.count()).select_from(APIKey)
                .where(APIKey.is_active == True)
            )
            stats.total_api_keys = result.scalar() or 0
        except Exception:
            pass

        # Storage
        try:
            result = await self.db.execute(
                select(func.coalesce(func.sum(FileUpload.file_size), 0))
                .select_from(FileUpload)
            )
            stats.storage_used_bytes = result.scalar() or 0
        except Exception:
            pass

        return stats

    # ── User Management ─────────────────────────────────────────────

    async def list_users(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        role_filter: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[AdminUserListItem], int]:
        """List users with pagination, search, and filters."""

        query = select(User).where(User.is_deleted == False)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_pattern)) |
                (User.full_name.ilike(search_pattern))
            )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply sorting and pagination
        sort_column = getattr(User, params.sort_by, User.created_at)
        if params.sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        query = query.offset(params.offset).limit(params.page_size)

        result = await self.db.execute(query)
        users = result.scalars().all()

        # Build response with roles
        items = []
        for user in users:
            roles = await self._get_user_roles(user.id)
            items.append(AdminUserListItem(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                company_name=user.company_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                roles=roles,
                login_count=user.login_count or 0,
                last_login_at=user.last_login_at,
                created_at=user.created_at,
            ))

        return items, total

    async def get_user(self, user_id: str) -> AdminUserListItem:
        """Get a single user by ID."""
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(User).where(User.id == uid, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        roles = await self._get_user_roles(user.id)
        return AdminUserListItem(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_name=user.company_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            roles=roles,
            login_count=user.login_count or 0,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    async def update_user(self, user_id: str, updates: AdminUserUpdate) -> AdminUserListItem:
        """Update a user's profile or roles (admin action)."""
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(User).where(User.id == uid, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Apply field updates
        if updates.full_name is not None:
            user.full_name = updates.full_name
        if updates.company_name is not None:
            user.company_name = updates.company_name
        if updates.is_active is not None:
            user.is_active = updates.is_active
        if updates.is_verified is not None:
            user.is_verified = updates.is_verified

        # Update roles if provided
        if updates.roles is not None:
            # Remove existing roles
            await self.db.execute(
                update(UserRole)
                .where(UserRole.user_id == uid)
                .values(is_active=False)
            )
            # Assign new roles
            for role_name in updates.roles:
                role_result = await self.db.execute(
                    select(Role).where(Role.name == role_name)
                )
                role = role_result.scalar_one_or_none()
                if role:
                    self.db.add(UserRole(
                        user_id=uid,
                        role_id=role.id,
                        is_active=True,
                    ))

        await self.db.commit()
        return await self.get_user(user_id)

    async def soft_delete_user(self, user_id: str):
        """Soft delete a user."""
        uid = uuid.UUID(user_id)
        await self.db.execute(
            update(User)
            .where(User.id == uid)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(timezone.utc),
                is_active=False,
            )
        )
        await self.db.commit()
        logger.info(f"User {user_id} soft deleted")

    async def restore_user(self, user_id: str):
        """Restore a soft-deleted user."""
        uid = uuid.UUID(user_id)
        await self.db.execute(
            update(User)
            .where(User.id == uid)
            .values(is_deleted=False, deleted_at=None, is_active=True)
        )
        await self.db.commit()
        logger.info(f"User {user_id} restored")

    # ── Roles ───────────────────────────────────────────────────────

    async def list_roles(self) -> list[RoleInfo]:
        """List all roles."""
        result = await self.db.execute(
            select(Role).order_by(desc(Role.hierarchy_level))
        )
        roles = result.scalars().all()
        return [
            RoleInfo(
                id=str(r.id),
                name=r.name,
                display_name=r.display_name,
                description=r.description,
                hierarchy_level=r.hierarchy_level,
                is_system=r.is_system,
            )
            for r in roles
        ]

    # ── Audit Logs ──────────────────────────────────────────────────

    async def get_audit_logs(
        self,
        params: PaginationParams,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> tuple[list[AuditLogEntry], int]:
        """Get audit logs with pagination and filters."""
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == uuid.UUID(user_id))
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset(params.offset).limit(params.page_size)

        result = await self.db.execute(query)
        logs = result.scalars().all()

        items = [
            AuditLogEntry(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                details=log.details or {},
                created_at=log.created_at,
            )
            for log in logs
        ]

        return items, total

    # ── Private Helpers ─────────────────────────────────────────────

    async def _get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        """Get active role names for a user."""
        result = await self.db.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, UserRole.is_active == True)
        )
        roles = [row[0] for row in result.all()]
        return roles if roles else ["viewer"]
