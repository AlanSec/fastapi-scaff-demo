import pytest
from pydantic import ValidationError
from src.bootstrap.config import DEV_SECRET_KEY, Settings


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.environment == "development"
        assert settings.secret_key == DEV_SECRET_KEY
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
        assert settings.database_url == "sqlite+aiosqlite:///./test.db"
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.max_login_attempts == 5
        assert settings.login_lockout_minutes == 30
        assert settings.server_host == "0.0.0.0"
        assert settings.server_port == 8000
        assert settings.server_reload is True
        assert settings.log_level == "INFO"
        assert settings.log_file is None
        assert "http://localhost:5173" in settings.cors_origins
        assert settings.require_email_verification is False

    def test_can_override_from_env(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        monkeypatch.setenv("SERVER_HOST", "127.0.0.1")
        monkeypatch.setenv("SERVER_PORT", "9000")
        monkeypatch.setenv("SERVER_RELOAD", "false")
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

        settings = Settings(_env_file=".env")

        assert settings.secret_key == "test-secret"
        assert settings.access_token_expire_minutes == 60
        assert settings.server_host == "127.0.0.1"
        assert settings.server_port == 9000
        assert settings.server_reload is False
        assert settings.cors_origins == "https://app.example.com"

    def test_production_requires_explicit_secret_key(self):
        """生产环境使用默认 SECRET_KEY 必须报错"""
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(environment="production")

    def test_production_accepts_explicit_secret_key(self):
        settings = Settings(environment="production", secret_key="real-secret-123")
        assert settings.secret_key == "real-secret-123"

    def test_development_allows_default_secret_key(self):
        settings = Settings(environment="development")
        assert settings.secret_key == DEV_SECRET_KEY
