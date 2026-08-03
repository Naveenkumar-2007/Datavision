"""
Analytics & Visual Models — Dashboards, charts, stories, visual pipelines, and computer vision tasks.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Dashboard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User analytics dashboards."""

    __tablename__ = "dashboards"
    __table_args__ = (
        Index("ix_dashboards_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), default="Untitled Dashboard", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    layout: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    charts: Mapped[list["Chart"]] = relationship(
        back_populates="dashboard", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} title={self.title}>"


class Chart(UUIDPrimaryKeyMixin, Base):
    """Individual chart component inside a dashboard."""

    __tablename__ = "charts"
    __table_args__ = (
        Index("ix_charts_dashboard_id", "dashboard_id"),
    )

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chart_type: Mapped[str] = mapped_column(String(50), nullable=False)  # bar, line, scatter, pie
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default="now()"
    )

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship(back_populates="charts")

    def __repr__(self) -> str:
        return f"<Chart title={self.title} type={self.chart_type}>"


class ComputerVisionTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Computer vision processing jobs (object detection, classification, segmentation)."""

    __tablename__ = "computer_vision_tasks"
    __table_args__ = (
        Index("ix_cv_tasks_user_id", "user_id"),
        Index("ix_cv_tasks_status", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(
        String(50), default="object_detection", nullable=False
    )  # object_detection, classification, ocr, segmentation
    model_name: Mapped[str] = mapped_column(String(100), default="yolov8n", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    detected_objects_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence_threshold: Mapped[float] = mapped_column(default=0.25, nullable=False)

    def __repr__(self) -> str:
        return f"<ComputerVisionTask name={self.task_name} status={self.status}>"


class Notification(UUIDPrimaryKeyMixin, Base):
    """System and AI notifications for users."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default="now()"
    )

    def __repr__(self) -> str:
        return f"<Notification title={self.title} read={self.is_read}>"
