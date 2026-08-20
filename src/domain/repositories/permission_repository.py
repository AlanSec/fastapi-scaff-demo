from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.permission import Permission


class PermissionRepository(ABC):

    @abstractmethod
    async def save(self, permission: Permission) -> Permission:
        pass

    @abstractmethod
    async def find_by_id(self, permission_id: UUID) -> Optional[Permission]:
        pass

    @abstractmethod
    async def find_by_action_and_resource(
        self, action: str, resource: str
    ) -> Optional[Permission]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        pass

    @abstractmethod
    async def delete(self, permission_id: UUID) -> bool:
        pass

    @abstractmethod
    async def assign_to_role(self, permission_id: UUID, role_id: UUID) -> bool:
        """将权限分配给角色"""
        pass

    @abstractmethod
    async def get_role_permission_ids(self, role_id: UUID) -> List[UUID]:
        """查询角色拥有的权限 ID 列表"""
        pass

    @abstractmethod
    async def get_permission_ids_for_roles(self, role_ids: List[UUID]) -> List[UUID]:
        """批量查询多个角色拥有的权限 ID（去重，避免 N+1）"""
        pass

    @abstractmethod
    async def find_by_ids(self, permission_ids: List[UUID]) -> List[Permission]:
        """按 ID 批量查询权限（避免 N+1）"""
        pass
