"""租户隔离集成测试——双租户场景验证 IDOR 防护、租户级数据可见性、邮箱租户内唯一。"""

import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel
from tests.integration.api.conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    admin_token,
    get_default_tenant_id,
    register_user,
)
from tests.integration.conftest import TestingSessionLocal


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def tenant_b(client):
    """通过平台 API 创建租户 B（admin 为 superuser，tenant:create 放行）"""
    r = client.post(
        "/api/v1/tenants",
        json={"name": "Tenant B", "domain": "b.example.com"},
        headers=_auth(admin_token(client)),
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture
def tenant_b_user(client, tenant_b):
    """租户 B 的用户（开放注册指定租户）"""
    email = "user-b@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123", "tenant_id": tenant_b},
    )
    assert r.status_code == 201, r.text
    return {"id": r.json()["user_id"], "email": email, "tenant_id": tenant_b}


@pytest.fixture
def tenant_b_user_token(client, tenant_b_user):
    r = client.post(
        "/api/v1/auth/login",
        json={
            "email": tenant_b_user["email"],
            "password": "Password123",
            "tenant_id": tenant_b_user["tenant_id"],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def tenant_b_role(db_session, tenant_b):
    """租户 B 的角色（直接插测试库，绕开 API——跨租户创建本身就是被禁止的场景）"""
    role = RoleModel(
        id=uuid4(),
        name="admin-b",
        description="Tenant B role",
        is_active=True,
        tenant_id=UUID(tenant_b),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


# ---------- 匿名访问（P0-3 回归） ----------

def test_anonymous_cannot_read_tenants_roles_permissions(client):
    for path in ("/api/v1/tenants", "/api/v1/roles", "/api/v1/permissions", "/api/v1/user"):
        r = client.get(path)
        assert r.status_code == 401, f"{path} should require auth, got {r.status_code}"


def test_change_password_requires_auth(client):
    """P0-2 回归：未登录不能改任何人的密码"""
    r = client.post("/api/v1/password/change", json={"current_password": "x", "new_password": "y"})
    assert r.status_code == 401


# ---------- 改密只作用于本人 ----------

def test_change_password_only_affects_self(client):
    """改密端点不接受 user_id，只能改自己的密码"""
    tid = get_default_tenant_id(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "tenant_id": tid},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    r = client.post(
        "/api/v1/password/change",
        json={"current_password": ADMIN_PASSWORD, "new_password": "NewAdmin123"},
        headers=_auth(token),
    )
    assert r.status_code == 200, r.text

    # 旧密码失效、新密码可登录
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "tenant_id": tid},
    )
    assert r.status_code == 401
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "NewAdmin123", "tenant_id": tid},
    )
    assert r.status_code == 200


# ---------- 角色：租户内可见 + 跨租户 404 ----------

def test_role_read_cross_tenant_returns_404(client, tenant_b_role):
    """租户 B 的角色对 Default Tenant 用户不可见（404，防枚举）"""
    tid = get_default_tenant_id(client)
    register_user(client, "role-reader@example.com")
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "role-reader@example.com", "password": "Password123", "tenant_id": tid},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    r = client.get(f"/api/v1/roles/{tenant_b_role.id}", headers=_auth(token))
    assert r.status_code == 404


def test_role_write_cross_tenant_returns_404(client, tenant_b_role):
    """跨租户更新/删除角色 → 404（即使调用者是 superuser，也不豁免租户隔离）"""
    ah = _auth(admin_token(client))
    r = client.put(
        f"/api/v1/roles/{tenant_b_role.id}",
        json={"description": "hacked"},
        headers=ah,
    )
    assert r.status_code == 404
    r = client.delete(f"/api/v1/roles/{tenant_b_role.id}", headers=ah)
    assert r.status_code == 404


def test_role_list_only_returns_own_tenant(client, tenant_b, tenant_b_role):
    """GET /roles 只返回本租户角色（不含租户 B）"""
    ah = _auth(admin_token(client))
    r = client.get("/api/v1/roles", headers=ah)
    assert r.status_code == 200
    role_ids = [item["id"] for item in r.json()["items"]]
    assert tenant_b_role.id not in role_ids


def test_role_create_rejects_tenant_id_in_body(client):
    """角色创建不再接受 tenant_id（租户取自认证上下文）"""
    ah = _auth(admin_token(client))
    r = client.post(
        "/api/v1/roles/",
        json={"name": "x", "description": "x", "tenant_id": str(uuid4())},
        headers=ah,
    )
    assert r.status_code == 422


def test_created_role_belongs_to_caller_tenant(client):
    """创建的角色必须归属调用者租户（而非请求体）"""
    ah = _auth(admin_token(client))
    r = client.post("/api/v1/roles/", json={"name": "own-role", "description": "x"}, headers=ah)
    assert r.status_code == 201, r.text
    assert r.json()["tenant_id"] == get_default_tenant_id(client)


# ---------- 用户管理：租户内可见 + 跨租户 404 ----------

def test_user_admin_scoped_to_tenant(client, tenant_b, tenant_b_user):
    ah = _auth(admin_token(client))

    # 列表只含本租户用户
    r = client.get("/api/v1/user/", headers=ah)
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()["items"]]
    assert tenant_b_user["email"] not in emails

    # 跨租户按 ID 访问 → 404
    r = client.get(f"/api/v1/user/{tenant_b_user['id']}", headers=ah)
    assert r.status_code == 404
    r = client.delete(f"/api/v1/user/{tenant_b_user['id']}", headers=ah)
    assert r.status_code == 404

    # 创建用户不接受 tenant_id
    r = client.post(
        "/api/v1/user/",
        json={"email": "x@example.com", "password": "Password123", "tenant_id": tenant_b},
        headers=ah,
    )
    assert r.status_code == 422


# ---------- 关联操作：跨租户拒绝 ----------

def test_cross_tenant_role_assignment_rejected(client, tenant_b, tenant_b_user, tenant_b_role):
    """把租户 B 的角色分配给 Default Tenant 用户 → 404（Role not found，跨租户不泄露存在性）"""
    user_id = register_user(client, "assign-target@example.com")
    ah = _auth(admin_token(client))

    # 防御性校验：目标用户确实在 Default Tenant
    r = client.get(f"/api/v1/user/{user_id}", headers=ah)
    assert r.status_code == 200

    r = client.post(f"/api/v1/roles/{tenant_b_role.id}/users/{user_id}", headers=ah)
    assert r.status_code == 404, r.text


# ---------- 邮箱：租户内唯一 ----------

def test_same_email_registers_in_multiple_tenants(client, tenant_b):
    tid_a = get_default_tenant_id(client)
    email = "shared@example.com"

    # 同一邮箱注册到两个租户均成功
    for tid in (tid_a, tenant_b):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Password123", "tenant_id": tid},
        )
        assert r.status_code == 201, r.text

    # 各自租户内可独立登录
    for tid in (tid_a, tenant_b):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123", "tenant_id": tid},
        )
        assert r.status_code == 200, r.text

    # 同一租户内重复注册被拒绝（409 冲突）
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123", "tenant_id": tid_a},
    )
    assert r.status_code == 409


# ---------- 租户停用后禁止登录 ----------

async def _set_tenant_active(tenant_id: str, active: bool) -> None:
    async with TestingSessionLocal() as session:
        model = await session.get(TenantModel, UUID(tenant_id))
        assert model is not None
        model.is_active = active
        await session.commit()


def test_login_rejected_for_inactive_tenant(client, tenant_b_user):
    asyncio.run(_set_tenant_active(tenant_b_user["tenant_id"], False))
    try:
        r = client.post(
            "/api/v1/auth/login",
            json={
                "email": tenant_b_user["email"],
                "password": "Password123",
                "tenant_id": tenant_b_user["tenant_id"],
            },
        )
        assert r.status_code == 401
    finally:
        asyncio.run(_set_tenant_active(tenant_b_user["tenant_id"], True))
