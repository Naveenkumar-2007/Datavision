"""
Reports Models — PDF/PPTX report generation, automated email delivery schedules, and report templates.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, BigInteger, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generated PDF / PPTX / Excel executive report."""

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_user_id", "user_id"),
        Index("ix_reports_format", "report_format"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_format: Mapped[str] = mapped_column(String(20), default="pdf", nullable=False)  # pdf, pptx, xlsx, html
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Report title={self.title} format={self.report_format}>"


class ScheduledReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Cron-based automated report generator and email dispatcher."""

    __tablename__ = "scheduled_reports"
    __table_args__ = (
        Index("ix_scheduled_reports_user_id", "user_id"),
        Index("ix_scheduled_reports_is_active", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), default="0 9 * * 1", nullable=False)  # e.g., weekly on Monday 9am
    recipients: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    report_format: Mapped[str] = mapped_column(String(20), default="pdf", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<ScheduledReport name={self.name} cron={self.cron_expression}>"
