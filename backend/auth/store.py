"""User persistence with pluggable backends (JSON default, PostgreSQL optional).

Public surface (unchanged): ``UserStore`` factory + ``PASSWORD_ITERATIONS``.
Password hashing (pbkdf2_sha256, 600k iterations) is identical in both
backends, so JSON-created accounts keep working after a Postgres migration.

Backend selection mirrors ChatStore: explicit ``store_path`` (tests) → JSON;
``JSON_FALLBACK=true`` (default) → JSON; otherwise PostgreSQL when reachable
with a logged, safe degradation to JSON when the database is down.
"""

import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.config import get_settings

logger = logging.getLogger(__name__)

PASSWORD_ITERATIONS = 600_000


def _store_path() -> Path:
    path = Path(get_settings().users_store_path)
    return path if path.is_absolute() else (Path(__file__).resolve().parents[2] / path)


class JsonUserStore:
    """Original JSON-file implementation (``{"users": {id: user}}``)."""

    backend_name = "json"

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = Path(store_path) if store_path else _store_path()
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._save({"users": {}})

    def _load(self) -> dict:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        self.store_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def get_by_email(self, email: str) -> Optional[dict]:
        normalized = email.strip().lower()
        return next(
            (user for user in self._load()["users"].values() if user["email"] == normalized),
            None,
        )

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return self._load()["users"].get(user_id)

    def get_by_provider_id(self, provider: str, provider_id: str) -> Optional[dict]:
        """Look up a user by a linked OAuth provider id (e.g. google_id)."""
        key = f"{provider}_id"
        return next(
            (user for user in self._load()["users"].values() if user.get(key) == provider_id),
            None,
        )

    def link_provider(self, user_id: str, provider: str, provider_id: str) -> Optional[dict]:
        data = self._load()
        user = data["users"].get(user_id)
        if not user:
            return None
        user[f"{provider}_id"] = provider_id
        self._save(data)
        return user

    def create(self, email: str, name: str, password: str) -> dict:
        normalized = email.strip().lower()
        now = datetime.now(timezone.utc).isoformat()
        user = {
            "id": str(uuid.uuid4()),
            "email": normalized,
            "name": name.strip(),
            "password_hash": self.hash_password(password),
            "created_at": now,
        }
        data = self._load()
        data["users"][user["id"]] = user
        self._save(data)
        return user

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            scheme, iterations, salt, expected = password_hash.split("$", 3)
            if scheme != "pbkdf2_sha256":
                return False
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt),
                int(iterations),
            ).hex()
            return hmac.compare_digest(derived, expected)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PASSWORD_ITERATIONS,
        ).hex()
        return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest}"


class PostgresUserStore:
    """SQLAlchemy implementation with identical dict shapes."""

    backend_name = "postgres"

    def __init__(self):
        from backend.db.models import UserModel  # noqa: F401  (fail fast)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        from backend.db.base import Base
        from backend.db.session import get_engine
        try:
            Base.metadata.create_all(get_engine())
        except Exception as exc:
            logger.warning("Could not ensure user schema: %s", exc.__class__.__name__)

    @staticmethod
    def _user_dict(u) -> dict:
        data = {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "password_hash": u.password_hash,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        data.update(u.extra or {})
        return data

    def get_by_email(self, email: str) -> Optional[dict]:
        from sqlalchemy import func, select
        from backend.db.models import UserModel
        from backend.db.session import session_scope

        normalized = email.strip().lower()
        with session_scope() as db:
            u = db.scalar(select(UserModel).where(func.lower(UserModel.email) == normalized))
            return self._user_dict(u) if u else None

    def get_by_id(self, user_id: str) -> Optional[dict]:
        from backend.db.models import UserModel
        from backend.db.session import session_scope

        with session_scope() as db:
            u = db.get(UserModel, user_id)
            return self._user_dict(u) if u else None

    def get_by_provider_id(self, provider: str, provider_id: str) -> Optional[dict]:
        from sqlalchemy import select
        from backend.db.models import UserModel
        from backend.db.session import session_scope

        key = f"{provider}_id"
        with session_scope() as db:
            u = db.scalar(
                select(UserModel).where(UserModel.extra[key].astext == str(provider_id))
            )
            return self._user_dict(u) if u else None

    def link_provider(self, user_id: str, provider: str, provider_id: str) -> Optional[dict]:
        from backend.db.models import UserModel
        from backend.db.session import session_scope

        with session_scope() as db:
            u = db.get(UserModel, user_id)
            if not u:
                return None
            u.extra = {**(u.extra or {}), f"{provider}_id": provider_id}
            return self._user_dict(u)

    def create(self, email: str, name: str, password: str) -> dict:
        from sqlalchemy import func, select
        from backend.db.models import UserModel
        from backend.db.session import session_scope

        normalized = email.strip().lower()
        with session_scope() as db:
            u = UserModel(
                email=normalized,
                name=name.strip(),
                password_hash=self.hash_password(password),
                extra={},
            )
            db.add(u)
            try:
                db.flush()
            except Exception:
                # Unique-email race: mirror JSON's tolerant behavior by
                # returning the existing account.
                db.rollback()
                existing = db.scalar(
                    select(UserModel).where(func.lower(UserModel.email) == normalized)
                )
                if existing is None:
                    raise
                return self._user_dict(existing)
            return self._user_dict(u)

    # Password hashing identical to the JSON backend (shared format)
    verify_password = staticmethod(JsonUserStore.verify_password)
    hash_password = staticmethod(JsonUserStore.hash_password)


def UserStore(store_path: Optional[Path] = None):
    """Factory returning the configured persistence backend."""
    if store_path is not None:
        return JsonUserStore(store_path)

    settings = get_settings()
    if not settings.json_fallback:
        from backend.db.session import pg_available

        if pg_available():
            return PostgresUserStore()
        logger.warning(
            "JSON_FALLBACK=false but PostgreSQL is unreachable — using JSON store at %s",
            _store_path(),
        )
    return JsonUserStore()
