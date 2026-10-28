from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.user_admin_dto import (
    AdminCreateUserInputDTO,
    UserAdminOutputDTO,
)
from src.application.use_cases.user_admin_use_case import (
    AdminCreateUserUseCase,
    AdminDeleteUserUseCase,
    AdminGetUserUseCase,
    AdminListUsersUseCase,
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
        tenant_id = uuid4()
        dto = AdminCreateUserInputDTO(
            email="new@example.com", password="Pass1234", is_superuser=False,
        )
        result = await use_case.execute(dto, tenant_id)
        assert isinstance(result, UserAdminOutputDTO)
        assert result.email == "new@example.com"
        assert result.tenant_id == tenant_id
        # 创建的用户必须归属于调用方租户（不是 DTO 指定）
        saved_user = mock_repo.save.call_args.args[0]
        assert saved_user.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_email.return_value = MagicMock(spec=User)
        dto = AdminCreateUserInputDTO(
            email="dup@example.com", password="Pass1234",
        )
        with pytest.raises(ValueError, match="already registered"):
            await use_case.execute(dto, uuid4())


class TestAdminListUsersUseCase:
    @pytest.mark.asyncio
    async def test_list_users_scoped_to_tenant(self):
        """列表必须按租户过滤（find_by_tenant）"""
        mock_repo = AsyncMock()
        mock_repo.find_by_tenant.return_value = []
        use_case = AdminListUsersUseCase(user_repository=mock_repo)
        tenant_id = uuid4()
        result = await use_case.execute(tenant_id, skip=0, limit=50)
        assert isinstance(result, list)
        mock_repo.find_by_tenant.assert_awaited_once_with(tenant_id, skip=0, limit=50)


class TestAdminGetUserUseCase:
    @pytest.mark.asyncio
    async def test_get_user_found(self):
        mock_repo = AsyncMock()
        from datetime import datetime
        tenant_id = uuid4()
        user = User(id=uuid4(), email=Email("u@t.com"), password=HashedPassword("$2b$12$x"),
                    tenant_id=tenant_id, is_active=True, is_verified=True, is_superuser=False,
                    created_at=datetime.now(), updated_at=datetime.now())
        mock_repo.find_by_id.return_value = user
        use_case = AdminGetUserUseCase(user_repository=mock_repo)
        result = await use_case.execute(user.id, tenant_id)
        assert result is not None
        assert result.email == "u@t.com"
        mock_repo.find_by_id.assert_awaited_once_with(user.id, tenant_id)

    @pytest.mark.asyncio
    async def test_get_user_cross_tenant_returns_none(self):
        """跨租户查询用户 → None（路由层映射 404）"""
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = AdminGetUserUseCase(user_repository=mock_repo)
        assert await use_case.execute(uuid4(), uuid4()) is None


class TestAdminDeleteUserUseCase:
    @pytest.mark.asyncio
    async def test_delete_user(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = AdminDeleteUserUseCase(user_repository=mock_repo)
        tenant_id = uuid4()
        assert await use_case.execute(uuid4(), tenant_id) is True
        mock_repo.delete.assert_awaited_once()
        assert mock_repo.delete.call_args.args[1] == tenant_id
