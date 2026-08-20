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
        is_superuser=True,
        reset_token="reset_token_1",
        reset_token_expires_at=now,
        verification_token="verify_token_1",
    )

    model = UserMapper.to_model(user)

    assert model.id == user_id
    assert model.email == "user@example.com"
    assert model.hashed_password == "hashed_value"
    assert model.tenant_id == tenant_id
    assert model.is_active is True
    assert model.email_verified is False
    assert model.is_superuser is True
    assert model.reset_token == "reset_token_1"
    assert model.reset_token_expires == now
    assert model.verification_token == "verify_token_1"
    assert model.last_login_at == user.last_login_at


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
        is_superuser=True,
        created_at=now,
        updated_at=now,
        email_verified=False,
        reset_token="reset_token_1",
        reset_token_expires=now,
        verification_token="verify_token_1",
        last_login_at=now,
    )

    user = UserMapper.to_entity(model)

    assert user.id == user_id
    assert str(user.email) == "user@example.com"
    assert user.password.value == "hashed_value"
    assert user.tenant_id == tenant_id
    assert user.is_active is True
    assert user.is_verified is False
    assert user.is_superuser is True
    assert user.reset_token == "reset_token_1"
    assert user.reset_token_expires_at == now
    assert user.verification_token == "verify_token_1"
    assert user.last_login_at == now
