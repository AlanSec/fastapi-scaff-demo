import os
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test_connection():
    db_url = str(settings.SQLALCHEMY_DATABASE_URI)
    print(f'Testing connection to: {db_url}')
    
    # 尝试不同的连接参数
    engine = create_async_engine(
        db_url,
        echo=True,
        pool_pre_ping=True,  # 连接前检查
        pool_recycle=3600,   # 每小时回收连接
    )
    
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text('SELECT 1'))
            print('Connection successful!')
    except Exception as e:
        print(f'Connection failed: {e}')
    finally:
        await engine.dispose()

asyncio.run(test_connection())
