"""RBAC 关联 UseCase 测试——真实 InMemory 仓储"""
from uuid import uuid4

import pytest
from src.application.use_cases.association_use_case import (
    AssignPermissionToRoleUseCase,
    AssignRoleToUserUseCase,
    GetRolePermissionsUseCase,
    GetUserPermissionsUseCase,
    GetUserRolesUseCase,
)
from src.domain.entities.permission import Permission, PermissionAction, Resource
from src.domain.entities.role import Role, RoleName
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.in_memory.in_memory_permission_repository import InMemoryPermissionRepository
from src.infrastructure.persistence.in_memory.in_memory_role_repository import InMemoryRoleRepository
from src.infrastructure.persistence.in_memory.in_memory_user_repository import InMemoryUserRepository


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def role_repo():
    return InMemoryRoleRepository()


@pytest.fixture
def permission_repo():
    return InMemoryPermissionRepository()


async def _make_user(user_repo) -> User:
    user = User.create(
        email=Email("test@example.com"),
        password=HashedPassword("hashed"),
        tenant_id=uuid4(),
    )
    await user_repo.save(user)
    return user


@pytest.mark.asyncio
async def test_assign_role_to_user_persists(user_repo, role_repo):
    user = await _make_user(user_repo)
    role = Role.create(RoleName.USER, "regular user", tenant_id=user.tenant_id)
    await role_repo.save(role)

    use_case = AssignRoleToUserUseCase(user_repo, role_repo)
    assert await use_case.execute(user.id, role.id) is True

    role_ids = await role_repo.get_user_role_ids(user.id)
    assert role.id in role_ids

    roles = await GetUserRolesUseCase(role_repo).execute(user.id)
    assert [r.id for r in roles] == [role.id]


@pytest.mark.asyncio
async def test_assign_role_to_missing_user_raises(user_repo, role_repo):
    role = Role.create(RoleName.USER, "regular user")
    await role_repo.save(role)

    use_case = AssignRoleToUserUseCase(user_repo, role_repo)
    with pytest.raises(ValueError, match="User not found"):
        await use_case.execute(uuid4(), role.id)


@pytest.mark.asyncio
async def test_assign_role_to_missing_role_raises(user_repo, role_repo):
    user = await _make_user(user_repo)

    use_case = AssignRoleToUserUseCase(user_repo, role_repo)
    with pytest.raises(ValueError, match="Role not found"):
        await use_case.execute(user.id, uuid4())


@pytest.mark.asyncio
async def test_assign_permission_to_role_persists(role_repo, permission_repo):
    role = Role.create(RoleName.ADMIN, "admin")
    await role_repo.save(role)
    permission = Permission.create_crud(Resource.TENANT, PermissionAction.CREATE)
    await permission_repo.save(permission)

    use_case = AssignPermissionToRoleUseCase(role_repo, permission_repo)
    assert await use_case.execute(role.id, permission.id) is True

    perm_ids = await permission_repo.get_role_permission_ids(role.id)
    assert permission.id in perm_ids

    perms = await GetRolePermissionsUseCase(permission_repo).execute(role.id)
    assert [p.id for p in perms] == [permission.id]


@pytest.mark.asyncio
async def test_assign_permission_to_missing_role_raises(role_repo, permission_repo):
    permission = Permission.create_crud(Resource.USER, PermissionAction.READ)
    await permission_repo.save(permission)

    use_case = AssignPermissionToRoleUseCase(role_repo, permission_repo)
    with pytest.raises(ValueError, match="Role not found"):
        await use_case.execute(uuid4(), permission.id)


@pytest.mark.asyncio
async def test_get_user_permissions_union_dedup(user_repo, role_repo, permission_repo):
    user = await _make_user(user_repo)
    tenant_id = user.tenant_id

    role_a = Role.create(RoleName.ADMIN, "admin", tenant_id=tenant_id)
    role_b = Role.create(RoleName.USER, "user", tenant_id=tenant_id)
    await role_repo.save(role_a)
    await role_repo.save(role_b)

    p1 = Permission.create_crud(Resource.TENANT, PermissionAction.CREATE)
    p2 = Permission.create_crud(Resource.USER, PermissionAction.READ)
    p3 = Permission.create_crud(Resource.ROLE, PermissionAction.UPDATE)
    for p in (p1, p2, p3):
        await permission_repo.save(p)

    await role_repo.assign_to_user(role_a.id, user.id)
    await role_repo.assign_to_user(role_b.id, user.id)
    await permission_repo.assign_to_role(p1.id, role_a.id)
    await permission_repo.assign_to_role(p2.id, role_a.id)
    await permission_repo.assign_to_role(p2.id, role_b.id)  # 与 role_a 重复
    await permission_repo.assign_to_role(p3.id, role_b.id)

    perms = await GetUserPermissionsUseCase(role_repo, permission_repo).execute(user.id)
    perm_keys = {f"{p.resource.value}:{p.action.value}" for p in perms}

    assert perm_keys == {"tenant:create", "user:read", "role:update"}


@pytest.mark.asyncio
async def test_user_without_roles_has_no_permissions(user_repo, role_repo, permission_repo):
    user = await _make_user(user_repo)

    perms = await GetUserPermissionsUseCase(role_repo, permission_repo).execute(user.id)
    assert perms == []


@pytest.mark.asyncio
async def test_inactive_permissions_are_excluded(user_repo, role_repo, permission_repo):
    """停用的权限不应出现在用户权限集中（即使角色仍关联着它）"""
    user = await _make_user(user_repo)
    role = Role.create(RoleName.USER, "user", tenant_id=user.tenant_id)
    await role_repo.save(role)

    p_active = Permission.create_crud(Resource.USER, PermissionAction.READ)
    p_inactive = Permission.create_crud(Resource.TENANT, PermissionAction.DELETE).deactivate()
    for p in (p_active, p_inactive):
        await permission_repo.save(p)

    await role_repo.assign_to_user(role.id, user.id)
    await permission_repo.assign_to_role(p_active.id, role.id)
    await permission_repo.assign_to_role(p_inactive.id, role.id)

    perms = await GetUserPermissionsUseCase(role_repo, permission_repo).execute(user.id)
    assert {p.id for p in perms} == {p_active.id}
