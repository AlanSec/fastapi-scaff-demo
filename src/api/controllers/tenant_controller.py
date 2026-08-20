from src.api.schemas.tenant_schema import (
    TenantCreateRequest,
    TenantListResponse,
    TenantResponse,
    TenantUpdateRequest,
)
from src.application.dto.tenant_dto import (
    CreateTenantInputDTO,
    UpdateTenantInputDTO,
)
from src.application.use_cases.tenant_use_case import (
    CreateTenantUseCase,
    DeleteTenantUseCase,
    GetTenantUseCase,
    ListTenantsUseCase,
    UpdateTenantUseCase,
)


class TenantController:

    def __init__(
        self,
        create_use_case: CreateTenantUseCase,
        get_use_case: GetTenantUseCase,
        list_use_case: ListTenantsUseCase,
        update_use_case: UpdateTenantUseCase,
        delete_use_case: DeleteTenantUseCase,
    ):
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._update_use_case = update_use_case
        self._delete_use_case = delete_use_case

    async def create(self, request: TenantCreateRequest) -> TenantResponse:
        dto = CreateTenantInputDTO(name=request.name, domain=request.domain)
        result = await self._create_use_case.execute(dto)
        return TenantResponse(
            id=result.id, name=result.name, domain=result.domain,
            is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def get_by_id(self, tenant_id) -> TenantResponse | None:
        result = await self._get_use_case.execute(tenant_id)
        if result is None:
            return None
        return TenantResponse(
            id=result.id, name=result.name, domain=result.domain,
            is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def list(self, skip: int = 0, limit: int = 100) -> TenantListResponse:
        items = await self._list_use_case.execute(skip=skip, limit=limit)
        return TenantListResponse(
            items=[
                TenantResponse(
                    id=t.id, name=t.name, domain=t.domain,
                    is_active=t.is_active,
                    created_at=t.created_at, updated_at=t.updated_at,
                )
                for t in items
            ],
            total=len(items),
        )

    async def update(self, tenant_id, request: TenantUpdateRequest) -> TenantResponse | None:
        dto = UpdateTenantInputDTO(
            name=request.name, domain=request.domain,
        )
        result = await self._update_use_case.execute(tenant_id, dto)
        if result is None:
            return None
        return TenantResponse(
            id=result.id, name=result.name, domain=result.domain,
            is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def delete(self, tenant_id) -> bool:
        return await self._delete_use_case.execute(tenant_id)
