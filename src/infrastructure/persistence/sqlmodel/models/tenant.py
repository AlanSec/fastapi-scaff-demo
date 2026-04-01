"""租户 SQLModel 模型"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from src.infrastructure.persistence.sqlmodel.models.role import RoleModel
    from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class TenantModel(SQLModel, table=True):
    """租户数据模型"""
    __tablename__ = "tenants"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    users: list["UserModel"] = Relationship(back_populates="tenant")
    roles: list["RoleModel"] = Relationship(back_populates="tenant")