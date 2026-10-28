from uuid import UUID

from src.api.schemas.user_admin_schema import (
    AdminCreateUserRequest,
    AdminUpdateCurrentUserRequest,
    AdminUpdateUserRequest,
    UserAdminListResponse,
    UserAdminResponse,
)
from src.application.dto.user_admin_dto import (
    AdminCreateUserInputDTO,
    AdminUpdateCurrentUserInputDTO,
    AdminUpdateUserInputDTO,
)
from src.application.use_cases.user_admin_use_case import (
    AdminCreateUserUseCase,
    AdminDeleteUserUseCase,
    AdminGetCurrentUserUseCase,
    AdminGetUserUseCase,
    AdminListUsersUseCase,
    AdminUpdateCurrentUserUseCase,
    AdminUpdateUserUseCase,
)


class UserAdminController:

    def __init__(
        self,
        create_use_case: AdminCreateUserUseCase,
        list_use_case: AdminListUsersUseCase,
        get_use_case: AdminGetUserUseCase,
        update_use_case: AdminUpdateUserUseCase,
        delete_use_case: AdminDeleteUserUseCase,
        get_current_use_case: AdminGetCurrentUserUseCase,
        update_current_use_case: AdminUpdateCurrentUserUseCase,
    ):
        self._create_use_case = create_use_case
        self._list_use_case = list_use_case
        self._get_use_case = get_use_case
        self._update_use_case = update_use_case
        self._delete_use_case = delete_use_case
        self._get_current_use_case = get_current_use_case
        self._update_current_use_case = update_current_use_case

    async def create(self, request: AdminCreateUserRequest, tenant_id: UUID) -> UserAdminResponse:
        dto = AdminCreateUserInputDTO(
            email=request.email,
            password=request.password,
            is_superuser=request.is_superuser,
        )
        result = await self._create_use_case.execute(dto, tenant_id)
        return self._to_response(result)

    async def list(self, tenant_id: UUID, skip: int = 0, limit: int = 100) -> UserAdminListResponse:
        items = await self._list_use_case.execute(tenant_id, skip=skip, limit=limit)
        return UserAdminListResponse(
            items=[self._to_response(r) for r in items],
            total=len(items),
        )

    async def get_by_id(self, user_id: UUID, tenant_id: UUID) -> UserAdminResponse:
        result = await self._get_use_case.execute(user_id, tenant_id)
        if result is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return self._to_response(result)

    async def update(
        self, user_id: UUID, request: AdminUpdateUserRequest, tenant_id: UUID
    ) -> UserAdminResponse:
        dto = AdminUpdateUserInputDTO(
            email=request.email,
            is_active=request.is_active,
            is_superuser=request.is_superuser,
        )
        result = await self._update_use_case.execute(user_id, dto, tenant_id)
        if result is None:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return self._to_response(result)

    async def delete(self, user_id: UUID, tenant_id: UUID) -> bool:
        return await self._delete_use_case.execute(user_id, tenant_id)

    async def get_me(self, user_id: UUID, tenant_id: UUID) -> UserAdminResponse:
        result = await self._get_current_use_case.execute(user_id, tenant_id)
        return self._to_response(result)

    async def update_me(
        self, user_id: UUID, request: AdminUpdateCurrentUserRequest, tenant_id: UUID
    ) -> UserAdminResponse:
        dto = AdminUpdateCurrentUserInputDTO(email=request.email)
        result = await self._update_current_use_case.execute(user_id, dto, tenant_id)
        return self._to_response(result)

    @staticmethod
    def _to_response(dto) -> UserAdminResponse:
        return UserAdminResponse(
            id=dto.id, email=dto.email,
            is_active=dto.is_active, is_verified=dto.is_verified,
            is_superuser=dto.is_superuser, tenant_id=dto.tenant_id,
            created_at=dto.created_at, updated_at=dto.updated_at,
            last_login_at=dto.last_login_at,
        )
