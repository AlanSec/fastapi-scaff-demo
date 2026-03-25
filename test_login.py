import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from app.services.auth import authenticate_user
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import os

async def test_login():
    # 直接从环境变量构建数据库URL
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    postgres_server = os.getenv("POSTGRES_SERVER", "127.0.0.1")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "aigc_db")
    
    db_url = f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{postgres_server}:{postgres_port}/{postgres_db}"
    print(f'Database URL: {db_url}')
    
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        try:
            user = await authenticate_user("admin", "12345678", session)
            if user:
                print(f'Login successful! User: {user.username}')
                print(f'Email: {user.email}')
                print(f'Is Superuser: {user.is_superuser}')
            else:
                print('Login failed!')
        except Exception as e:
            print(f'Error: {e}')
        finally:
            await engine.dispose()

asyncio.run(test_login())
