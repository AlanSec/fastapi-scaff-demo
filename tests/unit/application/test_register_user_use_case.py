import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.dto.auth_dto import RegisterUserInputDTO, RegisterUserOutputDTO
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


class TestRegisterUserUseCase:
    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_password_hasher(self):
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_user_repository, mock_password_hasher):
        return RegisterUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher
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