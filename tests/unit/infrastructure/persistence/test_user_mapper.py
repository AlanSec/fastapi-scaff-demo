import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.sqlmodel.mappers.user_mapper import UserMapper
from src.infrastructure.persistence.sqlmodel.models.user import UserModel


def test_user_to_model():
    """测试将 User 实体转换为 UserModel"""
    user_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now()
    
    user = User(
        id=user_id,
        email=Email("user@example.com"),
        password=HashedPassword("hashed_value"),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )
    
    model = UserMapper.to_model(user)
    
    assert model.id == user_id
    assert model.email == "user@example.com"
    assert model.hashed_password == "hashed_value"
    assert model.tenant_id == tenant_id
    assert model.is_active is True
    assert model.email_verified is False


def test_model_to_user():
    """测试将 UserModel 转换为 User 实体"""
    user_id = uuid4()
    tenant_id = uuid4()
    now = datetime.now()
    
    model = UserModel(
        id=user_id,
        email="user@example.com",
        username="testuser",
        hashed_password="hashed_value",
        tenant_id=tenant_id,
        is_active=True,
        is_superuser=False,
        created_at=now,
        updated_at=now,
        email_verified=False,
    )
    
    user = UserMapper.to_entity(model)
    
    assert user.id == user_id
    assert str(user.email) == "user@example.com"
    assert user.password.value == "hashed_value"
    assert user.tenant_id == tenant_id
    assert user.is_active is True
    assert user.is_verified is False