from typing import Optional, List, Dict
from uuid import UUID

from src.domain.entities.role import Role
from src.domain.repositories.role_repository import RoleRepository


class InMemoryRoleRepository(RoleRepository):

    def __init__(self):
        self._roles: Dict[UUID, Role] = {}

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

    async def delete(self, role_id: UUID) -> bool:
        return self._roles.pop(role_id, None) is not None
