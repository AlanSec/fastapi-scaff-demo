from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.role import RoleCreate, RoleUpdate, RoleOut
from app.schemas.role_permission import RolePermissionOut
from app.services.role import RoleService
from app.services.auth import get_current_active_superuser
from app.db.session import get_session

roles_router = APIRouter()
_tags = "Roles"
_active = True

async def get_role_service(db: AsyncSession = Depends(get_session)) -> RoleService:
    """获取角色服务实例"""
    return RoleService(db)


@roles_router.get("/role", response_model=list[RoleOut])
async def get_all_roles(
    service: RoleService = Depends(get_role_service)
):
    """获取所有角色列表"""
    return await service.get_all_roles()


@roles_router.post("/role", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    service: RoleService = Depends(get_role_service),
    _=Depends(get_current_active_superuser)
):
    """创建新角色"""
    return await service.create_role(role)


@roles_router.get("/role/{role_id}", response_model=RoleOut)
async def get_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service)
):
    """根据ID获取角色详情"""
    role = await service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return role


@roles_router.put("/role/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: UUID,
    role: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    _=Depends(get_current_active_superuser)
):
    """更新角色信息"""
    updated_role = await service.update_role(role_id, role)
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return updated_role


@roles_router.delete("/role/{role_id}")
async def delete_role(
    role_id: UUID,
    service: RoleService = Depends(get_role_service),
    _=Depends(get_current_active_superuser)
):
    """删除角色"""
    if not await service.delete_role(role_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return {"message": "角色删除成功"}


@roles_router.post("/role/{role_id}/permissions", response_model=RolePermissionOut)
async def add_permission_to_role(
    role_id: UUID,
    permission_id: UUID,
    service: RoleService = Depends(get_role_service),
    _=Depends(get_current_active_superuser)
):
    """为角色添加权限"""
    result = await service.add_permission_to_role(role_id, permission_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色或权限不存在"
        )
    return result


@roles_router.get("/role/{role_id}/permissions", response_model=list[RolePermissionOut])
async def get_role_permissions(
    role_id: UUID,
    service: RoleService = Depends(get_role_service)
):
    """获取角色的所有权限"""
    if not await service.role_exists(role_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    return await service.get_role_permissions(role_id)


@roles_router.delete("/role/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    service: RoleService = Depends(get_role_service),
    _=Depends(get_current_active_superuser)
):
    """从角色移除权限"""
    if not await service.remove_permission_from_role(role_id, permission_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色权限关联不存在"
        )
    return {"message": "权限移除成功"}
