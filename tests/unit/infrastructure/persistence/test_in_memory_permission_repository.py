from uuid import uuid4

import pytest
from src.domain.entities.permission import Permission, PermissionAction, Resource
from src.infrastructure.persistence.in_memory.in_memory_permission_repository import InMemoryPermissionRepository


@pytest.mark.asyncio
async def test_save_and_find_permission():
    repo = InMemoryPermissionRepository()
    perm = Permission.create(action=PermissionAction.READ, resource=Resource.USER, description="Read user")
    saved = await repo.save(perm)
    assert saved.id == perm.id

    found = await repo.find_by_id(perm.id)
    assert found is not None


@pytest.mark.asyncio
async def test_find_by_action_and_resource():
    repo = InMemoryPermissionRepository()
    perm = Permission.create(action=PermissionAction.CREATE, resource=Resource.TENANT, description="Create tenant")
    await repo.save(perm)

    found = await repo.find_by_action_and_resource("create", "tenant")
    assert found is not None


@pytest.mark.asyncio
async def test_find_all_permissions():
    repo = InMemoryPermissionRepository()
    p1 = Permission.create(action=PermissionAction.READ, resource=Resource.USER, description="Read user")
    p2 = Permission.create(action=PermissionAction.DELETE, resource=Resource.ROLE, description="Delete role")
    await repo.save(p1)
    await repo.save(p2)

    all_perms = await repo.find_all()
    assert len(all_perms) >= 2


@pytest.mark.asyncio
async def test_delete_permission():
    repo = InMemoryPermissionRepository()
    perm = Permission.create(action=PermissionAction.UPDATE, resource=Resource.PERMISSION, description="Update perm")
    await repo.save(perm)
    assert await repo.delete(perm.id) is True
    assert await repo.find_by_id(perm.id) is None
    assert await repo.delete(uuid4()) is False


@pytest.mark.asyncio
async def test_assign_to_role_and_get_role_permission_ids():
    repo = InMemoryPermissionRepository()
    perm = Permission.create(action=PermissionAction.READ, resource=Resource.USER, description="Read user")
    await repo.save(perm)
    role_id = uuid4()

    assert await repo.assign_to_role(perm.id, role_id) is True
    assert await repo.get_role_permission_ids(role_id) == [perm.id]

    # 未保存的权限分配失败
    assert await repo.assign_to_role(uuid4(), role_id) is False

    # 删除权限后关联被清理
    await repo.delete(perm.id)
    assert await repo.get_role_permission_ids(role_id) == []


@pytest.mark.asyncio
async def test_get_permission_ids_for_roles_dedups():
    repo = InMemoryPermissionRepository()
    p1 = Permission.create_crud(Resource.USER, PermissionAction.READ)
    p2 = Permission.create_crud(Resource.TENANT, PermissionAction.CREATE)
    await repo.save(p1)
    await repo.save(p2)

    role_a, role_b = uuid4(), uuid4()
    await repo.assign_to_role(p1.id, role_a)
    await repo.assign_to_role(p2.id, role_a)
    await repo.assign_to_role(p2.id, role_b)  # 与 role_a 重复

    ids = await repo.get_permission_ids_for_roles([role_a, role_b])
    assert sorted(ids) == sorted([p1.id, p2.id])

    assert await repo.get_permission_ids_for_roles([]) == []


@pytest.mark.asyncio
async def test_find_by_ids_batch():
    repo = InMemoryPermissionRepository()
    p1 = Permission.create_crud(Resource.USER, PermissionAction.READ)
    p2 = Permission.create_crud(Resource.ROLE, PermissionAction.UPDATE)
    await repo.save(p1)
    await repo.save(p2)

    found = await repo.find_by_ids([p1.id, p2.id, uuid4()])
    assert {p.id for p in found} == {p1.id, p2.id}

    assert await repo.find_by_ids([]) == []
