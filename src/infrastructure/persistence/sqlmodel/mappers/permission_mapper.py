from src.domain.entities.permission import Permission, PermissionAction, Resource
from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel


class PermissionMapper:

    @staticmethod
    def to_model(entity: Permission) -> PermissionModel:
        return PermissionModel(
            id=entity.id,
            action=entity.action.value,
            resource=entity.resource.value,
            description=entity.description,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(model: PermissionModel) -> Permission:
        action = PermissionAction(model.action) if model.action in PermissionAction._value2member_map_ else PermissionAction.READ
        resource = Resource(model.resource) if model.resource in Resource._value2member_map_ else Resource.USER
        return Permission(
            id=model.id,
            action=action,
            resource=resource,
            description=model.description or "",
            is_active=getattr(model, "is_active", True),
            created_at=model.created_at,
            updated_at=getattr(model, "updated_at", model.created_at),
        )
