from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.dto.role_dto import (
    CreateRoleInputDTO,
    RoleOutputDTO,
    UpdateRoleInputDTO,
)
from src.domain.entities.role import Role
from src.domain.exceptions import ConflictError, InvalidInputError
from src.domain.repositories.role_repository import RoleRepository


def _to_dto(role: Role) -> RoleOutputDTO:
    return RoleOutputDTO(
        id=role.id, name=role.name, description=role.description,
        is_active=role.is_active, tenant_id=role.tenant_id,
        created_at=role.created_at, updated_at=role.updated_at,
    )


@dataclass
class CreateRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, dto: CreateRoleInputDTO, tenant_id: UUID) -> RoleOutputDTO:
        """创建角色。tenant_id 来自认证上下文（调用方），不接受请求体指定。"""
        name = dto.name.strip()
        if not name:
            raise InvalidInputError("Role name cannot be empty")

        existing = await self.role_repository.find_by_name(name, tenant_id)
        if existing:
            raise ConflictError(f"Role '{name}' already exists in this tenant")

        role = Role.create(name=name, description=dto.description, tenant_id=tenant_id)
        await self.role_repository.save(role)

        return _to_dto(role)


@dataclass
class GetRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, role_id: UUID, tenant_id: UUID) -> RoleOutputDTO | None:
        """按 ID 查询角色，限定在指定租户内（跨租户返回 None → 404）"""
        role = await self.role_repository.find_by_id(role_id, tenant_id)
        if role is None:
            return None
        return _to_dto(role)


@dataclass
class ListRolesUseCase:
    role_repository: RoleRepository

    async def execute(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[RoleOutputDTO]:
        """仅返回指定租户内的角色"""
        roles = await self.role_repository.find_by_tenant(tenant_id, skip=skip, limit=limit)
        return [_to_dto(r) for r in roles]


@dataclass
class UpdateRoleUseCase:
    role_repository: RoleRepository

    async def execute(
        self, role_id: UUID, dto: UpdateRoleInputDTO, tenant_id: UUID
    ) -> RoleOutputDTO | None:
        role = await self.role_repository.find_by_id(role_id, tenant_id)
        if role is None:
            return None

        if dto.name is not None:
            role = role.update_name(dto.name.strip())
        if dto.description is not None:
            role = role.update_description(dto.description)

        await self.role_repository.save(role)
        return _to_dto(role)


@dataclass
class DeleteRoleUseCase:
    role_repository: RoleRepository

    async def execute(self, role_id: UUID, tenant_id: UUID) -> bool:
        return await self.role_repository.delete(role_id, tenant_id)
