"""Tenant Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.tenant_controller import TenantController
from src.api.middleware.auth_dependencies import require_permissions
from src.api.schemas.tenant_schema import (
    TenantCreateRequest,
    TenantListResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from src.bootstrap.container import get_container


def get_tenant_controller() -> TenantController:
    return get_container().tenant_controller


tenant_router = APIRouter(prefix="/tenants", tags=["tenants"])


@tenant_router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
    controller: TenantController = Depends(get_tenant_controller),
    _: str = Depends(require_permissions("tenant:create")),
):
    try:
        return await controller.create(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@tenant_router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    controller: TenantController = Depends(get_tenant_controller),
):
    result = await controller.get_by_id(tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return result


@tenant_router.get("", response_model=TenantListResponse)
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    controller: TenantController = Depends(get_tenant_controller),
):
    return await controller.list(skip=skip, limit=limit)


@tenant_router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    controller: TenantController = Depends(get_tenant_controller),
    _: str = Depends(require_permissions("tenant:update")),
):
    result = await controller.update(tenant_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return result


@tenant_router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    controller: TenantController = Depends(get_tenant_controller),
    _: str = Depends(require_permissions("tenant:delete")),
):
    deleted = await controller.delete(tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
