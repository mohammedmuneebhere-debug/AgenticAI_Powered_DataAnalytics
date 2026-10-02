"""pgvector repository - idempotent embedding upsert and cosine search.

Replaces the search-engine piece of the stack diagram: PostgreSQL + pgvector
covers the one query this product actually needs ("find records semantically
like this one"), including the HNSW cosine index created in migration
0001_initial. An external ES/OpenSearch cluster would add operational weight
without a second query shape to serve.

Every function degrades to a safe empty result when PostgreSQL is
unavailable, so callers can treat semantic features as optional.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def upsert_record_embeddings(entries: list[dict[str, Any]]) -> int:
    """Insert or refresh embeddings keyed by record hash.

    ``entries``: [{"record_hash", "content", "vector", "metadata"}, ...]
    Idempotent: re-embedding the same content updates the existing row
    instead of duplicating it.
    """
    if not entries:
        return 0
    try:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        from backend.db.models import RecordEmbeddingModel, utcnow
        from backend.db.session import session_scope

        with session_scope() as db:
            written = 0
            for entry in entries:
                vector = entry.get("vector")
                if not vector:
                    continue
                # The JSONB column is physically named "metadata" (the class
                # attribute is `meta`), so SET/EXCLUDED keys must use the
                # column name, addressed positionally via table columns.
                table = RecordEmbeddingModel.__table__
                stmt = pg_insert(RecordEmbeddingModel).values(
                    {
                        table.c.record_hash: entry["record_hash"],
                        table.c.content: str(entry.get("content", ""))[:2000],
                        table.c.embedding: list(vector),
                        table.c.metadata: entry.get("metadata") or {},
                        table.c.created_at: utcnow(),
                    }
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=[table.c.record_hash],
                    set_={
                        "content": stmt.excluded["content"],
                        "embedding": stmt.excluded["embedding"],
                        "metadata": stmt.excluded["metadata"],
                    },
                )
                db.execute(stmt)
                written += 1
            return written
    except Exception as exc:
        logger.info("Embedding upsert skipped (%s)", exc.__class__.__name__)
        return 0


def get_embedding_record(record_hash: str) -> Optional[dict[str, Any]]:
    try:
        from sqlalchemy import select

        from backend.db.models import RecordEmbeddingModel
        from backend.db.session import session_scope

        with session_scope() as db:
            row = db.scalar(
                select(RecordEmbeddingModel).where(RecordEmbeddingModel.record_hash == record_hash)
            )
            if not row:
                return None
            return {
                "record_hash": row.record_hash,
                "content": row.content,
                "metadata": row.meta or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
    except Exception as exc:
        logger.info("Embedding lookup skipped (%s)", exc.__class__.__name__)
        return None


def similar_records(
    record_hash: str, limit: int = 5, min_similarity: float = 0.3
) -> list[dict[str, Any]]:
    """Nearest records by cosine distance (HNSW-indexed), best first.

    ``min_similarity`` defaults to 0.3 because all-MiniLM-L6-v2 places
    topically related sentences around 0.4-0.7 and unrelated ones near 0.0;
    a 0.5 floor would drop most true matches.
    """
    try:
        from sqlalchemy import select

        from backend.db.models import RecordEmbeddingModel
        from backend.db.session import session_scope

        with session_scope() as db:
            source = db.scalar(
                select(RecordEmbeddingModel).where(RecordEmbeddingModel.record_hash == record_hash)
            )
            if not source or source.embedding is None:
                return []

            rows = db.execute(
                select(
                    RecordEmbeddingModel.record_hash,
                    RecordEmbeddingModel.content,
                    RecordEmbeddingModel.meta,
                    (1 - RecordEmbeddingModel.embedding.cosine_distance(source.embedding)).label(
                        "similarity"
                    ),
                )
                .where(RecordEmbeddingModel.record_hash != record_hash)
                .order_by(RecordEmbeddingModel.embedding.cosine_distance(source.embedding))
                .limit(max(1, limit) * 2)
            ).all()

            matches = [
                {
                    "record_hash": row.record_hash,
                    "content": row.content,
                    "metadata": row.meta or {},
                    "similarity": round(float(row.similarity), 4),
                }
                for row in rows
                if float(row.similarity) >= min_similarity
            ]
            return matches[: max(1, limit)]
    except Exception as exc:
        logger.info("Similarity search skipped (%s)", exc.__class__.__name__)
        return []


def embedding_stats() -> dict[str, int]:
    """Row count for the embeddings table (0 when unavailable)."""
    try:
        from sqlalchemy import func, select

        from backend.db.models import RecordEmbeddingModel
        from backend.db.session import session_scope

        with session_scope() as db:
            return {"count": int(db.scalar(select(func.count()).select_from(RecordEmbeddingModel)) or 0)}
    except Exception as exc:
        logger.info("Embedding stats skipped (%s)", exc.__class__.__name__)
        return {"count": 0}
