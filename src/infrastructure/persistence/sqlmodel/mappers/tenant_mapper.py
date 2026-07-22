from src.domain.entities.tenant import Tenant
from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel


class TenantMapper:

    @staticmethod
    def to_model(entity: Tenant) -> TenantModel:
        return TenantModel(
            id=entity.id,
            name=entity.name,
            domain=entity.domain,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def to_entity(model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            domain=model.domain or model.name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
