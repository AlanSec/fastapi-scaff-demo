from uuid import UUID

from src.api.schemas.permission_schema import (
    PermissionCreateRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from src.application.dto.permission_dto import (
    CreatePermissionInputDTO,
    UpdatePermissionInputDTO,
)
from src.application.use_cases.permission_use_case import (
    CreatePermissionUseCase,
    DeletePermissionUseCase,
    GetPermissionUseCase,
    ListPermissionsUseCase,
    UpdatePermissionUseCase,
)


class PermissionController:

    def __init__(
        self,
        create_use_case: CreatePermissionUseCase,
        get_use_case: GetPermissionUseCase,
        list_use_case: ListPermissionsUseCase,
        update_use_case: UpdatePermissionUseCase,
        delete_use_case: DeletePermissionUseCase,
        assign_to_role_use_case=None,
    ):
        self._create_use_case = create_use_case
        self._get_use_case = get_use_case
        self._list_use_case = list_use_case
        self._update_use_case = update_use_case
        self._delete_use_case = delete_use_case
        self._assign_to_role_use_case = assign_to_role_use_case

    async def create(self, request: PermissionCreateRequest) -> PermissionResponse:
        dto = CreatePermissionInputDTO(
            action=request.action,
            resource=request.resource,
            description=request.description,
        )
        result = await self._create_use_case.execute(dto)
        return PermissionResponse(
            id=result.id, action=result.action, resource=result.resource,
            description=result.description, is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def get_by_id(self, permission_id: UUID) -> PermissionResponse | None:
        result = await self._get_use_case.execute(permission_id)
        if result is None:
            return None
        return PermissionResponse(
            id=result.id, action=result.action, resource=result.resource,
            description=result.description, is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def list(self, skip: int = 0, limit: int = 100) -> PermissionListResponse:
        items = await self._list_use_case.execute(skip=skip, limit=limit)
        return PermissionListResponse(
            items=[
                PermissionResponse(
                    id=p.id, action=p.action, resource=p.resource,
                    description=p.description, is_active=p.is_active,
                    created_at=p.created_at, updated_at=p.updated_at,
                )
                for p in items
            ],
            total=len(items),
        )

    async def update(self, permission_id: UUID, request: PermissionUpdateRequest) -> PermissionResponse | None:
        dto = UpdatePermissionInputDTO(description=request.description)
        result = await self._update_use_case.execute(permission_id, dto)
        if result is None:
            return None
        return PermissionResponse(
            id=result.id, action=result.action, resource=result.resource,
            description=result.description, is_active=result.is_active,
            created_at=result.created_at, updated_at=result.updated_at,
        )

    async def delete(self, permission_id: UUID) -> bool:
        return await self._delete_use_case.execute(permission_id)

    async def assign_to_role(self, permission_id: UUID, role_id: UUID) -> bool:
        if self._assign_to_role_use_case is None:
            raise RuntimeError("assign_to_role use case not initialized")
        return await self._assign_to_role_use_case.execute(role_id, permission_id)
