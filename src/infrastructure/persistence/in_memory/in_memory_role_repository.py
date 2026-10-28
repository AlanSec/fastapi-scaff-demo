from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository


class InMemoryRoleRepository(RoleRepository):

    def __init__(self):
        self._roles: Dict[UUID, Role] = {}
        self._user_roles: Dict[UUID, set] = {}  # user_id -> set(role_id)

    async def save(self, role: Role) -> Role:
        self._roles[role.id] = role
        return role

    async def find_by_id(self, role_id: UUID, tenant_id: UUID) -> Optional[Role]:
        """按 ID 查询角色（限定租户，跨租户返回 None）"""
        role = self._roles.get(role_id)
        if role is None or role.tenant_id != tenant_id:
            return None
        return role

    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        for role in self._roles.values():
            if role.name == name and role.tenant_id == tenant_id:
                return role
        return None

    async def find_by_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        """查询指定租户下的角色（分页）"""
        items = sorted(
            (r for r in self._roles.values() if r.tenant_id == tenant_id),
            key=lambda r: r.created_at,
            reverse=True,
        )
        return items[skip:skip + limit]

    async def find_by_ids(self, role_ids: List[UUID], tenant_id: UUID) -> List[Role]:
        """按 ID 批量查询角色（避免 N+1），结果限定在指定租户内"""
        return [
            self._roles[rid]
            for rid in role_ids
            if rid in self._roles and self._roles[rid].tenant_id == tenant_id
        ]

    async def delete(self, role_id: UUID, tenant_id: UUID) -> bool:
        """删除指定租户内的角色（跨租户返回 False）"""
        role = self._roles.get(role_id)
        if role is None or role.tenant_id != tenant_id:
            return False
        self._roles.pop(role_id)
        for user_id, role_ids in self._user_roles.items():
            role_ids.discard(role_id)
        return True

    async def assign_to_user(self, role_id: UUID, user_id: UUID) -> bool:
        if role_id not in self._roles:
            return False
        self._user_roles.setdefault(user_id, set()).add(role_id)
        return True

    async def get_user_role_ids(self, user_id: UUID) -> List[UUID]:
        return list(self._user_roles.get(user_id, set()))
