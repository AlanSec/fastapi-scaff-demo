import pytest
from datetime import datetime
from uuid import uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository


def test_in_memory_user_repository_is_abstract():
    """测试 InMemoryUserRepository 继承自 UserRepository"""
    assert issubclass(InMemoryUserRepository, UserRepository)


@pytest.mark.asyncio
async def test_save_and_find_user():
    """测试保存和查找用户"""
    repository = InMemoryUserRepository()
    
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
    
    saved_user = await repository.save(user)
    
    assert saved_user.id == user_id
    assert str(saved_user.email) == "user@example.com"
    
    found_user = await repository.find_by_id(user_id)
    assert found_user is not None
    assert found_user.id == user_id


@pytest.mark.asyncio
async def test_find_by_email():
    """测试通过邮箱查找用户"""
    repository = InMemoryUserRepository()
    
    user_id = uuid4()
    tenant_id = uuid4()
    
    user = User(
        id=user_id,
        email=Email("user@example.com"),
        password=HashedPassword("hashed_value"),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    await repository.save(user)
    
    found_user = await repository.find_by_email("user@example.com", tenant_id)
    assert found_user is not None
    assert str(found_user.email) == "user@example.com"


@pytest.mark.asyncio
async def test_delete_user():
    """测试删除用户"""
    repository = InMemoryUserRepository()
    
    user_id = uuid4()
    tenant_id = uuid4()
    
    user = User(
        id=user_id,
        email=Email("user@example.com"),
        password=HashedPassword("hashed_value"),
        tenant_id=tenant_id,
        is_active=True,
        is_verified=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    await repository.save(user)
    
    deleted = await repository.delete(user_id)
    assert deleted is True
    
    found_user = await repository.find_by_id(user_id)
    assert found_user is None