from dataclasses import dataclass
from typing import List
from uuid import UUID

from src.application.dto.user_admin_dto import (
    AdminCreateUserInputDTO,
    AdminUpdateCurrentUserInputDTO,
    AdminUpdateUserInputDTO,
    UserAdminOutputDTO,
)
from src.domain.entities.user import User
from src.domain.exceptions import ConflictError, EntityNotFoundError
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import PasswordHasher
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password


@dataclass
class AdminCreateUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(self, dto: AdminCreateUserInputDTO, tenant_id: UUID) -> UserAdminOutputDTO:
        """创建用户到指定租户（tenant_id 来自认证上下文，不接受请求体指定）"""
        existing = await self.user_repository.find_by_email(dto.email, tenant_id)
        if existing:
            raise ConflictError("Email already registered")

        email = Email(dto.email)
        hashed = self.password_hasher.hash(Password(dto.password))
        user = User.create(
            email=email,
            password=hashed,
            tenant_id=tenant_id,
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

    async def execute(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> List[UserAdminOutputDTO]:
        """仅返回指定租户内的用户"""
        users = await self.user_repository.find_by_tenant(tenant_id, skip=skip, limit=limit)
        return [AdminCreateUserUseCase._to_dto(u) for u in users]


@dataclass
class AdminGetUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> UserAdminOutputDTO | None:
        """按 ID 查询用户，限定在指定租户内（跨租户返回 None → 404）"""
        user = await self.user_repository.find_by_id(user_id, tenant_id)
        if user is None:
            return None
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminUpdateUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    async def execute(
        self, user_id: UUID, dto: AdminUpdateUserInputDTO, tenant_id: UUID
    ) -> UserAdminOutputDTO | None:
        user = await self.user_repository.find_by_id(user_id, tenant_id)
        if user is None:
            return None

        if dto.email is not None:
            user = user.with_email(Email(dto.email))
        if dto.is_active is not None:
            user = user.deactivate() if not dto.is_active else user.activate()
        if dto.is_superuser is not None:
            user = user.with_superuser(dto.is_superuser)

        await self.user_repository.save(user)
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminDeleteUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> bool:
        return await self.user_repository.delete(user_id, tenant_id)


@dataclass
class AdminGetCurrentUserUseCase:
    user_repository: UserRepository

    async def execute(self, user_id: UUID, tenant_id: UUID) -> UserAdminOutputDTO:
        user = await self.user_repository.find_by_id(user_id, tenant_id)
        if user is None:
            raise EntityNotFoundError("User not found")
        return AdminCreateUserUseCase._to_dto(user)


@dataclass
class AdminUpdateCurrentUserUseCase:
    user_repository: UserRepository

    async def execute(
        self, user_id: UUID, dto: AdminUpdateCurrentUserInputDTO, tenant_id: UUID
    ) -> UserAdminOutputDTO:
        user = await self.user_repository.find_by_id(user_id, tenant_id)
        if user is None:
            raise EntityNotFoundError("User not found")

        if dto.email is not None:
            user = user.with_email(Email(dto.email))

        await self.user_repository.save(user)
        return AdminCreateUserUseCase._to_dto(user)
