"""JWT creation and password authentication primitives."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from backend.config import get_settings


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": user_id, "exp": expires, "jti": uuid.uuid4().hex},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token_payload(token: str) -> dict[str, Any]:
    """Full payload decode (sub, exp, jti) — used for logout/blacklist."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def decode_access_token(token: str) -> str:
    user_id = decode_token_payload(token).get("sub")
    if not user_id:
        raise JWTError("Token subject is missing")
    return user_id