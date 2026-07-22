import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.dto.role_dto import (
    CreateRoleInputDTO, UpdateRoleInputDTO, RoleOutputDTO,
)
from src.application.use_cases.role_use_case import (
    CreateRoleUseCase, ListRolesUseCase, UpdateRoleUseCase,
    DeleteRoleUseCase, GetRoleUseCase,
)
from src.domain.entities.role import Role, RoleName


class TestCreateRoleUseCase:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repo):
        return CreateRoleUseCase(role_repository=mock_repo)

    @pytest.mark.asyncio
    async def test_create_role_success(self, use_case, mock_repo):
        mock_repo.find_by_name.return_value = None
        dto = CreateRoleInputDTO(name="admin", description="Admin role", tenant_id=uuid4())
        result = await use_case.execute(dto)
        assert isinstance(result, RoleOutputDTO)
        assert result.name == "admin"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_name.return_value = MagicMock(spec=Role)
        dto = CreateRoleInputDTO(name="admin", description="Dup", tenant_id=uuid4())
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(dto)


class TestListRolesUseCase:
    @pytest.mark.asyncio
    async def test_list_roles(self):
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        use_case = ListRolesUseCase(role_repository=mock_repo)
        result = await use_case.execute()
        assert isinstance(result, list)


class TestUpdateRoleUseCase:
    @pytest.mark.asyncio
    async def test_update_role(self):
        mock_repo = AsyncMock()
        role = Role.create(name=RoleName.USER, description="Old", tenant_id=uuid4())
        mock_repo.find_by_id.return_value = role
        use_case = UpdateRoleUseCase(role_repository=mock_repo)
        dto = UpdateRoleInputDTO(description="New desc")
        result = await use_case.execute(role.id, dto)
        assert result is not None
        assert result.description == "New desc"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = UpdateRoleUseCase(role_repository=mock_repo)
        dto = UpdateRoleInputDTO(description="New")
        result = await use_case.execute(uuid4(), dto)
        assert result is None


class TestDeleteRoleUseCase:
    @pytest.mark.asyncio
    async def test_delete_role(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = DeleteRoleUseCase(role_repository=mock_repo)
        assert await use_case.execute(uuid4()) is True
