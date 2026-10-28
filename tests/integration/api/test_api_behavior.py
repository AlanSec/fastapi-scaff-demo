"""API 层集成测试——覆盖路由行为（错误格式、鉴权、限流、级联删除、刷新吊销）。"""

from tests.integration.api.conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    admin_token,
    get_default_tenant_id,
    register_user,
)

# ---------- 健康检查与错误格式 ----------

def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_validation_error_has_code_field(client):
    r = client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body and body["code"] == 422


def test_login_failure_has_code_field(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": "WrongPass1", "tenant_id": get_default_tenant_id(client)},
    )
    assert r.status_code == 401
    assert r.json()["code"] == 401


def test_not_found_has_code_field(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    assert r.json()["code"] == 404


# ---------- 鉴权 ----------

def test_user_me_requires_auth(client):
    r = client.get("/api/v1/user/me")
    assert r.status_code == 401


def test_user_me_with_valid_token(client):
    token = admin_token(client)
    r = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == ADMIN_EMAIL


def test_forbidden_without_permission(client):
    """普通用户无 tenant:create 权限，创建租户应 403"""
    register_user(client, "noperm@example.com")
    tid = get_default_tenant_id(client)

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "noperm@example.com", "password": "Password123", "tenant_id": tid},
    )
    assert r.status_code == 200, r.text
    uh = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/api/v1/tenants", json={"name": "X", "domain": "x.com"}, headers=uh)
    assert r.status_code == 403
    assert "Missing permissions" in r.json()["detail"]


# ---------- 限流 ----------

def test_login_rate_limit_returns_429(client):
    tid = get_default_tenant_id(client)
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "attacker@example.com", "password": "Wrong123", "tenant_id": tid},
        )
        assert r.status_code == 401

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "attacker@example.com", "password": "Wrong123", "tenant_id": tid},
    )
    assert r.status_code == 429
    assert r.json()["code"] == 429


def test_register_rate_limited_by_ip(client):
    """开放注册防滥用：单 IP 每小时 10 次后返回 429"""
    tid = get_default_tenant_id(client)
    for i in range(10):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": f"rl-{i}@example.com", "password": "Password123", "tenant_id": tid},
        )
        assert r.status_code == 201, r.text

    r = client.post(
        "/api/v1/auth/register",
        json={"email": "rl-over@example.com", "password": "Password123", "tenant_id": tid},
    )
    assert r.status_code == 429


def test_forgot_password_rate_limited_by_ip(client):
    """忘记密码防邮件轰炸：单 IP 每小时 5 次后返回 429"""
    for _ in range(5):
        r = client.post("/api/v1/password/forgot", json={"email": "nobody@example.com"})
        assert r.status_code == 200, r.text

    r = client.post("/api/v1/password/forgot", json={"email": "nobody@example.com"})
    assert r.status_code == 429


# ---------- 级联删除 ----------

def test_delete_user_cascades(client):
    """删除用户后其 refresh token 失效，无法再登录"""
    email = "delete-me@example.com"
    user_id = register_user(client, email)
    tid = get_default_tenant_id(client)

    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123", "tenant_id": tid})
    assert r.status_code == 200
    token = r.json()["access_token"]

    ah = {"Authorization": f"Bearer {admin_token(client)}"}
    r = client.delete(f"/api/v1/user/{user_id}", headers=ah)
    assert r.status_code == 204

    # 被删用户无法再登录，旧 access token 也失效（用户不存在）
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123", "tenant_id": tid})
    assert r.status_code == 401
    r = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_delete_tenant_cascades(client):
    ah = {"Authorization": f"Bearer {admin_token(client)}"}

    r = client.post("/api/v1/tenants", json={"name": "Doomed", "domain": "doomed.example.com"}, headers=ah)
    assert r.status_code == 201
    new_tid = r.json()["id"]

    r = client.delete(f"/api/v1/tenants/{new_tid}", headers=ah)
    assert r.status_code == 204

    r = client.get(f"/api/v1/tenants/{new_tid}", headers=ah)
    assert r.status_code == 404


def test_delete_role_cascades(client):
    ah = {"Authorization": f"Bearer {admin_token(client)}"}
    tid = get_default_tenant_id(client)

    # 角色创建不再接受 tenant_id（租户取自认证上下文）
    r = client.post("/api/v1/roles/", json={"name": "doomed-role", "description": "x"}, headers=ah)
    assert r.status_code == 201
    role_id = r.json()["id"]
    assert r.json()["tenant_id"] == tid

    r = client.delete(f"/api/v1/roles/{role_id}", headers=ah)
    assert r.status_code == 204

    r = client.get(f"/api/v1/roles/{role_id}", headers=ah)
    assert r.status_code == 404


# ---------- OAuth2 表单令牌端点 ----------

def test_oauth2_token_endpoint(client):
    """OAuth2 密码模式表单登录（修复 Swagger Authorize）"""
    r = client.post(
        "/api/v1/auth/token",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    # 返回的 token 可用于受保护接口
    r = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert r.status_code == 200


def test_oauth2_token_rejects_bad_credentials(client):
    r = client.post(
        "/api/v1/auth/token",
        data={"username": ADMIN_EMAIL, "password": "WrongPass1"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == 401


# ---------- 开放注册（免 tenant_id） ----------

def test_register_without_tenant_creates_personal_tenant(client):
    """注册不传 tenant_id 时自动创建独立租户"""
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "open-reg@example.com", "password": "Password123"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["tenant_id"]

    # 新租户确实存在（租户读端点 superuser-only，用 admin 令牌）
    r = client.get(f"/api/v1/tenants/{body['tenant_id']}", headers={"Authorization": f"Bearer {admin_token(client)}"})
    assert r.status_code == 200

    # 该用户可正常登录
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "open-reg@example.com", "password": "Password123", "tenant_id": body["tenant_id"]},
    )
    assert r.status_code == 200


# ---------- 刷新令牌吊销 ----------

def test_refresh_rotation_revokes_old_token(client):
    tid = get_default_tenant_id(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "tenant_id": tid},
    )
    assert r.status_code == 200
    refresh_token = r.json()["refresh_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200

    # 旧 refresh token 已吊销
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401
    assert r.json()["code"] == 401


def test_refresh_rejects_access_token(client):
    tid = get_default_tenant_id(client)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "tenant_id": tid},
    )
    access_token = r.json()["access_token"]

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401
