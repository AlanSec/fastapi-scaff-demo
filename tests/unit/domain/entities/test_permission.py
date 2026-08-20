from datetime import datetime
from uuid import UUID, uuid4

import pytest
from src.domain.entities.permission import Permission, PermissionAction, Resource


def test_permission_creation():
    """测试权限创建"""
    perm_id = uuid4()
    action = PermissionAction.READ
    resource = Resource.USER
    created_at = datetime.now()
    updated_at = datetime.now()

    permission = Permission(
        id=perm_id,
        action=action,
        resource=resource,
        description="读取用户权限",
        is_active=True,
        created_at=created_at,
        updated_at=updated_at
    )

    assert permission.id == perm_id
    assert permission.action == action
    assert permission.resource == resource
    assert permission.description == "读取用户权限"
    assert permission.is_active is True


def test_permission_create_factory_method():
    permission = Permission.create(
        action=PermissionAction.UPDATE,
        resource=Resource.TENANT,
        description="管理租户权限"
    )

    assert isinstance(permission.id, UUID)
    assert permission.action == PermissionAction.UPDATE
    assert permission.resource == Resource.TENANT
    assert permission.description == "管理租户权限"
    assert permission.is_active is True


def test_permission_create_crud_factory():
    read_perm = Permission.create_crud(Resource.USER, PermissionAction.READ)
    write_perm = Permission.create_crud(Resource.USER, PermissionAction.UPDATE)
    delete_perm = Permission.create_crud(Resource.USER, PermissionAction.DELETE)

    assert read_perm.action == PermissionAction.READ
    assert write_perm.action == PermissionAction.UPDATE
    assert delete_perm.action == PermissionAction.DELETE


def test_permission_deactivate():
    """测试停用权限"""
    permission = Permission.create(
        action=PermissionAction.READ,
        resource=Resource.USER,
        description="读取权限"
    )

    deactivated = permission.deactivate()

    assert deactivated.is_active is False
    assert permission.is_active is True


def test_permission_activate():
    """测试激活权限"""
    permission = Permission.create(
        action=PermissionAction.READ,
        resource=Resource.USER,
        description="读取权限"
    )
    deactivated = permission.deactivate()

    activated = deactivated.activate()

    assert activated.is_active is True
    assert deactivated.is_active is False


def test_permission_immutability():
    """测试权限实体不可变性"""
    permission = Permission.create(
        action=PermissionAction.READ,
        resource=Resource.USER,
        description="读取权限"
    )

    with pytest.raises(AttributeError):
        permission.action = PermissionAction.WRITE

    with pytest.raises(AttributeError):
        permission.is_active = False


def test_permission_equality():
    """测试权限实体相等性"""
    perm_id = uuid4()
    action = PermissionAction.READ
    resource = Resource.USER
    now = datetime.now()

    perm1 = Permission(
        id=perm_id,
        action=action,
        resource=resource,
        description="读取",
        is_active=True,
        created_at=now,
        updated_at=now
    )

    perm2 = Permission(
        id=perm_id,
        action=action,
        resource=resource,
        description="读取",
        is_active=True,
        created_at=now,
        updated_at=now
    )

    perm3 = Permission.create(
        action=PermissionAction.UPDATE,
        resource=Resource.USER,
        description="写入"
    )

    assert perm1 == perm2
    assert perm1 != perm3


def test_permission_action_enum_values():
    """测试权限动作枚举值"""
    assert PermissionAction.CREATE.value == "create"
    assert PermissionAction.READ.value == "read"
    assert PermissionAction.UPDATE.value == "update"
    assert PermissionAction.DELETE.value == "delete"


def test_permission_resource_enum_values():
    """测试资源枚举值"""
    assert Resource.USER.value == "user"
    assert Resource.TENANT.value == "tenant"
    assert Resource.ROLE.value == "role"
    assert Resource.PERMISSION.value == "permission"
