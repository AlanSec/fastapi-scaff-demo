from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class PermissionBase(SQLModel):
    """权限基础模型"""

    name: str = Field(index=True)
    code: str = Field(index=True, unique=True)
    description: str | None = None
    is_active: bool = Field(default=True)


class Permission(PermissionBase, table=True):
    """权限数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 外键
    tenant_id: UUID | None = Field(default=None, foreign_key="tenant.id")

    # 可选：支持权限层级
    parent_id: UUID | None = Field(default=None, foreign_key="permission.id")

    # 关系
    roles: list["RolePermission"] = Relationship(back_populates="permission")  # noqa: F821
