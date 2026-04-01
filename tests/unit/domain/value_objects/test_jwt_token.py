import pytest
from datetime import datetime, timedelta, timezone
from src.domain.value_objects.jwt_token import JWTToken, TokenType


def test_jwt_token_creation_with_valid_token():
    token = JWTToken(
        value="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        token_type=TokenType.ACCESS,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )
    assert token.value.startswith("eyJ")
    assert token.token_type == TokenType.ACCESS


def test_jwt_token_creation_with_empty_token_raises_value_error():
    with pytest.raises(ValueError, match="token value cannot be empty"):
        JWTToken(
            value="",
            token_type=TokenType.ACCESS,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
        )


def test_jwt_token_creation_with_expired_token():
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = JWTToken(
        value="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        token_type=TokenType.ACCESS,
        expires_at=expired_at
    )
    assert token.is_expired() is True


def test_jwt_token_creation_with_valid_token_not_expired():
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = JWTToken(
        value="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    assert token.is_expired() is False


def test_jwt_token_equality():
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    token1 = JWTToken(
        value="token123",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    token2 = JWTToken(
        value="token123",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    token3 = JWTToken(
        value="different",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    
    assert token1 == token2
    assert token1 != token3


def test_refresh_token_type():
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    token = JWTToken(
        value="refresh_token",
        token_type=TokenType.REFRESH,
        expires_at=expires_at
    )
    
    assert token.token_type == TokenType.REFRESH
    assert token.is_access_token() is False
    assert token.is_refresh_token() is True


def test_access_token_type():
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    token = JWTToken(
        value="access_token",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    
    assert token.token_type == TokenType.ACCESS
    assert token.is_access_token() is True
    assert token.is_refresh_token() is False


def test_jwt_token_is_immutable():
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    token = JWTToken(
        value="token",
        token_type=TokenType.ACCESS,
        expires_at=expires_at
    )
    
    with pytest.raises(AttributeError):
        token.value = "new_token"