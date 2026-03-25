from collections.abc import AsyncGenerator
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# 延迟创建引擎，确保配置已加载
_engine = None
_session_factory = None


def get_engine():
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        # 重新读取配置，确保环境变量已加载
        from dotenv import load_dotenv
        load_dotenv()
        
        # 重新加载配置
        from app.core.config import settings as fresh_settings
        db_url = str(fresh_settings.SQLALCHEMY_DATABASE_URI)
        _engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,  # 连接前检查
            pool_recycle=3600,   # 每小时回收连接
        )
    return _engine


def get_session_factory():
    """获取会话工厂"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return _session_factory


async def init_db() -> None:
    """初始化数据库，创建所有表"""
    engine = get_engine()
    async with engine.begin() as conn:
        # 导入所有模型确保它们被SQLModel注册
        from app.db.base import SQLModel  # noqa

        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖函数"""
    # 每次创建新的会话工厂，避免缓存问题
    from dotenv import load_dotenv
    load_dotenv()
    
    # 直接从环境变量构建数据库URL
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_server = os.getenv("POSTGRES_SERVER", "127.0.0.1")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "aigc_db")
    
    db_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
    
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,  # 连接前检查
        pool_recycle=3600,   # 每小时回收连接
    )
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()
