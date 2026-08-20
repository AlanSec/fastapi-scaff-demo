"""Role Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.role_controller import RoleController
from src.api.middleware.auth_dependencies import require_permissions
from src.api.schemas.role_schema import (
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleUpdateRequest,
)
from src.bootstrap.container import get_container


def get_role_controller() -> RoleController:
    return get_container().role_controller


role_router = APIRouter(prefix="/roles", tags=["roles"])


@role_router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    controller: RoleController = Depends(get_role_controller),
    _: str = Depends(require_permissions("role:create")),
):
    try:
        return await controller.create(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@role_router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    controller: RoleController = Depends(get_role_controller),
):
    result = await controller.get_by_id(role_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return result


@role_router.get("", response_model=RoleListResponse)
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    controller: RoleController = Depends(get_role_controller),
):
    return await controller.list(skip=skip, limit=limit)


@role_router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    request: RoleUpdateRequest,
    controller: RoleController = Depends(get_role_controller),
    _: str = Depends(require_permissions("role:update")),
):
    result = await controller.update(role_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return result


@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    controller: RoleController = Depends(get_role_controller),
    _: str = Depends(require_permissions("role:delete")),
):
    deleted = await controller.delete(role_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")


@role_router.post("/{role_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    role_id: UUID,
    user_id: UUID,
    controller: RoleController = Depends(get_role_controller),
    _: str = Depends(require_permissions("role:update")),
):
    try:
        assigned = await controller.assign_to_user(role_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not assigned:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or user not found")
    return {"assigned": True}
