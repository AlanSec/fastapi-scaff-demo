import os
import sys
from loguru import logger


def setup_logger(log_level="INFO"):
    """
    配置loguru日志

    参数:
        log_level: 日志级别，可以是 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    """
    # 移除默认的处理器
    logger.remove()

    # 添加控制台输出处理器，设置日志级别
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # 添加文件输出处理器
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 按日期轮转的日志文件
    logger.add(
        os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        encoding="utf-8"
    )

    return logger
