"""User Admin Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.user_admin_controller import UserAdminController
from src.api.middleware.auth_dependencies import get_current_active_superuser, get_current_active_user
from src.api.schemas.user_admin_schema import (
    AdminCreateUserRequest,
    AdminUpdateCurrentUserRequest,
    AdminUpdateUserRequest,
    UserAdminListResponse,
    UserAdminResponse,
)
from src.bootstrap.container import get_container
from src.domain.entities.user import User


def get_user_admin_controller() -> UserAdminController:
    return get_container().user_admin_controller


user_admin_router = APIRouter(prefix="/user", tags=["users"])


@user_admin_router.get("/me", response_model=UserAdminResponse)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    return await controller.get_me(current_user.id, current_user.tenant_id)


@user_admin_router.put("/me", response_model=UserAdminResponse)
async def update_user_me(
    request: AdminUpdateCurrentUserRequest,
    current_user: User = Depends(get_current_active_user),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    return await controller.update_me(current_user.id, request, current_user.tenant_id)


@user_admin_router.get("", response_model=UserAdminListResponse)
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    # 仅返回本租户用户（superuser 也不豁免租户隔离）
    return await controller.list(current_user.tenant_id, skip=skip, limit=limit)


@user_admin_router.post("", response_model=UserAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: AdminCreateUserRequest,
    current_user: User = Depends(get_current_active_superuser),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    # 用户所属租户强制取当前租户（请求体不再接受 tenant_id）；
    # 邮箱冲突（409）由全局领域异常 handler 映射
    return await controller.create(request, current_user.tenant_id)


@user_admin_router.get("/{user_id}", response_model=UserAdminResponse)
async def read_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    return await controller.get_by_id(user_id, current_user.tenant_id)


@user_admin_router.put("/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: UUID,
    request: AdminUpdateUserRequest,
    current_user: User = Depends(get_current_active_superuser),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    return await controller.update(user_id, request, current_user.tenant_id)


@user_admin_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    controller: UserAdminController = Depends(get_user_admin_controller),
):
    deleted = await controller.delete(user_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
