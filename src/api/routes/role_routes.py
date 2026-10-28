"""Role Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.role_controller import RoleController
from src.api.middleware.auth_dependencies import get_current_active_user, require_permissions
from src.api.schemas.role_schema import (
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleUpdateRequest,
)
from src.bootstrap.container import get_container
from src.domain.entities.user import User
from src.domain.exceptions import EntityNotFoundError


def get_role_controller() -> RoleController:
    return get_container().role_controller


role_router = APIRouter(prefix="/roles", tags=["roles"])


@role_router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    current_user: User = Depends(require_permissions("role:create")),
    controller: RoleController = Depends(get_role_controller),
):
    # 角色所属租户强制取自认证上下文（请求体不再接受 tenant_id）；
    # 重名冲突（409）由全局领域异常 handler 映射
    return await controller.create(request, current_user.tenant_id)


@role_router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_active_user),
    controller: RoleController = Depends(get_role_controller),
):
    result = await controller.get_by_id(role_id, current_user.tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return result


@role_router.get("", response_model=RoleListResponse)
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    controller: RoleController = Depends(get_role_controller),
):
    # 仅返回本租户角色
    return await controller.list(current_user.tenant_id, skip=skip, limit=limit)


@role_router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    request: RoleUpdateRequest,
    current_user: User = Depends(require_permissions("role:update")),
    controller: RoleController = Depends(get_role_controller),
):
    result = await controller.update(role_id, request, current_user.tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return result


@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(require_permissions("role:delete")),
    controller: RoleController = Depends(get_role_controller),
):
    deleted = await controller.delete(role_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")


@role_router.post("/{role_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    role_id: UUID,
    user_id: UUID,
    current_user: User = Depends(require_permissions("role:update")),
    controller: RoleController = Depends(get_role_controller),
):
    try:
        # 角色与用户必须同属当前租户（UseCase 内校验，跨租户/不存在 → 404）
        assigned = await controller.assign_to_user(role_id, user_id, current_user.tenant_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or user not found")
    if not assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or user not found")
    # 角色分配变更：立即失效权限缓存（否则目标用户最多延迟 TTL 才能获得新权限）
    get_container().permission_cache.clear()
    return {"assigned": True}
