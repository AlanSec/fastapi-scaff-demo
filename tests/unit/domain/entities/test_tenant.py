import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.entities.tenant import Tenant


def test_tenant_creation():
    tenant_id = uuid4()
    name = "Test Tenant"
    domain = "test.example.com"
    is_active = True
    created_at = datetime.now()
    
    tenant = Tenant(
        id=tenant_id,
        name=name,
        domain=domain,
        is_active=is_active,
        created_at=created_at,
        updated_at=created_at
    )
    
    assert tenant.id == tenant_id
    assert tenant.name == name
    assert tenant.domain == domain
    assert tenant.is_active is True
    assert tenant.created_at == created_at
    assert tenant.updated_at == created_at


def test_tenant_create_factory_method():
    name = "New Tenant"
    domain = "new.example.com"
    
    tenant = Tenant.create(name=name, domain=domain)
    
    assert isinstance(tenant.id, UUID)
    assert tenant.name == name
    assert tenant.domain == domain
    assert tenant.is_active is True


def test_tenant_deactivate():
    tenant = Tenant.create(name="Tenant", domain="example.com")
    
    deactivated = tenant.deactivate()
    
    assert deactivated.is_active is False
    assert tenant.is_active is True


def test_tenant_activate():
    tenant = Tenant.create(name="Tenant", domain="example.com")
    deactivated = tenant.deactivate()
    
    activated = deactivated.activate()
    
    assert activated.is_active is True
    assert deactivated.is_active is False


def test_tenant_update_domain():
    tenant = Tenant.create(name="Tenant", domain="old.example.com")
    
    updated = tenant.update_domain("new.example.com")
    
    assert updated.domain == "new.example.com"
    assert tenant.domain == "old.example.com"


def test_tenant_update_name():
    tenant = Tenant.create(name="Old Name", domain="example.com")
    
    updated = tenant.update_name("New Name")
    
    assert updated.name == "New Name"
    assert tenant.name == "Old Name"


def test_tenant_immutability():
    tenant = Tenant.create(name="Tenant", domain="example.com")
    
    with pytest.raises(AttributeError):
        tenant.name = "New Name"
    
    with pytest.raises(AttributeError):
        tenant.is_active = False


def test_tenant_equality():
    tenant_id = uuid4()
    name = "Tenant"
    domain = "example.com"
    now = datetime.now()
    
    tenant1 = Tenant(
        id=tenant_id,
        name=name,
        domain=domain,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    
    tenant2 = Tenant(
        id=tenant_id,
        name=name,
        domain=domain,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    
    tenant3 = Tenant.create(name="Other Tenant", domain="other.com")
    
    assert tenant1 == tenant2
    assert tenant1 != tenant3