from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.role import Role


class RoleRepository(ABC):

    @abstractmethod
    async def save(self, role: Role) -> Role:
        pass

    @abstractmethod
    async def find_by_id(self, role_id: UUID, tenant_id: UUID) -> Optional[Role]:
        """按 ID 查询角色，必须限定在指定租户内（跨租户返回 None）"""
        pass

    @abstractmethod
    async def find_by_name(self, name: str, tenant_id: UUID) -> Optional[Role]:
        pass

    @abstractmethod
    async def find_by_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Role]:
        """查询指定租户下的角色（分页）"""
        pass

    @abstractmethod
    async def find_by_ids(self, role_ids: List[UUID], tenant_id: UUID) -> List[Role]:
        """按 ID 批量查询角色（避免 N+1），结果限定在指定租户内"""
        pass

    @abstractmethod
    async def delete(self, role_id: UUID, tenant_id: UUID) -> bool:
        """删除指定租户内的角色（跨租户返回 False）"""
        pass

    @abstractmethod
    async def assign_to_user(self, role_id: UUID, user_id: UUID) -> bool:
        """将角色分配给用户"""
        pass

    @abstractmethod
    async def get_user_role_ids(self, user_id: UUID) -> List[UUID]:
        """查询用户拥有的角色 ID 列表"""
        pass
