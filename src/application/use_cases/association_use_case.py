from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.domain.entities.role import Role, RoleName
from src.domain.entities.permission import Permission
from src.domain.repositories.user_repository import UserRepository
from src.domain.repositories.role_repository import RoleRepository
from src.domain.repositories.permission_repository import PermissionRepository


@dataclass
class AssignRoleToUserUseCase:
    user_repository: UserRepository
    role_repository: RoleRepository

    async def execute(self, user_id: UUID, role_id: UUID) -> bool:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        role = await self.role_repository.find_by_id(role_id)
        if role is None:
            raise ValueError("Role not found")
        return True


@dataclass
class GetUserRolesUseCase:
    role_repository: RoleRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> List[Role]:
        return await self.role_repository.find_by_tenant(tenant_id)


@dataclass
class AssignPermissionToRoleUseCase:
    permission_repository: PermissionRepository

    async def execute(self, role_id: UUID, permission_id: UUID) -> bool:
        permission = await self.permission_repository.find_by_id(permission_id)
        if permission is None:
            raise ValueError("Permission not found")
        return True


@dataclass
class GetRolePermissionsUseCase:
    permission_repository: PermissionRepository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        return await self.permission_repository.find_all(skip=skip, limit=limit)
