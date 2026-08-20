from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.domain.entities.permission import Permission
from src.domain.entities.role import Role
from src.domain.repositories.permission_repository import PermissionRepository
from src.domain.repositories.role_repository import RoleRepository
from src.domain.repositories.user_repository import UserRepository


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
        return await self.role_repository.assign_to_user(role_id, user_id)


@dataclass
class AssignPermissionToRoleUseCase:
    role_repository: RoleRepository
    permission_repository: PermissionRepository

    async def execute(self, role_id: UUID, permission_id: UUID) -> bool:
        role = await self.role_repository.find_by_id(role_id)
        if role is None:
            raise ValueError("Role not found")
        permission = await self.permission_repository.find_by_id(permission_id)
        if permission is None:
            raise ValueError("Permission not found")
        return await self.permission_repository.assign_to_role(permission_id, role_id)


@dataclass
class GetUserRolesUseCase:
    role_repository: RoleRepository

    async def execute(self, user_id: UUID) -> List[Role]:
        role_ids = await self.role_repository.get_user_role_ids(user_id)
        return await self.role_repository.find_by_ids(role_ids)


@dataclass
class GetRolePermissionsUseCase:
    permission_repository: PermissionRepository

    async def execute(self, role_id: UUID) -> List[Permission]:
        permission_ids = await self.permission_repository.get_permission_ids_for_roles([role_id])
        return await self.permission_repository.find_by_ids(permission_ids)


@dataclass
class GetUserPermissionsUseCase:
    role_repository: RoleRepository
    permission_repository: PermissionRepository

    async def execute(self, user_id: UUID) -> List[Permission]:
        """收集用户经所有角色获得的权限（去重），仅返回有效权限"""
        role_ids = await self.role_repository.get_user_role_ids(user_id)
        permission_ids = await self.permission_repository.get_permission_ids_for_roles(role_ids)
        permissions = await self.permission_repository.find_by_ids(permission_ids)
        return [p for p in permissions if p.is_active]
