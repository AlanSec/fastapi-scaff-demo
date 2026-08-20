"""刷新令牌 UseCase 测试——含服务端吊销"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from src.application.dto.auth_dto import RefreshTokenInputDTO
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.in_memory.in_memory_refresh_token_repository import (
    InMemoryRefreshTokenRepository,
)
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.security.jwt_provider import JWTProviderImpl


@pytest.fixture
def jwt_provider():
    return JWTProviderImpl(
        secret_key="test-secret",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
    )


@pytest.fixture
def repo():
    return InMemoryUserRepository()


@pytest.fixture
def refresh_repo():
    return InMemoryRefreshTokenRepository()


def _make_user(repo: InMemoryUserRepository) -> User:
    user = User.create(
        email=Email("test@example.com"),
        password=HashedPassword("hashed"),
        tenant_id=uuid4(),
    )
    return user


async def _register_refresh_token(refresh_repo, jwt_provider, user) -> str:
    """创建 refresh token 并登记到服务端"""
    token = jwt_provider.create_refresh_token(user)
    payload = jwt_provider.verify_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=jwt_provider.get_refresh_token_expire_seconds()
    )
    await refresh_repo.save(payload["jti"], user.id, expires_at)
    return token


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens_and_rotates(repo, jwt_provider, refresh_repo):
    user = _make_user(repo)
    await repo.save(user)

    old_token = await _register_refresh_token(refresh_repo, jwt_provider, user)
    old_jti = jwt_provider.verify_token(old_token)["jti"]

    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)
    result = await use_case.execute(RefreshTokenInputDTO(refresh_token=old_token))

    assert result.user_id == user.id
    assert result.access_token != old_token
    assert result.refresh_token != old_token
    assert result.expires_in == 1800

    # 旧令牌已吊销，新令牌已登记
    old_record = await refresh_repo.find_by_token(old_jti)
    assert old_record is not None and old_record.is_revoked is True
    new_jti = jwt_provider.verify_token(result.refresh_token)["jti"]
    new_record = await refresh_repo.find_by_token(new_jti)
    assert new_record is not None and new_record.is_revoked is False


@pytest.mark.asyncio
async def test_old_refresh_token_cannot_be_reused(repo, jwt_provider, refresh_repo):
    """轮换后旧 refresh token 再次使用必须被拒绝"""
    user = _make_user(repo)
    await repo.save(user)

    old_token = await _register_refresh_token(refresh_repo, jwt_provider, user)
    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)

    # 第一次刷新成功
    result = await use_case.execute(RefreshTokenInputDTO(refresh_token=old_token))
    assert result.refresh_token != old_token

    # 旧令牌第二次使用被拒绝（已吊销）
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token=old_token))


@pytest.mark.asyncio
async def test_refresh_rejects_unregistered_token(repo, jwt_provider, refresh_repo):
    """有效签名但从未登记（如伪造/来自其他服务）的令牌被拒绝"""
    user = _make_user(repo)
    await repo.save(user)

    unregistered = jwt_provider.create_refresh_token(user)
    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token=unregistered))


@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token(repo, jwt_provider, refresh_repo):
    user = _make_user(repo)
    await repo.save(user)

    token = await _register_refresh_token(refresh_repo, jwt_provider, user)
    jti = jwt_provider.verify_token(token)["jti"]
    await refresh_repo.revoke(jti)

    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token=token))


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(repo, jwt_provider, refresh_repo):
    """access token 不能用于刷新"""
    user = _make_user(repo)
    await repo.save(user)

    access_token = jwt_provider.create_access_token(user)
    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)

    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token=access_token))


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_token(repo, jwt_provider, refresh_repo):
    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token="bogus.token.here"))


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_user(repo, jwt_provider, refresh_repo):
    """令牌已登记但用户已删除时拒绝刷新"""
    user = _make_user(repo)
    token = await _register_refresh_token(refresh_repo, jwt_provider, user)

    use_case = RefreshTokenUseCase(repo, jwt_provider, refresh_repo)
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await use_case.execute(RefreshTokenInputDTO(refresh_token=token))
