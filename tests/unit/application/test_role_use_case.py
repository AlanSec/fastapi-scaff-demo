from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.role_dto import (
    CreateRoleInputDTO,
    RoleOutputDTO,
    UpdateRoleInputDTO,
)
from src.application.use_cases.role_use_case import (
    CreateRoleUseCase,
    DeleteRoleUseCase,
    ListRolesUseCase,
    UpdateRoleUseCase,
)
from src.domain.entities.role import Role


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
        tenant_id = uuid4()
        dto = CreateRoleInputDTO(name="admin", description="Admin role")
        result = await use_case.execute(dto, tenant_id)
        assert isinstance(result, RoleOutputDTO)
        assert result.name == "admin"
        assert result.tenant_id == tenant_id
        mock_repo.save.assert_called_once()
        # 保存的角色必须归属于调用方租户（不是随机 UUID）
        saved_role = mock_repo.save.call_args.args[0]
        assert saved_role.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_create_role_with_custom_name(self, use_case, mock_repo):
        """自定义角色名（不再受 RoleName 枚举限制）"""
        mock_repo.find_by_name.return_value = None
        dto = CreateRoleInputDTO(name="tenant-manager", description="Custom role")
        result = await use_case.execute(dto, uuid4())
        assert result.name == "tenant-manager"

    @pytest.mark.asyncio
    async def test_create_role_empty_name_raises(self, use_case):
        dto = CreateRoleInputDTO(name="   ", description="Empty")
        with pytest.raises(ValueError, match="cannot be empty"):
            await use_case.execute(dto, uuid4())

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_name.return_value = MagicMock(spec=Role)
        dto = CreateRoleInputDTO(name="admin", description="Dup")
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(dto, uuid4())


class TestListRolesUseCase:
    @pytest.mark.asyncio
    async def test_list_roles_scoped_to_tenant(self):
        """列表必须按租户过滤（find_by_tenant）"""
        mock_repo = AsyncMock()
        mock_repo.find_by_tenant.return_value = []
        use_case = ListRolesUseCase(role_repository=mock_repo)
        tenant_id = uuid4()
        result = await use_case.execute(tenant_id, skip=0, limit=50)
        assert isinstance(result, list)
        mock_repo.find_by_tenant.assert_awaited_once_with(tenant_id, skip=0, limit=50)


class TestUpdateRoleUseCase:
    @pytest.mark.asyncio
    async def test_update_role(self):
        mock_repo = AsyncMock()
        tenant_id = uuid4()
        role = Role.create(name="user", description="Old", tenant_id=tenant_id)
        mock_repo.find_by_id.return_value = role
        use_case = UpdateRoleUseCase(role_repository=mock_repo)
        dto = UpdateRoleInputDTO(description="New desc")
        result = await use_case.execute(role.id, dto, tenant_id)
        assert result is not None
        assert result.description == "New desc"
        mock_repo.find_by_id.assert_awaited_once_with(role.id, tenant_id)

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = UpdateRoleUseCase(role_repository=mock_repo)
        dto = UpdateRoleInputDTO(description="New")
        result = await use_case.execute(uuid4(), dto, uuid4())
        assert result is None


class TestDeleteRoleUseCase:
    @pytest.mark.asyncio
    async def test_delete_role(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = DeleteRoleUseCase(role_repository=mock_repo)
        tenant_id = uuid4()
        assert await use_case.execute(uuid4(), tenant_id) is True
        mock_repo.delete.assert_awaited_once_with(mock_repo.delete.call_args.args[0], tenant_id)
