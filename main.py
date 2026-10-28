
import logging
import os

from dotenv import load_dotenv
load_dotenv()

import uvicorn
from src.bootstrap.config import settings


def _init_logging() -> None:
    """日志配置由 Settings 驱动（LOG_LEVEL / LOG_FILE），不再硬编码相对路径。"""
    handlers = [logging.StreamHandler()]
    if settings.log_file:
        handlers.append(logging.FileHandler(settings.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
    )


_init_logging()
logger = logging.getLogger(__name__)
logger.info("日志系统已初始化（level=%s, file=%s）", settings.log_level, settings.log_file or "console-only")


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
        log_level=settings.log_level.lower(),
        factory=True,
    )


if __name__ == "__main__":
    main()
