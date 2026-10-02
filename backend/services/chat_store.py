"""User-scoped chat session persistence with pluggable backends.

Public surface (unchanged from the original JSON store):

    ChatStore                      — factory returning the configured backend
    DEFAULT_USER_ID                — "local"
    JsonChatStore                  — JSON-file backend (default; no Docker needed)
    PostgresChatStore              — SQLAlchemy backend (JSON_FALLBACK=false)

Backend selection:
    * an explicit ``store_path`` (tests, scripts) always selects JSON;
    * ``JSON_FALLBACK=true`` (default) selects JSON;
    * otherwise PostgreSQL is used when reachable — if the database is down
      at startup the factory logs a warning and degrades to JSON so the app
      always stays green.

Session dicts and list shapes are identical across backends:
    {id, title, created_at, updated_at, messages, last_domain, owner_user_id}
"""

import json
import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "local"


def _store_path() -> Path:
    path = Path(get_settings().sessions_store_path)
    return path if path.is_absolute() else (Path(__file__).resolve().parents[2] / path)


def _json_safe(value: Any) -> Any:
    """Recursively coerce values PostgreSQL JSONB cannot store natively.

    The JSON store writes with ``default=str`` and therefore tolerates
    datetimes/UUIDs nested in message metadata (e.g. the provenance record).
    JSONB has no such fallback, so the PostgreSQL store applies the same
    coercion here - otherwise the same payload succeeds on one backend and
    500s on the other.
    """
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


class JsonChatStore:
    """Original JSON-file implementation (``{"by_user": {user: {sid: session}}}``)."""

    backend_name = "json"

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = Path(store_path) if store_path else _store_path()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._save({"by_user": {}})

    def _load(self) -> dict:
        data = json.loads(self.store_path.read_text(encoding="utf-8"))
        if "by_user" not in data:
            # Migrate legacy top-level {"sessions": {...}} layout
            data = {"by_user": {DEFAULT_USER_ID: data.get("sessions", {})}}
            self._save(data)
        data["by_user"].setdefault(DEFAULT_USER_ID, {})
        return data

    def _save(self, data: dict) -> None:
        self.store_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def _bucket(data: dict, user_id: str) -> dict:
        return data["by_user"].setdefault(user_id, {})

    def list_sessions(self, user_id: str) -> list[dict]:
        data = self._load()
        sessions = []
        for sid, s in self._bucket(data, user_id).items():
            sessions.append(
                {
                    "id": sid,
                    "title": s.get("title", "New chat"),
                    "domain": s.get("last_domain"),
                    "updated_at": s.get("updated_at"),
                    "message_count": len(s.get("messages", [])),
                }
            )
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    def get_session(self, session_id: str, user_id: str) -> Optional[dict]:
        return self._bucket(self._load(), user_id).get(session_id)

    def owns_session(self, session_id: str, user_id: str) -> bool:
        data = self._load()
        return session_id in self._bucket(data, user_id) or any(
            session_id in bucket for bucket in data["by_user"].values()
        )

    def create_session(self, user_id: str, title: str = "New chat") -> dict:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session = {
            "id": sid,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "last_domain": None,
            "owner_user_id": user_id,
        }
        data = self._load()
        self._bucket(data, user_id)[sid] = session
        self._save(data)
        return session

    def delete_session(self, session_id: str, user_id: str) -> bool:
        data = self._load()
        bucket = self._bucket(data, user_id)
        if session_id not in bucket:
            return False
        del bucket[session_id]
        self._save(data)
        return True

    def ensure_session(self, session_id: str, user_id: str) -> dict:
        data = self._load()
        bucket = self._bucket(data, user_id)
        if session_id not in bucket:
            now = datetime.now(timezone.utc).isoformat()
            bucket[session_id] = {
                "id": session_id,
                "title": "New chat",
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "last_domain": None,
                "owner_user_id": user_id,
            }
            self._save(data)
        return bucket[session_id]

    def add_message(
        self, session_id: str, role: str, content: str,
        metadata: Optional[dict] = None, user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        data = self._load()
        bucket = self._bucket(data, user_id)
        if session_id not in bucket:
            now = datetime.now(timezone.utc).isoformat()
            bucket[session_id] = {
                "id": session_id,
                "title": "New chat",
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "last_domain": None,
                "owner_user_id": user_id,
            }

        session = bucket[session_id]
        msg = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        session["messages"].append(msg)
        session["updated_at"] = msg["created_at"]

        if metadata and metadata.get("domain"):
            session["last_domain"] = metadata["domain"]
        if len(session["messages"]) == 1 and role == "user":
            session["title"] = content[:60] + ("…" if len(content) > 60 else "")

        self._save(data)
        return msg

    def get_messages(self, session_id: str, user_id: str) -> list[dict]:
        session = self.get_session(session_id, user_id)
        return session["messages"] if session else []


class PostgresChatStore:
    """SQLAlchemy implementation with identical return shapes."""

    backend_name = "postgres"

    def __init__(self):
        from backend.db.models import ChatMessageModel  # noqa: F401  (fail fast)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables when the database is reachable but unmigrated.

        Normal deployments run ``alembic upgrade head``; this is a safety net
        so a fresh database does not 500 on first use.
        """
        from backend.db.base import Base
        from backend.db.session import get_engine
        try:
            Base.metadata.create_all(get_engine())
        except Exception as exc:
            logger.warning("Could not ensure chat schema: %s", exc.__class__.__name__)

    # -- dict shape helpers -------------------------------------------------

    @staticmethod
    def _iso(dt) -> Optional[str]:
        return dt.isoformat() if dt else None

    @classmethod
    def _message_dict(cls, m) -> dict:
        return {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "metadata": m.meta or {},
            "created_at": cls._iso(m.created_at),
        }

    @classmethod
    def _session_dict(cls, s, messages) -> dict:
        return {
            "id": s.id,
            "title": s.title,
            "created_at": cls._iso(s.created_at),
            "updated_at": cls._iso(s.updated_at),
            "messages": messages,
            "last_domain": s.last_domain,
            "owner_user_id": s.user_id,
        }

    # -- API ----------------------------------------------------------------

    def list_sessions(self, user_id: str) -> list[dict]:
        from sqlalchemy import func, select
        from backend.db.models import ChatMessageModel, ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            counts = dict(
                db.execute(
                    select(ChatMessageModel.session_id, func.count())
                    .group_by(ChatMessageModel.session_id)
                ).all()
            )
            rows = db.scalars(
                select(ChatSessionModel)
                .where(ChatSessionModel.user_id == user_id)
                .order_by(ChatSessionModel.updated_at.desc())
            ).all()
            return [
                {
                    "id": s.id,
                    "title": s.title,
                    "domain": s.last_domain,
                    "updated_at": self._iso(s.updated_at),
                    "message_count": counts.get(s.id, 0),
                }
                for s in rows
            ]

    def get_session(self, session_id: str, user_id: str) -> Optional[dict]:
        from sqlalchemy import select
        from backend.db.models import ChatMessageModel, ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            s = db.scalar(
                select(ChatSessionModel).where(
                    ChatSessionModel.id == session_id,
                    ChatSessionModel.user_id == user_id,
                )
            )
            if not s:
                return None
            messages = db.scalars(
                select(ChatMessageModel)
                .where(ChatMessageModel.session_id == session_id)
                .order_by(ChatMessageModel.seq)
            ).all()
            return self._session_dict(s, [self._message_dict(m) for m in messages])

    def owns_session(self, session_id: str, user_id: str) -> bool:
        from sqlalchemy import select
        from backend.db.models import ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            return (
                db.scalar(
                    select(ChatSessionModel.id).where(ChatSessionModel.id == session_id).limit(1)
                )
                is not None
            )

    def create_session(self, user_id: str, title: str = "New chat") -> dict:
        from backend.db.models import ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            s = ChatSessionModel(user_id=user_id, title=title)
            db.add(s)
            db.flush()
            return self._session_dict(s, [])

    def delete_session(self, session_id: str, user_id: str) -> bool:
        from sqlalchemy import delete
        from backend.db.models import ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            result = db.execute(
                delete(ChatSessionModel).where(
                    ChatSessionModel.id == session_id,
                    ChatSessionModel.user_id == user_id,
                )
            )
            return bool(result.rowcount)

    def ensure_session(self, session_id: str, user_id: str) -> dict:
        from sqlalchemy import select
        from backend.db.models import ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            s = db.scalar(
                select(ChatSessionModel).where(
                    ChatSessionModel.id == session_id,
                    ChatSessionModel.user_id == user_id,
                )
            )
            if not s:
                s = ChatSessionModel(id=session_id, user_id=user_id)
                db.add(s)
                db.flush()
            return self._session_dict(s, [])

    def add_message(
        self, session_id: str, role: str, content: str,
        metadata: Optional[dict] = None, user_id: str = DEFAULT_USER_ID,
    ) -> dict:
        from sqlalchemy import func, select
        from backend.db.models import ChatMessageModel, ChatSessionModel
        from backend.db.session import session_scope

        with session_scope() as db:
            s = db.get(ChatSessionModel, session_id)
            if not s:
                s = ChatSessionModel(id=session_id, user_id=user_id)
                db.add(s)
                db.flush()

            msg = ChatMessageModel(
                session_id=s.id, role=role, content=content, meta=_json_safe(metadata or {})
            )
            db.add(msg)
            db.flush()

            first_user_message = role == "user" and not db.scalar(
                select(func.count()).select_from(ChatMessageModel).where(
                    ChatMessageModel.session_id == session_id,
                    ChatMessageModel.id != msg.id,
                )
            )
            if first_user_message:
                s.title = content[:60] + ("…" if len(content) > 60 else "")
            if metadata and metadata.get("domain"):
                s.last_domain = metadata["domain"]
            s.updated_at = msg.created_at
            return self._message_dict(msg)

    def get_messages(self, session_id: str, user_id: str) -> list[dict]:
        session = self.get_session(session_id, user_id)
        return session["messages"] if session else []


def ChatStore(store_path: Optional[Path] = None):
    """Factory returning the configured persistence backend."""
    if store_path is not None:
        return JsonChatStore(store_path)

    settings = get_settings()
    if not settings.json_fallback:
        from backend.db.session import pg_available

        if pg_available():
            return PostgresChatStore()
        logger.warning(
            "JSON_FALLBACK=false but PostgreSQL is unreachable — using JSON store at %s",
            _store_path(),
        )
    return JsonChatStore()
