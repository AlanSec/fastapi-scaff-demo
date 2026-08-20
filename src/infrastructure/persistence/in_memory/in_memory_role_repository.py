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

    async def find_by_id(self, role_id: UUID) -> Optional[Role]:
        return self._roles.get(role_id)

    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        for role in self._roles.values():
            if role.name.value == name and role.tenant_id == tenant_id:
                return role
        return None

    async def find_by_tenant(self, tenant_id: UUID) -> List[Role]:
        return [r for r in self._roles.values() if r.tenant_id == tenant_id]

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        items = sorted(self._roles.values(), key=lambda r: r.created_at, reverse=True)
        return items[skip:skip + limit]

    async def find_by_ids(self, role_ids: List[UUID]) -> List[Role]:
        """按 ID 批量查询角色（避免 N+1）"""
        return [self._roles[rid] for rid in role_ids if rid in self._roles]

    async def delete(self, role_id: UUID) -> bool:
        removed = self._roles.pop(role_id, None) is not None
        if removed:
            for user_id, role_ids in self._user_roles.items():
                role_ids.discard(role_id)
        return removed

    async def assign_to_user(self, role_id: UUID, user_id: UUID) -> bool:
        if role_id not in self._roles:
            return False
        self._user_roles.setdefault(user_id, set()).add(role_id)
        return True

    async def get_user_role_ids(self, user_id: UUID) -> List[UUID]:
        return list(self._user_roles.get(user_id, set()))
