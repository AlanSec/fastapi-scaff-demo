
import logging
import os

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from src.bootstrap.config import settings


logging.basicConfig(
    level=logging.INFO,
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
    logger.info("正在启动 FastAPI Enterprise 架构...")

    # 使用uvicorn启动FastAPI应用
    # 注意：必须使用 import string 而不是 app 对象，否则 reload 会失效
    uvicorn.run(
        "src.bootstrap.lifespan:create_app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        log_level="info",
        factory=True,
    )


if __name__ == "__main__":
    main()
