"""RedisRateLimiter 单元测试——mock redis 客户端，覆盖正常路径与降级路径"""
from unittest.mock import AsyncMock

import pytest
from src.infrastructure.security.redis_rate_limiter import RedisRateLimiter


@pytest.fixture
def redis_client():
    return AsyncMock()


@pytest.fixture
def limiter(redis_client):
    return RedisRateLimiter(redis_client, key_prefix="rl")


@pytest.mark.asyncio
async def test_check_rate_limit_under_limit(limiter, redis_client):
    redis_client.eval = AsyncMock(return_value=1)

    assert await limiter.check_rate_limit("login:user@example.com", 5, 60) is True

    # Lua 脚本 + key 前缀 + 窗口参数
    redis_client.eval.assert_awaited_once()
    call = redis_client.eval.await_args
    assert call.args[1] == 1  # numkeys
    assert call.args[2] == "rl:login:user@example.com"  # 带前缀的 key
    assert call.args[3] == 60  # window seconds


@pytest.mark.asyncio
async def test_check_rate_limit_over_limit(limiter, redis_client):
    redis_client.eval = AsyncMock(return_value=6)

    assert await limiter.check_rate_limit("login:x", 5, 60) is False


@pytest.mark.asyncio
async def test_get_remaining(limiter, redis_client):
    redis_client.get = AsyncMock(return_value=b"3")
    assert await limiter.get_remaining("login:x", 5, 60) == 2

    redis_client.get = AsyncMock(return_value=None)
    assert await limiter.get_remaining("login:x", 5, 60) == 5

    redis_client.get = AsyncMock(return_value=b"9")
    assert await limiter.get_remaining("login:x", 5, 60) == 0


@pytest.mark.asyncio
async def test_reset(limiter, redis_client):
    redis_client.delete = AsyncMock(return_value=1)
    await limiter.reset("login:x")
    redis_client.delete.assert_awaited_once_with("rl:login:x")


@pytest.mark.asyncio
async def test_degrades_to_memory_when_redis_down(limiter, redis_client):
    """Redis 不可用时降级到内存实现，应用不崩溃"""
    redis_client.eval = AsyncMock(side_effect=ConnectionError("no redis"))

    # 首次调用降级：内存计数 1，未超限
    assert await limiter.check_rate_limit("login:x", 2, 60) is True
    # 连续调用：内存计数 2、3，第 3 次超限返回 False
    assert await limiter.check_rate_limit("login:x", 2, 60) is True
    assert await limiter.check_rate_limit("login:x", 2, 60) is False

    # 降级后 get_remaining 也走内存
    redis_client.get = AsyncMock(side_effect=ConnectionError("no redis"))
    assert await limiter.get_remaining("login:x", 2, 60) == 0


@pytest.mark.asyncio
async def test_reset_degrades_to_memory(limiter, redis_client):
    redis_client.delete = AsyncMock(side_effect=ConnectionError("no redis"))
    await limiter.reset("login:x")  # 不应抛异常


@pytest.mark.asyncio
async def test_fail_closed_rejects_when_redis_down():
    """生产模式（fail_closed=True）：Redis 不可用时拒绝放行，不降级内存"""
    redis_client = AsyncMock()
    redis_client.eval = AsyncMock(side_effect=ConnectionError("no redis"))
    redis_client.get = AsyncMock(side_effect=ConnectionError("no redis"))
    limiter = RedisRateLimiter(redis_client, key_prefix="rl", fail_closed=True)

    # check_rate_limit → False（拒绝请求）
    assert await limiter.check_rate_limit("login:x", 5, 60) is False
    # get_remaining → 0（视为锁定）
    assert await limiter.get_remaining("login:x", 5, 60) == 0
    # reset 不抛异常
    await limiter.reset("login:x")


@pytest.mark.asyncio
async def test_fail_closed_still_works_when_redis_up():
    """fail_closed 只影响降级路径，Redis 正常时行为不变"""
    redis_client = AsyncMock()
    redis_client.eval = AsyncMock(return_value=1)
    limiter = RedisRateLimiter(redis_client, key_prefix="rl", fail_closed=True)
    assert await limiter.check_rate_limit("login:x", 5, 60) is True
