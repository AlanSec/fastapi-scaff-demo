from dataclasses import dataclass
from uuid import uuid4

from src.application.dto.auth_dto import RegisterUserInputDTO, RegisterUserOutputDTO
from src.domain.entities.tenant import Tenant
from src.domain.entities.user import User
from src.domain.exceptions import ConflictError, InvalidInputError
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
        created_tenant: Tenant | None = None
        if tenant_id is None:
            # 开放注册：未指定租户时自动创建独立租户
            tenant = await self._create_personal_tenant(dto.email)
            tenant_id = tenant.id
            created_tenant = tenant
        else:
            # 指定租户必须存在且激活，否则拒绝注册（防外键脏数据）
            tenant = await self.tenant_repository.find_by_id(tenant_id)
            if tenant is None or not tenant.is_active:
                raise InvalidInputError("Tenant not found or inactive")

        existing = await self.user_repository.find_by_email(dto.email, tenant_id)
        if existing:
            # 自动创建的租户尚未绑定用户：删除它，避免留下孤儿租户
            await self._rollback_created_tenant(created_tenant)
            raise ConflictError("User already exists")

        hashed_password = self.password_hasher.hash(password)

        email = Email(dto.email)
        user = User.create(
            email=email,
            password=hashed_password,
            tenant_id=tenant_id
        )

        try:
            await self.user_repository.save(user)
        except Exception:
            # 用户保存失败（如并发重复注册触发唯一约束）：补偿删除自动创建的租户。
            # 补偿失败只记录日志，不掩盖原始异常。
            await self._rollback_created_tenant(created_tenant)
            raise

        return RegisterUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            is_verified=user.is_verified
        )

    async def _rollback_created_tenant(self, tenant: Tenant | None) -> None:
        """删除本用例自动创建的租户（补偿回滚，避免孤儿租户）"""
        if tenant is None:
            return
        try:
            await self.tenant_repository.delete(tenant.id)
        except Exception:  # noqa: BLE001 - 补偿失败不掩盖原始异常
            import logging
            logging.getLogger(__name__).exception(
                "Failed to roll back created tenant %s after register failure", tenant.id
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
