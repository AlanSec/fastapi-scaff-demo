from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.domain.entities.permission import Permission
from src.domain.entities.role import Role
from src.domain.exceptions import EntityNotFoundError
from src.domain.repositories.permission_repository import PermissionRepository
from src.domain.repositories.role_repository import RoleRepository
from src.domain.repositories.user_repository import UserRepository


@dataclass
class AssignRoleToUserUseCase:
    user_repository: UserRepository
    role_repository: RoleRepository

    async def execute(self, user_id: UUID, role_id: UUID, tenant_id: UUID) -> bool:
        """将角色分配给用户。user 与 role 必须同属 tenant_id（跨租户抛错）。"""
        user = await self.user_repository.find_by_id(user_id, tenant_id)
        if user is None:
            raise EntityNotFoundError("User not found")
        role = await self.role_repository.find_by_id(role_id, tenant_id)
        if role is None:
            raise EntityNotFoundError("Role not found")
        return await self.role_repository.assign_to_user(role_id, user_id)


@dataclass
class AssignPermissionToRoleUseCase:
    role_repository: RoleRepository
    permission_repository: PermissionRepository

    async def execute(self, role_id: UUID, permission_id: UUID, tenant_id: UUID) -> bool:
        """将权限分配给角色。role 必须属于 tenant_id（权限本身是全局资源）。"""
        role = await self.role_repository.find_by_id(role_id, tenant_id)
        if role is None:
            raise EntityNotFoundError("Role not found")
        permission = await self.permission_repository.find_by_id(permission_id)
        if permission is None:
            raise EntityNotFoundError("Permission not found")
        return await self.permission_repository.assign_to_role(permission_id, role_id)


@dataclass
class GetUserRolesUseCase:
    role_repository: RoleRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> List[Role]:
        role_ids = await self.role_repository.get_user_role_ids(user_id)
        return await self.role_repository.find_by_ids(role_ids, tenant_id)


@dataclass
class GetRolePermissionsUseCase:
    role_repository: RoleRepository
    permission_repository: PermissionRepository

    async def execute(self, role_id: UUID, tenant_id: UUID) -> List[Permission]:
        """查询角色拥有的权限。仅限本租户角色（跨租户返回空列表）。"""
        role = await self.role_repository.find_by_id(role_id, tenant_id)
        if role is None:
            return []
        permission_ids = await self.permission_repository.get_permission_ids_for_roles([role_id])
        return await self.permission_repository.find_by_ids(permission_ids)


@dataclass
class GetUserPermissionsUseCase:
    role_repository: RoleRepository
    permission_repository: PermissionRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> List[Permission]:
        """收集用户经所有角色获得的权限（去重），仅返回有效权限。"""
        role_ids = await self.role_repository.get_user_role_ids(user_id)
        # 防御性过滤：仅统计本租户内的角色（数据不一致时兜底）
        roles = await self.role_repository.find_by_ids(role_ids, tenant_id)
        role_ids = [r.id for r in roles]
        permission_ids = await self.permission_repository.get_permission_ids_for_roles(role_ids)
        permissions = await self.permission_repository.find_by_ids(permission_ids)
        return [p for p in permissions if p.is_active]
