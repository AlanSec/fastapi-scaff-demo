
import logging
import os

from dotenv import load_dotenv
load_dotenv()

import uvicorn

from app.core.config import settings


logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
logger.info("日志系统已初始化")


def main():
    """应用程序入口点"""
    logger.info("正在启动AIGC一站式平台...")
    logger.info(f"数据库URI: {settings.SQLALCHEMY_DATABASE_URI}")

    # 使用uvicorn启动FastAPI应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
