import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.infrastructure.persistence.sqlmodel.models import User, Tenant, Role, Permission
from src.infrastructure.persistence.sqlmodel.models.role_permission import RolePermission
from src.infrastructure.persistence.sqlmodel.models.user_role import UserRole
from uuid import uuid4
from datetime import datetime, timezone

pytest_plugins = ("pytest_asyncio",)

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


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
    tenant = Tenant(
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
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$hashed",
        tenant_id=default_tenant.id,
        is_active=True,
        is_verified=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_role(default_tenant, db_session: AsyncSession):
    role = Role(
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