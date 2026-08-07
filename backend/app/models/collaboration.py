"""
Collaboration Models — Multi-tenant Workspaces, team member management, shared links, and comments.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Workspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Team workspace for sharing projects, datasets, and dashboards."""

    __tablename__ = "workspaces"
    __table_args__ = (
        Index("ix_workspaces_owner_id", "owner_id"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Workspace name={self.name} slug={self.slug}>"


class WorkspaceMember(UUIDPrimaryKeyMixin, Base):
    """Members inside a workspace with assigned team roles."""

    __tablename__ = "workspace_members"
    __table_args__ = (
        Index("ix_workspace_members_workspace_id", "workspace_id"),
        Index("ix_workspace_members_user_id", "user_id"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)  # owner, admin, member, viewer
    joined_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="members")

    def __repr__(self) -> str:
        return f"<WorkspaceMember workspace={self.workspace_id} user={self.user_id}>"


class SharedLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Public/private share links for dashboards, reports, and models."""

    __tablename__ = "shared_links"
    __table_args__ = (
        Index("ix_shared_links_token", "share_token", unique=True),
    )

    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # dashboard, report, dataset, model
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    share_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    access_count: Mapped[int] = mapped_column(default=0, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<SharedLink token={self.share_token} type={self.resource_type}>"


class ChatChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Channels for collaboration."""
    __tablename__ = "chat_channels"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ChannelMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Messages inside a collaboration channel."""
    __tablename__ = "channel_messages"
    
    channel_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user: Mapped[Optional["app.models.user.User"]] = relationship("User")


class MessageReaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Emoji reactions on channel messages."""
    __tablename__ = "message_reactions"
    
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    emoji: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    user: Mapped["app.models.user.User"] = relationship("User")
