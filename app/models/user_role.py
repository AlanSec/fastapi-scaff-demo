from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class UserRoleBase(SQLModel):
    """用户-角色关联基础模型"""

    is_active: bool = Field(default=True)


class UserRole(UserRoleBase, table=True):
    """用户-角色关联数据模型"""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 外键
    user_id: UUID = Field(foreign_key="user.id")
    role_id: UUID = Field(foreign_key="role.id")

    # 关系
    user: "app.models.user.User" = Relationship(back_populates="roles")
    role: "app.models.role.Role" = Relationship(back_populates="users")
