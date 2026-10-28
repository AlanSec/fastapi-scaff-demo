"""PermissionMapper 测试——未知 action/resource 必须抛错而非静默兜底"""
from datetime import datetime

import pytest
from src.domain.entities.permission import PermissionAction, Resource
from src.infrastructure.persistence.sqlmodel.mappers.permission_mapper import PermissionMapper
from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel


def _model(action: str, resource: str) -> PermissionModel:
    return PermissionModel(
        id="00000000-0000-0000-0000-000000000001",
        action=action,
        resource=resource,
        description="x",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_to_entity_maps_valid_values():
    entity = PermissionMapper.to_entity(_model("create", "tenant"))
    assert entity.action == PermissionAction.CREATE
    assert entity.resource == Resource.TENANT


def test_to_entity_unknown_action_raises():
    """数据库中出现未知 action 必须抛错（兜底会掩盖数据错误）"""
    with pytest.raises(ValueError, match="Unknown permission"):
        PermissionMapper.to_entity(_model("exploit", "tenant"))


def test_to_entity_unknown_resource_raises():
    with pytest.raises(ValueError, match="Unknown permission"):
        PermissionMapper.to_entity(_model("create", "billing"))
