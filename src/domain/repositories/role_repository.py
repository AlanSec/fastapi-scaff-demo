from abc import ABC, abstractmethod
from typing import Optional, List
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
    async def delete(self, role_id: UUID) -> bool:
        pass
