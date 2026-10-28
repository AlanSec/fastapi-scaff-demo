from uuid import UUID

from src.api.schemas.role_schema import (
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleUpdateRequest,
)
from src.application.dto.role_dto import (
    CreateRoleInputDTO,
    UpdateRoleInputDTO,
)
from src.application.use_cases.role_use_case import (
    CreateRoleUseCase,
    DeleteRoleUseCase,
    GetRoleUseCase,
    ListRolesUseCase,
    UpdateRoleUseCase,
)


class RoleController:

    def __init__(
        self,
        create_use_case: CreateRoleUseCase,
        get_use_case: GetRoleUseCase,
        list_use_case: ListRolesUseCase,
        update_use_case: UpdateRoleUseCase,
        delete_use_case: DeleteRoleUseCase,
        assign_to_user_use_case=None,
    ):
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._update_use_case = update_use_case
        self._delete_use_case = delete_use_case
        self._assign_to_user_use_case = assign_to_user_use_case

    async def create(self, request: RoleCreateRequest, tenant_id: UUID) -> RoleResponse:
        dto = CreateRoleInputDTO(
            name=request.name,
            description=request.description,
        )
        result = await self._create_use_case.execute(dto, tenant_id)
        return RoleResponse(
            id=result.id, name=result.name, description=result.description,
            is_active=result.is_active, tenant_id=result.tenant_id,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def get_by_id(self, role_id: UUID, tenant_id: UUID) -> RoleResponse | None:
        result = await self._get_use_case.execute(role_id, tenant_id)
        if result is None:
            return None
        return RoleResponse(
            id=result.id, name=result.name, description=result.description,
            is_active=result.is_active, tenant_id=result.tenant_id,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def list(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> RoleListResponse:
        items = await self._list_use_case.execute(tenant_id, skip=skip, limit=limit)
        return RoleListResponse(
            items=[
                RoleResponse(
                    id=r.id, name=r.name, description=r.description,
                    is_active=r.is_active, tenant_id=r.tenant_id,
                    created_at=r.created_at, updated_at=r.updated_at,
                )
                for r in items
            ],
            total=len(items),
        )

    async def update(
        self, role_id: UUID, request: RoleUpdateRequest, tenant_id: UUID
    ) -> RoleResponse | None:
        dto = UpdateRoleInputDTO(name=request.name, description=request.description)
        result = await self._update_use_case.execute(role_id, dto, tenant_id)
        if result is None:
            return None
        return RoleResponse(
            id=result.id, name=result.name, description=result.description,
            is_active=result.is_active, tenant_id=result.tenant_id,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def delete(self, role_id: UUID, tenant_id: UUID) -> bool:
        return await self._delete_use_case.execute(role_id, tenant_id)

    async def assign_to_user(self, role_id: UUID, user_id: UUID, tenant_id: UUID) -> bool:
        if self._assign_to_user_use_case is None:
            raise RuntimeError("assign_to_user use case not initialized")
        return await self._assign_to_user_use_case.execute(user_id, role_id, tenant_id)
