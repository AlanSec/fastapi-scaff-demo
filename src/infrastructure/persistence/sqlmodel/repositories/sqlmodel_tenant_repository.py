from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from src.domain.entities.tenant import Tenant
from src.domain.repositories.tenant_repository import TenantRepository
from src.infrastructure.persistence.database import session_scope
from src.infrastructure.persistence.sqlmodel.mappers.tenant_mapper import TenantMapper
from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel


class SQLModelTenantRepository(TenantRepository):

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def save(self, tenant: Tenant) -> Tenant:
        async with session_scope(self._session_factory) as session:
            existing = await session.get(TenantModel, tenant.id)
            if existing is not None:
                model = TenantMapper.apply_to_model(existing, tenant)
                session.add(model)
            else:
                model = TenantMapper.to_model(tenant)
                session.add(model)
            await session.commit()
            await session.refresh(model)
            return TenantMapper.to_entity(model)

    async def find_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        async with session_scope(self._session_factory) as session:
            model = await session.get(TenantModel, tenant_id)
            if model is None:
                return None
            return TenantMapper.to_entity(model)

    async def find_by_name(self, name: str) -> Optional[Tenant]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(TenantModel).where(TenantModel.name == name)
            )
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return TenantMapper.to_entity(model)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        async with session_scope(self._session_factory) as session:
            result = await session.execute(
                select(TenantModel).offset(skip).limit(limit)
            )
            models = result.scalars().all()
            return [TenantMapper.to_entity(m) for m in models]

    async def delete(self, tenant_id: UUID) -> bool:
        async with session_scope(self._session_factory) as session:
            model = await session.get(TenantModel, tenant_id)
            if model is None:
                return False
            await session.delete(model)
            await session.commit()
            return True
