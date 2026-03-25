from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionOut
from app.services.permission import PermissionService
from app.services.auth import get_current_active_superuser
from app.db.session import get_session

permissions_router = APIRouter()
_tag = "permission"
_active = True

async def get_permission_service(db: AsyncSession = Depends(get_session)) -> PermissionService:
    """获取权限服务实例"""
    return PermissionService(db)


@permissions_router.get("/permission", response_model=list[PermissionOut])
async def get_all_permissions(
    service: PermissionService = Depends(get_permission_service)
):
    """获取所有权限列表"""
    return await service.get_all_permissions()


@permissions_router.post("/permission", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission: PermissionCreate,
    service: PermissionService = Depends(get_permission_service),
    _=Depends(get_current_active_superuser)
):
    """创建新权限"""
    return await service.create_permission(permission)


@permissions_router.get("/permission/{permission_id}", response_model=PermissionOut)
async def get_permission(
    permission_id: UUID,
    service: PermissionService = Depends(get_permission_service)
):
    """根据ID获取权限详情"""
    permission = await service.get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return permission


@permissions_router.put("/permission/{permission_id}", response_model=PermissionOut)
async def update_permission(
    permission_id: UUID,
    permission: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
    _=Depends(get_current_active_superuser)
):
    """更新权限信息"""
    updated_permission = await service.update_permission(permission_id, permission)
    if not updated_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return updated_permission


@permissions_router.delete("/permission/{permission_id}")
async def delete_permission(
    permission_id: UUID,
    service: PermissionService = Depends(get_permission_service),
    _=Depends(get_current_active_superuser)
):
    """删除权限"""
    if not await service.delete_permission(permission_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    return {"message": "权限删除成功"}
