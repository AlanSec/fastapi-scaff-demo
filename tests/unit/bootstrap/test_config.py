import pytest
from src.bootstrap.config import Settings


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.secret_key == "dev-secret-key-change-in-production"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
        assert settings.database_url == "sqlite+aiosqlite:///./test.db"

    def test_can_override_from_env(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        
        settings = Settings(_env_file=".env")
        
        assert settings.secret_key == "test-secret"
        assert settings.access_token_expire_minutes == 60