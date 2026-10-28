from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.auth_dto import RegisterUserInputDTO, RegisterUserOutputDTO
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.domain.entities.user import User
from src.domain.value_objects.password import HashedPassword


class TestRegisterUserUseCase:
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_hasher(self):
        # PasswordHasher.hash 是同步方法
        return MagicMock()

    @pytest.fixture
    def mock_tenant_repository(self):
        repo = AsyncMock()
        repo.find_by_id.return_value = MagicMock(is_active=True)
        return repo

    @pytest.fixture
    def use_case(self, mock_user_repository, mock_password_hasher, mock_tenant_repository):
        return RegisterUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            tenant_repository=mock_tenant_repository,
        )

    @pytest.mark.asyncio
    async def test_execute_creates_user_successfully(self, use_case, mock_user_repository, mock_password_hasher):
        email = "test@example.com"
        password = "Password123"
        tenant_id = uuid4()
        hashed = HashedPassword("$2b$12$hashedpassword")

        mock_user_repository.find_by_email.return_value = None
        mock_password_hasher.hash.return_value = hashed
        mock_user_repository.save.return_value = None

        input_dto = RegisterUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        result = await use_case.execute(input_dto)

        assert isinstance(result, RegisterUserOutputDTO)
        assert result.email == email
        assert result.tenant_id == tenant_id
        assert result.is_verified is False
        mock_user_repository.find_by_email.assert_called_once_with(email, tenant_id)
        mock_user_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_raises_when_tenant_missing_or_inactive(
        self, use_case, mock_user_repository, mock_tenant_repository
    ):
        """指定不存在的租户注册 → 拒绝（防外键脏数据 / 垃圾租户）"""
        mock_tenant_repository.find_by_id.return_value = None
        input_dto = RegisterUserInputDTO(
            email="nobody@example.com", password="Password123", tenant_id=uuid4()
        )
        with pytest.raises(ValueError, match="Tenant not found or inactive"):
            await use_case.execute(input_dto)
        mock_user_repository.find_by_email.assert_not_called()

        # 停用租户同样拒绝
        mock_tenant_repository.find_by_id.return_value = MagicMock(is_active=False)
        with pytest.raises(ValueError, match="Tenant not found or inactive"):
            await use_case.execute(input_dto)

    @pytest.mark.asyncio
    async def test_execute_raises_when_email_exists(self, use_case, mock_user_repository):
        email = "test@example.com"
        password = "Password123"
        tenant_id = uuid4()

        existing_user = MagicMock(spec=User)
        mock_user_repository.find_by_email.return_value = existing_user

        input_dto = RegisterUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        with pytest.raises(ValueError, match="User already exists"):
            await use_case.execute(input_dto)

    @pytest.mark.asyncio
    async def test_execute_raises_on_weaker_password(self, use_case):
        email = "test@example.com"
        password = "weak"
        tenant_id = uuid4()

        input_dto = RegisterUserInputDTO(
            email=email,
            password=password,
            tenant_id=tenant_id
        )

        with pytest.raises(ValueError, match="password must be at least 8 characters"):
            await use_case.execute(input_dto)

    @pytest.mark.asyncio
    async def test_execute_without_tenant_creates_personal_tenant(
        self, use_case, mock_user_repository, mock_password_hasher, mock_tenant_repository
    ):
        """未指定租户时自动创建独立租户"""
        hashed = HashedPassword("$2b$12$hashedpassword")
        mock_user_repository.find_by_email.return_value = None
        mock_password_hasher.hash.return_value = hashed
        mock_user_repository.save.return_value = None

        input_dto = RegisterUserInputDTO(email="open@example.com", password="Password123")

        result = await use_case.execute(input_dto)

        # 自动创建了租户，用户归属该租户
        mock_tenant_repository.save.assert_awaited_once()
        created_tenant = mock_tenant_repository.save.await_args.args[0]
        assert result.tenant_id == created_tenant.id
        assert created_tenant.name.startswith("tenant-")
        assert result.email == "open@example.com"

    @pytest.mark.asyncio
    async def test_rolls_back_created_tenant_on_save_failure(
        self, use_case, mock_user_repository, mock_password_hasher, mock_tenant_repository
    ):
        """自动创建租户后保存用户失败 → 补偿删除孤儿租户（防脏数据）"""
        hashed = HashedPassword("$2b$12$hashedpassword")
        mock_user_repository.find_by_email.return_value = None
        mock_password_hasher.hash.return_value = hashed
        mock_user_repository.save.side_effect = Exception("db error")

        input_dto = RegisterUserInputDTO(email="fail@example.com", password="Password123")
        with pytest.raises(Exception, match="db error"):
            await use_case.execute(input_dto)

        created_tenant = mock_tenant_repository.save.await_args.args[0]
        mock_tenant_repository.delete.assert_awaited_once_with(created_tenant.id)

    @pytest.mark.asyncio
    async def test_rolls_back_created_tenant_on_duplicate_email(
        self, use_case, mock_user_repository, mock_tenant_repository
    ):
        """自动创建租户后发现邮箱已存在 → 补偿删除孤儿租户"""
        mock_user_repository.find_by_email.return_value = MagicMock(spec=User)

        input_dto = RegisterUserInputDTO(email="dup@example.com", password="Password123")
        with pytest.raises(ValueError, match="User already exists"):
            await use_case.execute(input_dto)

        created_tenant = mock_tenant_repository.save.await_args.args[0]
        mock_tenant_repository.delete.assert_awaited_once_with(created_tenant.id)
