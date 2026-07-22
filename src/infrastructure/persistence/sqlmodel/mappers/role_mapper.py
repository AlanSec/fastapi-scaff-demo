from src.domain.entities.role import Role, RoleName
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel


class RoleMapper:

    @staticmethod
    def to_model(entity: Role) -> RoleModel:
        return RoleModel(
            id=entity.id,
            name=entity.name.value,
            description=entity.description,
            is_active=entity.is_active,
            tenant_id=entity.tenant_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=RoleName(model.name) if model.name in RoleName._value2member_map_ else RoleName.USER,
            description=model.description or "",
            is_active=model.is_active,
            tenant_id=model.tenant_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
