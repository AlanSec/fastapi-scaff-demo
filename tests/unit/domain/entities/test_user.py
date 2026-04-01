import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


def test_user_creation():
    user_id = uuid4()
    tenant_id = uuid4()
    email = Email("user@example.com")
    password = HashedPassword("hashed_password")
    created_at = datetime.now()
    
    user = User(
        id=user_id,
        email=email,
        password=password,
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=created_at,
        updated_at=created_at
    )
    
    assert user.id == user_id
    assert user.email == email
    assert user.password == password
    assert user.tenant_id == tenant_id
    assert user.is_active is True
    assert user.is_verified is False
    assert user.created_at == created_at
    assert user.updated_at == created_at
    assert user.last_login_at is None


def test_user_create_factory_method():
    email = Email("new@example.com")
    password = HashedPassword("hashed_password")
    tenant_id = uuid4()
    
    user = User.create(
        email=email,
        password=password,
        tenant_id=tenant_id
    )
    
    assert isinstance(user.id, UUID)
    assert user.email == email
    assert user.password == password
    assert user.tenant_id == tenant_id
    assert user.is_active is True
    assert user.is_verified is False
    assert user.last_login_at is None


def test_user_verify():
    user = User.create(
        email=Email("user@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4()
    )
    
    verified_user = user.verify()
    
    assert verified_user.is_verified is True
    assert verified_user.id == user.id
    assert verified_user.email == user.email
    assert user.is_verified is False


def test_user_update_last_login():
    user = User.create(
        email=Email("user@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4()
    )
    
    updated_user = user.update_last_login()
    
    assert updated_user.last_login_at is not None
    assert user.last_login_at is None


def test_user_deactivate():
    user = User.create(
        email=Email("user@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4()
    )
    
    deactivated_user = user.deactivate()
    
    assert deactivated_user.is_active is False
    assert user.is_active is True


def test_user_activate():
    user = User.create(
        email=Email("user@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4()
    )
    deactivated = user.deactivate()
    
    activated = deactivated.activate()
    
    assert activated.is_active is True
    assert deactivated.is_active is False


def test_user_immutability():
    user = User.create(
        email=Email("user@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4()
    )
    
    with pytest.raises(AttributeError):
        user.is_active = False
    
    with pytest.raises(AttributeError):
        user.email = Email("new@example.com")


def test_user_equality():
    user_id = uuid4()
    email = Email("user@example.com")
    password = HashedPassword("hashed_password")
    tenant_id = uuid4()
    now = datetime.now()
    
    user1 = User(
        id=user_id,
        email=email,
        password=password,
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now
    )
    
    user2 = User(
        id=user_id,
        email=email,
        password=password,
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now
    )
    
    user3 = User.create(
        email=Email("other@example.com"),
        password=password,
        tenant_id=tenant_id
    )
    
    assert user1 == user2
    assert user1 != user3