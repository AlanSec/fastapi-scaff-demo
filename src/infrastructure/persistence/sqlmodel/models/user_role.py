"""用户-角色关联 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel
from src.infrastructure.persistence.sqlmodel.models.time import utcnow

if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
    from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class UserRoleModel(SQLModel, table=True):
    """用户-角色关联数据模型"""
    __tablename__ = "user_roles"
    # 同一用户不可重复分配同一角色（数据库层兜底，防竞态重复）
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    role_id: UUID = Field(foreign_key="roles.id", index=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    user: "UserModel" = Relationship(back_populates="roles")
    role: "RoleModel" = Relationship(back_populates="users")
