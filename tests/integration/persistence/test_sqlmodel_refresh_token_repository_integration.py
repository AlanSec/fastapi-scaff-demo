"""SQLModel 刷新令牌仓储集成测试——验证 jti 持久化与吊销"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from src.infrastructure.persistence.sqlmodel.models.refresh_token import RefreshTokenModel
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_refresh_token_repository import (
    SQLModelRefreshTokenRepository,
)
from tests.integration.conftest import TestingSessionLocal


@pytest.fixture
def repo():
    return SQLModelRefreshTokenRepository(TestingSessionLocal)


@pytest.mark.asyncio
async def test_save_find_and_revoke_roundtrip(default_tenant, repo):
    jti = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await repo.save(jti, default_tenant.id, expires_at)

    record = await repo.find_by_token(jti)
    assert record is not None
    assert record.jti == jti
    assert record.user_id == default_tenant.id
    assert record.is_revoked is False

    assert await repo.revoke(jti) is True
    revoked = await repo.find_by_token(jti)
    assert revoked is not None and revoked.is_revoked is True


@pytest.mark.asyncio
async def test_revoke_missing_token_returns_false(repo):
    assert await repo.revoke(str(uuid4())) is False


@pytest.mark.asyncio
async def test_find_missing_token_returns_none(repo):
    assert await repo.find_by_token(str(uuid4())) is None


@pytest.mark.asyncio
async def test_delete_expired_removes_only_expired(default_tenant, repo):
    now = datetime.now(timezone.utc)
    # 直接插入，绕过 save() 的自动清理
    async with TestingSessionLocal() as session:
        session.add(RefreshTokenModel(
            token="expired-jti", user_id=default_tenant.id,
            expires_at=now - timedelta(days=1),
        ))
        session.add(RefreshTokenModel(
            token="fresh-jti", user_id=default_tenant.id,
            expires_at=now + timedelta(days=7),
        ))
        await session.commit()

    deleted = await repo.delete_expired(now)
    assert deleted == 1

    assert await repo.find_by_token("expired-jti") is None
    assert await repo.find_by_token("fresh-jti") is not None


@pytest.mark.asyncio
async def test_save_does_not_purge_expired_records(default_tenant, repo):
    """save() 不再顺带清理过期记录（清理已移出热路径，由 delete_expired 后台任务负责）"""
    now = datetime.now(timezone.utc)
    expired_jti = str(uuid4())
    await repo.save(expired_jti, default_tenant.id, now - timedelta(days=1))

    await repo.save(str(uuid4()), default_tenant.id, now + timedelta(days=7))

    # save 不清理：过期记录仍在
    assert await repo.find_by_token(expired_jti) is not None

    # 显式调用 delete_expired 才清理
    deleted = await repo.delete_expired(now)
    assert deleted == 1
    assert await repo.find_by_token(expired_jti) is None
