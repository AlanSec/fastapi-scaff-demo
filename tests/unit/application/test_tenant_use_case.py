from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.application.dto.tenant_dto import (
    CreateTenantInputDTO,
    TenantOutputDTO,
    UpdateTenantInputDTO,
)
from src.application.use_cases.tenant_use_case import (
    CreateTenantUseCase,
    DeleteTenantUseCase,
    ListTenantsUseCase,
    UpdateTenantUseCase,
)
from src.domain.entities.tenant import Tenant


class TestCreateTenantUseCase:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_repo):
        return CreateTenantUseCase(tenant_repository=mock_repo)

    @pytest.mark.asyncio
    async def test_create_tenant_success(self, use_case, mock_repo):
        mock_repo.find_by_name.return_value = None
        dto = CreateTenantInputDTO(name="Test Tenant", domain="test.example.com")
        result = await use_case.execute(dto)
        assert isinstance(result, TenantOutputDTO)
        assert result.name == "Test Tenant"
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self, use_case, mock_repo):
        mock_repo.find_by_name.return_value = MagicMock(spec=Tenant)
        dto = CreateTenantInputDTO(name="Duplicate", domain="dup.com")
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(dto)


class TestListTenantsUseCase:
    @pytest.mark.asyncio
    async def test_list_tenants(self):
        mock_repo = AsyncMock()
        mock_repo.find_all.return_value = []
        use_case = ListTenantsUseCase(tenant_repository=mock_repo)
        result = await use_case.execute()
        assert isinstance(result, list)


class TestUpdateTenantUseCase:
    @pytest.mark.asyncio
    async def test_update_tenant(self):
        mock_repo = AsyncMock()
        tenant = Tenant.create(name="Old", domain="old.com")
        mock_repo.find_by_id.return_value = tenant
        use_case = UpdateTenantUseCase(tenant_repository=mock_repo)
        dto = UpdateTenantInputDTO(name="New")
        result = await use_case.execute(tenant.id, dto)
        assert result is not None
        assert result.name == "New"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.find_by_id.return_value = None
        use_case = UpdateTenantUseCase(tenant_repository=mock_repo)
        dto = UpdateTenantInputDTO(name="New")
        result = await use_case.execute(uuid4(), dto)
        assert result is None


class TestDeleteTenantUseCase:
    @pytest.mark.asyncio
    async def test_delete_tenant(self):
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        use_case = DeleteTenantUseCase(tenant_repository=mock_repo)
        assert await use_case.execute(uuid4()) is True
        assert await use_case.execute(uuid4()) is True
