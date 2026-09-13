"""Tests for the Apify X/Twitter scraper integration."""

import asyncio
from datetime import datetime, timezone

import pytest

import agents.data_acquisition.agent as acquisition_module
from agents.data_acquisition.agent import DataAcquisitionAgent
from backend.services.tools_registry import get_tools_catalog


def _run(coro):
    return asyncio.run(coro)


# ── Registry ──────────────────────────────────────────────────────────


def test_registry_includes_x_scraper_source():
    sources = {s.id: s for s in get_tools_catalog()["sources"]}
    assert "x_scraper" in sources
    assert sources["x_scraper"].requires_key == "APIFY_API_KEY"
    assert sources["x_scraper"].default_enabled is False


# ── Timestamp parsing ─────────────────────────────────────────────────


class TestTimestampParsing:
    def test_epoch_milliseconds(self):
        ts = DataAcquisitionAgent._parse_tweet_timestamp({"createdAt": 1726200000000})
        parsed = datetime.fromisoformat(ts)
        assert parsed.year == 2024

    def test_legacy_twitter_format(self):
        ts = DataAcquisitionAgent._parse_tweet_timestamp(
            {"createdAt": "Wed Oct 10 20:19:24 +0000 2018"}
        )
        assert ts == "2018-10-10T20:19:24+00:00"

    def test_iso_with_z_suffix(self):
        ts = DataAcquisitionAgent._parse_tweet_timestamp({"createdAt": "2026-01-05T10:00:00Z"})
        assert ts == "2026-01-05T10:00:00+00:00"

    def test_missing_date_returns_valid_iso_now(self):
        ts = DataAcquisitionAgent._parse_tweet_timestamp({})
        datetime.fromisoformat(ts)  # must not raise


# ── _fetch_x_scraper against a mocked Apify API ───────────────────────


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Captures the run-sync request and returns canned dataset items."""

    last_request = None

    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, params=None, json=None):
        _FakeAsyncClient.last_request = {"url": url, "params": params, "json": json}
        return _FakeResponse(self._payload)


APIFY_ITEMS = [
    {
        "id": "123",
        "text": "Big coffee news today",
        "author": {"userName": "beanfan"},
        "createdAt": "2026-09-10T08:00:00.000Z",
        "likeCount": 42,
        "retweetCount": 7,
        "replyCount": 3,
        "viewCount": 1000,
        "url": "https://x.com/beanfan/status/123",
    },
    {"id": "124", "text": "", "author": {"userName": "empty"}},  # dropped: no text
]


@pytest.fixture()
def scraper_agent(monkeypatch):
    monkeypatch.setenv("APIFY_API_KEY", "test-apify-key")
    monkeypatch.setenv("APIFY_X_SCRAPER_ACTOR", "acme~tweet-scraper")
    from backend.config import get_settings

    get_settings.cache_clear()
    return DataAcquisitionAgent()


def test_fetch_x_scraper_call_shape_and_normalization(scraper_agent, monkeypatch):
    monkeypatch.setattr(
        acquisition_module.httpx, "AsyncClient", lambda timeout=None: _FakeAsyncClient(APIFY_ITEMS)
    )

    records = _run(scraper_agent._fetch_x_scraper("coffee trends", ["coffee"]))

    req = _FakeAsyncClient.last_request
    assert req["url"].startswith("https://api.apify.com/v2/acts/acme~tweet-scraper/")
    assert req["url"].endswith("run-sync-get-dataset-items")
    assert req["params"]["token"] == "test-apify-key"
    assert req["json"]["searchTerms"] == ["coffee trends coffee"]
    assert req["json"]["maxItems"] == 20

    # Records are normalized to the internal schema
    assert len(records) == 1  # empty-text item dropped
    rec = records[0]
    assert rec["platform"] == "x_scraper"
    assert rec["id"] == "123"
    assert rec["author"] == "beanfan"
    assert rec["engagement"] == {"likes": 42, "reposts": 7, "replies": 3, "views": 1000}
    assert rec["url"] == "https://x.com/beanfan/status/123"


def test_fetch_x_scraper_unwraps_envelope(scraper_agent, monkeypatch):
    monkeypatch.setattr(
        acquisition_module.httpx,
        "AsyncClient",
        lambda timeout=None: _FakeAsyncClient({"items": APIFY_ITEMS}),
    )
    records = _run(scraper_agent._fetch_x_scraper("coffee", []))
    assert len(records) == 1


def test_fetch_x_scraper_http_error_raises(scraper_agent, monkeypatch):
    import httpx

    class _FailingClient(_FakeAsyncClient):
        async def post(self, url, params=None, json=None):
            return _FakeResponse([], status_code=401)

    monkeypatch.setattr(
        acquisition_module.httpx, "AsyncClient", lambda timeout=None: _FailingClient([])
    )
    with pytest.raises(httpx.HTTPStatusError):
        _run(scraper_agent._fetch_x_scraper("coffee", []))


# ── acquire() routing ─────────────────────────────────────────────────


def test_acquire_routes_x_scraper_when_enabled(scraper_agent, monkeypatch):
    calls = []

    async def fake_fetch(query, entities):
        calls.append(query)
        return [
            {
                "id": "s1",
                "platform": "x_scraper",
                "text": "scraped post",
                "author": "someone",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 1, "reposts": 0, "replies": 0},
            }
        ]

    monkeypatch.setattr(scraper_agent, "_fetch_x_scraper", fake_fetch)

    result = _run(scraper_agent.acquire("coffee trends", ["coffee"], ["x_scraper"]))

    assert calls == ["coffee trends"]  # acquire passes the raw query; query building is internal
    assert result["live_sources"] == ["x_scraper"]
    assert result["count"] == 1
    assert result["records"][0]["platform"] == "x_scraper"


def test_acquire_skips_x_scraper_without_key(monkeypatch):
    monkeypatch.setenv("APIFY_API_KEY", "")
    from backend.config import get_settings

    get_settings.cache_clear()
    agent = DataAcquisitionAgent()

    def _no_call(query, entities):
        raise AssertionError("fetcher must not run without an API key")

    monkeypatch.setattr(agent, "_fetch_x_scraper", _no_call)

    # Only request x_scraper; without a key the fetcher is skipped entirely,
    # so there must be no live source and no crash.
    result = _run(agent.acquire("coffee", ["coffee"], ["x_scraper"]))
    assert "x_scraper" not in result["live_sources"]
