import uuid
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BIGINT,
    Column,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from packages.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(64), nullable=False, index=True)
    source_uri = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="processing")
    content_type = Column(String(128), nullable=False)
    byte_size = Column(BIGINT, nullable=False)
    embed_model = Column(String(128), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("workspace_id", "source_uri", name="uq_workspace_source"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=False)
    tsv_content = Column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(section_title, '')), 'A') || "
            "setweight(to_tsvector('english', content), 'B')",
            persisted=True,
        ),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_tsv", "tsv_content", postgresql_using="gin"),
        Index(
            "idx_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(64), nullable=False)
    workspace_id = Column(String(64), nullable=False)
    query_text = Column(Text, nullable=False)
    status = Column(String(32), nullable=False)
    latency_ms = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

