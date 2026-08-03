"""
RBAC Models — Role-Based Access Control with hierarchical roles and granular permissions.
"""

import uuid
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Index, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Named roles in the system.
    Seeded with: super_admin, admin, manager, ml_engineer, data_scientist, viewer.
    """

    __tablename__ = "roles"
    __table_args__ = (
        Index("ix_roles_name", "name", unique=True),
    )

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hierarchy_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", lazy="selectin"
    )
    users: Mapped[list["UserRole"]] = relationship(
        back_populates="role", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name} level={self.hierarchy_level}>"


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Granular permissions (e.g., 'users:read', 'models:deploy').
    """

    __tablename__ = "permissions"
    __table_args__ = (
        Index("ix_permissions_codename", "codename", unique=True),
    )

    codename: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    roles: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Permission codename={self.codename}>"


class RolePermission(UUIDPrimaryKeyMixin, Base):
    """Join table: which permissions belong to which roles."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="roles")


class UserRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Join table: which roles are assigned to which users.
    A user can have multiple roles.
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        Index("ix_user_roles_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"


# Forward reference
from app.models.user import User  # noqa: E402
