from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from src.domain.entities.permission import Permission
from src.domain.repositories.permission_repository import PermissionRepository
from src.infrastructure.persistence.database import session_scope
from src.infrastructure.persistence.sqlmodel.mappers.permission_mapper import PermissionMapper
from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel
from src.infrastructure.persistence.sqlmodel.models.role_permission import RolePermissionModel


class SQLModelPermissionRepository(PermissionRepository):

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, permission: Permission) -> Permission:
        async with session_scope(self._session_factory) as session:
            existing = await session.get(PermissionModel, permission.id)
            if existing is not None:
                model = PermissionMapper.apply_to_model(existing, permission)
                session.add(model)
            else:
                model = PermissionMapper.to_model(permission)
                session.add(model)
            await session.commit()
            await session.refresh(model)
            return PermissionMapper.to_entity(model)

    async def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        async with session_scope(self._session_factory) as session:
            model = await session.get(PermissionModel, permission_id)
            if model is None:
                return None
            return PermissionMapper.to_entity(model)

    async def find_by_action_and_resource(self, action: str, resource: str) -> Optional[Permission]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(PermissionModel).where(
                    PermissionModel.action == action,
                    PermissionModel.resource == resource
                )
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return PermissionMapper.to_entity(model)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(PermissionModel).offset(skip).limit(limit)
            )
            models = result.scalars().all()
            return [PermissionMapper.to_entity(m) for m in models]

    async def delete(self, permission_id: UUID) -> bool:
        async with session_scope(self._session_factory) as session:
            model = await session.get(PermissionModel, permission_id)
            if model is None:
                return False
            await session.delete(model)
            await session.commit()
            return True

    async def assign_to_role(self, permission_id: UUID, role_id: UUID) -> bool:
        """将权限分配给角色"""
        from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
        async with session_scope(self._session_factory) as session:
            permission = await session.get(PermissionModel, permission_id)
            role = await session.get(RoleModel, role_id)
            if permission is None or role is None:
                return False
            existing = await session.execute(
                select(RolePermissionModel).where(
                    RolePermissionModel.permission_id == permission_id,
                    RolePermissionModel.role_id == role_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                return True  # 已分配，幂等
            session.add(RolePermissionModel(permission_id=permission_id, role_id=role_id))
            await session.commit()
            return True

    async def get_role_permission_ids(self, role_id: UUID) -> List[UUID]:
        """查询角色拥有的权限 ID 列表"""
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RolePermissionModel.permission_id).where(
                    RolePermissionModel.role_id == role_id
                )
            )
            return list(result.scalars().all())

    async def get_permission_ids_for_roles(self, role_ids: List[UUID]) -> List[UUID]:
        """批量查询多个角色拥有的权限 ID（去重，避免 N+1）"""
        if not role_ids:
            return []
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RolePermissionModel.permission_id)
                .where(RolePermissionModel.role_id.in_(role_ids))
                .distinct()
            )
            return list(result.scalars().all())

    async def find_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        """按 ID 批量查询权限（避免 N+1）"""
        if not permission_ids:
            return []
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(PermissionModel).where(PermissionModel.id.in_(permission_ids))
            )
            return [PermissionMapper.to_entity(m) for m in result.scalars().all()]
