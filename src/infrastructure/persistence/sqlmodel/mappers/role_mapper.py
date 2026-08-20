from src.domain.entities.role import Role
from src.infrastructure.persistence.sqlmodel.models.role import RoleModel


class RoleMapper:

    @staticmethod
    def to_model(entity: Role) -> RoleModel:
        return RoleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            is_active=entity.is_active,
            tenant_id=entity.tenant_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def apply_to_model(model: RoleModel, entity: Role) -> RoleModel:
        """将角色实体的变更应用到已存在的 RoleModel（用于更新）"""
        model.name = entity.name
        model.description = entity.description
        model.is_active = entity.is_active
        model.tenant_id = entity.tenant_id
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at
        return model

    @staticmethod
    def to_entity(model: RoleModel) -> Role:
        return Role(
            id=model.id,
            name=model.name,
            description=model.description or "",
            is_active=model.is_active,
            tenant_id=model.tenant_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
