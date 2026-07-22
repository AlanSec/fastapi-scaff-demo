from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.dto.role_dto import (
    CreateRoleInputDTO,
    UpdateRoleInputDTO,
    RoleOutputDTO,
)
from src.domain.entities.role import Role, RoleName
from src.domain.repositories.role_repository import RoleRepository


@dataclass
class CreateRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, dto: CreateRoleInputDTO) -> RoleOutputDTO:
        existing = await self.role_repository.find_by_name(dto.name, dto.tenant_id)
        if existing:
            raise ValueError(f"Role '{dto.name}' already exists in this tenant")

        role = Role.create(name=RoleName(dto.name), description=dto.description)
        await self.role_repository.save(role)

        return RoleOutputDTO(
            id=role.id, name=role.name.value, description=role.description,
            is_active=role.is_active, tenant_id=role.tenant_id,
            created_at=role.created_at, updated_at=role.updated_at,
        )


@dataclass
class GetRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, role_id: UUID) -> RoleOutputDTO | None:
        role = await self.role_repository.find_by_id(role_id)
        if role is None:
            return None
        return RoleOutputDTO(
            id=role.id, name=role.name.value, description=role.description,
            is_active=role.is_active, tenant_id=role.tenant_id,
            created_at=role.created_at, updated_at=role.updated_at,
        )


@dataclass
class ListRolesUseCase:
    role_repository: RoleRepository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[RoleOutputDTO]:
        roles = await self.role_repository.find_all(skip=skip, limit=limit)
        return [
            RoleOutputDTO(
                id=r.id, name=r.name.value, description=r.description,
                is_active=r.is_active, tenant_id=r.tenant_id,
                created_at=r.created_at, updated_at=r.updated_at,
            )
            for r in roles
        ]


@dataclass
class UpdateRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, role_id: UUID, dto: UpdateRoleInputDTO) -> RoleOutputDTO | None:
        role = await self.role_repository.find_by_id(role_id)
        if role is None:
            return None

        if dto.name is not None:
            role = role.update_name(RoleName(dto.name))
        if dto.description is not None:
            role = role.update_description(dto.description)

        await self.role_repository.save(role)
        return RoleOutputDTO(
            id=role.id, name=role.name.value, description=role.description,
            is_active=role.is_active, tenant_id=role.tenant_id,
            created_at=role.created_at, updated_at=role.updated_at,
        )


@dataclass
class DeleteRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, role_id: UUID) -> bool:
        return await self.role_repository.delete(role_id)
