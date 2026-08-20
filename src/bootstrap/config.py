from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    environment: str = Field(default="development", description="运行环境：development/production")
    secret_key: str = Field(default=DEV_SECRET_KEY, description="JWT密钥")
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")
    database_url: str = Field(default="sqlite+aiosqlite:///./test.db", description="数据库连接URL")

    # 服务启动配置（python main.py 使用）
    server_host: str = Field(default="0.0.0.0", description="服务监听地址")
    server_port: int = Field(default=8000, description="服务监听端口")
    server_reload: bool = Field(default=True, description="开发热重载（生产环境建议关闭）")

    # CORS 白名单（逗号分隔；前端部署后把域名加进来）
    cors_origins: str = Field(
        default=(
            "http://localhost:8000,http://localhost:3000,"
            "http://localhost:5173,http://localhost:5174,"
            "http://127.0.0.1:8000,http://127.0.0.1:3000,"
            "http://127.0.0.1:5173,http://127.0.0.1:5174"
        ),
        description="允许的 CORS 来源（逗号分隔）",
    )

    # 限流存储（本地 Redis；不可用时自动降级为内存实现）
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis 连接URL")

    # 登录限流配置
    max_login_attempts: int = Field(default=5, description="窗口内最大登录失败次数")
    login_lockout_minutes: int = Field(default=30, description="登录锁定时长(分钟)")

    # 邮箱验证配置（开启后未验证邮箱的用户不能登录）
    require_email_verification: bool = Field(default=False, description="是否强制邮箱验证")

    # 管理员配置
    admin_email: str = Field(default="admin@example.com", description="管理员邮箱")
    admin_username: str = Field(default="admin", description="管理员用户名")
    admin_password: str = Field(default="Admin123456", description="管理员密码")
    admin_is_superuser: bool = Field(default=True, description="管理员是否超级用户")

    @model_validator(mode="after")
    def _validate_production_secret(self):
        if self.environment == "production" and self.secret_key == DEV_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY must be explicitly set in production environment "
                "(generate one with: openssl rand -hex 32)"
            )
        return self


settings = Settings()
