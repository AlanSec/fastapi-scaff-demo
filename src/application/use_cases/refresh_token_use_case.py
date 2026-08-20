from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.application.dto.auth_dto import LoginUserOutputDTO, RefreshTokenInputDTO
from src.domain.repositories.refresh_token_repository import RefreshTokenRepository
from src.domain.repositories.user_repository import UserRepository
from src.domain.services.security_interfaces import JWTProvider


@dataclass
class RefreshTokenUseCase:
    user_repository: UserRepository
    jwt_provider: JWTProvider
    refresh_token_repository: RefreshTokenRepository

    async def execute(self, dto: RefreshTokenInputDTO) -> LoginUserOutputDTO:
        payload = self.jwt_provider.verify_token(dto.refresh_token)

        # 只接受 type=refresh 的令牌（access token 不能用于刷新）
        if payload is None or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if jti is None or user_id is None:
            raise ValueError("Invalid refresh token")

        # 服务端吊销校验：令牌必须已登记且未被吊销/过期
        stored = await self.refresh_token_repository.find_by_token(jti)
        if stored is None or stored.is_revoked:
            raise ValueError("Invalid refresh token")
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            # SQLite 等存储返回 naive datetime，统一按 UTC 处理
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            await self.refresh_token_repository.revoke(jti)
            raise ValueError("Invalid refresh token")

        try:
            user = await self.user_repository.find_by_id(UUID(user_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid refresh token")

        if user is None:
            raise ValueError("Invalid refresh token")

        if not user.is_active:
            raise ValueError("User is inactive")

        # 轮换：吊销旧令牌，签发并登记新令牌
        await self.refresh_token_repository.revoke(jti)

        access_token = self.jwt_provider.create_access_token(user)
        refresh_token = self.jwt_provider.create_refresh_token(user)
        await self._persist_refresh_token(user.id, refresh_token)

        return LoginUserOutputDTO(
            user_id=user.id,
            email=str(user.email),
            tenant_id=user.tenant_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_provider.get_access_token_expire_seconds(),
        )

    async def _persist_refresh_token(self, user_id, refresh_token: str) -> None:
        """将新 refresh token 的 jti 持久化"""
        new_payload = self.jwt_provider.verify_token(refresh_token)
        new_jti = new_payload.get("jti") if new_payload else None
        if new_jti is None:
            return
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self.jwt_provider.get_refresh_token_expire_seconds()
        )
        await self.refresh_token_repository.save(new_jti, user_id, expires_at)
