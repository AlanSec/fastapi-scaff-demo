import json
import logging
from typing import Any

from pydantic import AnyHttpUrl, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # 项目基础配置
    PROJECT_NAME: str = "AIGC Backend"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    BASE_URL: str = "http://127.0.0.1:8000"

    # 安全配置（必须通过环境变量设置）
    SECRET_KEY: str = ""  # 必须通过环境变量设置，无默认值
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # 刷新令牌配置
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 刷新令牌有效期30天

    # 登录限制配置
    MAX_LOGIN_ATTEMPTS: int = 5  # 最大登录尝试次数
    LOGIN_LOCKOUT_MINUTES: int = 30  # 锁定时间（分钟）

    # 管理员配置（必须通过环境变量设置）
    ADMIN_EMAIL: str = ""
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""  # 必须通过环境变量设置，无默认值
    ADMIN_IS_SUPERUSER: bool = True

    # 数据库配置（必须通过环境变量设置）
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""  # 必须通过环境变量设置，无默认值
    POSTGRES_DB: str = "aigc_db"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: str | None = None  # 必须通过环境变量设置，无默认值


    @field_validator("SQLALCHEMY_DATABASE_URI", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            port=int(info.data.get("POSTGRES_PORT", "5432")),
            path=f"{info.data.get('POSTGRES_DB') or ''}",
        )

    # SD WebUI配置
    SD_WEBUI_NODES: list[dict[str, Any]] = []
    SD_WEBUI_TIMEOUT: int = 60

    @field_validator("SD_WEBUI_NODES", mode="before")
    def parse_sd_webui_nodes(cls, v: str | list) -> list:
        if isinstance(v, str):
            return json.loads(v)
        return v

    # 媒体文件配置
    MEDIA_ROOT: str = "media"
    GALLERY_PATH: str = "media/gallery"

    @property
    def media_root_path(self) -> Path:
        """获取绝对路径"""
        return Path(__file__).parent.parent / self.MEDIA_ROOT
    @ property
    def gallery_path(self) -> Path:
        """获取绝对路径"""
        return Path(__file__).parent.parent / self.GALLERY_PATH

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # CORS配置
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl | str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    # SMTP邮件配置（用于发送验证邮件和密码重置邮件）
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # 必须通过环境变量设置
    SMTP_PASSWORD: str = ""  # 必须通过环境变量设置
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_FROM_NAME: str = "FastAPI App"

    class Config:
        env_file = str(Path(__file__).parent.parent.parent / ".env")
        case_sensitive = True


settings = Settings()
