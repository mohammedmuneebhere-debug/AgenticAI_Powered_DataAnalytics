"""initial schema: users, chat sessions/messages, provenance records, embeddings

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension must exist before the embeddings table (the compose
    # image is pgvector/pgvector:pg16, so this succeeds there).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("extra", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(128), nullable=False, index=True),
        sa.Column("title", sa.String(256), nullable=False, server_default="New chat"),
        sa.Column("last_domain", sa.String(64), nullable=True),
        sa.Column("dossier", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("seq", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "provenance_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_hash", sa.String(64), nullable=False, index=True),
        sa.Column("insight_hash", sa.String(64), nullable=False, index=True),
        sa.Column("evidence_hash", sa.String(64), nullable=True),
        sa.Column("model_version", sa.String(64), nullable=True),
        sa.Column("payload", JSONB, nullable=True),
        sa.Column("cid", sa.String(128), nullable=True),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "record_embeddings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("record_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        # 384-dim MiniLM vectors (all-MiniLM-L6-v2)
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_record_embeddings_hnsw",
        "record_embeddings",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("record_embeddings")
    op.drop_table("provenance_records")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("users")
