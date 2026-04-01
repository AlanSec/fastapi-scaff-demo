from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = str(settings.SQLALCHEMY_DATABASE_URI)
        _engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        from app.db.base import SQLModel

        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def dispose_engine():
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
