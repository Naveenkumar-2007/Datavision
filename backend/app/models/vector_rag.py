"""
Vector AI & RAG Models — Knowledge bases, document embeddings, chunking, and RAG retrieval logs.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, Integer, Float, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VectorStore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Vector database index / knowledge collection (FAISS, pgvector, Qdrant)."""

    __tablename__ = "vector_stores"
    __table_args__ = (
        Index("ix_vector_stores_user_id", "user_id"),
        Index("ix_vector_stores_name", "name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-3-small", nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, default=1536, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    index_type: Mapped[str] = mapped_column(String(50), default="HNSW", nullable=False)

    def __repr__(self) -> str:
        return f"<VectorStore name={self.name} chunks={self.total_chunks}>"


class DocumentChunk(UUIDPrimaryKeyMixin, Base):
    """Segmented text chunk stored for semantic similarity search."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_vector_store_id", "vector_store_id"),
    )

    vector_store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vector_stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    def __repr__(self) -> str:
        return f"<DocumentChunk store={self.vector_store_id} idx={self.chunk_index}>"


class RAGQueryLog(UUIDPrimaryKeyMixin, Base):
    """Retrieval-Augmented Generation (RAG) query execution audit."""

    __tablename__ = "rag_query_logs"
    __table_args__ = (
        Index("ix_rag_query_logs_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    similarity_score_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    sources_retrieved: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default="now()", nullable=False)

    def __repr__(self) -> str:
        return f"<RAGQueryLog query={self.query_text[:30]}...>"
