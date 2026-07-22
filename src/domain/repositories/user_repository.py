from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(ABC):
    
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: UUID) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_tenant(
        self, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        pass
    
    @abstractmethod
    async def find_by_reset_token(self, token: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_verification_token(self, token: str) -> Optional[User]:
        pass
