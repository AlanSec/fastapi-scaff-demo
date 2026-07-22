from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.password import Password, HashedPassword


class PasswordHasher(ABC):
    """Password hashing interface"""

    @abstractmethod
    def hash(self, password: Password) -> HashedPassword:
        pass

    @abstractmethod
    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        pass


class JWTProvider(ABC):
    """JWT token provider interface"""

    @abstractmethod
    def create_access_token(self, user: User) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user: User) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict]:
        pass


class RateLimiter(ABC):
    """Rate limiter interface"""

    @abstractmethod
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        pass

    @abstractmethod
    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        pass
