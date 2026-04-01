"""SQLModel 用户仓储测试"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_user_repository import SQLModelUserRepository
from src.infrastructure.persistence.sqlmodel.models.user import UserModel


def test_sqlmodel_user_repository_is_abstract():
    """测试 SQLModelUserRepository 继承自 UserRepository"""
    assert issubclass(SQLModelUserRepository, UserRepository)


@pytest.mark.asyncio
async def test_save_user_with_mock():
    """测试保存用户（使用 Mock）"""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    repository = SQLModelUserRepository(session=mock_session)
    
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
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_find_by_email_returns_none_when_not_found():
    """测试查找不存在的用户返回 None"""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    
    repository = SQLModelUserRepository(session=mock_session)
    
    result = await repository.find_by_email("notfound@example.com", uuid4())
    
    assert result is None