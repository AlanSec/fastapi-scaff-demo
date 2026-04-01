from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.token import LoginRequest, Token, RefreshTokenRequest
from app.services.auth import authenticate_user, create_user_token, refresh_access_token, get_current_user
from app.api.rate_limit import rate_limit

auth_router = APIRouter()
_active = True
_tag = "auth"


@auth_router.post("/token", response_model=Token)
@rate_limit(max_requests=5, window_seconds=60)
async def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
) -> Any:
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_user_token(user.id, db)


@auth_router.post("/login/json", response_model=Token)
@rate_limit(max_requests=5, window_seconds=60)
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> Any:
    user = await authenticate_user(login_data.username, login_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_user_token(user.id, db)


@auth_router.post("/refresh", response_model=Token)
@rate_limit(max_requests=10, window_seconds=60)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_session),
) -> Any:
    return await refresh_access_token(refresh_data.refresh_token, db)


@auth_router.post("/test-token", response_model=User)
async def test_token(current_user: User = Depends(get_current_user)) -> Any:
    return current_user
