from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.application.dto.auth_dto import LoginUserInputDTO, LoginUserOutputDTO
from src.domain.exceptions import InvalidCredentialsError
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from src.domain.repositories.tenant_repository import TenantRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import JWTProvider, PasswordHasher, RateLimiter, RateLimitExceeded
from src.domain.value_objects.password import HashedPassword, Password

# 恒时比较占位哈希：用户不存在时也执行一次 bcrypt verify，
# 避免响应时间差泄露账号是否存在（计时枚举）。
_DUMMY_PASSWORD_HASH = "$2b$12$T.jD2D0hjxOguD8PBFe/A.NaLhuaB8T6w9H.eUFnQ6w9w2p5uapf2"


@dataclass
class LoginUserUseCase:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    jwt_provider: JWTProvider
    rate_limiter: RateLimiter
    refresh_token_repository: RefreshTokenRepository
    tenant_repository: TenantRepository
    max_attempts: int = 5
    lockout_window_seconds: int = 1800
    require_email_verification: bool = False

    async def execute(self, dto: LoginUserInputDTO) -> LoginUserOutputDTO:
        key = f"login:{dto.email.lower()}"

        # 先检查是否已被锁定（锁定状态下即使凭证正确也拒绝）
        remaining = await self.rate_limiter.get_remaining(
            key, self.max_attempts, self.lockout_window_seconds
        )
        if remaining <= 0:
            raise RateLimitExceeded("Too many login attempts, please try again later")

        # 租户必须存在且激活；失败统一走"凭证错误"路径（防租户枚举）
        tenant = await self.tenant_repository.find_by_id(dto.tenant_id)
        if tenant is None or not tenant.is_active:
            await self.rate_limiter.check_rate_limit(
                key, self.max_attempts, self.lockout_window_seconds
            )
            raise InvalidCredentialsError("Invalid credentials")

        user = await self.user_repository.find_by_email(dto.email, dto.tenant_id)

        if user is None:
            # 恒时：对占位哈希执行一次 verify（消耗与真实校验相近的时间）
            self.password_hasher.verify(
                Password(dto.password), HashedPassword(_DUMMY_PASSWORD_HASH)
            )
            await self.rate_limiter.check_rate_limit(
                key, self.max_attempts, self.lockout_window_seconds
            )
            raise InvalidCredentialsError("Invalid credentials")

        if not self.password_hasher.verify(Password(dto.password), user.password):
            # 失败尝试计数；达到阈值后抛限流异常
            await self.rate_limiter.check_rate_limit(
                key, self.max_attempts, self.lockout_window_seconds
            )
            raise InvalidCredentialsError("Invalid credentials")

        if not user.is_active:
            raise InvalidCredentialsError("Invalid credentials")

        if self.require_email_verification and not user.is_verified:
            raise InvalidCredentialsError("Invalid credentials")

        access_token = self.jwt_provider.create_access_token(user)
        refresh_token = self.jwt_provider.create_refresh_token(user)
        await self._persist_refresh_token(user.id, refresh_token)

        updated_user = user.update_last_login()
        await self.user_repository.save(updated_user)

        return LoginUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_provider.get_access_token_expire_seconds()
        )

    async def _persist_refresh_token(self, user_id, refresh_token: str) -> None:
        """将 refresh token 的 jti 持久化，供服务端吊销使用"""
        payload = self.jwt_provider.verify_token(refresh_token)
        jti = payload.get("jti") if payload else None
        if jti is None:
            return
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.jwt_provider.get_refresh_token_expire_seconds()
        )
        await self.refresh_token_repository.save(jti, user_id, expires_at)
