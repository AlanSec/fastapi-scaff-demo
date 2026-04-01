from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserUpdateMe
from app.services.auth import get_current_active_superuser, get_current_user
from app.services.user import UserService

users_router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "users"  # 标签（默认模块名或子目录名）

async def get_user_service(db: AsyncSession = Depends(get_session)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


@users_router.get("/user/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> Any:
    """获取当前用户信息"""
    user = await service.read_user_me(current_user)
    return user


@users_router.put("/user/me", response_model=User)
async def update_user_me(
    user_in: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> Any:
    """更新当前用户信息"""
    user = await service.update_user_me(user_in, current_user)
    return user


@users_router.delete("/user/{user_id}", response_model=User)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """删除指定用户（仅超级管理员）"""
    user = await service.delete_user(user_id)
    return user


@users_router.get("/user", response_model=list[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """获取所有用户列表（仅超级管理员）"""
    users = await service.get_users(skip=skip, limit=limit)
    return users


@users_router.post("/user", response_model=User)
async def create_user(
    user_in: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """创建新用户（仅超级管理员）"""
    db_user = await service.create_user(user_in)
    return db_user


@users_router.get("/user/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """获取指定用户信息（仅超级管理员）"""
    user = await service.read_users(user_id)
    return user


@users_router.put("/user/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """更新指定用户信息（仅超级管理员）"""
    user = await service.update_user(user_id, user_in)
    return user
