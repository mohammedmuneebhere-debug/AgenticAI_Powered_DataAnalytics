"""ORM models for the SOCIALIQ persistence layer.

Shape parity with the JSON stores is intentional: every store method returns
plain dicts identical to the JSON-backed implementations, so callers (and the
existing tests) cannot tell the backends apart.

``dossier`` on chat_sessions holds the last assistant analytics payload (the
"intelligence dossier" the dashboard renders) so a session can be reopened
without replaying message metadata.
"""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    # OAuth provider ids (google_id, ...) live in `extra` — mirrors the JSON
    # store where unknown keys were added to the user dict directly.
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="New chat")
    last_domain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dossier: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Stable insertion order (created_at alone can collide within a microsecond)
    seq: Mapped[int] = mapped_column(Integer, Identity(), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # "metadata" is reserved by Declarative, so the attribute is `meta`
    meta: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class ProvenanceRecordModel(Base):
    __tablename__ = "provenance_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    dataset_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    insight_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    evidence_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # IPFS content identifier (Phase 5); null = hash-chain only
    cid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pinned: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class RecordEmbeddingModel(Base):
    __tablename__ = "record_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    # Content hash of the source record — upsert key for idempotent embedding
    record_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
