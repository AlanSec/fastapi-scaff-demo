"""SQLModel 用户仓储集成测试——使用 SQLite 内存库验证实体↔模型往返。"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_user_repository import SQLModelUserRepository
from tests.integration.conftest import TestingSessionLocal


def _make_user(tenant_id, email: str = "test@example.com") -> User:
    return User.create(
        email=Email(email),
        password=HashedPassword("hashed:Password123"),
        tenant_id=tenant_id,
    )


@pytest.fixture
def repo():
    return SQLModelUserRepository(TestingSessionLocal)


@pytest.mark.asyncio
async def test_save_and_find_by_reset_token_roundtrip(default_tenant, repo):
    user = _make_user(default_tenant.id)
    expires_at = datetime.now() + timedelta(minutes=30)
    user = user.with_reset_token("reset_token_abc", expires_at)

    saved = await repo.save(user)

    found = await repo.find_by_reset_token("reset_token_abc")
    assert found is not None
    assert found.id == saved.id
    assert found.reset_token == "reset_token_abc"
    assert found.reset_token_expires_at is not None


@pytest.mark.asyncio
async def test_save_and_find_by_verification_token_roundtrip(default_tenant, repo):
    user = _make_user(default_tenant.id).with_verification_token("verify_token_xyz")

    saved = await repo.save(user)

    found = await repo.find_by_verification_token("verify_token_xyz")
    assert found is not None
    assert found.id == saved.id
    assert found.verification_token == "verify_token_xyz"
    assert found.is_verified is False


@pytest.mark.asyncio
async def test_save_preserves_superuser_and_maps_all_fields(default_tenant, repo):
    user = User(
        id=uuid4(),
        email=Email("admin@example.com"),
        password=HashedPassword("hashed:Password123"),
        tenant_id=default_tenant.id,
        is_active=True,
        is_verified=True,
        is_superuser=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        last_login_at=datetime.now(),
    )

    await repo.save(user)
    found = await repo.find_by_id(user.id)

    assert found is not None
    assert found.is_superuser is True
    assert found.is_verified is True
    assert found.last_login_at is not None


@pytest.mark.asyncio
async def test_clear_token_persists(default_tenant, repo):
    user = _make_user(default_tenant.id).with_reset_token("reset_token_1", datetime.now() + timedelta(minutes=30))
    await repo.save(user)

    cleared = user.clear_reset_token()
    await repo.save(cleared)

    assert await repo.find_by_reset_token("reset_token_1") is None
