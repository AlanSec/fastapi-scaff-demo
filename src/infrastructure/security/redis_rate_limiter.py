"""Redis 限流器实现。

- 固定窗口计数：Lua 脚本原子执行 INCR + 首次 EXPIRE（兼容 Redis < 7 的无 NX 服务端）
- Redis 不可用时：
  - 开发环境（fail_closed=False）：自动降级为内存实现并告警（应用不因限流器崩溃）
  - 生产环境（fail_closed=True）：拒绝放行（宁可拒绝服务，不可放开闸门——
    否则攻击者可通过打挂 Redis 来绕过限流）
"""
import logging

from src.domain.services.security_interfaces import RateLimiter
from src.infrastructure.security.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)

_INCR_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class RedisRateLimiter(RateLimiter):
    """基于 redis.asyncio 的限流器，key 前缀隔离命名空间"""

    def __init__(
        self,
        redis_client,
        key_prefix: str = "rate_limit",
        fail_closed: bool = False,
    ):
        self._redis = redis_client
        self._prefix = key_prefix
        self._fallback = InMemoryRateLimiter()
        self._degraded = False
        self._fail_closed = fail_closed

    @classmethod
    def from_url(
        cls, url: str, key_prefix: str = "rate_limit", fail_closed: bool = False
    ) -> "RedisRateLimiter":
        import redis.asyncio as aioredis

        client = aioredis.from_url(
            url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        return cls(client, key_prefix=key_prefix, fail_closed=fail_closed)

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            count = await self._redis.eval(
                _INCR_SCRIPT, 1, self._key(key), window_seconds
            )
            return count <= limit
        except Exception as e:  # noqa: BLE001 - 限流器不应让请求失败
            if self._fail_closed:
                logger.error(
                    "Rate limiter unavailable in fail-closed mode (%s: %s), refusing request",
                    type(e).__name__,
                    e,
                )
                return False
            self._degrade(e)
            return await self._fallback.check_rate_limit(key, limit, window_seconds)

    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        try:
            raw = await self._redis.get(self._key(key))
            count = int(raw) if raw else 0
            return max(0, limit - count)
        except Exception as e:  # noqa: BLE001
            if self._fail_closed:
                logger.error(
                    "Rate limiter unavailable in fail-closed mode (%s: %s), treating as locked",
                    type(e).__name__,
                    e,
                )
                return 0
            self._degrade(e)
            return await self._fallback.get_remaining(key, limit, window_seconds)

    async def reset(self, key: str) -> None:
        try:
            await self._redis.delete(self._key(key))
        except Exception as e:  # noqa: BLE001
            if self._fail_closed:
                logger.error(
                    "Rate limiter unavailable in fail-closed mode (%s: %s)",
                    type(e).__name__,
                    e,
                )
                return
            self._degrade(e)
            await self._fallback.reset(key)

    def _degrade(self, error: Exception) -> None:
        if not self._degraded:
            self._degraded = True
            logger.warning(
                "Redis unavailable (%s: %s), rate limiter degraded to in-memory",
                type(error).__name__,
                error,
            )
