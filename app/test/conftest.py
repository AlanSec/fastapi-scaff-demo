'''
测试配置文件
为认证系统测试提供基础配置
'''

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio

# 配置pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

# 为所有异步测试启用asyncio标记
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as asyncio test"
    )
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlmodel import SQLModel

# 导入所有模型以确保SQLModel.metadata包含所有表
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.tenant import Tenant

from app.db.session import get_session
from app.api.v1.register import register_router
from app.api.v1.password import password_router
from app.api.v1.verify import verify_router
from app.api.v1.auth import auth_router

# 创建测试FastAPI应用（只包含认证相关路由）
app = FastAPI(title="测试应用", description="认证系统测试应用")

# 注册认证相关路由
app.include_router(register_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(password_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(verify_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# 测试数据库URL - 使用内存SQLite数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, future=True
)

# 创建异步会话工厂
TestingSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop_policy():
    """设置事件循环策略"""
    return asyncio.WindowsSelectorEventLoopPolicy()

@pytest.fixture(scope="session")
def event_loop(event_loop_policy):
    """为异步测试创建事件循环"""
    asyncio.set_event_loop_policy(event_loop_policy)
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database() -> AsyncGenerator:
    """为每个测试函数设置和清理数据库"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 插入默认测试数据（默认租户、角色、权限）
    async with TestingSessionLocal() as session:
        from uuid import uuid4
        from datetime import datetime
        from app.models.tenant import Tenant
        from app.models.role import Role
        from app.models.permission import Permission
        from app.models.role_permission import RolePermission

        # 创建默认租户（如果不存在）
        result = await session.execute(select(Tenant).where(Tenant.is_active == True))
        default_tenant = result.scalar_one_or_none()

        if not default_tenant:
            default_tenant = Tenant(
                id=uuid4(),
                name="测试默认租户",
                domain="test.example.com",
                description="测试环境默认租户",
                is_active=True
            )
            session.add(default_tenant)
            await session.commit()
            await session.refresh(default_tenant)

        # 创建admin和user角色（如果不存在）
        result = await session.execute(
            select(Role).where(
                Role.name.in_(["admin", "user"]),
                Role.tenant_id == default_tenant.id
            )
        )
        existing_roles = result.scalars().all()
        existing_role_names = {role.name for role in existing_roles}

        roles_to_create = []
        if "admin" not in existing_role_names:
            admin_role = Role(
                id=uuid4(),
                name="admin",
                description="系统管理员，拥有所有权限",
                is_active=True,
                tenant_id=default_tenant.id
            )
            roles_to_create.append(admin_role)

        if "user" not in existing_role_names:
            user_role = Role(
                id=uuid4(),
                name="user",
                description="普通用户",
                is_active=True,
                tenant_id=default_tenant.id
            )
            roles_to_create.append(user_role)

        if roles_to_create:
            for role in roles_to_create:
                session.add(role)
            await session.commit()
            for role in roles_to_create:
                await session.refresh(role)

        # 获取或创建角色对象
        result = await session.execute(
            select(Role).where(
                Role.name == "admin",
                Role.tenant_id == default_tenant.id
            )
        )
        admin_role = result.scalar_one_or_none()

        result = await session.execute(
            select(Role).where(
                Role.name == "user",
                Role.tenant_id == default_tenant.id
            )
        )
        user_role = result.scalar_one_or_none()

        # 创建基本权限（如果不存在）
        # 这里只创建最少必需的权限，避免测试复杂性
        result = await session.execute(select(Permission).where(Permission.is_active == True))
        existing_permissions = result.scalars().all()

        if not existing_permissions:
            # 创建一些基本权限
            basic_permissions = [
                Permission(
                    id=uuid4(),
                    name="用户管理-查看",
                    code="user:read",
                    description="查看用户信息",
                    is_active=True
                ),
                Permission(
                    id=uuid4(),
                    name="用户管理-创建",
                    code="user:create",
                    description="创建新用户",
                    is_active=True
                ),
            ]

            for perm in basic_permissions:
                session.add(perm)
            await session.commit()
            for perm in basic_permissions:
                await session.refresh(perm)

            # 为admin角色分配所有权限
            if admin_role:
                for perm in basic_permissions:
                    role_perm = RolePermission(
                        id=uuid4(),
                        role_id=admin_role.id,
                        permission_id=perm.id,
                        is_active=True
                    )
                    session.add(role_perm)
                await session.commit()

    yield

    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def test_client(db_session: AsyncSession) -> TestClient:
    """提供FastAPI测试客户端"""

    # 覆盖get_session依赖项
    async def override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as client:
        yield client

    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def default_tenant(db_session: AsyncSession):
    """创建默认租户用于测试"""
    from app.models.tenant import Tenant
    from uuid import uuid4

    tenant = Tenant(
        id=uuid4(),
        name="测试租户",
        domain="test.example.com",
        is_active=True
    )

    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    return tenant


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, default_tenant):
    """创建测试用户"""
    from app.models.user import User
    from uuid import uuid4

    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        tenant_id=default_tenant.id,
        is_active=True
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user