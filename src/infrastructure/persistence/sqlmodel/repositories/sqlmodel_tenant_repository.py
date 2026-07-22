from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.tenant import Tenant
from src.domain.repositories.tenant_repository import TenantRepository
from src.infrastructure.persistence.sqlmodel.mappers.tenant_mapper import TenantMapper
from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel


class SQLModelTenantRepository(TenantRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, tenant: Tenant) -> Tenant:
        model = TenantMapper.to_model(tenant)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return TenantMapper.to_entity(model)

    async def find_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        model = await self._session.get(TenantModel, tenant_id)
        if model is None:
            return None
        return TenantMapper.to_entity(model)

    async def find_by_name(self, name: str) -> Optional[Tenant]:
        result = await self._session.execute(
            select(TenantModel).where(TenantModel.name == name)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return TenantMapper.to_entity(model)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        result = await self._session.execute(
            select(TenantModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [TenantMapper.to_entity(m) for m in models]

    async def delete(self, tenant_id: UUID) -> bool:
        model = await self._session.get(TenantModel, tenant_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.commit()
        return True
