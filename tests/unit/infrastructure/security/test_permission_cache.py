"""PermissionCache 单元测试——TTL、失效与容量上限"""
from src.infrastructure.security.permission_cache import PermissionCache


def test_set_and_get():
    cache = PermissionCache(ttl_seconds=60)
    cache.set("u1", {"tenant:create", "user:read"})
    assert cache.get("u1") == {"tenant:create", "user:read"}


def test_miss_returns_none():
    cache = PermissionCache()
    assert cache.get("nobody") is None


def test_expiry():
    cache = PermissionCache(ttl_seconds=0)
    cache.set("u1", {"tenant:create"})
    # ttl=0 立即过期
    assert cache.get("u1") is None


def test_invalidate():
    cache = PermissionCache()
    cache.set("u1", {"tenant:create"})
    cache.invalidate("u1")
    assert cache.get("u1") is None
    # 其他键不受影响
    cache.set("u2", {"user:read"})
    cache.invalidate("u1")
    assert cache.get("u2") == {"user:read"}


def test_clear():
    cache = PermissionCache()
    cache.set("u1", {"a:b"})
    cache.set("u2", {"c:d"})
    cache.clear()
    assert cache.get("u1") is None
    assert cache.get("u2") is None


def test_max_entries_triggers_full_clear():
    """超过容量上限时整体清空（防随机 user_id 撑爆内存）"""
    cache = PermissionCache(max_entries=2)
    cache.set("u1", {"a:b"})
    cache.set("u2", {"c:d"})
    # 第 3 个键触发清空
    cache.set("u3", {"e:f"})
    assert cache.get("u1") is None
    assert cache.get("u2") is None
    assert cache.get("u3") == {"e:f"}


def test_set_overwrites_and_refreshes():
    cache = PermissionCache(ttl_seconds=60)
    cache.set("u1", {"a:b"})
    cache.set("u1", {"c:d"})
    assert cache.get("u1") == {"c:d"}
