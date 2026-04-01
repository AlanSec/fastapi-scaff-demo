from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True, eq=True)
class JWTToken:
    value: str = field()
    token_type: TokenType = field()
    expires_at: datetime = field()
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("token value cannot be empty")
        
        if not isinstance(self.token_type, TokenType):
            raise ValueError("invalid token type")
    
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_access_token(self) -> bool:
        return self.token_type == TokenType.ACCESS
    
    def is_refresh_token(self) -> bool:
        return self.token_type == TokenType.REFRESH
    
    def __str__(self) -> str:
        return f"{self.token_type.value}_token"
    
    def __repr__(self) -> str:
        return f"JWTToken(type={self.token_type}, expires_at={self.expires_at})"