import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.entities.role import Role, RoleName


def test_role_creation():
    role_id = uuid4()
    name = RoleName.ADMIN
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
    role = Role.create(name=RoleName.USER, description="normal user")
    assert isinstance(role.id, UUID)
    assert role.name == RoleName.USER
    assert role.is_active is True


def test_role_deactivate():
    role = Role.create(name=RoleName.USER, description="user role")
    deactivated = role.deactivate()
    assert deactivated.is_active is False
    assert role.is_active is True


def test_role_activate():
    role = Role.create(name=RoleName.USER, description="user role")
    deactivated = role.deactivate()
    activated = deactivated.activate()
    assert activated.is_active is True
    assert deactivated.is_active is False


def test_role_update_description():
    role = Role.create(name=RoleName.USER, description="old desc")
    updated = role.update_description("new desc")
    assert updated.description == "new desc"
    assert role.description == "old desc"


def test_role_immutability():
    role = Role.create(name=RoleName.USER, description="user role")
    with pytest.raises(AttributeError):
        role.name = RoleName.ADMIN
    with pytest.raises(AttributeError):
        role.is_active = False


def test_role_equality():
    role_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now()

    role1 = Role(
        id=role_id, name=RoleName.ADMIN, description="admin",
        is_active=True, tenant_id=tenant_id,
        created_at=now, updated_at=now,
    )
    role2 = Role(
        id=role_id, name=RoleName.ADMIN, description="admin",
        is_active=True, tenant_id=tenant_id,
        created_at=now, updated_at=now,
    )
    role3 = Role.create(name=RoleName.USER, description="user")

    assert role1 == role2
    assert role1 != role3


def test_role_name_enum_values():
    assert RoleName.ADMIN.value == "admin"
    assert RoleName.USER.value == "user"
    assert RoleName.GUEST.value == "guest"
