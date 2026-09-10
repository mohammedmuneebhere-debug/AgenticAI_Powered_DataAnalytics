"""Auth flow, per-user session scoping, and LLM routing tests."""

import json
import httpx
import pytest

from backend.auth.store import UserStore
from backend.services.chat_store import ChatStore
from agents.insight.agent import InsightAgent


# ── Authentication ─────────────────────────────────────────────────────


class TestAuthFlow:
    def test_register_login_me_roundtrip(self, client):
        payload = {"email": "roundtrip@example.com", "name": "Round Trip", "password": "supersecret1"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        token = resp.json()["access_token"]

        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "roundtrip@example.com"

    def test_login_rejects_wrong_password(self, client, registered_user):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_protected_route_requires_token_when_api_key_set(self, client, monkeypatch):
        from backend.config import get_settings

        monkeypatch.setenv("N8N_API_KEY", "secret-key")
        get_settings.cache_clear()
        try:
            resp = client.get("/api/v1/sessions")
            assert resp.status_code == 401

            keyed = client.get("/api/v1/sessions", headers={"X-API-Key": "secret-key"})
            assert keyed.status_code == 200
        finally:
            get_settings.cache_clear()

    def test_bad_token_rejected(self, client):
        resp = client.get("/api/v1/sessions", headers={"Authorization": "Bearer not-a-jwt"})
        assert resp.status_code == 401


# ── Per-user session storage ───────────────────────────────────────────


class TestPerUserSessions:
    def test_users_cannot_see_each_others_sessions(self, client):
        a = client.post(
            "/api/v1/auth/register",
            json={"email": "a@example.com", "name": "A", "password": "supersecret1"},
        ).json()
        b = client.post(
            "/api/v1/auth/register",
            json={"email": "b@example.com", "name": "B", "password": "supersecret1"},
        ).json()

        ha = {"Authorization": f"Bearer {a['access_token']}"}
        hb = {"Authorization": f"Bearer {b['access_token']}"}

        created_resp = client.post("/api/v1/sessions", headers=ha)
        assert created_resp.status_code == 200, created_resp.text
        created = created_resp.json()
        assert client.get(f"/api/v1/sessions/{created['id']}", headers=ha).status_code == 200
        assert client.get(f"/api/v1/sessions/{created['id']}", headers=hb).status_code == 404

        listed = client.get("/api/v1/sessions", headers=hb).json()
        assert all(s["id"] != created["id"] for s in listed)

    def test_legacy_sessions_migrate_into_local_bucket(self, tmp_path):
        path = tmp_path / "sessions.json"
        legacy = {
            "sessions": {
                "old-session": {
                    "id": "old-session",
                    "title": "Legacy chat",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "messages": [],
                    "last_domain": None,
                }
            }
        }
        path.write_text(json.dumps(legacy), encoding="utf-8")

        store = ChatStore(path)
        migrated = store.list_sessions("local")
        assert [s["id"] for s in migrated] == ["old-session"]

    def test_same_session_id_isolated_between_users(self, stores):
        _, chat = stores
        chat.add_message("shared-id", "user", "hello", user_id="alice")
        chat.add_message("shared-id", "user", "hello", user_id="bob")

        assert len(chat.get_messages("shared-id", "alice")) == 1
        assert len(chat.get_messages("shared-id", "bob")) == 1
        assert chat.get_messages("shared-id", "alice") != chat.get_messages("shared-id", "bob")

    def test_user_cannot_delete_foreign_session(self, stores):
        _, chat = stores
        chat.create_session("alice", title="Alice's chat")
        sessions = chat.list_sessions("alice")
        assert not chat.delete_session(sessions[0]["id"], "bob")


# ── LLM model routing (OpenAI vs Ollama) ──────────────────────────────


class TestModelRouting:
    @pytest.mark.asyncio
    async def test_ollama_prefix_routes_to_ollama(self, monkeypatch):
        agent = InsightAgent()

        captured = {}

        async def fake_post(self, url, json=None, **kwargs):
            captured["url"] = url
            captured["model"] = json["model"]

            class Resp:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"message": {"content": "local answer"}}

            return Resp()

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        result = await agent.generate(
            query="test", evidence=[], analytics={}, intent="general",
            llm_model="ollama:llama3.2",
        )
        assert result["model_version"] == "ollama:llama3.2"
        assert captured["model"] == "llama3.2"
        assert captured["url"].endswith("/api/chat")

    @pytest.mark.asyncio
    async def test_no_api_key_falls_back_to_template(self):
        result = await InsightAgent().generate(
            query="test", evidence=[], analytics={}, intent="general",
        )
        assert result["model_version"] == "socialiq-template-0.2"

    def test_resolve_provider(self):
        agent = InsightAgent()
        assert agent.resolve_provider("ollama:mistral") == ("ollama", "mistral")
        assert agent.resolve_provider("gpt-4o") == ("openai", "gpt-4o")


# ── Web search tool guards ─────────────────────────────────────────────


class TestWebSearchTool:
    @pytest.mark.asyncio
    async def test_tool_result_filters_disallowed_domains(self, monkeypatch):
        from backend.config import get_settings

        monkeypatch.setenv("WEB_SEARCH_ALLOWED_DOMAINS", "reuters.com")
        get_settings.cache_clear()
        try:
            async def fake_tool(query, max_results):
                return [
                    {"title": "Allowed", "url": "https://www.reuters.com/a", "content": "x" * 2000},
                    {"title": "Blocked", "url": "https://evil.example.com/b", "content": "y"},
                ]

            result = await InsightAgent()._run_tool_call(fake_tool, "web_search", {"query": "btc"})
            urls = [r["url"] for r in result["results"]]
            assert urls == ["https://www.reuters.com/a"]
            assert len(result["results"][0]["content"]) <= 1200
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_unknown_tool_errors(self):
        async def fake_tool(query, max_results):
            return []

        result = await InsightAgent()._run_tool_call(fake_tool, "not_a_tool", {})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_empty_query_errors(self):
        async def fake_tool(query, max_results):
            return []

        result = await InsightAgent()._run_tool_call(fake_tool, "web_search", {"query": ""})
        assert "error" in result


# ── User store OAuth-ready schema ──────────────────────────────────────


class TestUserStoreProviders:
    def test_provider_link_roundtrip(self, tmp_path):
        store = UserStore(tmp_path / "u.json")
        user = store.create("linked@example.com", "Linked", "supersecret1")
        assert store.get_by_provider_id("google", "missing") is None

        store.link_provider(user["id"], "google", "gid-1")
        assert store.get_by_provider_id("google", "gid-1")["id"] == user["id"]
