"""JWT Provider 实现"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.domain.services.security_interfaces import JWTProvider
from src.domain.entities.user import User


class JWTProviderImpl(JWTProvider):
    """基于 PyJWT 的 JWT Provider 实现"""
    
    def __init__(
        self, 
        secret_key: str, 
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "email": str(user.email),
            "tenant_id": str(user.tenant_id),
            "type": "access",
            "exp": expire
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """创建刷新令牌"""
        expire = datetime.now(timezone.utc) + timedelta(days=self._refresh_token_expire_days)
        payload = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": expire
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                self._secret_key, 
                algorithms=[self._algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
