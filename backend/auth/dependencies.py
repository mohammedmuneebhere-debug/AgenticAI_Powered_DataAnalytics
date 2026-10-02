"""FastAPI dependencies for authenticated requests."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.auth.security import decode_token_payload
from backend.auth.store import UserStore
from backend.services.redis_client import get_redis_cache

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
user_store = UserStore()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token_payload(token)
    except JWTError as exc:
        raise credentials_error from exc

    # Redis-backed logout blacklist; no-op (never blacklisted) when Redis is down
    jti = payload.get("jti")
    if jti and get_redis_cache().is_blacklisted(jti):
        raise credentials_error

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_error

    user = user_store.get_by_id(user_id)
    if not user:
        raise credentials_error
    return user