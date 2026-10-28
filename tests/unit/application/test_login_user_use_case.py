from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.auth_dto import LoginUserInputDTO, LoginUserOutputDTO
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.domain.entities.user import User
from src.domain.services.security_interfaces import RateLimitExceeded
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.security.rate_limiter import InMemoryRateLimiter


class TestLoginUserUseCase:
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_hasher(self):
        return MagicMock()

    @pytest.fixture
    def mock_jwt_provider(self):
        return MagicMock()

    @pytest.fixture
    def rate_limiter(self):
        return InMemoryRateLimiter()

    @pytest.fixture
    def mock_refresh_token_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_tenant_repository(self):
        repo = AsyncMock()
        repo.find_by_id.return_value = MagicMock(is_active=True)
        return repo

    @pytest.fixture
    def use_case(
        self,
        mock_user_repository,
        mock_password_hasher,
        mock_jwt_provider,
        rate_limiter,
        mock_refresh_token_repository,
        mock_tenant_repository,
    ):
        return LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=rate_limiter,
            refresh_token_repository=mock_refresh_token_repository,
            tenant_repository=mock_tenant_repository,
        )

    @pytest.mark.asyncio
    async def test_execute_login_success(self, use_case, mock_user_repository, mock_password_hasher, mock_jwt_provider):
        email = "test@example.com"
        password = "Password123"
        tenant_id = uuid4()
        user_id = uuid4()

        user = User(
            id=user_id,
            email=Email(email),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=tenant_id,
            is_active=True,
            is_verified=True,
            created_at=MagicMock(),
            updated_at=MagicMock()
        )

        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = True
        mock_jwt_provider.create_access_token.return_value = "access_token"
        mock_jwt_provider.create_refresh_token.return_value = "refresh_token"
        mock_jwt_provider.get_access_token_expire_seconds.return_value = 1800
        mock_jwt_provider.get_refresh_token_expire_seconds.return_value = 604800
        mock_user_repository.save.return_value = user

        input_dto = LoginUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        result = await use_case.execute(input_dto)

        assert isinstance(result, LoginUserOutputDTO)
        assert result.user_id == user_id
        assert result.email == email
        assert result.tenant_id == tenant_id
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        mock_password_hasher.verify.assert_called_once()
        mock_jwt_provider.create_access_token.assert_called_once()
        mock_jwt_provider.create_refresh_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_when_tenant_missing_or_inactive(
        self, mock_user_repository, mock_password_hasher, mock_jwt_provider, mock_tenant_repository
    ):
        """租户不存在或停用 → 统一 'Invalid credentials'（防租户枚举）"""
        mock_tenant_repository.find_by_id.return_value = None
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=InMemoryRateLimiter(),
            refresh_token_repository=AsyncMock(),
            tenant_repository=mock_tenant_repository,
        )
        dto = LoginUserInputDTO(email="test@example.com", password="Password123", tenant_id=uuid4())
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(dto)

        # 停用租户同样拒绝
        mock_tenant_repository.find_by_id.return_value = MagicMock(is_active=False)
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(dto)

    @pytest.mark.asyncio
    async def test_execute_raises_when_user_not_found(self, use_case, mock_user_repository, mock_password_hasher):
        """用户不存在时仍执行一次 verify（恒时比较，防计时枚举）"""
        mock_user_repository.find_by_email.return_value = None

        input_dto = LoginUserInputDTO(
            email="notfound@example.com",
            password="Password123",
            tenant_id=uuid4()
        )

        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(input_dto)
        # 恒时：即使账号不存在，hasher.verify 也须被调用一次
        mock_password_hasher.verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_when_password_invalid(self, use_case, mock_user_repository, mock_password_hasher):
        from datetime import datetime
        user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=uuid4(),
            is_active=True,
            is_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = False

        input_dto = LoginUserInputDTO(
            email="test@example.com",
            password="Wrong123",
            tenant_id=user.tenant_id
        )

        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(input_dto)

    @pytest.mark.asyncio
    async def test_execute_raises_when_user_inactive(self, use_case, mock_user_repository, mock_password_hasher):
        user = MagicMock(spec=User)
        user.is_active = False
        user.password = HashedPassword("$2b$12$hashed")
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = True

        input_dto = LoginUserInputDTO(
            email="test@example.com",
            password="Password123",
            tenant_id=uuid4()
        )

        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(input_dto)

    @pytest.mark.asyncio
    async def test_successful_logins_do_not_consume_budget(
        self, mock_user_repository, mock_password_hasher, mock_jwt_provider
    ):
        """成功登录不消耗失败配额，多次成功登录不应被锁定"""
        from datetime import datetime
        limiter = InMemoryRateLimiter()
        tenant_repo = AsyncMock()
        tenant_repo.find_by_id.return_value = MagicMock(is_active=True)
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=limiter,
            refresh_token_repository=AsyncMock(),
            tenant_repository=tenant_repo,
            max_attempts=2,
            lockout_window_seconds=3600,
        )
        user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=uuid4(),
            is_active=True,
            is_verified=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = True
        mock_jwt_provider.create_access_token.return_value = "access"
        mock_jwt_provider.create_refresh_token.return_value = "refresh"
        mock_jwt_provider.get_access_token_expire_seconds.return_value = 1800
        mock_jwt_provider.get_refresh_token_expire_seconds.return_value = 604800
        mock_user_repository.save.return_value = user

        dto = LoginUserInputDTO(email="test@example.com", password="Password123", tenant_id=user.tenant_id)
        for _ in range(3):
            result = await use_case.execute(dto)
            assert result.access_token == "access"

    @pytest.mark.asyncio
    async def test_locked_account_rejects_even_with_correct_password(
        self, mock_user_repository, mock_password_hasher, mock_jwt_provider
    ):
        """达到失败阈值后，即使凭证正确也被锁定（抛 RateLimitExceeded）"""
        from datetime import datetime
        limiter = InMemoryRateLimiter()
        tenant_repo = AsyncMock()
        tenant_repo.find_by_id.return_value = MagicMock(is_active=True)
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=limiter,
            refresh_token_repository=AsyncMock(),
            tenant_repository=tenant_repo,
            max_attempts=2,
            lockout_window_seconds=3600,
        )
        user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=uuid4(),
            is_active=True,
            is_verified=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = False

        dto = LoginUserInputDTO(email="test@example.com", password="Wrong123", tenant_id=user.tenant_id)
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(dto)
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(dto)

        # 第 3 次：即使密码正确，也被限流拒绝
        mock_password_hasher.verify.return_value = True
        with pytest.raises(RateLimitExceeded):
            await use_case.execute(dto)

    @pytest.mark.asyncio
    async def test_unverified_email_allowed_by_default(
        self, mock_user_repository, mock_password_hasher, mock_jwt_provider, mock_refresh_token_repository
    ):
        """默认不强制邮箱验证，未验证用户可登录"""
        from datetime import datetime
        user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=uuid4(),
            is_active=True,
            is_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = True
        mock_jwt_provider.create_access_token.return_value = "access"
        mock_jwt_provider.create_refresh_token.return_value = "refresh"
        mock_jwt_provider.get_access_token_expire_seconds.return_value = 1800
        mock_jwt_provider.get_refresh_token_expire_seconds.return_value = 604800
        mock_user_repository.save.return_value = user

        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=InMemoryRateLimiter(),
            refresh_token_repository=mock_refresh_token_repository,
            tenant_repository=AsyncMock(),
        )
        dto = LoginUserInputDTO(email="test@example.com", password="Password123", tenant_id=user.tenant_id)
        result = await use_case.execute(dto)
        assert result.access_token == "access"

    @pytest.mark.asyncio
    async def test_unverified_email_rejected_when_required(
        self, mock_user_repository, mock_password_hasher, mock_jwt_provider, mock_refresh_token_repository
    ):
        """开启 require_email_verification 后，未验证用户被拒绝"""
        from datetime import datetime
        user = User(
            id=uuid4(),
            email=Email("test@example.com"),
            password=HashedPassword("$2b$12$hashed"),
            tenant_id=uuid4(),
            is_active=True,
            is_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_user_repository.find_by_email.return_value = user
        mock_password_hasher.verify.return_value = True

        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider,
            rate_limiter=InMemoryRateLimiter(),
            refresh_token_repository=mock_refresh_token_repository,
            tenant_repository=AsyncMock(),
            require_email_verification=True,
        )
        dto = LoginUserInputDTO(email="test@example.com", password="Password123", tenant_id=user.tenant_id)
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(dto)
