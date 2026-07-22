import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.dto.user_admin_dto import (
    AdminCreateUserInputDTO, AdminUpdateUserInputDTO, UserAdminOutputDTO,
)
from src.application.use_cases.user_admin_use_case import (
    AdminCreateUserUseCase, AdminListUsersUseCase,
    AdminGetUserUseCase, AdminUpdateUserUseCase, AdminDeleteUserUseCase,
)
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


class TestAdminCreateUserUseCase:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_hasher(self):
        return MagicMock()

    @pytest.fixture
    def use_case(self, mock_repo, mock_hasher):
        return AdminCreateUserUseCase(user_repository=mock_repo, password_hasher=mock_hasher)

    @pytest.mark.asyncio
    async def test_create_user_success(self, use_case, mock_repo, mock_hasher):
        mock_repo.find_by_email.return_value = None
        mock_hasher.hash.return_value = HashedPassword("$2b$12$hashed")
        dto = AdminCreateUserInputDTO(
            email="new@example.com", password="Pass1234",
            tenant_id=uuid4(), is_superuser=False,
        )
        result = await use_case.execute(dto)
        assert isinstance(result, UserAdminOutputDTO)
        assert result.email == "new@example.com"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_email.return_value = MagicMock(spec=User)
        dto = AdminCreateUserInputDTO(
            email="dup@example.com", password="Pass1234", tenant_id=uuid4(),
        )
        with pytest.raises(ValueError, match="already registered"):
            await use_case.execute(dto)


class TestAdminListUsersUseCase:
    @pytest.mark.asyncio
    async def test_list_users(self):
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        use_case = AdminListUsersUseCase(user_repository=mock_repo)
        result = await use_case.execute()
        assert isinstance(result, list)


class TestAdminGetUserUseCase:
    @pytest.mark.asyncio
    async def test_get_user_found(self):
        mock_repo = AsyncMock()
        from datetime import datetime
        user = User(id=uuid4(), email=Email("u@t.com"), password=HashedPassword("$2b$12$x"),
                    tenant_id=uuid4(), is_active=True, is_verified=True, is_superuser=False,
                    created_at=datetime.now(), updated_at=datetime.now())
        mock_repo.find_by_id.return_value = user
        use_case = AdminGetUserUseCase(user_repository=mock_repo)
        result = await use_case.execute(user.id)
        assert result is not None
        assert result.email == "u@t.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = AdminGetUserUseCase(user_repository=mock_repo)
        assert await use_case.execute(uuid4()) is None


class TestAdminDeleteUserUseCase:
    @pytest.mark.asyncio
    async def test_delete_user(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = AdminDeleteUserUseCase(user_repository=mock_repo)
        assert await use_case.execute(uuid4()) is True
