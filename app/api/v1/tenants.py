import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.auth import get_current_active_superuser, get_current_user
from app.services.tenants import TenantsServices

tenants_router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "tenants"  # 标签（默认模块名或子目录名）

async def get_tenants_service(db: AsyncSession = Depends(get_session)) -> TenantsServices:
    """获取租户服务实例"""
    return TenantsServices(db)


@tenants_router.get("/tenants", response_model=list[Tenant])
async def read_tenants(
    skip: int = 0,
    limit: int = 100,
    service: TenantsServices = Depends(get_tenants_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """获取所有租户列表（仅超级管理员）"""
    tenants = await service.read_tenant_users(skip=skip, limit=limit)
    return tenants


@tenants_router.post("/tenants", response_model=Tenant)
async def create_tenant(
    tenant_in: TenantCreate,
    service: TenantsServices = Depends(get_tenants_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """创建新租户（仅超级管理员）"""
    tenant = await service.create_tenant(tenant_in)
    return tenant


@tenants_router.get("/tenants/{tenant_id}", response_model=Tenant)
async def read_tenant_by_id(
    tenant_id: str,
    service: TenantsServices = Depends(get_tenants_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取指定租户信息"""
    # 租户隔离检查：超级管理员可访问所有租户，普通用户只能访问自己的租户
    if not current_user.is_superuser and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该租户信息"
        )
    tenant = await service.read_tenant(tenant_id, current_user)
    return tenant


@tenants_router.put("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(
    tenant_id: str,
    tenant_in: TenantUpdate,
    service: TenantsServices = Depends(get_tenants_service),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """更新指定租户信息（仅超级管理员）"""
    if not current_user.is_superuser and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新该租户信息"
        )
    tenant = await service.update_tenant(tenant_id, tenant_in)
    return tenant


@tenants_router.get("/tenants/{tenant_id}/users", response_model=list[User])
async def read_tenant_users(
    tenant_id: str,
    skip: int = 0,
    limit: int = 100,
    service: TenantsServices = Depends(get_tenants_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取指定租户的用户列表"""
    if not current_user.is_superuser and str(current_user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该租户用户列表"
        )
    users = await service.read_tenant_by_id(tenant_id, skip, limit, current_user)
    return users
