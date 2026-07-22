from typing import Optional, List, Dict
from uuid import UUID

from src.domain.entities.permission import Permission
from src.domain.repositories.permission_repository import PermissionRepository


class InMemoryPermissionRepository(PermissionRepository):

    def __init__(self):
        self._permissions: Dict[UUID, Permission] = {}

    async def save(self, permission: Permission) -> Permission:
        self._permissions[permission.id] = permission
        return permission

    async def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        return self._permissions.get(permission_id)

    async def find_by_action_and_resource(self, action: str, resource: str) -> Optional[Permission]:
        for p in self._permissions.values():
            if p.action.value == action and p.resource.value == resource:
                return p
        return None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        items = sorted(self._permissions.values(), key=lambda p: p.created_at, reverse=True)
        return items[skip:skip + limit]

    async def delete(self, permission_id: UUID) -> bool:
        return self._permissions.pop(permission_id, None) is not None
