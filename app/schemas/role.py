from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    description: Optional[str] = None
    is_active: bool = True
    tenant_id: UUID


class RoleCreate(RoleBase):
    """创建角色模型"""
    pass


class RoleUpdate(BaseModel):
    """更新角色模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    tenant_id: Optional[UUID] = None


class RoleOut(RoleBase):
    """角色输出模型"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
