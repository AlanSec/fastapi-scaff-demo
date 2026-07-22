import pytest
from uuid import uuid4

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
