from dataclasses import dataclass
from typing import List

from src.application.dto.tenant_dto import (
    CreateTenantInputDTO,
    UpdateTenantInputDTO,
    TenantOutputDTO,
)
from src.domain.entities.tenant import Tenant
from src.domain.repositories.tenant_repository import TenantRepository


@dataclass
class CreateTenantUseCase:
    tenant_repository: TenantRepository

    async def execute(self, dto: CreateTenantInputDTO) -> TenantOutputDTO:
        existing = await self.tenant_repository.find_by_name(dto.name)
        if existing:
            raise ValueError(f"Tenant '{dto.name}' already exists")

        tenant = Tenant.create(name=dto.name, domain=dto.domain)
        await self.tenant_repository.save(tenant)

        return TenantOutputDTO(
            id=tenant.id,
            name=tenant.name,
            domain=tenant.domain,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )


@dataclass
class GetTenantUseCase:
    tenant_repository: TenantRepository

    async def execute(self, tenant_id) -> TenantOutputDTO | None:
        tenant = await self.tenant_repository.find_by_id(tenant_id)
        if tenant is None:
            return None
        return TenantOutputDTO(
            id=tenant.id,
            name=tenant.name,
            domain=tenant.domain,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )


@dataclass
class ListTenantsUseCase:
    tenant_repository: TenantRepository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[TenantOutputDTO]:
        tenants = await self.tenant_repository.find_all(skip=skip, limit=limit)
        return [
            TenantOutputDTO(
                id=t.id, name=t.name, domain=t.domain,
                is_active=t.is_active, created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in tenants
        ]


@dataclass
class UpdateTenantUseCase:
    tenant_repository: TenantRepository

    async def execute(self, tenant_id, dto: UpdateTenantInputDTO) -> TenantOutputDTO | None:
        tenant = await self.tenant_repository.find_by_id(tenant_id)
        if tenant is None:
            return None

        if dto.name is not None:
            tenant = tenant.update_name(dto.name)
        if dto.domain is not None:
            tenant = tenant.update_domain(dto.domain)

        await self.tenant_repository.save(tenant)
        return TenantOutputDTO(
            id=tenant.id, name=tenant.name, domain=tenant.domain,
            is_active=tenant.is_active, created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )


@dataclass
class DeleteTenantUseCase:
    tenant_repository: TenantRepository

    async def execute(self, tenant_id) -> bool:
        return await self.tenant_repository.delete(tenant_id)
