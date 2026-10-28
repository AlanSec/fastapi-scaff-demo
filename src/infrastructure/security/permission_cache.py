"""用户权限集合的内存 TTL 缓存（进程内）。

背景：`require_permissions` 每次请求需要用户的角色 → 权限集合，
不经缓存时每请求 4~5 次 DB 往返。本缓存把结果缓存 TTL 秒。

- 键：user_id；值：(expires_at, permissions)
- 默认 TTL 60 秒：权限变更后最多 TTL 延迟生效
- 关联变更（分配角色/权限）时调用方主动 clear()/invalidate()，立即生效
- 多 worker 部署下每进程独立缓存（可接受：权限变更延迟 <= TTL）
- 容量上限：超过 max_entries 时整体清空（防随机 user_id 撑爆内存）
"""
import time
from threading import Lock


class PermissionCache:

    def __init__(self, ttl_seconds: int = 60, max_entries: int = 10_000):
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._entries: dict[str, tuple[float, set[str]]] = {}
        self._lock = Lock()

    def get(self, user_id: str) -> set[str] | None:
        """返回缓存的权限集合；未命中或已过期返回 None。"""
        with self._lock:
            item = self._entries.get(user_id)
            if item is None:
                return None
            expires_at, permissions = item
            if time.monotonic() > expires_at:
                self._entries.pop(user_id, None)
                return None
            return permissions

    def set(self, user_id: str, permissions: set[str]) -> None:
        with self._lock:
            if len(self._entries) >= self._max_entries:
                self._entries.clear()
            self._entries[user_id] = (time.monotonic() + self._ttl, permissions)

    def invalidate(self, user_id: str) -> None:
        with self._lock:
            self._entries.pop(user_id, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
