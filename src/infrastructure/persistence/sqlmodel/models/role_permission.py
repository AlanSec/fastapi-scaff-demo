"""角色-权限关联 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from src.infrastructure.persistence.sqlmodel.models.time import utcnow

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel
    from src.infrastructure.persistence.sqlmodel.models.role import RoleModel


class RolePermissionModel(SQLModel, table=True):
    """角色-权限关联数据模型"""
    __tablename__ = "role_permissions"
    # 同一角色不可重复关联同一权限（数据库层兜底，防竞态重复）
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role_id: UUID = Field(foreign_key="roles.id")
    permission_id: UUID = Field(foreign_key="permissions.id", index=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    role: "RoleModel" = Relationship(back_populates="permissions")
    permission: "PermissionModel" = Relationship(back_populates="role_permissions")
