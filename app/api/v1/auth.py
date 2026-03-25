from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.token import LoginRequest, Token, RefreshTokenRequest
from app.services.auth import authenticate_user, create_user_token, refresh_access_token, get_current_user


auth_router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "auth"  # 标签（默认模块名或子目录名）



@auth_router.post("/token", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """使用表单获取OAuth2兼容的令牌，用于用户登录（兼容OAuth2客户端）"""
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_user_token(user.id, db)


@auth_router.post("/login/json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """使用JSON格式获取令牌，用于用户登录"""
    user = await authenticate_user(login_data.username, login_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await create_user_token(user.id, db)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """使用刷新令牌获取新的访问令牌"""
    return await refresh_access_token(refresh_data.refresh_token, db)


@auth_router.post("/test-token", response_model=User)
async def test_token(current_user: User = Depends(get_current_user)) -> Any:
    """测试访问令牌"""
    return current_user
