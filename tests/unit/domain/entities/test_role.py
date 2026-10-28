from datetime import datetime
from uuid import UUID, uuid4

import pytest
from src.domain.entities.role import Role


def test_role_creation():
    role_id = uuid4()
    name = "admin"
    is_active = True
    created_at = datetime.now()
    updated_at = datetime.now()
    tenant_id = uuid4()

    role = Role(
        id=role_id, name=name, description="admin role",
        is_active=is_active, tenant_id=tenant_id,
        created_at=created_at, updated_at=updated_at,
    )

    assert role.id == role_id
    assert role.name == name
    assert role.is_active is True


def test_role_create_factory_method():
    tenant_id = uuid4()
    role = Role.create(name="user", description="normal user", tenant_id=tenant_id)
    assert isinstance(role.id, UUID)
    assert role.name == "user"
    assert role.is_active is True
    # 角色必须归属于调用方指定的租户（不允许随机生成）
    assert role.tenant_id == tenant_id


def test_role_create_requires_tenant_id():
    with pytest.raises(TypeError):
        Role.create(name="user", description="no tenant")


def test_role_deactivate():
    role = Role.create(name="user", description="user role", tenant_id=uuid4())
    deactivated = role.deactivate()
    assert deactivated.is_active is False
    assert role.is_active is True


def test_role_activate():
    role = Role.create(name="user", description="user role", tenant_id=uuid4())
    deactivated = role.deactivate()
    activated = deactivated.activate()
    assert activated.is_active is True
    assert deactivated.is_active is False


def test_role_update_description():
    role = Role.create(name="user", description="old desc", tenant_id=uuid4())
    updated = role.update_description("new desc")
    assert updated.description == "new desc"
    assert role.description == "old desc"


def test_role_immutability():
    role = Role.create(name="user", description="user role", tenant_id=uuid4())
    with pytest.raises(AttributeError):
        role.name = "admin"
    with pytest.raises(AttributeError):
        role.is_active = False


def test_role_equality():
    role_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now()

    role1 = Role(
        id=role_id, name="admin", description="admin",
        is_active=True, tenant_id=tenant_id,
        created_at=now, updated_at=now,
    )
    role2 = Role(
        id=role_id, name="admin", description="admin",
        is_active=True, tenant_id=tenant_id,
        created_at=now, updated_at=now,
    )
    role3 = Role.create(name="user", description="user", tenant_id=uuid4())

    assert role1 == role2
    assert role1 != role3
