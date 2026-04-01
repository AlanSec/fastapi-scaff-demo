import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.dto.auth_dto import LoginUserInputDTO, LoginUserOutputDTO
from src.application.use_cases.login_user_use_case import LoginUserUseCase
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


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
    def use_case(self, mock_user_repository, mock_password_hasher, mock_jwt_provider):
        return LoginUserUseCase(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
            jwt_provider=mock_jwt_provider
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
    async def test_execute_raises_when_user_not_found(self, use_case, mock_user_repository):
        mock_user_repository.find_by_email.return_value = None
        
        input_dto = LoginUserInputDTO(
            email="notfound@example.com",
            password="Password123",
            tenant_id=uuid4()
        )
        
        with pytest.raises(ValueError, match="Invalid credentials"):
            await use_case.execute(input_dto)
    
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
        
        with pytest.raises(ValueError, match="User is inactive"):
            await use_case.execute(input_dto)