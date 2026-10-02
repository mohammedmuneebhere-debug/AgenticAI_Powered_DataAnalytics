"""Synchronous SQLAlchemy engine + session helpers.

The store interfaces (ChatStore / UserStore) and their callers are
synchronous, so the persistence layer uses the psycopg2 driver. The asyncpg
URL from settings is translated transparently; `alembic` uses the same
translation in migrations/env.py.
"""

import logging
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings

logger = logging.getLogger(__name__)


def sync_url(url: str | None = None) -> str:
    """Translate an asyncpg-style URL to the psycopg2 sync driver."""
    url = url or get_settings().database_url
    return url.replace("+asyncpg", "+psycopg2")


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        sync_url(),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "connect_timeout": 3,
            "options": "-c timezone=utc",
        },
        future=True,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


@contextmanager
def session_scope():
    """Transactional scope: commit on success, rollback on error."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    """Return True when the configured PostgreSQL answers `SELECT 1`."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("PostgreSQL unreachable: %s", exc.__class__.__name__)
        return False
    except Exception as exc:  # driver-level failures (e.g. psycopg2 missing)
        logger.warning("PostgreSQL check failed: %s", exc)
        return False


@lru_cache(maxsize=1)
def pg_available() -> bool:
    """Check-once-per-process gate used by the persistence facades."""
    return ping()
