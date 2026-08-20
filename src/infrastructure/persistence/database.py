"""数据库引擎与会话管理（新架构持久化入口）"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from src.bootstrap.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False, future=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SessionFactory = Callable[[], AsyncSession]


@asynccontextmanager
async def session_scope(session_factory: SessionFactory):
    """仓储每次操作使用独立会话，结束后自动关闭（适配单例 DI 容器）"""
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


async def init_db() -> None:
    """启动时创建所有表（幂等）"""
    from src.infrastructure.persistence.sqlmodel import models  # noqa: F401  # 确保模型注册到 metadata

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables ensured")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：请求级会话（供未来请求作用域仓储使用）"""
    async with async_session_maker() as session:
        yield session
