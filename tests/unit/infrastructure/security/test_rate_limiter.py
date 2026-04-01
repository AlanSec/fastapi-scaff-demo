"""RateLimiter 测试"""
import pytest
import asyncio

from src.infrastructure.security.rate_limiter import RateLimiter, InMemoryRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """测试在限制范围内允许请求"""
    limiter = InMemoryRateLimiter()
    
    result = await limiter.check_rate_limit("test-key", limit=5, window_seconds=60)
    
    assert result is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_when_exceeded():
    """测试超过限制时阻止请求"""
    limiter = InMemoryRateLimiter()
    
    for _ in range(5):
        await limiter.check_rate_limit("test-key", limit=5, window_seconds=60)
    
    result = await limiter.check_rate_limit("test-key", limit=5, window_seconds=60)
    
    assert result is False


@pytest.mark.asyncio
async def test_rate_limiter_get_remaining():
    """测试获取剩余次数"""
    limiter = InMemoryRateLimiter()
    
    await limiter.check_rate_limit("test-key", limit=5, window_seconds=60)
    
    remaining = await limiter.get_remaining("test-key", limit=5, window_seconds=60)
    
    assert remaining == 4


@pytest.mark.asyncio
async def test_rate_limiter_reset():
    """测试重置限制"""
    limiter = InMemoryRateLimiter()
    
    for _ in range(5):
        await limiter.check_rate_limit("test-key", limit=5, window_seconds=60)
    
    await limiter.reset("test-key")
    
    remaining = await limiter.get_remaining("test-key", limit=5, window_seconds=60)
    
    assert remaining == 5