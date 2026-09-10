"""JSON-backed user persistence for the local SOCIALIQ deployment.

The schema is intentionally future-proof: OAuth provider identifiers can be
attached to an account without a migration, while basic email/password
authentication remains the default flow.
"""

import json
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.config import get_settings

PASSWORD_ITERATIONS = 600_000


def _store_path() -> Path:
    path = Path(get_settings().users_store_path)
    return path if path.is_absolute() else (Path(__file__).resolve().parents[2] / path)


class UserStore:
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
        """Look up a user by a linked OAuth provider id (e.g. google_id).

        Kept so the planned OAuth flow can attach accounts without a schema
        migration; unused by the basic email/password flow.
        """
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
