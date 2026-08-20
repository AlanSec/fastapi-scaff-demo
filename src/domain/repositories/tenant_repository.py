from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.tenant import Tenant


class TenantRepository(ABC):

    @abstractmethod
    async def save(self, tenant: Tenant) -> Tenant:
        pass

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Tenant]:
        pass

    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        pass

    @abstractmethod
    async def delete(self, tenant_id: UUID) -> bool:
        pass
