"""RBAC + 刷新令牌冒烟测试脚本"""
import asyncio
import os
import sys

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./smoke_test.db"
os.environ["ADMIN_PASSWORD"] = "Admin123456"
os.environ["MAX_LOGIN_ATTEMPTS"] = "100"
os.environ.pop("SECRET_KEY", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 每次从干净的数据库开始
for f in ("smoke_test.db",):
    if os.path.exists(f):
        os.remove(f)

from fastapi.testclient import TestClient  # noqa: E402 - 需先设置环境变量
from src.bootstrap.container import get_container  # noqa: E402
from src.bootstrap.lifespan import create_app  # noqa: E402


def _default_tenant_id() -> str:
    """从仓储直查默认租户（API 的 GET /tenants 已改为 superuser-only，不做匿名依赖）"""
    tenant = asyncio.run(get_container().tenant_repository.find_by_name("Default Tenant"))
    assert tenant is not None, "Default Tenant not found"
    return str(tenant.id)


def main():
    with TestClient(create_app()) as client:
        # 必须在 lifespan 建表 + ensure_admin 之后取租户（且不能匿名调 API）
        tenant_id = _default_tenant_id()

        # 注册普通用户 + admin 登录
        r = client.post("/api/v1/auth/register", json={
            "email": "smoke2@example.com", "password": "Password123", "tenant_id": tenant_id})
        assert r.status_code == 201, r.text
        r = client.post("/api/v1/auth/login", json={
            "email": "admin@example.com", "password": "Admin123456", "tenant_id": tenant_id})
        assert r.status_code == 200, r.text
        admin_token = r.json()["access_token"]
        ah = {"Authorization": f"Bearer {admin_token}"}
        print("1) 注册普通用户 + admin 登录 OK")

        # admin(superuser 绕过权限检查) 搭建 RBAC
        r = client.post("/api/v1/permissions/", json={
            "action": "create", "resource": "tenant", "description": "Create tenant"}, headers=ah)
        assert r.status_code == 201, r.text
        perm_id = r.json()["id"]
        # 角色所属租户由认证上下文决定（不再接受 tenant_id 字段）
        r = client.post("/api/v1/roles/", json={
            "name": "user", "description": "Can create tenants"}, headers=ah)
        assert r.status_code == 201, r.text
        role_id = r.json()["id"]
        assert r.json()["tenant_id"] == tenant_id
        r = client.post(f"/api/v1/permissions/{perm_id}/roles/{role_id}", headers=ah)
        assert r.status_code == 200, r.text
        print("2) admin 创建权限/角色并完成 角色->权限 分配 OK")

        # 无权限用户先验证 403
        r = client.post("/api/v1/auth/login", json={
            "email": "smoke2@example.com", "password": "Password123", "tenant_id": tenant_id})
        user_token = r.json()["access_token"]
        uh = {"Authorization": f"Bearer {user_token}"}
        r = client.post("/api/v1/tenants", json={
            "name": "Acme", "domain": "acme.example.com"}, headers=uh)
        assert r.status_code == 403, (r.status_code, r.text)
        print("3) 分配前无权限创建租户 403 OK")

        # 分配角色给用户
        r = client.get("/api/v1/user/", headers=ah)
        user_id = next(u["id"] for u in r.json()["items"] if u["email"] == "smoke2@example.com")
        r = client.post(f"/api/v1/roles/{role_id}/users/{user_id}", headers=ah)
        assert r.status_code == 200, r.text
        print("4) admin 将角色分配给用户 OK")

        # 分配后普通用户可创建租户
        r = client.post("/api/v1/tenants", json={
            "name": "Acme", "domain": "acme.example.com"}, headers=uh)
        assert r.status_code == 201, r.text
        print("5) 获得 tenant:create 权限后创建租户成功(201) OK")

        # 刷新令牌链路
        r = client.post("/api/v1/auth/login", json={
            "email": "smoke2@example.com", "password": "Password123", "tenant_id": tenant_id})
        refresh_token = r.json()["refresh_token"]
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 200, r.text
        new_refresh = r.json()["refresh_token"]
        assert new_refresh != refresh_token
        print("6) /auth/refresh 轮换令牌 OK")

        # 旧 refresh token 已被吊销，再次使用返回 401
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 401, (r.status_code, r.text)
        print("7) 旧 refresh token 被吊销后不可复用(401) OK")

        r = client.post("/api/v1/auth/refresh", json={"refresh_token": user_token})
        assert r.status_code == 401, (r.status_code, r.text)
        print("8) access token 用于刷新被拒绝(401) OK")

        r = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {refresh_token}"})
        assert r.status_code == 401, (r.status_code, r.text)
        print("9) refresh token 访问 /user/me 被拒绝(401) OK")

        # 自定义角色名（不再受 RoleName 枚举限制）
        r = client.post("/api/v1/roles/", json={
            "name": "tenant-manager", "description": "Custom role name"}, headers=ah)
        assert r.status_code == 201, r.text
        print("10) 自定义角色名创建成功 OK")

    print("SMOKE TEST ALL PASSED")


if __name__ == "__main__":
    main()
