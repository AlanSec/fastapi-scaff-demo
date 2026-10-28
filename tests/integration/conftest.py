from datetime import datetime, timezone
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from src.infrastructure.persistence.sqlmodel.models import (
    RoleModel,
    TenantModel,
    UserModel,
)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# StaticPool + check_same_thread=False：让所有连接共享同一个内存库
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def dispose_engine():
    """会话结束后释放引擎，避免 aiosqlite 后台线程阻止进程退出"""
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def default_tenant(db_session: AsyncSession):
    tenant = TenantModel(
        id=uuid4(),
        name="Test Tenant",
        domain="test.example.com",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture(scope="function")
async def test_user(default_tenant, db_session: AsyncSession):
    user = UserModel(
        id=uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$hashed",
        tenant_id=default_tenant.id,
        is_active=True,
        email_verified=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_role(default_tenant, db_session: AsyncSession):
    role = RoleModel(
        id=uuid4(),
        name="admin",
        description="Admin role",
        is_active=True,
        tenant_id=default_tenant.id,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role
