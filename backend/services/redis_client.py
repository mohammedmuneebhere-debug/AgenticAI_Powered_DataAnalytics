"""Lazy Redis access for caching and the JWT blacklist.

Everything degrades to a no-op when Redis is unreachable (Docker down, etc.):
``available()`` returns False, reads return None, writes are dropped. Callers
must treat Redis as a pure optimization — correctness never depends on it.
"""

import json
import logging
from functools import lru_cache
from typing import Any, Optional

import redis as redis_lib

from backend.config import get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    ANALYSIS_PREFIX = "socialiq:analysis:"
    BLACKLIST_PREFIX = "socialiq:blacklist:"

    def __init__(self) -> None:
        self._client: Optional[redis_lib.Redis] = None
        self._checked = False

    def _get_client(self) -> Optional[redis_lib.Redis]:
        if self._client is None and not self._checked:
            self._checked = True
            try:
                client = redis_lib.Redis.from_url(
                    get_settings().redis_url,
                    socket_connect_timeout=1.5,
                    socket_timeout=1.5,
                    decode_responses=True,
                )
                client.ping()
                self._client = client
                logger.info("Redis connected at %s", get_settings().redis_url)
            except Exception as exc:
                logger.info("Redis unavailable (%s) — cache/blacklist disabled", exc.__class__.__name__)
        return self._client

    def available(self) -> bool:
        return self._get_client() is not None

    # -- generic JSON cache --------------------------------------------------

    def get_json(self, key: str) -> Optional[Any]:
        client = self._get_client()
        if client is None:
            return None
        try:
            raw = client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> bool:
        client = self._get_client()
        if client is None or ttl_seconds <= 0:
            return False
        try:
            client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
            return True
        except Exception:
            return False

    # -- analysis results (keyed by dataset hash; Phase 3 consumers) ---------

    def cache_analysis(self, cache_key: str, payload: Any) -> bool:
        ttl = get_settings().analysis_cache_ttl_seconds
        return self.set_json(f"{self.ANALYSIS_PREFIX}{cache_key}", payload, ttl)

    def get_analysis(self, cache_key: str) -> Optional[Any]:
        return self.get_json(f"{self.ANALYSIS_PREFIX}{cache_key}")

    # -- JWT blacklist (logout revocation) -----------------------------------

    def blacklist_token(self, jti: str, ttl_seconds: int) -> bool:
        return self.set_json(f"{self.BLACKLIST_PREFIX}{jti}", True, ttl_seconds)

    def is_blacklisted(self, jti: str) -> bool:
        client = self._get_client()
        if client is None:
            return False
        try:
            return client.exists(f"{self.BLACKLIST_PREFIX}{jti}") > 0
        except Exception:
            return False


@lru_cache(maxsize=1)
def get_redis_cache() -> RedisCache:
    return RedisCache()
