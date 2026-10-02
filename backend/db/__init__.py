"""SQLAlchemy persistence layer (Phase 1).

PostgreSQL is the durable store for users, chat sessions/messages and
provenance records. The app deliberately degrades gracefully: when
``JSON_FALLBACK`` is true (the default) the JSON file stores are used and
nothing in this package is imported at runtime.
"""

from backend.db.base import Base
from backend.db.session import get_engine, session_scope, ping, pg_available

__all__ = ["Base", "get_engine", "session_scope", "ping", "pg_available"]
