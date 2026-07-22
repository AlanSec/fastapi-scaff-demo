"""Tenant Routes"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.api.controllers.tenant_controller import TenantController
from src.api.schemas.tenant_schema import (
    TenantCreateRequest,
    TenantUpdateRequest,
    TenantResponse,
    TenantListResponse,
)


_controller: Optional[TenantController] = None


def set_tenant_controller(controller: TenantController):
    global _controller
    _controller = controller


def get_tenant_controller() -> TenantController:
    if _controller is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant controller not initialized"
        )
    return _controller


tenant_router = APIRouter(prefix="/tenants", tags=["tenants"])


@tenant_router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
    controller: TenantController = Depends(get_tenant_controller),
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
):
    result = await controller.update(tenant_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return result


@tenant_router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    controller: TenantController = Depends(get_tenant_controller),
):
    deleted = await controller.delete(tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
