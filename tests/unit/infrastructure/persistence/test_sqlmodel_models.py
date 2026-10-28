"""SQLModel 数据模型测试"""
from datetime import datetime
from uuid import uuid4

from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel
from src.infrastructure.persistence.sqlmodel.models.user import UserModel


def test_user_model_creation():
    """测试用户模型创建"""
    user = UserModel(
        id=uuid4(),
        email="user@example.com",
        hashed_password="hashed_value",
        tenant_id=uuid4(),
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert user.email == "user@example.com"
    assert user.is_active is True


def test_tenant_model_creation():
    """测试租户模型创建"""
    tenant = TenantModel(
        id=uuid4(),
        name="测试租户",
        description="测试描述",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert tenant.name == "测试租户"
    assert tenant.description == "测试描述"
    assert tenant.is_active is True


def test_role_model_creation():
    """测试角色模型创建"""
    role = RoleModel(
        id=uuid4(),
        name="admin",
        description="管理员角色",
        is_active=True,
        tenant_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    assert role.name == "admin"
    assert role.description == "管理员角色"
    assert role.is_active is True


def test_permission_model_creation():
    """测试权限模型创建"""
    permission = PermissionModel(
        id=uuid4(),
        action="CREATE",
        resource="user",
        description="创建用户权限",
        created_at=datetime.now(),
    )

    assert permission.action == "CREATE"
    assert permission.resource == "user"


def test_user_model_tablename():
    """测试用户模型表名"""
    assert UserModel.__tablename__ == "users"


def test_tenant_model_tablename():
    """测试租户模型表名"""
    assert TenantModel.__tablename__ == "tenants"


def test_role_model_tablename():
    """测试角色模型表名"""
    assert RoleModel.__tablename__ == "roles"


def test_permission_model_tablename():
    """测试权限模型表名"""
    assert PermissionModel.__tablename__ == "permissions"
