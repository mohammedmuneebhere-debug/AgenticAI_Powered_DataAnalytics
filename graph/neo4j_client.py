"""Lazy Neo4j driver wrapper (optional graph persistence).

Phase 1 delivers the connection utility only; Phase 3 lets GraphAnalyzer
mirror its results into Neo4j when GRAPH_STORE=neo4j and the database is
reachable. All failures degrade gracefully to the in-memory graph store.
"""

import logging
from functools import lru_cache
from typing import Any, Optional

from backend.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self) -> None:
        self._driver = None
        self._checked = False

    def _get_driver(self):
        if self._driver is None and not self._checked:
            self._checked = True
            try:
                from neo4j import GraphDatabase

                settings = get_settings()
                driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                    connection_timeout=2.0,
                )
                driver.verify_connectivity()
                self._driver = driver
                logger.info("Neo4j connected at %s", settings.neo4j_uri)
            except Exception as exc:
                logger.info("Neo4j unavailable (%s) — using in-memory graph store", exc.__class__.__name__)
                self._driver = None
        return self._driver

    def available(self) -> bool:
        return self._get_driver() is not None

    def run(self, cypher: str, **params) -> list[dict]:
        """Run a write/read query; returns plain dicts ([] when unavailable)."""
        driver = self._get_driver()
        if driver is None:
            return []
        try:
            with driver.session() as session:
                return [dict(record) for record in session.run(cypher, dict(params))]
        except Exception as exc:
            logger.warning("Neo4j query failed: %s", exc.__class__.__name__)
            return []

    def close(self) -> None:
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                pass
            self._driver = None
            self._checked = False


@lru_cache(maxsize=1)
def get_neo4j_client() -> Neo4jClient:
    return Neo4jClient()
