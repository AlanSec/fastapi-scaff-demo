from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.dto.user_admin_dto import (
    AdminCreateUserInputDTO,
    AdminUpdateUserInputDTO,
    AdminUpdateCurrentUserInputDTO,
    UserAdminOutputDTO,
)
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password
from src.domain.services.security_interfaces import PasswordHasher


@dataclass
class AdminCreateUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, dto: AdminCreateUserInputDTO) -> UserAdminOutputDTO:
        existing = await self.user_repository.find_by_email(dto.email, dto.tenant_id)
        if existing:
            raise ValueError("Email already registered")

        email = Email(dto.email)
        hashed = self.password_hasher.hash(Password(dto.password))
        user = User.create(
            email=email,
            password=hashed,
            tenant_id=dto.tenant_id,
            is_superuser=dto.is_superuser,
        )
        await self.user_repository.save(user)
        return self._to_dto(user)

    @staticmethod
    def _to_dto(user: User) -> UserAdminOutputDTO:
        return UserAdminOutputDTO(
            id=user.id, email=str(user.email),
            is_active=user.is_active, is_verified=user.is_verified,
            is_superuser=user.is_superuser, tenant_id=user.tenant_id,
            created_at=user.created_at, updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )


@dataclass
class AdminListUsersUseCase:
    user_repository: UserRepository

    async def execute(self, skip: int = 0, limit: int = 100) -> List[UserAdminOutputDTO]:
        users = await self.user_repository.find_all(skip=skip, limit=limit)
        return [AdminCreateUserUseCase._to_dto(u) for u in users]


@dataclass
class AdminGetUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID) -> UserAdminOutputDTO | None:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            return None
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminUpdateUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, user_id: UUID, dto: AdminUpdateUserInputDTO) -> UserAdminOutputDTO | None:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            return None

        if dto.email is not None:
            user = User(id=user.id, email=Email(dto.email), password=user.password,
                        tenant_id=user.tenant_id, is_active=user.is_active,
                        is_verified=user.is_verified, is_superuser=user.is_superuser,
                        created_at=user.created_at, updated_at=user.updated_at,
                        last_login_at=user.last_login_at)
        if dto.is_active is not None:
            user = user.deactivate() if not dto.is_active else user.activate()
        if dto.is_superuser is not None:
            user = User(id=user.id, email=user.email, password=user.password,
                        tenant_id=user.tenant_id, is_active=user.is_active,
                        is_verified=user.is_verified, is_superuser=dto.is_superuser,
                        created_at=user.created_at, updated_at=user.updated_at,
                        last_login_at=user.last_login_at)
        if dto.tenant_id is not None:
            user = User(id=user.id, email=user.email, password=user.password,
                        tenant_id=dto.tenant_id, is_active=user.is_active,
                        is_verified=user.is_verified, is_superuser=user.is_superuser,
                        created_at=user.created_at, updated_at=user.updated_at,
                        last_login_at=user.last_login_at)

        await self.user_repository.save(user)
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminDeleteUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID) -> bool:
        return await self.user_repository.delete(user_id)


@dataclass
class AdminGetCurrentUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID) -> UserAdminOutputDTO:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminUpdateCurrentUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID, dto: AdminUpdateCurrentUserInputDTO) -> UserAdminOutputDTO:
        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        if dto.email is not None:
            user = User(id=user.id, email=Email(dto.email), password=user.password,
                        tenant_id=user.tenant_id, is_active=user.is_active,
                        is_verified=user.is_verified, is_superuser=user.is_superuser,
                        created_at=user.created_at, updated_at=user.updated_at,
                        last_login_at=user.last_login_at)

        await self.user_repository.save(user)
        return AdminCreateUserUseCase._to_dto(user)
