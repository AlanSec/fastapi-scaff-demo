"""角色 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel
from src.infrastructure.persistence.sqlmodel.models.time import utcnow

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role_permission import RolePermissionModel
    from src.infrastructure.persistence.sqlmodel.models.tenant import TenantModel
    from src.infrastructure.persistence.sqlmodel.models.user_role import UserRoleModel


class RoleModel(SQLModel, table=True):
    """角色数据模型"""
    __tablename__ = "roles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    is_active: bool = Field(default=True)
    tenant_id: UUID = Field(foreign_key="tenants.id")
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    tenant: "TenantModel" = Relationship(back_populates="roles")
    users: list["UserRoleModel"] = Relationship(
        back_populates="role", cascade_delete=True
    )
    permissions: list["RolePermissionModel"] = Relationship(
        back_populates="role", cascade_delete=True
    )
