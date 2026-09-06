"""JSON-backed user persistence for the local SOCIALIQ deployment."""

import json
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "users.json"
PASSWORD_ITERATIONS = 600_000


class UserStore:
    def __init__(self):
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not STORE_PATH.exists():
            self._save({"users": {}})

    def _load(self) -> dict:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        STORE_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def get_by_email(self, email: str) -> Optional[dict]:
        normalized = email.strip().lower()
        return next(
            (user for user in self._load()["users"].values() if user["email"] == normalized),
            None,
        )

    def get_by_id(self, user_id: str) -> Optional[dict]:
        return self._load()["users"].get(user_id)

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