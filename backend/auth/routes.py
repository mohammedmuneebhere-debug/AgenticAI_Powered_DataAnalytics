"""Authentication endpoints used by the SOCIALIQ client and integrations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import get_current_user, user_store
from backend.auth.security import create_access_token
from backend.models.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def to_user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=datetime.fromisoformat(user["created_at"]),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest):
    if user_store.get_by_email(request.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = user_store.create(request.email, request.name, request.password)
    return TokenResponse(access_token=create_access_token(user["id"]), user=to_user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    user = user_store.get_by_email(request.email)
    if not user or not user_store.verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user["id"]), user=to_user_response(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user: dict = Depends(get_current_user)):
    return to_user_response(current_user)