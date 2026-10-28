"""Permission Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.permission_controller import PermissionController
from src.api.middleware.auth_dependencies import get_current_active_user, require_permissions
from src.api.schemas.permission_schema import (
    PermissionCreateRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from src.bootstrap.container import get_container
from src.domain.entities.user import User
from src.domain.exceptions import EntityNotFoundError


def get_permission_controller() -> PermissionController:
    return get_container().permission_controller


permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permission_router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    request: PermissionCreateRequest,
    current_user: User = Depends(require_permissions("permission:create")),
    controller: PermissionController = Depends(get_permission_controller),
):
    # 重名冲突（409）由全局领域异常 handler 映射
    return await controller.create(request)


@permission_router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_active_user),
    controller: PermissionController = Depends(get_permission_controller),
):
    result = await controller.get_by_id(permission_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return result


@permission_router.get("", response_model=PermissionListResponse)
async def list_permissions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    controller: PermissionController = Depends(get_permission_controller),
):
    # 权限为全局目录（平台定义），登录用户可读
    return await controller.list(skip=skip, limit=limit)


@permission_router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    request: PermissionUpdateRequest,
    current_user: User = Depends(require_permissions("permission:update")),
    controller: PermissionController = Depends(get_permission_controller),
):
    result = await controller.update(permission_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return result


@permission_router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: UUID,
    current_user: User = Depends(require_permissions("permission:delete")),
    controller: PermissionController = Depends(get_permission_controller),
):
    deleted = await controller.delete(permission_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")


@permission_router.post("/{permission_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
    permission_id: UUID,
    role_id: UUID,
    current_user: User = Depends(require_permissions("permission:update")),
    controller: PermissionController = Depends(get_permission_controller),
):
    try:
        # 角色必须属于当前租户（UseCase 内校验，跨租户/不存在 → 404）；权限本身为全局资源
        assigned = await controller.assign_to_role(permission_id, role_id, current_user.tenant_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission or role not found")
    if not assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission or role not found")
    # 权限分配变更：立即失效权限缓存（影响所有拥有该角色的用户）
    get_container().permission_cache.clear()
    return {"assigned": True}
