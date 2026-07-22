import pytest
from uuid import uuid4

from src.domain.entities.tenant import Tenant
from src.infrastructure.persistence.in_memory.in_memory_tenant_repository import InMemoryTenantRepository


@pytest.mark.asyncio
async def test_save_and_find_tenant():
    repo = InMemoryTenantRepository()
    tenant = Tenant.create(name="Test Tenant", domain="test.example.com")
    saved = await repo.save(tenant)
    assert saved.id == tenant.id

    found = await repo.find_by_id(tenant.id)
    assert found is not None
    assert found.name == "Test Tenant"


@pytest.mark.asyncio
async def test_find_by_name():
    repo = InMemoryTenantRepository()
    tenant = Tenant.create(name="Unique", domain="unique.example.com")
    await repo.save(tenant)

    found = await repo.find_by_name("Unique")
    assert found is not None

    missing = await repo.find_by_name("NotFound")
    assert missing is None


@pytest.mark.asyncio
async def test_find_all():
    repo = InMemoryTenantRepository()
    t1 = Tenant.create(name="A", domain="a.com")
    t2 = Tenant.create(name="B", domain="b.com")
    await repo.save(t1)
    await repo.save(t2)

    all_tenants = await repo.find_all()
    assert len(all_tenants) >= 2


@pytest.mark.asyncio
async def test_delete_tenant():
    repo = InMemoryTenantRepository()
    tenant = Tenant.create(name="ToDelete", domain="delete.com")
    await repo.save(tenant)

    deleted = await repo.delete(tenant.id)
    assert deleted is True

    found = await repo.find_by_id(tenant.id)
    assert found is None
    assert await repo.delete(uuid4()) is False
