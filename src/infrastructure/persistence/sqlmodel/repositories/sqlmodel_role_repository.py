from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository
from src.infrastructure.persistence.database import session_scope
from src.infrastructure.persistence.sqlmodel.mappers.role_mapper import RoleMapper
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
from src.infrastructure.persistence.sqlmodel.models.user_role import UserRoleModel


class SQLModelRoleRepository(RoleRepository):

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, role: Role) -> Role:
        async with session_scope(self._session_factory) as session:
            existing = await session.get(RoleModel, role.id)
            if existing is not None:
                model = RoleMapper.apply_to_model(existing, role)
                session.add(model)
            else:
                model = RoleMapper.to_model(role)
                session.add(model)
            await session.commit()
            await session.refresh(model)
            return RoleMapper.to_entity(model)

    async def find_by_id(self, role_id: UUID, tenant_id: UUID) -> Optional[Role]:
        """按 ID 查询角色（限定租户，跨租户返回 None）"""
        async with session_scope(self._session_factory) as session:
            model = await session.get(RoleModel, role_id)
            if model is None or model.tenant_id != tenant_id:
                return None
            return RoleMapper.to_entity(model)

    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RoleModel).where(RoleModel.name == name, RoleModel.tenant_id == tenant_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return RoleMapper.to_entity(model)

    async def find_by_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        """查询指定租户下的角色（分页）"""
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RoleModel)
                .where(RoleModel.tenant_id == tenant_id)
                .offset(skip)
                .limit(limit)
            )
            models = result.scalars().all()
            return [RoleMapper.to_entity(m) for m in models]

    async def find_by_ids(self, role_ids: List[UUID], tenant_id: UUID) -> List[Role]:
        """按 ID 批量查询角色（避免 N+1），结果限定在指定租户内"""
        if not role_ids:
            return []
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(RoleModel).where(
                    RoleModel.id.in_(role_ids),
                    RoleModel.tenant_id == tenant_id,
                )
            )
            return [RoleMapper.to_entity(m) for m in result.scalars().all()]

    async def delete(self, role_id: UUID, tenant_id: UUID) -> bool:
        """删除指定租户内的角色（跨租户返回 False）"""
        async with session_scope(self._session_factory) as session:
            model = await session.get(RoleModel, role_id)
            if model is None or model.tenant_id != tenant_id:
                return False
            await session.delete(model)
            await session.commit()
            return True

    async def assign_to_user(self, role_id: UUID, user_id: UUID) -> bool:
        """将角色分配给用户"""
        from src.infrastructure.persistence.sqlmodel.models.user import UserModel
        async with session_scope(self._session_factory) as session:
            role = await session.get(RoleModel, role_id)
            user = await session.get(UserModel, user_id)
            if role is None or user is None:
                return False
            existing = await session.execute(
                select(UserRoleModel).where(
                    UserRoleModel.role_id == role_id,
                    UserRoleModel.user_id == user_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                return True  # 已分配，幂等
            session.add(UserRoleModel(role_id=role_id, user_id=user_id))
            await session.commit()
            return True

    async def get_user_role_ids(self, user_id: UUID) -> List[UUID]:
        """查询用户拥有的角色 ID 列表"""
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(UserRoleModel.role_id).where(UserRoleModel.user_id == user_id)
            )
            return list(result.scalars().all())
