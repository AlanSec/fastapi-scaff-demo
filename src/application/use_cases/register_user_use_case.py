from dataclasses import dataclass
from uuid import uuid4

from src.application.dto.auth_dto import RegisterUserInputDTO, RegisterUserOutputDTO
from src.domain.entities.tenant import Tenant
from src.domain.entities.user import User
from src.domain.repositories.tenant_repository import TenantRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password


@dataclass
class RegisterUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    tenant_repository: TenantRepository

    async def execute(self, dto: RegisterUserInputDTO) -> RegisterUserOutputDTO:
        password = Password(dto.password)

        tenant_id = dto.tenant_id
        if tenant_id is None:
            # 开放注册：未指定租户时自动创建独立租户
            tenant = await self._create_personal_tenant(dto.email)
            tenant_id = tenant.id

        existing = await self.user_repository.find_by_email(dto.email, tenant_id)
        if existing:
            raise ValueError("User already exists")

        hashed_password = self.password_hasher.hash(password)

        email = Email(dto.email)
        user = User.create(
            email=email,
            password=hashed_password,
            tenant_id=tenant_id
        )

        await self.user_repository.save(user)

        return RegisterUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            is_verified=user.is_verified
        )

    async def _create_personal_tenant(self, email: str) -> Tenant:
        """为开放注册用户创建一个独立租户"""
        suffix = uuid4().hex[:8]
        domain = email.split("@")[-1] if "@" in email else "example.com"
        tenant = Tenant.create(
            name=f"tenant-{suffix}",
            domain=f"{suffix}.{domain}",
        )
        await self.tenant_repository.save(tenant)
        return tenant
