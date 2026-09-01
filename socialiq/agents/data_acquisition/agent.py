"""Data Acquisition Agent — retrieves data from social platforms and search engines."""

import json
import re
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Awaitable

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)
SAMPLE_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample"

PLATFORM_SAMPLE_FILES = {
    "x": {"coffee": "coffee_posts.json", "btc": "btc_posts.json", "default": "coffee_posts.json"},
    "telegram": {"coffee": "coffee_posts.json", "btc": "btc_posts.json", "default": "coffee_posts.json"},
    "instagram": {"default": "instagram_posts.json"},
    "pinterest": {"default": "pinterest_pins.json"},
    "google_search": {"coffee": "google_search_results.json", "btc": "google_search_results.json", "default": "google_search_results.json"},
}


class DataAcquisitionAgent:
    """Targeted retrieval from social platforms, search engines, and sample sources."""

    def __init__(self):
        self.settings = get_settings()

    async def acquire(
        self,
        query: str,
        entities: list[str],
        platforms: list[str],
        time_range: str = "recent",
        domain: str = "general",
    ) -> dict[str, Any]:
        records: list[dict] = []
        sources_hit: list[str] = []

        fetchers: dict[str, tuple[bool, Callable[..., Awaitable[list[dict]]]]] = {
            "x": (bool(self.settings.x_bearer_token), self._fetch_x),
            "telegram": (bool(self.settings.telegram_bot_token), self._fetch_telegram),
            "instagram": (bool(self.settings.instagram_access_token), self._fetch_instagram),
            "pinterest": (bool(self.settings.pinterest_access_token), self._fetch_pinterest),
            "google_search": (
                bool(self.settings.google_search_api_key and self.settings.google_search_cx),
                self._fetch_google_search,
            ),
        }

        active_platforms = [p for p in platforms if p != "sample"]
        if not active_platforms:
            active_platforms = ["x", "telegram", "instagram", "pinterest", "google_search"]

        for platform in active_platforms:
            has_creds, fetcher = fetchers.get(platform, (False, None))
            platform_records: list[dict] = []

            if fetcher and has_creds:
                try:
                    platform_records = await fetcher(query, entities)
                except Exception as exc:
                    logger.warning("Live fetch failed for %s: %s", platform, exc)

            if not platform_records:
                platform_records = self._load_platform_sample(platform, entities, query, domain)

            if platform_records:
                records.extend(platform_records)
                sources_hit.append(platform)

        if not records:
            records = self._load_domain_sample(entities, query, domain)
            sources_hit.append("sample")

        snapshot_id = hashlib.sha256(
            json.dumps(records, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        return {
            "records": records,
            "platforms": sources_hit or platforms,
            "query": query,
            "time_range": time_range,
            "snapshot_id": snapshot_id,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "count": len(records),
        }

    # ── Live API integrations ──────────────────────────────────────────

    async def _fetch_x(self, query: str, entities: list[str]) -> list[dict]:
        """X API v2 recent search — https://docs.x.com/x-api/posts/search/quickstart/recent-search"""
        search_query = self._build_search_query(query, entities)
        headers = {"Authorization": f"Bearer {self.settings.x_bearer_token}"}
        params = {
            "query": search_query,
            "max_results": 20,
            "tweet.fields": "created_at,public_metrics,author_id",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://api.x.com/2/tweets/search/recent",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        records = []
        for tweet in data.get("data", []):
            metrics = tweet.get("public_metrics", {})
            records.append({
                "id": tweet["id"],
                "platform": "x",
                "text": tweet.get("text", ""),
                "author": tweet.get("author_id", "unknown"),
                "timestamp": tweet.get("created_at", datetime.now(timezone.utc).isoformat()),
                "engagement": {
                    "likes": metrics.get("like_count", 0),
                    "reposts": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                },
            })
        return records

    async def _fetch_telegram(self, query: str, entities: list[str]) -> list[dict]:
        """Telegram Bot API — https://core.telegram.org/bots/api#getupdates"""
        token = self.settings.telegram_bot_token
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        params = {"limit": 50}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        if not data.get("ok"):
            return []

        keywords = self._query_keywords(query, entities)
        records = []
        for update in data.get("result", []):
            msg = update.get("message") or update.get("channel_post")
            if not msg or not msg.get("text"):
                continue
            text = msg["text"]
            if keywords and not any(kw in text.lower() for kw in keywords):
                continue
            chat = msg.get("chat", {})
            records.append({
                "id": str(msg.get("message_id", update.get("update_id"))),
                "platform": "telegram",
                "text": text,
                "author": chat.get("title") or chat.get("username", "unknown"),
                "timestamp": datetime.fromtimestamp(
                    msg.get("date", 0), tz=timezone.utc
                ).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
            })
        return records[:20]

    async def _fetch_instagram(self, query: str, entities: list[str]) -> list[dict]:
        """Instagram Graph API — https://developers.facebook.com/docs/instagram-api/reference/ig-user/media"""
        user_id = self.settings.instagram_user_id
        token = self.settings.instagram_access_token
        url = f"https://graph.facebook.com/v19.0/{user_id}/media"
        params = {
            "fields": "id,caption,timestamp,like_count,comments_count,permalink",
            "access_token": token,
            "limit": 25,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        keywords = self._query_keywords(query, entities)
        records = []
        for item in data.get("data", []):
            caption = item.get("caption") or ""
            if keywords and not any(kw in caption.lower() for kw in keywords):
                continue
            records.append({
                "id": item["id"],
                "platform": "instagram",
                "text": caption or f"Instagram media {item['id']}",
                "author": f"@{user_id}",
                "timestamp": item.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "engagement": {
                    "likes": item.get("like_count", 0),
                    "reposts": 0,
                    "replies": item.get("comments_count", 0),
                    "saves": 0,
                },
                "url": item.get("permalink"),
            })
        return records

    async def _fetch_pinterest(self, query: str, entities: list[str]) -> list[dict]:
        """Pinterest API v5 — https://developers.pinterest.com/docs/api/v5/#tag/search"""
        search_query = self._build_search_query(query, entities)
        headers = {"Authorization": f"Bearer {self.settings.pinterest_access_token}"}
        params = {"query": search_query, "page_size": 20}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://api.pinterest.com/v5/search/pins",
                headers=headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        records = []
        for pin in data.get("items", []):
            title = pin.get("title") or ""
            desc = pin.get("description") or ""
            text = f"{title}. {desc}".strip() or f"Pinterest pin {pin.get('id', '')}"
            records.append({
                "id": pin.get("id", ""),
                "platform": "pinterest",
                "text": text,
                "author": pin.get("board_owner", {}).get("username", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement": {
                    "likes": 0,
                    "reposts": 0,
                    "replies": 0,
                    "saves": pin.get("save_count", 0),
                },
                "url": pin.get("link") or pin.get("media", {}).get("media_type"),
            })
        return records

    async def _fetch_google_search(self, query: str, entities: list[str]) -> list[dict]:
        """Google Custom Search JSON API — https://developers.google.com/custom-search/v1/overview"""
        search_query = self._build_search_query(query, entities)
        params = {
            "key": self.settings.google_search_api_key,
            "cx": self.settings.google_search_cx,
            "q": search_query,
            "num": 10,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        records = []
        for item in data.get("items", []):
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            records.append({
                "id": item.get("cacheId") or item.get("link", "")[:32],
                "platform": "google_search",
                "text": f"{title} — {snippet}",
                "author": item.get("displayLink", "web"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                "url": item.get("link"),
            })
        return records

    # ── Sample data fallbacks ──────────────────────────────────────────

    def _load_platform_sample(
        self, platform: str, entities: list[str], query: str, domain: str
    ) -> list[dict]:
        files = PLATFORM_SAMPLE_FILES.get(platform)
        if not files:
            return []

        entity_key = self._resolve_entity_key(entities, query, domain)
        filename = files.get(entity_key) or files.get("default")
        path = SAMPLE_DATA_PATH / filename
        if not path.exists():
            return []

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [r for r in data if r.get("platform") == platform]

    def _load_domain_sample(self, entities: list[str], query: str, domain: str) -> list[dict]:
        entity_key = self._resolve_entity_key(entities, query, domain)
        domain_files = {
            "financial": "btc_posts.json",
            "consumer": "coffee_posts.json",
            "creator": "instagram_posts.json",
        }
        filename = domain_files.get(domain, {"coffee": "coffee_posts.json", "btc": "btc_posts.json"}.get(entity_key, "coffee_posts.json"))
        path = SAMPLE_DATA_PATH / filename
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return [{
            "id": "sample-1",
            "platform": "sample",
            "text": f"Sample post related to: {query}",
            "author": "@sample_user",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engagement": {"likes": 120, "reposts": 34, "replies": 12},
        }]

    # ── Helpers ────────────────────────────────────────────────────────

    def _resolve_entity_key(self, entities: list[str], query: str, domain: str) -> str:
        q = query.lower()
        if domain == "financial" or re.search(r"\b(btc|bitcoin|crypto)\b", q):
            return "btc"
        if "btc" in entities or "crypto" in entities:
            return "btc"
        if domain == "consumer" or re.search(r"\bcoffee\b", q):
            return "coffee"
        return entities[0] if entities else "default"

    def _build_search_query(self, query: str, entities: list[str]) -> str:
        if entities and entities[0] != "general":
            return f"{query} {entities[0]}"
        return query

    def _query_keywords(self, query: str, entities: list[str]) -> list[str]:
        words = re.findall(r"\b[a-z]{3,}\b", query.lower())
        stop = {"the", "and", "for", "what", "why", "how", "tell", "analyze", "should", "this", "that", "with"}
        kws = [w for w in words if w not in stop]
        kws.extend(e for e in entities if e != "general")
        return list(dict.fromkeys(kws))[:8]
