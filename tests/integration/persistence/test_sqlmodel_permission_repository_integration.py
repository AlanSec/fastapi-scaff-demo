"""SQLModel 权限/角色仓储批量查询集成测试——验证 N+1 优化方法与 RBAC 全链路"""
from uuid import uuid4

import pytest
from src.application.use_cases.association_use_case import (
    GetRolePermissionsUseCase,
    GetUserPermissionsUseCase,
    GetUserRolesUseCase,
)
from src.domain.entities.permission import Permission, PermissionAction, Resource
from src.domain.entities.role import Role, RoleName
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_permission_repository import (
    SQLModelPermissionRepository,
)
from src.infrastructure.persistence.sqlmodel.repositories.sqlmodel_role_repository import SQLModelRoleRepository
from tests.integration.conftest import TestingSessionLocal


@pytest.fixture
def permission_repo():
    return SQLModelPermissionRepository(TestingSessionLocal)


@pytest.fixture
def role_repo():
    return SQLModelRoleRepository(TestingSessionLocal)


async def _seed_rbac(default_tenant, test_user, role_repo, permission_repo):
    """建 2 角色 + 3 权限（1 个停用），角色-用户/权限-角色各分配好"""
    role_a = Role.create(RoleName.ADMIN, "admin", tenant_id=default_tenant.id)
    role_b = Role.create(RoleName.USER, "user", tenant_id=default_tenant.id)
    await role_repo.save(role_a)
    await role_repo.save(role_b)

    p1 = Permission.create_crud(Resource.TENANT, PermissionAction.CREATE)
    p2 = Permission.create_crud(Resource.USER, PermissionAction.READ)
    p3 = Permission.create_crud(Resource.ROLE, PermissionAction.UPDATE).deactivate()
    for p in (p1, p2, p3):
        await permission_repo.save(p)

    await role_repo.assign_to_user(role_a.id, test_user.id)
    await role_repo.assign_to_user(role_b.id, test_user.id)
    await permission_repo.assign_to_role(p1.id, role_a.id)
    await permission_repo.assign_to_role(p2.id, role_a.id)
    await permission_repo.assign_to_role(p2.id, role_b.id)  # 重复分配
    await permission_repo.assign_to_role(p3.id, role_b.id)  # 停用权限
    return role_a, role_b, p1, p2, p3


@pytest.mark.asyncio
async def test_get_user_permissions_dedup_and_active_only(default_tenant, test_user, role_repo, permission_repo):
    await _seed_rbac(default_tenant, test_user, role_repo, permission_repo)

    perms = await GetUserPermissionsUseCase(role_repo, permission_repo).execute(test_user.id)
    keys = {f"{p.resource.value}:{p.action.value}" for p in perms}

    assert keys == {"tenant:create", "user:read"}  # role:update 已停用，被过滤


@pytest.mark.asyncio
async def test_get_user_permissions_no_roles(default_tenant, role_repo, permission_repo):
    perms = await GetUserPermissionsUseCase(role_repo, permission_repo).execute(uuid4())
    assert perms == []


@pytest.mark.asyncio
async def test_get_role_permissions_batch(default_tenant, test_user, role_repo, permission_repo):
    role_a, _, p1, p2, _ = await _seed_rbac(default_tenant, test_user, role_repo, permission_repo)

    perms = await GetRolePermissionsUseCase(permission_repo).execute(role_a.id)
    assert {p.id for p in perms} == {p1.id, p2.id}


@pytest.mark.asyncio
async def test_get_user_roles_batch(default_tenant, test_user, role_repo, permission_repo):
    role_a, role_b, _, _, _ = await _seed_rbac(default_tenant, test_user, role_repo, permission_repo)

    roles = await GetUserRolesUseCase(role_repo).execute(test_user.id)
    assert {r.id for r in roles} == {role_a.id, role_b.id}


@pytest.mark.asyncio
async def test_permission_find_by_ids_batch(default_tenant, test_user, role_repo, permission_repo):
    _, _, p1, p2, p3 = await _seed_rbac(default_tenant, test_user, role_repo, permission_repo)

    found = await permission_repo.find_by_ids([p1.id, p2.id, p3.id, uuid4()])
    assert {p.id for p in found} == {p1.id, p2.id, p3.id}

    assert await permission_repo.find_by_ids([]) == []


@pytest.mark.asyncio
async def test_role_find_by_ids_batch(default_tenant, test_user, role_repo, permission_repo):
    role_a, role_b, _, _, _ = await _seed_rbac(default_tenant, test_user, role_repo, permission_repo)

    found = await role_repo.find_by_ids([role_a.id, role_b.id, uuid4()])
    assert {r.id for r in found} == {role_a.id, role_b.id}

    assert await role_repo.find_by_ids([]) == []
