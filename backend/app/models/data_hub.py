"""
Data Foundation Models — Data Hub & Data Lineage.
Supports database integrations (PostgreSQL, Snowflake, S3, Kafka), ingestion jobs, and visual lineage graph DAGs.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, BigInteger, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DataConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """External data sources (PostgreSQL, Snowflake, S3, Redshift, Kafka)."""

    __tablename__ = "data_connections"
    __table_args__ = (
        Index("ix_data_connections_user_id", "user_id"),
        Index("ix_data_connections_source_type", "source_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # postgresql, snowflake, s3, kafka, mysql
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    database_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    schema_name: Mapped[Optional[str]] = mapped_column(String(255), default="public", nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), default="idle", nullable=False)
    connection_params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<DataConnection name={self.name} type={self.source_type}>"


class DataIngestionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Background data pipeline ingestion & sync jobs."""

    __tablename__ = "data_ingestion_jobs"
    __table_args__ = (
        Index("ix_ingestion_jobs_connection_id", "connection_id"),
        Index("ix_ingestion_jobs_status", "status"),
    )

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_table: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)  # running, success, failed
    rows_imported: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_imported: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DataIngestionJob target={self.target_table} status={self.status}>"


class LineageNode(UUIDPrimaryKeyMixin, Base):
    """Nodes in the visual Data Lineage DAG (Sources, Transformations, Tables, Models, Reports)."""

    __tablename__ = "lineage_nodes"
    __table_args__ = (
        Index("ix_lineage_nodes_user_id", "user_id"),
        Index("ix_lineage_nodes_node_type", "node_type"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)  # source, table, transformation, model, report
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    schema_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    def __repr__(self) -> str:
        return f"<LineageNode label={self.label} type={self.node_type}>"


class LineageEdge(UUIDPrimaryKeyMixin, Base):
    """Directed edges in the Data Lineage DAG representing data flow."""

    __tablename__ = "lineage_edges"

    source_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lineage_nodes.id", ondelete="CASCADE"),
        nullable=False,
    )
    transformation_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transformation_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    def __repr__(self) -> str:
        return f"<LineageEdge {self.source_node_id} -> {self.target_node_id}>"
