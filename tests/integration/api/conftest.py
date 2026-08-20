"""API 层集成测试 conftest——用测试库引擎替换容器仓储，TestClient 全链路。"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from src.bootstrap import lifespan as lifespan_module
from src.bootstrap.container import get_container
from src.bootstrap.lifespan import create_app
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_permission_repository import (
    SQLModelPermissionRepository,
)
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_refresh_token_repository import (
    SQLModelRefreshTokenRepository,
)
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_role_repository import SQLModelRoleRepository
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_tenant_repository import SQLModelTenantRepository
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_user_repository import SQLModelUserRepository
from src.infrastructure.security.rate_limiter import InMemoryRateLimiter
from tests.integration.conftest import TestingSessionLocal, test_engine

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123456"


@pytest.fixture
def client(monkeypatch):
    """TestClient：建表走测试引擎，容器仓储替换为测试库实现，限流用内存（避免 Redis 超时拖慢测试）。"""

    async def _init_test_db():
        async with test_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    monkeypatch.setattr(lifespan_module, "init_db", _init_test_db)

    container = get_container()
    # 重置容器全部缓存，注入测试库仓储
    for name in list(vars(container)):
        if name.startswith("_") and name != "_initialized":
            setattr(container, name, None)
    container._user_repository = SQLModelUserRepository(TestingSessionLocal)
    container._tenant_repository = SQLModelTenantRepository(TestingSessionLocal)
    container._role_repository = SQLModelRoleRepository(TestingSessionLocal)
    container._permission_repository = SQLModelPermissionRepository(TestingSessionLocal)
    container._refresh_token_repository = SQLModelRefreshTokenRepository(TestingSessionLocal)
    container._rate_limiter = InMemoryRateLimiter()

    with TestClient(create_app()) as tc:
        yield tc


def get_default_tenant_id(client) -> str:
    """获取 ensure_admin 创建的默认租户 ID"""
    r = client.get("/api/v1/tenants")
    assert r.status_code == 200, r.text
    items = r.json()["items"] if "items" in r.json() else r.json()
    return next(t["id"] for t in items if t["name"] == "Default Tenant")


def admin_token(client) -> str:
    """admin 登录获取 access token（admin 为 superuser）"""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "tenant_id": get_default_tenant_id(client)},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def register_user(client, email: str, password: str = "Password123") -> str:
    """注册普通用户并返回其 id"""
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "tenant_id": get_default_tenant_id(client)},
    )
    assert r.status_code == 201, r.text
    return r.json()["user_id"]
