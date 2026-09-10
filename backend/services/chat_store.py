"""User-scoped, JSON-backed chat session persistence.

Each session is owned by a user id. Legacy files store sessions at the top
level; on first load they are migrated into a per-user ``{"by_user": {...}}``
structure. Ownership is added lazily for unknown sessions (single-user local
mode), so existing local data keeps working.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.config import get_settings

DEFAULT_USER_ID = "local"


def _store_path() -> Path:
    path = Path(get_settings().sessions_store_path)
    return path if path.is_absolute() else (Path(__file__).resolve().parents[2] / path)


class ChatStore:
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
