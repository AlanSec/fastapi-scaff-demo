from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.role import Role
from app.models.role_permission import RolePermission
from app.schemas.role import RoleCreate, RoleUpdate, RoleOut
from app.schemas.role_permission import RolePermissionOut


class RoleService:
    """角色服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_roles(self) -> List[RoleOut]:
        """获取所有角色"""
        result = await self.db.execute(select(Role).filter(Role.is_active == True))
        roles = result.scalars().all()
        return [RoleOut.model_validate(role) for role in roles]

    async def get_role_by_id(self, role_id: UUID) -> Optional[RoleOut]:
        """根据 ID 获取角色"""
        result = await self.db.execute(
            select(Role).filter(
                Role.id == role_id,
                Role.is_active == True
            )
        )
        role = result.scalar_one_or_none()
        return RoleOut.model_validate(role) if role else None

    async def create_role(self, role_create: RoleCreate) -> RoleOut:
        """创建角色"""
        role = Role(**role_create.dict())
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return RoleOut.model_validate(role)

    async def update_role(
        self,
        role_id: UUID,
        role_update: RoleUpdate
    ) -> Optional[RoleOut]:
        """更新角色"""
        result = await self.db.execute(
            select(Role).filter(
                Role.id == role_id,
                Role.is_active == True
            )
        )
        role = result.scalar_one_or_none()

        if not role:
            return None

        for key, value in role_update.dict(exclude_unset=True).items():
            setattr(role, key, value)

        await self.db.commit()
        await self.db.refresh(role)
        return RoleOut.model_validate(role)

    async def delete_role(self, role_id: UUID) -> bool:
        """删除角色(软删除)"""
        result = await self.db.execute(
            select(Role).filter(
                Role.id == role_id,
                Role.is_active == True
            )
        )
        role = result.scalar_one_or_none()

        if not role:
            return False

        role.is_active = False
        await self.db.commit()
        return True

    async def add_permission_to_role(
        self,
        role_id: UUID,
        permission_id: UUID
    ) -> Optional[RolePermissionOut]:
        """为角色添加权限"""
        # 检查角色是否存在
        role_result = await self.db.execute(
            select(Role).filter(
                Role.id == role_id,
                Role.is_active == True
            )
        )
        role = role_result.scalar_one_or_none()
        if not role:
            return None

        # 检查是否已存在该关联
        existing_result = await self.db.execute(
            select(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
                RolePermission.is_active == True
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return RolePermissionOut.model_validate(existing)

        # 创建新关联
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
            is_active=True
        )
        self.db.add(role_permission)
        await self.db.commit()
        await self.db.refresh(role_permission)
        return RolePermissionOut.model_validate(role_permission)

    async def get_role_permissions(self, role_id: UUID) -> List[RolePermissionOut]:
        """获取角色的所有权限"""
        result = await self.db.execute(
            select(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.is_active == True
            )
        )
        role_permissions = result.scalars().all()
        return [RolePermissionOut.model_validate(rp) for rp in role_permissions]

    async def remove_permission_from_role(
        self,
        role_id: UUID,
        permission_id: UUID
    ) -> bool:
        """从角色移除权限(软删除)"""
        result = await self.db.execute(
            select(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id,
                RolePermission.is_active == True
            )
        )
        role_permission = result.scalar_one_or_none()

        if not role_permission:
            return False

        role_permission.is_active = False
        await self.db.commit()
        return True

    async def role_exists(self, role_id: UUID) -> bool:
        """检查角色是否存在"""
        result = await self.db.execute(
            select(Role).filter(
                Role.id == role_id,
                Role.is_active == True
            )
        )
        return result.scalar_one_or_none() is not None
