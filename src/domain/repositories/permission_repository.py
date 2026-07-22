from abc import ABC, abstractmethod
from typing import Optional, List
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
