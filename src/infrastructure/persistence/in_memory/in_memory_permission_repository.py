from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.permission import Permission
from src.domain.repositories.permission_repository import PermissionRepository


class InMemoryPermissionRepository(PermissionRepository):

    def __init__(self):
        self._permissions: Dict[UUID, Permission] = {}
        self._role_permissions: Dict[UUID, set] = {}  # role_id -> set(permission_id)

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
        removed = self._permissions.pop(permission_id, None) is not None
        if removed:
            for role_id, perm_ids in self._role_permissions.items():
                perm_ids.discard(permission_id)
        return removed

    async def assign_to_role(self, permission_id: UUID, role_id: UUID) -> bool:
        if permission_id not in self._permissions:
            return False
        self._role_permissions.setdefault(role_id, set()).add(permission_id)
        return True

    async def get_role_permission_ids(self, role_id: UUID) -> List[UUID]:
        return list(self._role_permissions.get(role_id, set()))

    async def get_permission_ids_for_roles(self, role_ids: List[UUID]) -> List[UUID]:
        """批量查询多个角色拥有的权限 ID（去重，避免 N+1）"""
        ids: set = set()
        for role_id in role_ids:
            ids.update(self._role_permissions.get(role_id, set()))
        return list(ids)

    async def find_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        """按 ID 批量查询权限（避免 N+1）"""
        return [self._permissions[pid] for pid in permission_ids if pid in self._permissions]
