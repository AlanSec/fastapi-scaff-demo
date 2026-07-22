from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository
from src.infrastructure.persistence.sqlmodel.mappers.role_mapper import RoleMapper
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel


class SQLModelRoleRepository(RoleRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, role: Role) -> Role:
        model = RoleMapper.to_model(role)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return RoleMapper.to_entity(model)

    async def find_by_id(self, role_id: UUID) -> Optional[Role]:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            return None
        return RoleMapper.to_entity(model)

    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.name == name, RoleModel.tenant_id == tenant_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return RoleMapper.to_entity(model)

    async def find_by_tenant(self, tenant_id: UUID) -> List[Role]:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.tenant_id == tenant_id)
        )
        models = result.scalars().all()
        return [RoleMapper.to_entity(m) for m in models]

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        result = await self._session.execute(
            select(RoleModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [RoleMapper.to_entity(m) for m in models]

    async def delete(self, role_id: UUID) -> bool:
        model = await self._session.get(RoleModel, role_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.commit()
        return True
