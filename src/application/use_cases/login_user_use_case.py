from dataclasses import dataclass
from uuid import UUID

from src.application.dto.auth_dto import LoginUserInputDTO, LoginUserOutputDTO
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword, Password


@dataclass
class LoginUserUseCase:
    user_repository: UserRepository
    password_hasher: 'HasherProtocol'
    jwt_provider: 'JWTProtocol'
    
    async def execute(self, dto: LoginUserInputDTO) -> LoginUserOutputDTO:
        user = await self.user_repository.find_by_email(dto.email, dto.tenant_id)
        
        if not user:
            raise ValueError("Invalid credentials")
        
        password = Password(dto.password)
        if not self.password_hasher.verify(password, user.password):
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("User is inactive")
        
        access_token = self.jwt_provider.create_access_token(user)
        refresh_token = self.jwt_provider.create_refresh_token(user)
        
        updated_user = user.update_last_login()
        await self.user_repository.save(updated_user)
        
        return LoginUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800
        )


class HasherProtocol:
    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        pass


class JWTProtocol:
    def create_access_token(self, user: User) -> str:
        pass
    
    def create_refresh_token(self, user: User) -> str:
        pass