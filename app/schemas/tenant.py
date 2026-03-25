from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantBase(BaseModel):
    """租户基础模式"""

    name: str
    description: str | None = None
    is_active: bool = True


class TenantCreate(TenantBase):
    """创建租户的请求模式"""

    pass


class TenantUpdate(BaseModel):
    """更新租户的请求模式"""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class TenantRead(TenantBase):
    """租户响应模式"""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """配置类"""

        from_attributes = True
