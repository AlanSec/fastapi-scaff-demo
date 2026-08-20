from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.permission_dto import (
    CreatePermissionInputDTO,
    PermissionOutputDTO,
    UpdatePermissionInputDTO,
)
from src.application.use_cases.permission_use_case import (
    CreatePermissionUseCase,
    DeletePermissionUseCase,
    ListPermissionsUseCase,
    UpdatePermissionUseCase,
)
from src.domain.entities.permission import Permission, PermissionAction, Resource


class TestCreatePermissionUseCase:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repo):
        return CreatePermissionUseCase(permission_repository=mock_repo)

    @pytest.mark.asyncio
    async def test_create_permission_success(self, use_case, mock_repo):
        mock_repo.find_by_action_and_resource.return_value = None
        dto = CreatePermissionInputDTO(action="read", resource="user", description="Read user")
        result = await use_case.execute(dto)
        assert isinstance(result, PermissionOutputDTO)
        assert result.action == "read"
        assert result.resource == "user"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_action_and_resource.return_value = MagicMock(spec=Permission)
        dto = CreatePermissionInputDTO(action="read", resource="user", description="Dup")
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(dto)


class TestListPermissionsUseCase:
    @pytest.mark.asyncio
    async def test_list_permissions(self):
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        use_case = ListPermissionsUseCase(permission_repository=mock_repo)
        result = await use_case.execute()
        assert isinstance(result, list)


class TestUpdatePermissionUseCase:
    @pytest.mark.asyncio
    async def test_update_permission(self):
        mock_repo = AsyncMock()
        perm = Permission.create(action=PermissionAction.READ, resource=Resource.USER, description="Old desc")
        mock_repo.find_by_id.return_value = perm
        use_case = UpdatePermissionUseCase(permission_repository=mock_repo)
        dto = UpdatePermissionInputDTO(description="New desc")
        result = await use_case.execute(perm.id, dto)
        assert result is not None
        assert result.description == "New desc"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = UpdatePermissionUseCase(permission_repository=mock_repo)
        dto = UpdatePermissionInputDTO(description="New")
        result = await use_case.execute(uuid4(), dto)
        assert result is None


class TestDeletePermissionUseCase:
    @pytest.mark.asyncio
    async def test_delete_permission(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = DeletePermissionUseCase(permission_repository=mock_repo)
        assert await use_case.execute(uuid4()) is True
