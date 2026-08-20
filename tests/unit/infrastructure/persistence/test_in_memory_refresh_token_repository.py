"""内存刷新令牌仓储测试"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from src.infrastructure.persistence.in_memory.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)


@pytest.fixture
def repo():
    return InMemoryRefreshTokenRepository()


@pytest.mark.asyncio
async def test_save_find_revoke_roundtrip(repo):
    jti = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await repo.save(jti, uuid4(), expires_at)

    record = await repo.find_by_token(jti)
    assert record is not None and record.is_revoked is False

    assert await repo.revoke(jti) is True
    assert (await repo.find_by_token(jti)).is_revoked is True

    assert await repo.revoke(str(uuid4())) is False


@pytest.mark.asyncio
async def test_delete_expired_removes_only_expired(repo):
    now = datetime.now(timezone.utc)
    expired_jti = str(uuid4())
    fresh_jti = str(uuid4())

    await repo.save(expired_jti, uuid4(), now - timedelta(days=1))
    await repo.save(fresh_jti, uuid4(), now + timedelta(days=7))

    deleted = await repo.delete_expired(now)
    assert deleted == 1

    assert await repo.find_by_token(expired_jti) is None
    assert await repo.find_by_token(fresh_jti) is not None
