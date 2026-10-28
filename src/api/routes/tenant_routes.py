"""Tenant Routes"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.controllers.tenant_controller import TenantController
from src.api.middleware.auth_dependencies import get_current_active_superuser, require_permissions
from src.api.schemas.tenant_schema import (
    TenantCreateRequest,
    TenantListResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from src.bootstrap.container import get_container
from src.domain.entities.user import User


def get_tenant_controller() -> TenantController:
    return get_container().tenant_controller


tenant_router = APIRouter(prefix="/tenants", tags=["tenants"])


@tenant_router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
    current_user: User = Depends(require_permissions("tenant:create")),
    controller: TenantController = Depends(get_tenant_controller),
):
    # 重名冲突（409）由全局领域异常 handler 映射
    return await controller.create(request)


@tenant_router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_active_superuser),
    controller: TenantController = Depends(get_tenant_controller),
):
    """租户为平台级资源：读取仅限 superuser（防匿名枚举）"""
    result = await controller.get_by_id(tenant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return result


@tenant_router.get("", response_model=TenantListResponse)
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    controller: TenantController = Depends(get_tenant_controller),
):
    """租户为平台级资源：列表仅限 superuser（防匿名枚举）"""
    return await controller.list(skip=skip, limit=limit)


@tenant_router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    current_user: User = Depends(require_permissions("tenant:update")),
    controller: TenantController = Depends(get_tenant_controller),
):
    result = await controller.update(tenant_id, request)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return result


@tenant_router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    current_user: User = Depends(require_permissions("tenant:delete")),
    controller: TenantController = Depends(get_tenant_controller),
):
    deleted = await controller.delete(tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
