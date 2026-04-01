import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.entities.role import Role, RoleName


def test_role_creation():
    """测试角色创建"""
    role_id = uuid4()
    name = RoleName.ADMIN
    is_active = True
    created_at = datetime.now()
    updated_at = datetime.now()

    role = Role(
        id=role_id,
        name=name,
        description="管理员角色",
        is_active=is_active,
        created_at=created_at,
        updated_at=updated_at
    )

    assert role.id == role_id
    assert role.name == name
    assert role.description == "管理员角色"
    assert role.is_active is True


def test_role_create_factory_method():
    """测试角色工厂方法"""
    role = Role.create(
        name=RoleName.USER,
        description="普通用户角色"
    )

    assert isinstance(role.id, UUID)
    assert role.name == RoleName.USER
    assert role.description == "普通用户角色"
    assert role.is_active is True
    assert role.created_at <= datetime.now()
    assert role.updated_at == role.created_at


def test_role_deactivate():
    """测试停用角色"""
    role = Role.create(name=RoleName.USER, description="用户角色")

    deactivated = role.deactivate()

    assert deactivated.is_active is False
    assert role.is_active is True  # 原始角色不变


def test_role_activate():
    """测试激活角色"""
    role = Role.create(name=RoleName.USER, description="用户角色")
    deactivated = role.deactivate()

    activated = deactivated.activate()

    assert activated.is_active is True
    assert deactivated.is_active is False


def test_role_update_description():
    """测试更新角色描述"""
    role = Role.create(name=RoleName.USER, description="旧描述")

    updated = role.update_description("新描述")

    assert updated.description == "新描述"
    assert role.description == "旧描述"  # 原始角色不变


def test_role_immutability():
    """测试角色实体不可变性"""
    role = Role.create(name=RoleName.USER, description="用户角色")

    with pytest.raises(AttributeError):
        role.name = RoleName.ADMIN

    with pytest.raises(AttributeError):
        role.is_active = False


def test_role_equality():
    """测试角色实体相等性"""
    role_id = uuid4()
    name = RoleName.ADMIN
    now = datetime.now()

    role1 = Role(
        id=role_id,
        name=name,
        description="管理员",
        is_active=True,
        created_at=now,
        updated_at=now
    )

    role2 = Role(
        id=role_id,
        name=name,
        description="管理员",
        is_active=True,
        created_at=now,
        updated_at=now
    )

    role3 = Role.create(name=RoleName.USER, description="用户")

    assert role1 == role2
    assert role1 != role3


def test_role_name_enum_values():
    """测试角色名称枚举值"""
    assert RoleName.ADMIN.value == "admin"
    assert RoleName.USER.value == "user"
    assert RoleName.GUEST.value == "guest"