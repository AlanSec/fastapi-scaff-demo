from uuid import uuid4

import pytest
from src.domain.entities.role import Role, RoleName
from src.infrastructure.persistence.in_memory.in_memory_role_repository import InMemoryRoleRepository


@pytest.mark.asyncio
async def test_save_and_find_role():
    repo = InMemoryRoleRepository()
    tenant_id = uuid4()
    role = Role.create(name=RoleName.ADMIN, description="Admin role", tenant_id=tenant_id)
    saved = await repo.save(role)
    assert saved.id == role.id

    found = await repo.find_by_id(role.id)
    assert found is not None


@pytest.mark.asyncio
async def test_find_by_name():
    repo = InMemoryRoleRepository()
    tenant_id = uuid4()
    role = Role.create(name=RoleName.USER, description="User role", tenant_id=tenant_id)
    await repo.save(role)

    found = await repo.find_by_name("user", tenant_id)
    assert found is not None


@pytest.mark.asyncio
async def test_find_by_tenant():
    repo = InMemoryRoleRepository()
    tid = uuid4()
    r1 = Role.create(name=RoleName.ADMIN, description="Admin", tenant_id=tid)
    r2 = Role.create(name=RoleName.USER, description="User", tenant_id=tid)
    await repo.save(r1)
    await repo.save(r2)

    roles = await repo.find_by_tenant(tid)
    assert len(roles) == 2


@pytest.mark.asyncio
async def test_delete_role():
    repo = InMemoryRoleRepository()
    role = Role.create(name=RoleName.GUEST, description="Guest", tenant_id=uuid4())
    await repo.save(role)
    assert await repo.delete(role.id) is True
    assert await repo.find_by_id(role.id) is None
    assert await repo.delete(uuid4()) is False


@pytest.mark.asyncio
async def test_assign_to_user_and_get_user_role_ids():
    repo = InMemoryRoleRepository()
    role = Role.create(name=RoleName.USER, description="User", tenant_id=uuid4())
    await repo.save(role)
    user_id = uuid4()

    assert await repo.assign_to_user(role.id, user_id) is True
    assert await repo.get_user_role_ids(user_id) == [role.id]

    # 未保存的角色分配失败
    assert await repo.assign_to_user(uuid4(), user_id) is False

    # 删除角色后关联被清理
    await repo.delete(role.id)
    assert await repo.get_user_role_ids(user_id) == []


@pytest.mark.asyncio
async def test_find_by_ids_batch():
    repo = InMemoryRoleRepository()
    tid = uuid4()
    r1 = Role.create(name=RoleName.ADMIN, description="Admin", tenant_id=tid)
    r2 = Role.create(name=RoleName.USER, description="User", tenant_id=tid)
    await repo.save(r1)
    await repo.save(r2)

    found = await repo.find_by_ids([r1.id, r2.id, uuid4()])
    assert {r.id for r in found} == {r1.id, r2.id}

    assert await repo.find_by_ids([]) == []
