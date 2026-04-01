
import logging
import os

from dotenv import load_dotenv
load_dotenv()

import uvicorn


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

    # 使用新架构的 create_app()
    from src.bootstrap.lifespan import create_app
    app = create_app()

    logger.info("应用已创建，使用 src 架构")

    # 使用uvicorn启动FastAPI应用
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
