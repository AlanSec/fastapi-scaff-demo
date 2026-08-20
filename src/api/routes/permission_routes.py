"""Permission Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.permission_controller import PermissionController
from src.api.middleware.auth_dependencies import require_permissions
from src.api.schemas.permission_schema import (
    PermissionCreateRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from src.bootstrap.container import get_container


def get_permission_controller() -> PermissionController:
    return get_container().permission_controller


permission_router = APIRouter(prefix="/permissions", tags=["permissions"])


@permission_router.post("", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    request: PermissionCreateRequest,
    controller: PermissionController = Depends(get_permission_controller),
    _: str = Depends(require_permissions("permission:create")),
):
    try:
        return await controller.create(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@permission_router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: UUID,
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
    controller: PermissionController = Depends(get_permission_controller),
):
    return await controller.list(skip=skip, limit=limit)


@permission_router.put("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    request: PermissionUpdateRequest,
    controller: PermissionController = Depends(get_permission_controller),
    _: str = Depends(require_permissions("permission:update")),
):
    result = await controller.update(permission_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return result


@permission_router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: UUID,
    controller: PermissionController = Depends(get_permission_controller),
    _: str = Depends(require_permissions("permission:delete")),
):
    deleted = await controller.delete(permission_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")


@permission_router.post("/{permission_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
async def assign_permission_to_role(
    permission_id: UUID,
    role_id: UUID,
    controller: PermissionController = Depends(get_permission_controller),
    _: str = Depends(require_permissions("permission:update")),
):
    try:
        assigned = await controller.assign_to_role(permission_id, role_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission or role not found")
    return {"assigned": True}
