from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.dto.permission_dto import (
    CreatePermissionInputDTO,
    PermissionOutputDTO,
    UpdatePermissionInputDTO,
)
from src.domain.entities.permission import Permission, PermissionAction, Resource
from src.domain.exceptions import ConflictError
from src.domain.repositories.permission_repository import PermissionRepository


@dataclass
class CreatePermissionUseCase:
    permission_repository: PermissionRepository

    async def execute(self, dto: CreatePermissionInputDTO) -> PermissionOutputDTO:
        existing = await self.permission_repository.find_by_action_and_resource(
            dto.action, dto.resource
        )
        if existing:
            raise ConflictError(f"Permission '{dto.action}:{dto.resource}' already exists")

        permission = Permission.create(
            action=PermissionAction(dto.action),
            resource=Resource(dto.resource),
            description=dto.description,
        )
        await self.permission_repository.save(permission)

        return PermissionOutputDTO(
            id=permission.id, action=permission.action.value,
            resource=permission.resource.value, description=permission.description,
            is_active=permission.is_active,
            created_at=permission.created_at, updated_at=permission.updated_at,
        )


@dataclass
class GetPermissionUseCase:
    permission_repository: PermissionRepository

    async def execute(self, permission_id: UUID) -> PermissionOutputDTO | None:
        p = await self.permission_repository.find_by_id(permission_id)
        if p is None:
            return None
        return PermissionOutputDTO(
            id=p.id, action=p.action.value, resource=p.resource.value,
            description=p.description, is_active=p.is_active,
            created_at=p.created_at, updated_at=p.updated_at,
        )


@dataclass
class ListPermissionsUseCase:
    permission_repository: PermissionRepository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[PermissionOutputDTO]:
        permissions = await self.permission_repository.find_all(skip=skip, limit=limit)
        return [
            PermissionOutputDTO(
                id=p.id, action=p.action.value, resource=p.resource.value,
                description=p.description, is_active=p.is_active,
                created_at=p.created_at, updated_at=p.updated_at,
            )
            for p in permissions
        ]


@dataclass
class UpdatePermissionUseCase:
    permission_repository: PermissionRepository

    async def execute(self, permission_id: UUID, dto: UpdatePermissionInputDTO) -> PermissionOutputDTO | None:
        p = await self.permission_repository.find_by_id(permission_id)
        if p is None:
            return None

        if dto.description is not None:
            p = Permission(
                id=p.id, action=p.action, resource=p.resource,
                description=dto.description, is_active=p.is_active,
                created_at=p.created_at, updated_at=p.updated_at,
            )

        await self.permission_repository.save(p)
        return PermissionOutputDTO(
            id=p.id, action=p.action.value, resource=p.resource.value,
            description=p.description, is_active=p.is_active,
            created_at=p.created_at, updated_at=p.updated_at,
        )


@dataclass
class DeletePermissionUseCase:
    permission_repository: PermissionRepository

    async def execute(self, permission_id: UUID) -> bool:
        return await self.permission_repository.delete(permission_id)
