from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionOut


class PermissionService:
    """权限服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_permissions(self) -> List[PermissionOut]:
        """获取所有权限"""
        result = await self.db.execute(select(Permission).filter(Permission.is_active == True))
        permissions = result.scalars().all()
        return [PermissionOut.model_validate(permission) for permission in permissions]

    async def get_permission_by_id(self, permission_id: UUID) -> Optional[PermissionOut]:
        """根据 ID 获取权限"""
        result = await self.db.execute(
            select(Permission).filter(
                Permission.id == permission_id,
                Permission.is_active == True
            )
        )
        permission = result.scalar_one_or_none()
        return PermissionOut.model_validate(permission) if permission else None

    async def create_permission(self, permission_create: PermissionCreate) -> PermissionOut:
        """创建权限"""
        permission = Permission(**permission_create.dict())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return PermissionOut.model_validate(permission)

    async def update_permission(
        self,
        permission_id: UUID,
        permission_update: PermissionUpdate
    ) -> Optional[PermissionOut]:
        """更新权限"""
        result = await self.db.execute(
            select(Permission).filter(
                Permission.id == permission_id,
                Permission.is_active == True
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return None

        for key, value in permission_update.dict(exclude_unset=True).items():
            setattr(permission, key, value)

        await self.db.commit()
        await self.db.refresh(permission)
        return PermissionOut.model_validate(permission)

    async def delete_permission(self, permission_id: UUID) -> bool:
        """删除权限(软删除)"""
        result = await self.db.execute(
            select(Permission).filter(
                Permission.id == permission_id,
                Permission.is_active == True
            )
        )
        permission = result.scalar_one_or_none()

        if not permission:
            return False

        permission.is_active = False
        await self.db.commit()
        return True

    async def permission_exists(self, permission_id: UUID) -> bool:
        """检查权限是否存在"""
        result = await self.db.execute(
            select(Permission).filter(
                Permission.id == permission_id,
                Permission.is_active == True
            )
        )
        return result.scalar_one_or_none() is not None
