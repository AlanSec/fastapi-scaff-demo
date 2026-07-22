from dataclasses import dataclass

from src.application.dto.auth_dto import RegisterUserInputDTO, RegisterUserOutputDTO
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword, Password


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    
    async def execute(self, dto: RegisterUserInputDTO) -> RegisterUserOutputDTO:
        password = Password(dto.password)
        
        existing = await self.user_repository.find_by_email(dto.email, dto.tenant_id)
        if existing:
            raise ValueError("User already exists")
        
        hashed_password = self.password_hasher.hash(password)
        
        email = Email(dto.email)
        user = User.create(
            email=email,
            password=hashed_password,
            tenant_id=dto.tenant_id
        )
        
        await self.user_repository.save(user)
        
        return RegisterUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            is_verified=user.is_verified
        )
