from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password, HashedPassword


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: Password) -> HashedPassword:
        pass

    @abstractmethod
    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        pass


class JWTProvider(ABC):
    @abstractmethod
    def create_access_token(self, user: User) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user: User) -> str:
        pass

    @abstractmethod
    def verify_token(self, token: str) -> Optional[dict]:
        pass