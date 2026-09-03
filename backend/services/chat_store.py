"""JSON-backed chat session persistence."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "sessions.json"


class ChatStore:
    def __init__(self):
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not STORE_PATH.exists():
            self._save({"sessions": {}})

    def _load(self) -> dict:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))

    def _save(self, data: dict):
        STORE_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def list_sessions(self) -> list[dict]:
        data = self._load()
        sessions = []
        for sid, s in data["sessions"].items():
            sessions.append({
                "id": sid,
                "title": s.get("title", "New chat"),
                "domain": s.get("last_domain"),
                "updated_at": s.get("updated_at"),
                "message_count": len(s.get("messages", [])),
            })
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions

    def get_session(self, session_id: str) -> Optional[dict]:
        return self._load()["sessions"].get(session_id)

    def create_session(self, title: str = "New chat") -> dict:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session = {"id": sid, "title": title, "created_at": now, "updated_at": now, "messages": [], "last_domain": None}
        data = self._load()
        data["sessions"][sid] = session
        self._save(data)
        return session

    def delete_session(self, session_id: str) -> bool:
        data = self._load()
        if session_id not in data["sessions"]:
            return False
        del data["sessions"][session_id]
        self._save(data)
        return True

    def ensure_session(self, session_id: str) -> dict:
        data = self._load()
        if session_id not in data["sessions"]:
            now = datetime.now(timezone.utc).isoformat()
            data["sessions"][session_id] = {
                "id": session_id, "title": "New chat", "created_at": now,
                "updated_at": now, "messages": [], "last_domain": None,
            }
            self._save(data)
        return data["sessions"][session_id]

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[dict] = None) -> dict:
        data = self._load()
        if session_id not in data["sessions"]:
            now = datetime.now(timezone.utc).isoformat()
            data["sessions"][session_id] = {
                "id": session_id, "title": "New chat", "created_at": now,
                "updated_at": now, "messages": [], "last_domain": None,
            }

        session = data["sessions"][session_id]
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

    def get_messages(self, session_id: str) -> list[dict]:
        session = self.get_session(session_id)
        return session["messages"] if session else []
