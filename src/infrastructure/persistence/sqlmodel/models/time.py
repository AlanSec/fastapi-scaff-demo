"""UTC 时间工具——模型默认值的统一时间来源。

独立模块（不依赖 database/engine），避免 Alembic 同步迁移上下文
因 import 模型而连带创建异步 engine。
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """UTC aware 当前时间——实体与模型统一的时间来源（避免 naive/aware 混用）。"""
    return datetime.now(timezone.utc)
