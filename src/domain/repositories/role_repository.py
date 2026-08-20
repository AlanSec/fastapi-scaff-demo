from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.role import Role


class RoleRepository(ABC):

    @abstractmethod
    async def save(self, role: Role) -> Role:
        pass

    @abstractmethod
    async def find_by_id(self, role_id: UUID) -> Optional[Role]:
        pass

    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        pass

    @abstractmethod
    async def find_by_tenant(self, tenant_id: UUID) -> List[Role]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        pass

    @abstractmethod
    async def find_by_ids(self, role_ids: List[UUID]) -> List[Role]:
        """按 ID 批量查询角色（避免 N+1）"""
        pass

    @abstractmethod
    async def delete(self, role_id: UUID) -> bool:
        pass

    @abstractmethod
    async def assign_to_user(self, role_id: UUID, user_id: UUID) -> bool:
        """将角色分配给用户"""
        pass

    @abstractmethod
    async def get_user_role_ids(self, user_id: UUID) -> List[UUID]:
        """查询用户拥有的角色 ID 列表"""
        pass
