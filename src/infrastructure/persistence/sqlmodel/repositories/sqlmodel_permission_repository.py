from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.permission import Permission
from src.domain.repositories.permission_repository import PermissionRepository
from src.infrastructure.persistence.sqlmodel.mappers.permission_mapper import PermissionMapper
from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel


class SQLModelPermissionRepository(PermissionRepository):

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, permission: Permission) -> Permission:
        model = PermissionMapper.to_model(permission)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return PermissionMapper.to_entity(model)

    async def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        model = await self._session.get(PermissionModel, permission_id)
        if model is None:
            return None
        return PermissionMapper.to_entity(model)

    async def find_by_action_and_resource(self, action: str, resource: str) -> Optional[Permission]:
        result = await self._session.execute(
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
        result = await self._session.execute(
            select(PermissionModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [PermissionMapper.to_entity(m) for m in models]

    async def delete(self, permission_id: UUID) -> bool:
        model = await self._session.get(PermissionModel, permission_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.commit()
        return True
