"""用户映射器"""
from datetime import datetime
from uuid import UUID

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.sqlmodel.models.user import UserModel


class UserMapper:
    """用户实体与模型之间的映射器"""
    
    @staticmethod
    def to_model(user: User) -> UserModel:
        """将 User 实体转换为 UserModel"""
        return UserModel(
            id=user.id,
            email=str(user.email),
            username=str(user.email).split("@")[0],
            hashed_password=user.password.value,
            tenant_id=user.tenant_id,
            is_active=user.is_active,
            is_superuser=False,
            created_at=user.created_at,
            updated_at=user.updated_at,
            email_verified=user.is_verified,
            last_login_at=user.last_login_at,
        )
    
    @staticmethod
    def to_entity(model: UserModel) -> User:
        """将 UserModel 转换为 User 实体"""
        return User(
            id=model.id,
            email=Email(model.email),
            password=HashedPassword(model.hashed_password),
            tenant_id=model.tenant_id,
            is_active=model.is_active,
            is_verified=model.email_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=getattr(model, "last_login_at", None),
        )