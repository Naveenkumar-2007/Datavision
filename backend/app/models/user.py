"""
User Models — Core user profile and preferences.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Index, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Core user table — every person on the platform."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_is_active", "is_active"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash_algorithm: Mapped[str] = mapped_column(
        String(20), default="bcrypt", nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # OAuth fields
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_provider_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    preferences: Mapped[Optional["UserPreferences"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class UserPreferences(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-user preferences and settings."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        Index("ix_user_preferences_user_id", "user_id", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    currency_code: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    currency_symbol: Mapped[str] = mapped_column(String(5), default="₹", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_save_conversations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_chat_mode: Mapped[str] = mapped_column(String(50), default="auto", nullable=False)
    custom_settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="preferences")

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id}>"


# Forward references for type checking
from app.models.auth import UserSession  # noqa: E402
from app.models.rbac import UserRole  # noqa: E402
