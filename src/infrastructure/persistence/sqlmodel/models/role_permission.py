"""角色-权限关联 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
    from src.infrastructure.persistence.sqlmodel.models.permission import PermissionModel


class RolePermissionModel(SQLModel, table=True):
    """角色-权限关联数据模型"""
    __tablename__ = "role_permissions"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role_id: UUID = Field(foreign_key="roles.id")
    permission_id: UUID = Field(foreign_key="permissions.id")
    created_at: datetime = Field(default_factory=datetime.now)
    
    role: "RoleModel" = Relationship(back_populates="permissions")
    permission: "PermissionModel" = Relationship(back_populates="role_permissions")