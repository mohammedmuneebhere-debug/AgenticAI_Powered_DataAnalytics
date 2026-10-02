"""One-time seeder: JSON stores -> PostgreSQL (Phase 1 cutover).

Reads data/users.json and data/sessions.json and upserts everything into the
PostgreSQL schema created by `alembic upgrade head`. Idempotent: users are
matched by email, sessions/messages by their existing ids, so re-running is
safe and existing PG rows are not duplicated or overwritten with older data.

Usage:
    .venv/Scripts/python scripts/seed_postgres.py [--users data/users.json --sessions data/sessions.json]
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def seed_users(path: Path) -> tuple[int, int]:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from backend.auth.store import JsonUserStore
    from backend.db.models import UserModel
    from backend.db.session import session_scope

    payload = _load(path)
    raw_users = payload.get("users", {})
    created = skipped = 0
    for user in raw_users.values():
        extra = {
            key: value
            for key, value in user.items()
            if key not in {"id", "email", "name", "password_hash", "created_at"}
        }
        with session_scope() as db:
            stmt = (
                pg_insert(UserModel)
                .values(
                    id=user["id"],
                    email=user["email"].strip().lower(),
                    name=user.get("name", ""),
                    password_hash=user.get("password_hash", ""),
                    extra=extra,
                    created_at=user.get("created_at"),
                )
                .on_conflict_do_nothing(index_elements=["email"])
            )
            result = db.execute(stmt)
            created += result.rowcount or 0
    # rows that already existed are "skipped"
    skipped = len(raw_users) - created
    return created, skipped


def seed_sessions(path: Path) -> tuple[int, int]:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from backend.db.models import ChatMessageModel, ChatSessionModel
    from backend.db.session import session_scope

    payload = _load(path)
    sessions_created = 0
    messages_created = 0
    buckets = payload.get("by_user", {})
    if not buckets and payload.get("sessions"):
        # legacy top-level layout
        buckets = {"local": payload["sessions"]}

    for user_id, sessions in buckets.items():
        for sid, session in sessions.items():
            with session_scope() as db:
                stmt = (
                    pg_insert(ChatSessionModel)
                    .values(
                        id=sid,
                        user_id=session.get("owner_user_id") or user_id,
                        title=session.get("title", "New chat"),
                        last_domain=session.get("last_domain"),
                        created_at=session.get("created_at"),
                        updated_at=session.get("updated_at"),
                    )
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                sessions_created += db.execute(stmt).rowcount or 0

                for msg in session.get("messages", []):
                    meta = msg.get("metadata") or {}
                    stmt = (
                        pg_insert(ChatMessageModel)
                        .values(
                            id=msg["id"],
                            session_id=sid,
                            role=msg.get("role", "user"),
                            content=msg.get("content", ""),
                            meta=meta,
                            created_at=msg.get("created_at"),
                        )
                        .on_conflict_do_nothing(index_elements=["id"])
                    )
                    messages_created += db.execute(stmt).rowcount or 0
    return sessions_created, messages_created


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed PostgreSQL from JSON stores")
    parser.add_argument("--users", default=str(PROJECT_ROOT / "data" / "users.json"))
    parser.add_argument("--sessions", default=str(PROJECT_ROOT / "data" / "sessions.json"))
    args = parser.parse_args()

    from backend.db.session import ping

    if not ping():
        print("ERROR: PostgreSQL unreachable — start docker compose postgres first.")
        return 1

    users_created, users_skipped = seed_users(Path(args.users))
    print(f"users: {users_created} created, {users_skipped} already present")

    sessions_created, messages_created = seed_sessions(Path(args.sessions))
    print(f"sessions: {sessions_created} created; messages: {messages_created} created")
    print("Done. Start the backend with JSON_FALLBACK=false to use PostgreSQL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
