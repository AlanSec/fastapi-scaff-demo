from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.tenant import Tenant
from src.domain.repositories.tenant_repository import TenantRepository


class InMemoryTenantRepository(TenantRepository):

    def __init__(self):
        self._tenants: Dict[UUID, Tenant] = {}
        self._name_index: Dict[str, UUID] = {}

    async def save(self, tenant: Tenant) -> Tenant:
        self._tenants[tenant.id] = tenant
        self._name_index[tenant.name.lower()] = tenant.id
        return tenant

    async def find_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    async def find_by_name(self, name: str) -> Optional[Tenant]:
        user_id = self._name_index.get(name.lower())
        if user_id is None:
            return None
        return self._tenants.get(user_id)

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        items = sorted(self._tenants.values(), key=lambda t: t.created_at, reverse=True)
        return items[skip:skip + limit]

    async def delete(self, tenant_id: UUID) -> bool:
        tenant = self._tenants.pop(tenant_id, None)
        if tenant is None:
            return False
        self._name_index.pop(tenant.name.lower(), None)
        return True
