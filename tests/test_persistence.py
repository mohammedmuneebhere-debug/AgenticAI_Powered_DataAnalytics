"""Phase 1 persistence tests.

The JSON-facade tests always run (no Docker needed). The PostgreSQL-backed
store tests auto-skip when no database answers on DATABASE_URL, so the suite
stays green on machines without Docker.
"""

import uuid

import pytest

from backend.services.chat_store import DEFAULT_USER_ID, ChatStore, JsonChatStore
from backend.auth.store import UserStore, JsonUserStore


def _pg_up() -> bool:
    try:
        from backend.db.session import ping

        return ping()
    except Exception:
        return False


pg = pytest.mark.skipif(not _pg_up(), reason="PostgreSQL not available")


class TestFacadeSelection:
    def test_default_settings_choose_json(self, monkeypatch):
        import backend.config as config

        # Force the default explicitly: a developer .env may set
        # JSON_FALLBACK=false, which is a valid runtime choice, not a failure.
        monkeypatch.setenv("JSON_FALLBACK", "true")
        config.get_settings.cache_clear()
        store = ChatStore()
        assert isinstance(store, JsonChatStore)
        assert store.backend_name == "json"

    def test_explicit_path_always_json(self, tmp_path):
        assert isinstance(ChatStore(tmp_path / "s.json"), JsonChatStore)
        assert isinstance(UserStore(tmp_path / "u.json"), JsonUserStore)

    def test_unreachable_pg_degrades_to_json(self, monkeypatch):
        monkeypatch.setenv("JSON_FALLBACK", "false")
        import backend.config as config

        # pg_available is imported lazily inside the factory from db.session,
        # so patching it there intercepts the factory's check.
        import backend.db.session as db_session

        monkeypatch.setattr(db_session, "pg_available", lambda: False, raising=False)
        store = ChatStore()
        assert isinstance(store, JsonChatStore)
        config.get_settings.cache_clear()


class TestJsonSessionLifecycle:
    def test_create_add_message_delete(self, tmp_path):
        store = ChatStore(tmp_path / "s.json")
        user = uuid.uuid4().hex

        session = store.create_session(user)
        msg = store.add_message(session["id"], "user", "Hello world", user_id=user)
        assert msg["metadata"] == {}

        got = store.get_session(session["id"], user)
        assert got["title"].startswith("Hello")
        assert got["owner_user_id"] == user
        assert got["messages"][0]["content"] == "Hello world"

        sessions = store.list_sessions(user)
        assert sessions[0]["message_count"] == 1

        assert store.delete_session(session["id"], user) is True
        assert store.delete_session(session["id"], user) is False
        assert store.get_session(session["id"], user) is None


@pg
class TestPostgresChatStore:
    def test_full_lifecycle(self):
        from backend.services.chat_store import PostgresChatStore

        store = PostgresChatStore()
        user = f"pgtest-{uuid.uuid4().hex[:12]}"

        session = store.create_session(user)
        assert session["title"] == "New chat"
        assert session["owner_user_id"] == user

        m1 = store.add_message(session["id"], "user", "What is trend analysis?", user_id=user)
        m2 = store.add_message(
            session["id"],
            "assistant",
            "Answer",
            metadata={"domain": "trends", "confidence": 0.9},
            user_id=user,
        )
        assert m1["id"] != m2["id"]

        got = store.get_session(session["id"], user)
        assert got["messages"][0]["content"] == "What is trend analysis?"
        assert got["last_domain"] == "trends"
        assert got["title"] == "What is trend analysis?"

        listed = store.list_sessions(user)
        assert [s["id"] for s in listed] == [session["id"]]
        assert listed[0]["message_count"] == 2

        assert store.owns_session(session["id"], user) is True
        assert store.get_messages(session["id"], user) == got["messages"]

        assert store.delete_session(session["id"], user) is True
        assert store.get_session(session["id"], user) is None

    def test_ensure_session_idempotent(self):
        from backend.services.chat_store import PostgresChatStore

        store = PostgresChatStore()
        user = f"pgtest-{uuid.uuid4().hex[:12]}"
        sid = uuid.uuid4().hex

        first = store.ensure_session(sid, user)
        second = store.ensure_session(sid, user)
        assert first["id"] == second["id"] == sid
        store.delete_session(sid, user)


@pg
class TestPostgresUserStore:
    def test_create_get_auth_shape(self):
        from backend.auth.store import PostgresUserStore

        store = PostgresUserStore()
        email = f"pg-{uuid.uuid4().hex[:10]}@example.com"

        user = store.create(email, "PG Test", "password123!")
        assert user["email"] == email
        assert user["password_hash"].startswith("pbkdf2_sha256$")

        assert store.get_by_email(email)["id"] == user["id"]
        assert store.get_by_email(email.upper())["id"] == user["id"]
        assert store.get_by_id(user["id"])["name"] == "PG Test"
        assert store.get_by_id(uuid.uuid4().hex) is None
        assert store.verify_password("password123!", user["password_hash"]) is True
        assert store.verify_password("wrong", user["password_hash"]) is False

    def test_provider_link(self):
        from backend.auth.store import PostgresUserStore

        store = PostgresUserStore()
        email = f"pg-{uuid.uuid4().hex[:10]}@example.com"
        user = store.create(email, "OAuth User", "password123!")

        # Unique per run: provider ids are not globally unique across users
        google_id = f"gid-{uuid.uuid4().hex[:12]}"
        linked = store.link_provider(user["id"], "google", google_id)
        assert linked["google_id"] == google_id
        assert store.get_by_provider_id("google", google_id)["id"] == user["id"]
        assert store.get_by_provider_id("github", google_id) is None

class TestJsonSafeMetadata:
    """Regression: message metadata carries datetimes (provenance record),
    which PostgreSQL JSONB cannot serialize natively."""

    def test_json_safe_coerces_datetimes_recursively(self):
        from datetime import datetime, timezone

        from backend.services.chat_store import _json_safe

        payload = {
            "provenance": {"timestamp": datetime(2026, 10, 2, 12, 0, tzinfo=timezone.utc)},
            "items": [{"when": datetime(2026, 1, 1)}],
            "count": 3,
            "flag": True,
            "none": None,
            "uuid_like": object(),
        }
        safe = _json_safe(payload)
        assert safe["provenance"]["timestamp"] == "2026-10-02T12:00:00+00:00"
        assert safe["items"][0]["when"] == "2026-01-01T00:00:00"
        assert safe["count"] == 3 and safe["flag"] is True and safe["none"] is None
        assert isinstance(safe["uuid_like"], str)
        import json

        json.dumps(safe)  # must not raise

    @pg
    def test_postgres_store_accepts_datetime_metadata(self):
        from datetime import datetime, timezone

        from backend.services.chat_store import PostgresChatStore

        store = PostgresChatStore()
        user = f"pgtest-{uuid.uuid4().hex[:12]}"
        session = store.create_session(user)
        store.add_message(
            session["id"],
            "assistant",
            "answer",
            metadata={"provenance": {"timestamp": datetime.now(timezone.utc)}},
            user_id=user,
        )
        stored = store.get_session(session["id"], user)
        assert isinstance(stored["messages"][0]["metadata"]["provenance"]["timestamp"], str)
        store.delete_session(session["id"], user)
