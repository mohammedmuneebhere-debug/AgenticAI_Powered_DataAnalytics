"""FastAPI dependencies for authenticated requests."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from backend.auth.security import decode_access_token
from backend.auth.store import UserStore

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
user_store = UserStore()


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except JWTError as exc:
        raise credentials_error from exc

    user = user_store.get_by_id(user_id)
    if not user:
        raise credentials_error
    return user