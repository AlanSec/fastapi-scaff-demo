"""JWT Provider 测试"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.domain.entities.auth import JWTProvider
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.security.jwt_provider import JWTProviderImpl


def test_jwt_provider_is_implementation():
    """测试 JWTProviderImpl 实现 JWTProvider 接口"""
    assert issubclass(JWTProviderImpl, JWTProvider)


def test_create_access_token():
    """测试创建访问令牌"""
    provider = JWTProviderImpl(secret_key="test-secret-key")
    
    user = User(
        id=uuid4(),
        email=Email("user@example.com"),
        password=HashedPassword("hashed"),
        tenant_id=uuid4(),
        is_active=True,
        is_verified=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    token = provider.create_access_token(user)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """测试创建刷新令牌"""
    provider = JWTProviderImpl(secret_key="test-secret-key")
    
    user = User(
        id=uuid4(),
        email=Email("user@example.com"),
        password=HashedPassword("hashed"),
        tenant_id=uuid4(),
        is_active=True,
        is_verified=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    token = provider.create_refresh_token(user)
    
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token():
    """测试验证令牌"""
    provider = JWTProviderImpl(secret_key="test-secret-key")
    
    user = User(
        id=uuid4(),
        email=Email("user@example.com"),
        password=HashedPassword("hashed"),
        tenant_id=uuid4(),
        is_active=True,
        is_verified=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    token = provider.create_access_token(user)
    payload = provider.verify_token(token)
    
    assert payload is not None
    assert "sub" in payload
    assert payload["sub"] == str(user.id)