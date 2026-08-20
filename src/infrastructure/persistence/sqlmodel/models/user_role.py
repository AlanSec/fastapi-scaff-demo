"""用户-角色关联 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
    from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class UserRoleModel(SQLModel, table=True):
    """用户-角色关联数据模型"""
    __tablename__ = "user_roles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    role_id: UUID = Field(foreign_key="roles.id")
    created_at: datetime = Field(default_factory=datetime.now)

    user: "UserModel" = Relationship(back_populates="roles")
    role: "RoleModel" = Relationship(back_populates="users")
