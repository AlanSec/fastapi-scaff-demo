"""权限 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel
from src.infrastructure.persistence.sqlmodel.models.time import utcnow

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role_permission import RolePermissionModel


class PermissionModel(SQLModel, table=True):
    """权限数据模型"""
    __tablename__ = "permissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    action: str = Field(index=True)
    resource: str = Field(index=True)
    description: str | None = None
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    is_active: bool = Field(default=True)
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    role_permissions: list["RolePermissionModel"] = Relationship(
        back_populates="permission", cascade_delete=True
    )
