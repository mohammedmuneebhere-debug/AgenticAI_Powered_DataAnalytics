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
        assert result["model_version"] == "socialiq-template-0.3"

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


# ── Dynamic offline composer ──────────────────────────────────────────


class TestDynamicComposer:
    def _analytics(self) -> dict:
        """Realistic analytics with distinctive values nothing can hardcode."""
        return {
            "record_count": 14,
            "source_counts": {"x": 8, "reddit": 4, "news": 2},
            "sentiment": {
                "overall_label": "positive",
                "average_score": 0.68,
                "confidence": 0.72,
                "distribution": {"positive": 9, "negative": 2, "neutral": 3},
            },
            "emotion": {
                "dominant_emotion": "excitement",
                "distribution": {"excitement": 7, "anxiety": 1, "support": 2, "frustration": 0},
                "confidence": 0.65,
            },
            "topics": {"topics": [{"term": "semiconductor", "count": 11}], "topic_count": 1},
            "trends": {
                "top_trends": [
                    {"topic": "semiconductor", "mentions": 11, "engagement": 4200, "velocity": 6.9, "confidence": 0.9},
                    {"topic": "chip supply", "mentions": 4, "engagement": 800, "velocity": 2.1, "confidence": 0.7},
                ],
                "trend_count": 2,
            },
            "temporal": {
                "timeline": [
                    {"period": "2026-09-12", "sentiment_score": 0.55, "signal_count": 6, "distribution": {}},
                    {"period": "2026-09-13", "sentiment_score": 0.71, "signal_count": 8, "distribution": {}},
                ],
                "spike_detected": True,
            },
        }

    def _evidence(self) -> list:
        return [
            {"type": "statistical", "label": "Overall Sentiment", "value": "positive", "confidence": 0.72, "source": "sentiment_model"},
            {"type": "semantic", "label": "Trend: semiconductor", "value": "velocity=6.90", "confidence": 0.9, "source": "trend_detector"},
        ]

    @pytest.mark.asyncio
    async def test_composer_renders_real_values_no_canned_claims(self):
        result = await InsightAgent().generate(
            query="What is happening with semiconductor supply?",
            evidence=self._evidence(),
            analytics=self._analytics(),
            intent="trend",
            domain="consumer",
            domain_label="Consumer Social Intelligence",
        )
        text = result["text"]
        assert result["model_version"] == "socialiq-template-0.3"

        # Real values rendered
        assert "semiconductor" in text
        assert "14" in text
        assert "x (8)" in text
        assert "0.68" in text
        assert "excitement" in text
        assert "4200" in text or "4,200" in text
        assert "rose from 0.55" in text
        assert "spike was detected" in text

        # The old fabricated claims must be gone for good
        assert "cold brew" not in text.lower()
        assert "+34%" not in text
        assert "tue/thu" not in text.lower()
        assert "2.4x" not in text

    @pytest.mark.asyncio
    async def test_composer_handles_empty_analytics_gracefully(self):
        result = await InsightAgent().generate(
            query="test", evidence=[], analytics={}, intent="general",
        )
        text = result["text"]
        assert "No records were returned" in text
        assert "Insufficient signal diversity" in text
        assert "Re-run with more sources" in text

    @pytest.mark.asyncio
    async def test_composer_renders_domain_analytics_when_present(self):
        analytics = self._analytics() | {
            "volatility": {"level": "HIGH", "index": 0.81},
            "scenarios": [
                {"name": "Breakout", "probability": 0.35, "trigger": "ETF inflow acceleration"},
            ],
        }
        result = await InsightAgent().generate(
            query="test", evidence=self._evidence(), analytics=analytics,
            intent="market", domain="financial", domain_label="Financial Market Intelligence",
        )
        text = result["text"]
        assert "HIGH" in text and "0.81" in text
        assert "Breakout" in text and "35%" in text and "ETF inflow acceleration" in text

    @pytest.mark.asyncio
    async def test_composer_renders_real_regional_interest(self):
        """Regional interest comes from real Google Trends data, never invented."""
        analytics = self._analytics() | {
            "google_trends": {
                "interest_by_region": [
                    {"location": "United States", "geo": "US", "value": 87},
                    {"location": "Germany", "geo": "DE", "value": 64},
                ],
                "related_topics": [],
                "related_queries": [],
            },
        }
        result = await InsightAgent().generate(
            query="test", evidence=self._evidence(), analytics=analytics,
            intent="trend", domain="general", domain_label="General Social Intelligence",
        )
        text = result["text"]
        assert "United States (87)" in text
        assert "Germany (64)" in text
        assert "0-100" in text  # honest unit disclosure

    @pytest.mark.asyncio
    async def test_composer_discloses_missing_regional_data(self):
        result = await InsightAgent().generate(
            query="test", evidence=self._evidence(), analytics=self._analytics(),
            intent="trend", domain="general", domain_label="General Social Intelligence",
        )
        assert "No regional interest data" in result["text"]


# ── Auto-fallback chain (OpenAI → Ollama → composer) ──────────────────


class TestAutoFallbackChain:
    @pytest.mark.asyncio
    async def test_ollama_auto_fallback_when_reachable(self, monkeypatch):
        from backend.config import get_settings

        monkeypatch.setenv("OLLAMA_AUTO_FALLBACK", "true")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()

            async def fake_get(self, url):
                class Resp:
                    status_code = 200

                return Resp()

            async def fake_post(self, url, json=None, **kwargs):
                class Resp:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {"message": {"content": "local ollama answer"}}

                return Resp()

            monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
            monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

            result = await agent.generate(
                query="test", evidence=[], analytics={}, intent="general",
            )
            assert result["model_version"] == f"ollama:{agent.settings.ollama_model}"
            assert "local ollama answer" in result["text"]
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_falls_back_to_composer_when_ollama_unreachable(self, monkeypatch):
        from backend.config import get_settings

        monkeypatch.setenv("OLLAMA_AUTO_FALLBACK", "true")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()

            async def fail_get(self, url):
                raise httpx.ConnectError("connection refused")

            monkeypatch.setattr(httpx.AsyncClient, "get", fail_get)

            result = await agent.generate(
                query="test", evidence=[], analytics={}, intent="general",
            )
            assert result["model_version"] == "socialiq-template-0.3"
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_openai_failure_still_tries_ollama(self, monkeypatch):
        """Chain requirement: OpenAI failing must NOT skip Ollama."""
        from backend.config import get_settings

        monkeypatch.setenv("OPENAI_API_KEY", "sk-invalid")
        monkeypatch.setenv("OLLAMA_AUTO_FALLBACK", "true")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()

            async def fake_get(self, url):
                class Resp:
                    status_code = 200

                return Resp()

            async def fake_post(self, url, json=None, **kwargs):
                class Resp:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {"message": {"content": "ollama rescued the answer"}}

                return Resp()

            monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
            monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

            class FailingCompletions:
                async def create(self, **kwargs):
                    raise RuntimeError("simulated openai outage")

            class FailingChat:
                completions = FailingCompletions()

            class FailingOpenAI:
                def __init__(self, **kwargs):
                    self.chat = FailingChat()

            import sys
            import types

            fake_module = types.ModuleType("openai")
            fake_module.AsyncOpenAI = FailingOpenAI
            monkeypatch.setitem(sys.modules, "openai", fake_module)

            result = await agent.generate(
                query="test", evidence=[], analytics={}, intent="general",
            )
            assert result["model_version"].startswith("ollama:")
            assert "ollama rescued the answer" in result["text"]
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_openai_takes_priority_over_live_ollama(self, monkeypatch):
        from backend.config import get_settings

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OLLAMA_AUTO_FALLBACK", "true")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()

            ollama_called = {"post": False}

            async def fake_get(self, url):
                class Resp:
                    status_code = 200

                return Resp()

            async def fake_post(self, url, json=None, **kwargs):
                if "ollama" in url or ":11434" in url:
                    ollama_called["post"] = True
                    raise httpx.ConnectError("ollama must not be called")

                class Resp:
                    def json(self):
                        return {}

                raise AssertionError("openai SDK should be used, not raw httpx POST")

            monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
            monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

            class FakeCompletions:
                async def create(self, **kwargs):
                    class FakeMessage:
                        content = "openai narrative"
                        tool_calls = None

                    class FakeChoice:
                        message = FakeMessage()

                    class FakeResponse:
                        choices = [FakeChoice()]

                    return FakeResponse()

            class FakeChat:
                completions = FakeCompletions()

            class FakeOpenAI:
                def __init__(self, **kwargs):
                    self.chat = FakeChat()

            import sys
            import types

            fake_module = types.ModuleType("openai")
            fake_module.AsyncOpenAI = FakeOpenAI
            monkeypatch.setitem(sys.modules, "openai", fake_module)

            result = await agent.generate(
                query="test", evidence=[], analytics={}, intent="general",
            )
            assert result["model_version"] == "gpt-4o-mini"
            assert "openai narrative" in result["text"]
            assert not ollama_called["post"]
        finally:
            get_settings.cache_clear()


# ── OpenAI 401 circuit breaker ────────────────────────────────────────


class TestOpenAICircuitBreaker:
    @pytest.mark.asyncio
    async def test_auth_error_trips_breaker_and_next_call_skips_openai(self, monkeypatch):
        """After an OpenAI AuthenticationError, the next request must go
        straight to Ollama without touching OpenAI again."""
        from backend.config import get_settings

        monkeypatch.setenv("OPENAI_API_KEY", "sk-invalid")
        monkeypatch.setenv("OLLAMA_AUTO_FALLBACK", "true")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()
            openai_calls = {"count": 0}

            async def fake_get(self, url):
                class Resp:
                    status_code = 200

                return Resp()

            async def fake_post(self, url, json=None, **kwargs):
                class Resp:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {"message": {"content": "ollama after breaker"}}

                return Resp()

            monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
            monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

            class AuthFailCompletions:
                async def create(self, **kwargs):
                    openai_calls["count"] += 1
                    import openai

                    raise openai.AuthenticationError(
                        message="bad key",
                        response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com")),
                        body=None,
                    )

            class AuthFailChat:
                completions = AuthFailCompletions()

            class AuthFailOpenAI:
                def __init__(self, **kwargs):
                    self.chat = AuthFailChat()

            import sys
            import types

            fake_module = types.ModuleType("openai")
            fake_module.AsyncOpenAI = AuthFailOpenAI
            fake_module.AuthenticationError = __import__("openai").AuthenticationError
            monkeypatch.setitem(sys.modules, "openai", fake_module)

            # First call: OpenAI attempted, 401s, breaker trips, Ollama answers
            first = await agent.generate(query="q1", evidence=[], analytics={}, intent="general")
            assert openai_calls["count"] == 1
            assert first["model_version"].startswith("ollama:")

            # Second call: breaker open -> OpenAI must NOT be attempted
            second = await agent.generate(query="q2", evidence=[], analytics={}, intent="general")
            assert openai_calls["count"] == 1, "OpenAI retried despite open breaker"
            assert second["model_version"].startswith("ollama:")
        finally:
            get_settings.cache_clear()


# ── Ollama keep_alive (cold-start prevention) ─────────────────────────


class TestOllamaKeepAlive:
    @pytest.mark.asyncio
    async def test_keep_alive_sent_in_ollama_payload(self, monkeypatch):
        """Every /api/chat payload must carry keep_alive so models stay warm."""
        from backend.config import get_settings

        monkeypatch.setenv("OLLAMA_KEEP_ALIVE", "45m")
        get_settings.cache_clear()
        try:
            agent = InsightAgent()
            captured: dict = {}

            async def fake_post(self, url, json=None, **kwargs):
                captured["url"] = url
                captured["payload"] = json

                class Resp:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {"message": {"content": "warm answer"}}

                return Resp()

            monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

            result = await agent._ollama_generate(
                "test-model", "q", [], {}, "general", "general", "General"
            )
            assert captured["payload"]["keep_alive"] == "45m"
            assert captured["payload"]["model"] == "test-model"
            assert result["model_version"] == "ollama:test-model"
        finally:
            get_settings.cache_clear()


# ── Top relevant posts ranking ────────────────────────────────────────


class TestTopRelevantPosts:
    def _planner(self):
        from agents.master.planner import MasterAgent

        return MasterAgent()

    def test_ranks_by_engagement_plus_term_overlap(self):
        planner = self._planner()
        records = [
            {"platform": "x_scraper", "text": "GTA 6 looks incredible, can't wait for the trailer", "author": "gamer1", "engagement": {"likes": 10, "replies": 1, "reposts": 2, "views": 100}},
            {"platform": "x_scraper", "text": "Random unrelated post about cooking pasta", "author": "chef", "engagement": {"likes": 5000, "replies": 100, "reposts": 900, "views": 90000}},
            {"platform": "x_scraper", "text": "GTA 6 release date rumors are everywhere", "author": "newsbot", "engagement": {"likes": 300, "replies": 20, "reposts": 40, "views": 20000}, "url": "https://x.com/newsbot/1"},
            {"platform": "news", "text": "Not an X post", "author": "reuters", "engagement": {}},
        ]
        posts = planner._top_relevant_posts(records, "What is new with GTA 6?")

        assert len(posts) == 3  # news record excluded
        # Relevant posts beat raw engagement: the pasta post has 50x the
        # engagement but zero term overlap with the query
        assert posts[0]["author"] in ("gamer1", "newsbot")
        assert all("GTA" in p["text"] or "GTA" in p["text"].lower() or p["author"] == "chef" for p in posts)
        assert posts[0]["rank"] == 1
        assert posts[0]["engagement_total"] >= 0

    def test_no_x_records_returns_empty(self):
        planner = self._planner()
        posts = planner._top_relevant_posts(
            [{"platform": "news", "text": "hello", "author": "x"}], "query"
        )
        assert posts == []

    def test_sample_posts_rank_below_live_data(self):
        planner = self._planner()
        records = [
            {"platform": "x", "text": "query topic here", "author": "@live_user", "engagement": {"likes": 5, "replies": 0, "reposts": 0, "views": 0}},
            {"platform": "x", "text": "query topic here", "author": "@sample_user", "engagement": {"likes": 500, "replies": 50, "reposts": 60, "views": 9000}},
        ]
        posts = planner._top_relevant_posts(records, "query topic")
        assert posts[0]["author"] == "@live_user"

    def test_append_top_posts_formats_markdown(self):
        planner = self._planner()
        posts = [{
            "rank": 1, "text": "GTA 6 news", "author": "newsbot", "platform": "x_scraper",
            "url": "https://x.com/newsbot/1", "engagement_total": 1234, "relevance_score": 88.0,
        }]
        out = planner._append_top_posts("Base response.", posts)
        assert "Most relevant X posts" in out
        assert "@newsbot" in out
        assert "1,234 engagements" in out
        assert "https://x.com/newsbot/1" in out
        # No posts -> unchanged response
        assert planner._append_top_posts("Base.", []) == "Base."
