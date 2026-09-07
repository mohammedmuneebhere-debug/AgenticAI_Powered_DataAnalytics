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
    "google_trends": {"coffee": "google_search_results.json", "btc": "google_search_results.json", "default": "google_search_results.json"},
    "news": {"coffee": "coffee_posts.json", "btc": "btc_posts.json", "default": "coffee_posts.json"},
    "reddit": {"coffee": "coffee_posts.json", "btc": "btc_posts.json", "default": "coffee_posts.json"},
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
        live_sources: list[str] = []

        fetchers: dict[str, tuple[bool, Callable[..., Awaitable[list[dict]]]]] = {
            "x": (bool(self.settings.x_bearer_token), self._fetch_x),
            "telegram": (bool(self.settings.telegram_bot_token), self._fetch_telegram),
            "instagram": (bool(self.settings.instagram_access_token), self._fetch_instagram),
            "pinterest": (bool(self.settings.pinterest_access_token), self._fetch_pinterest),
            "google_search": (
                bool(self.settings.serpapi_api_key),
                self._fetch_google_search,
            ),
            "google_trends": (
                bool(self.settings.serpapi_api_key),
                self._fetch_google_trends,
            ),
            "news": (bool(self.settings.news_api_key), self._fetch_news),
            "reddit": (bool(self.settings.reddit_client_id), self._fetch_reddit),
        }

        active_platforms = [p for p in platforms if p != "sample"]
        if not active_platforms:
            active_platforms = ["x", "telegram", "instagram", "pinterest", "google_search", "google_trends", "news", "reddit"]

        for platform in active_platforms:
            has_creds, fetcher = fetchers.get(platform, (False, None))
            platform_records: list[dict] = []

            if fetcher and has_creds:
                try:
                    platform_records = await fetcher(query, entities)
                    if platform_records:
                        live_sources.append(platform)
                except Exception as exc:
                    if isinstance(exc, httpx.HTTPStatusError):
                        logger.warning(
                            "Live fetch failed for %s with HTTP status %s",
                            platform,
                            exc.response.status_code,
                        )
                    else:
                        logger.warning("Live fetch failed for %s: %s", platform, type(exc).__name__)

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
            "live_sources": live_sources,
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
        """Google Search results through SerpAPI."""
        search_query = self._build_search_query(query, entities)
        params = {
            "api_key": self.settings.serpapi_api_key,
            "engine": "google",
            "q": search_query,
            "num": 10,
            "hl": "en",
        }
        if self.settings.serpapi_google_domain:
            params["google_domain"] = self.settings.serpapi_google_domain
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()

        records = []
        for item in data.get("organic_results", [])[:10]:
            snippet = item.get("snippet", "")
            title = item.get("title", "")
            records.append({
                "id": str(item.get("position") or item.get("link", "")[:32]),
                "platform": "google_search",
                "text": f"{title} — {snippet}",
                "author": item.get("source") or item.get("displayed_link", "web"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                "url": item.get("link"),
            })
        return records

    async def _fetch_google_trends(self, query: str, entities: list[str]) -> list[dict]:
        """Google Trends chart data through SerpAPI."""
        search_query = self._build_search_query(query, entities)
        params = {
            "api_key": self.settings.serpapi_api_key,
            "engine": "google_trends",
            "q": search_query,
            "hl": "en",
        }
        if self.settings.serpapi_trends_date:
            params["date"] = self.settings.serpapi_trends_date
        if self.settings.serpapi_trends_geo:
            params["geo"] = self.settings.serpapi_trends_geo

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()

        records = []
        for point in data.get("interest_over_time", {}).get("timeline_data", []):
            values = point.get("values") or []
            value = values[0].get("value", 0) if values else 0
            records.append({
                "id": f"google-trends-{point.get('timestamp', point.get('date', 'unknown'))}",
                "platform": "google_trends",
                "text": f"{search_query} search interest: {value}",
                "author": "Google Trends",
                "timestamp": point.get("timestamp") or point.get("date") or datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                "trend_value": value,
                "trend_kind": "interest_over_time",
                "url": "https://trends.google.com/",
            })

        for region in self._trend_items(data.get("interest_by_region")):
            location = str(region.get("location") or region.get("geo") or "Unknown region")
            value = self._trend_value(region)
            records.append({
                "id": f"google-trends-region-{region.get('geo', location)}",
                "platform": "google_trends",
                "text": f"{search_query} search interest in {location}: {value}",
                "author": "Google Trends",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                "trend_value": value,
                "trend_value_label": region.get("value"),
                "trend_kind": "interest_by_region",
                "region": location,
                "region_code": region.get("geo"),
                "coordinates": region.get("coordinates"),
                "url": "https://trends.google.com/",
            })

        for section, trend_kind, label_key in (
            ("related_topics", "related_topic", "topic"),
            ("related_queries", "related_query", "query"),
        ):
            related = data.get(section) or {}
            if not isinstance(related, dict):
                continue
            for ranking, items in related.items():
                if ranking not in {"top", "rising"}:
                    continue
                for item in self._trend_items(items):
                    label = self._related_label(item, label_key)
                    if not label:
                        continue
                    value = self._trend_value(item)
                    records.append({
                        "id": f"google-trends-{trend_kind}-{ranking}-{label}",
                        "platform": "google_trends",
                        "text": f"Related Google Trends {label_key} for {search_query}: {label}",
                        "author": "Google Trends",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                        "trend_value": value,
                        "trend_value_label": item.get("value"),
                        "trend_kind": trend_kind,
                        "trend_category": ranking,
                        "related_term": label,
                        "related_type": (
                            item.get("topic", {}).get("type")
                            if isinstance(item.get("topic"), dict)
                            else None
                        ),
                        "url": item.get("link") or "https://trends.google.com/",
                    })
        return records

    def _trend_items(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        return []

    def _trend_value(self, item: dict[str, Any]) -> float:
        raw_value = item.get("extracted_value", item.get("value", 0))
        if isinstance(raw_value, str):
            match = re.search(r"-?\d+(?:\.\d+)?", raw_value.replace(",", ""))
            raw_value = match.group(0) if match else 0
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            return 0.0

    def _related_label(self, item: dict[str, Any], label_key: str) -> str:
        value = item.get(label_key)
        if isinstance(value, dict):
            value = value.get("title") or value.get("value")
        return str(value or "").strip()

    async def _fetch_news(self, query: str, entities: list[str]) -> list[dict]:
        """NewsAPI search — https://newsapi.org/docs/endpoints/everything"""
        if not self.settings.news_api_key:
            return []
        search_query = self._build_search_query(query, entities)
        params = {
            "apiKey": self.settings.news_api_key,
            "q": search_query,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 20,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://newsapi.org/v2/everything", params=params)
            resp.raise_for_status()
            data = resp.json()

        records = []
        for article in data.get("articles", []):
            title = article.get("title") or "News article"
            description = article.get("description") or ""
            records.append({
                "id": article.get("url") or article.get("publishedAt") or title,
                "platform": "news",
                "text": f"{title} — {description}".strip(" — "),
                "author": article.get("source", {}).get("name", "news"),
                "timestamp": article.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                "engagement": {"likes": 0, "reposts": 0, "replies": 0},
                "url": article.get("url"),
                "title": title,
                "description": description,
                "source": article.get("source", {}).get("name", "news"),
                "published_at": article.get("publishedAt"),
            })
        return records

    async def _fetch_reddit(self, query: str, entities: list[str]) -> list[dict]:
        """Reddit search via OAuth client credentials — https://www.reddit.com/dev/api/"""
        client_id = self.settings.reddit_client_id
        client_secret = self.settings.reddit_client_secret
        if not client_id or not client_secret:
            return []

        search_query = self._build_search_query(query, entities)
        user_agent = "socialiq/0.1"
        auth = httpx.BasicAuth(client_id, client_secret)
        headers = {"User-Agent": user_agent}

        async with httpx.AsyncClient(timeout=20) as client:
            token_resp = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                data={"grant_type": "client_credentials"},
                auth=auth,
                headers=headers,
            )
            token_resp.raise_for_status()
            token = token_resp.json().get("access_token")
            if not token:
                return []

            search_resp = await client.get(
                "https://oauth.reddit.com/search",
                params={"q": search_query, "restrict_sr": "false", "sort": "relevance", "limit": 10, "t": "week"},
                headers={**headers, "Authorization": f"bearer {token}"},
            )
            search_resp.raise_for_status()
            data = search_resp.json()

        records = []
        for item in data.get("data", {}).get("children", []):
            post = item.get("data", {})
            title = post.get("title") or "Reddit discussion"
            selftext = post.get("selftext") or ""
            text = f"{title} — {selftext}".strip(" — ")
            records.append({
                "id": str(post.get("id", "")),
                "platform": "reddit",
                "text": text,
                "author": post.get("author", "reddit"),
                "timestamp": datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc).isoformat(),
                "engagement": {
                    "likes": post.get("ups", 0),
                    "reposts": 0,
                    "replies": post.get("num_comments", 0),
                },
                "url": f"https://www.reddit.com{post.get('permalink', '')}",
            })
        return records

    # ── Sample data fallbacks ──────────────────────────────────────────

    def _load_platform_sample(
        self, platform: str, entities: list[str], query: str, domain: str
    ) -> list[dict]:
        if domain == "general" and self._resolve_entity_key(entities, query, domain) == "general":
            return []
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
        if domain == "general" and entity_key not in {"coffee", "btc"}:
            now = datetime.now(timezone.utc).isoformat()
            return [
                {
                    "id": f"query-sample-{index}",
                    "platform": "sample",
                    "text": f"{query} discussion signal {index}",
                    "author": f"sample_source_{index}",
                    "timestamp": now,
                    "engagement": {"likes": 10 + index * 4, "reposts": index},
                }
                for index in range(1, 6)
            ]
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
