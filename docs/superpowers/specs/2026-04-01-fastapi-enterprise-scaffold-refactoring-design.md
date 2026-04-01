# FastAPI 企业级脚手架重构设计规范

**日期**: 2026-04-01  
**项目**: FastAPI 多租户 RBAC 认证系统企业级脚手架重构  
**状态**: 已批准 ✅  
**作者**: Claude Code (Anthropic)  
**审核人**: AlanSec (用户)

## 1. 概述

### 1.1 设计目标
将现有 FastAPI 多租户 RBAC 认证系统重构为企业级开发脚手架，提供：
1. **高可维护性** - 清晰的分层架构与职责分离
2. **高性能与可扩展性** - 异步架构 + 基础设施抽象
3. **强安全性** - 企业级安全与合规性保障
4. **卓越开发体验** - 完整工具链与自动化工作流

### 1.2 核心原则
- **领域驱动设计 (DDD)** - 业务逻辑集中于领域层
- **依赖注入** - 显式依赖声明与可测试性
- **基础设施抽象** - 可插拔的技术实现
- **配置驱动** - 环境无关的应用配置
- **健康检查** - 生产就绪的监控与探针

## 2. 架构设计

### 2.1 总体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP 层 (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   API端点   │  │  中间件     │  │  异常处理器      │   │
│  │  (路由)     │  │  (CORS/限流)│  │  (统一错误响应)  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────┘   │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   应用层 (Application)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  用例服务   │  │  DTO转换器  │  │  领域事件发布    │   │
│  │  (业务编排) │  │  (入/出适配)│  │  (跨域一致性)    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────┘   │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   领域层 (Domain)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  实体       │  │  值对象     │  │  领域服务        │   │
│  │  (核心业务) │  │  (不可变)   │  │  (跨实体逻辑)    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────┘   │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│              基础设施层 (Infrastructure)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  仓储实现   │  │  消息队列   │  │  外部API客户端   │   │
│  │  (DB/缓存)  │  │  (事件总线) │  │  (第三方集成)    │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬───────┘   │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│              外部依赖 (External Dependencies)                │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │  数据库     │  │  缓存服务   │  │  对象存储        │   │
│  │  (PostgreSQL)│  (Redis)      │  │  (S3/MinIO)      │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 依赖流向规则
- **单向依赖**: 上层可依赖下层，下层不可依赖上层
- **领域层纯净**: 不依赖任何基础设施或框架代码
- **依赖注入**: 所有外部依赖通过接口注入
- **端口适配器**: 外部系统通过适配器接入

## 3. 目录结构重构

### 3.1 新的目录结构

```
fastapi-enterprise-scaffold/
├── src/
│   ├── application/                    # 应用层
│   │   ├── usecases/                   # 用例服务
│   │   │   ├── auth/                   # 认证用例
│   │   │   │   ├── commands/           # 写操作（CQRS）
│   │   │   │   │   ├── register_user.py
│   │   │   │   │   ├── login_user.py
│   │   │   │   │   └── change_password.py
│   │   │   │   └── queries/            # 读操作（CQRS）
│   │   │   │       ├── get_user_profile.py
│   │   │   │       └── list_users.py
│   │   │   ├── tenant/                 # 租户管理用例
│   │   │   └── role/                   # 角色权限用例
│   │   ├── dtos/                       # 数据传输对象
│   │   │   ├── auth_dtos.py
│   │   │   ├── tenant_dtos.py
│   │   │   └── role_dtos.py
│   │   └── events/                     # 应用事件
│   │       ├── user_registered.py
│   │       └── password_changed.py
│   │
│   ├── domain/                         # 领域层（核心）
│   │   ├── entities/                   # 领域实体
│   │   │   ├── user.py                 # 用户实体
│   │   │   ├── tenant.py               # 租户实体
│   │   │   ├── role.py                 # 角色实体
│   │   │   └── permission.py           # 权限实体
│   │   ├── value_objects/              # 值对象
│   │   │   ├── email.py                # 邮箱值对象
│   │   │   ├── password.py             # 密码值对象
│   │   │   └── jwt_token.py            # JWT令牌值对象
│   │   ├── services/                   # 领域服务
│   │   │   ├── auth_service.py         # 认证领域服务
│   │   │   └── permission_service.py   # 权限领域服务
│   │   ├── repositories/               # 仓储接口（端口）
│   │   │   ├── user_repository.py
│   │   │   ├── tenant_repository.py
│   │   │   └── role_repository.py
│   │   └── events/                     # 领域事件
│   │       ├── user_events.py
│   │       └── tenant_events.py
│   │
│   ├── infrastructure/                 # 基础设施层
│   │   ├── persistence/                # 持久化实现
│   │   │   ├── sqlmodel/               # SQLModel实现
│   │   │   │   ├── models/             # 数据模型（ORM）
│   │   │   │   │   ├── user_model.py
│   │   │   │   │   ├── tenant_model.py
│   │   │   │   │   └── role_model.py
│   │   │   │   └── repositories/       # 仓储实现
│   │   │   │       ├── user_repository_impl.py
│   │   │   │       └── tenant_repository_impl.py
│   │   │   ├── redis/                  # Redis缓存实现
│   │   │   └── in_memory/              # 内存实现（测试用）
│   │   ├── messaging/                  # 消息传递
│   │   │   ├── event_bus.py            # 事件总线接口
│   │   │   ├── in_memory_event_bus.py  # 内存实现
│   │   │   └── redis_event_bus.py      # Redis实现
│   │   ├── external/                   # 外部服务
│   │   │   ├── email/                  # 邮件服务
│   │   │   │   ├── email_service.py
│   │   │   │   ├── smtp_email_service.py
│   │   │   │   └── sendgrid_email_service.py
│   │   │   └── storage/                # 对象存储
│   │   │       ├── storage_service.py
│   │   │       ├── local_storage.py
│   │   │       └── s3_storage.py
│   │   └── security/                   # 安全实现
│   │       ├── jwt_provider.py         # JWT提供者
│   │       ├── bcrypt_hasher.py        # 密码哈希
│   │       └── rate_limiter.py         # 限流器
│   │
│   ├── api/                            # 接口层（HTTP/RPC）
│   │   ├── http/                       # HTTP API
│   │   │   ├── v1/                     # API版本1
│   │   │   │   ├── auth/               # 认证端点
│   │   │   │   │   ├── routes.py       # 路由定义
│   │   │   │   │   └── controllers.py  # 控制器
│   │   │   │   ├── tenants/            # 租户端点
│   │   │   │   └── roles/              # 角色端点
│   │   │   ├── middleware/             # 中间件
│   │   │   │   ├── auth_middleware.py
│   │   │   │   ├── cors_middleware.py
│   │   │   │   └── request_logging.py
│   │   │   └── exceptions/             # HTTP异常处理
│   │   │       ├── http_exceptions.py
│   │   │       └── exception_handlers.py
│   │   └── grpc/                       # gRPC接口（预留）
│   │
│   └── bootstrap/                      # 应用启动
│       ├── di/                         # 依赖注入容器
│       │   ├── container.py            # DI容器
│       │   ├── modules/                # 模块注册
│       │   │   ├── auth_module.py
│       │   │   ├── persistence_module.py
│       │   │   └── security_module.py
│       │   └── providers/              # 提供者工厂
│       │       ├── database_provider.py
│       │       └── cache_provider.py
│       ├── config/                     # 配置管理
│       │   ├── settings.py             # 主配置
│       │   ├── database.py             # 数据库配置
│       │   ├── security.py             # 安全配置
│       │   └── logging.py              # 日志配置
│       └── lifespan/                   # 应用生命周期
│           ├── lifespan.py             # FastAPI lifespan
│           ├── startup_handlers.py     # 启动处理器
│           └── shutdown_handlers.py    # 关闭处理器
│
├── tests/                              # 测试目录
│   ├── unit/                           # 单元测试
│   │   ├── domain/                     # 领域层测试
│   │   ├── application/                # 应用层测试
│   │   └── infrastructure/             # 基础设施测试
│   ├── integration/                    # 集成测试
│   │   ├── api/                        # API集成测试
│   │   └── persistence/                # 持久化集成测试
│   ├── e2e/                            # 端到端测试
│   └── fixtures/                       # 测试夹具
│
├── scripts/                            # 脚本工具
│   ├── dev/                            # 开发脚本
│   ├── deploy/                         # 部署脚本
│   └── db/                             # 数据库脚本
│
├── docs/                               # 文档
│   ├── api/                            # API文档
│   ├── architecture/                   # 架构文档
│   └── deployment/                     # 部署文档
│
└── pyproject.toml                      # 项目配置
```

### 3.2 迁移策略
1. **渐进式迁移** - 逐个模块重构，保持系统可用
2. **并行运行** - 新旧代码并行，通过特性开关切换
3. **数据兼容** - 保持数据库模式向后兼容
4. **测试保障** - 每个重构步骤都有完整测试覆盖

## 4. Auth领域完整演示

### 4.1 领域实体定义

```python
# src/domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


@dataclass(frozen=True)
class User:
    """用户领域实体（不可变）"""
    id: UUID
    email: Email
    password: HashedPassword
    tenant_id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        email: Email,
        password: HashedPassword,
        tenant_id: UUID
    ) -> "User":
        """工厂方法：创建新用户"""
        now = datetime.utcnow()
        return cls(
            id=UUID.uuid4(),
            email=email,
            password=password,
            tenant_id=tenant_id,
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now
        )
    
    def verify(self) -> "User":
        """验证用户邮箱"""
        return self._replace(is_verified=True)
    
    def update_last_login(self) -> "User":
        """更新最后登录时间"""
        return self._replace(last_login_at=datetime.utcnow())
    
    def _replace(self, **kwargs):
        """不可变对象的属性替换"""
        return self.__class__(**{**self.__dict__, **kwargs})
```

### 4.2 仓储接口（端口）

```python
# src/domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(ABC):
    """用户仓储接口（端口）"""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """保存用户"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID查找用户"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户"""
        pass
    
    @abstractmethod
    async def find_by_tenant(
        self, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """查找租户下的用户"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        pass
```

### 4.3 应用服务（用例）

```python
# src/application/usecases/auth/commands/register_user.py
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import Password, HashedPassword
from src.infrastructure.security.bcrypt_hasher import PasswordHasher


class RegisterUserCommand:
    """注册用户命令"""
    
    def __init__(
        self,
        email: str,
        plain_password: str,
        tenant_id: UUID
    ):
        self.email = Email(email)
        self.password = Password(plain_password)
        self.tenant_id = tenant_id


class RegisterUserUseCase:
    """注册用户用例"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def execute(self, command: RegisterUserCommand) -> User:
        """执行用户注册"""
        # 1. 检查邮箱是否已存在
        existing_user = await self.user_repository.find_by_email(
            str(command.email)
        )
        if existing_user:
            raise ValueError("邮箱已存在")
        
        # 2. 哈希密码
        hashed_password = self.password_hasher.hash(str(command.password))
        
        # 3. 创建用户实体
        user = User.create(
            email=command.email,
            password=HashedPassword(hashed_password),
            tenant_id=command.tenant_id
        )
        
        # 4. 保存用户
        saved_user = await self.user_repository.save(user)
        
        # 5. 发布领域事件
        # await self.event_bus.publish(UserRegistered(user_id=saved_user.id))
        
        return saved_user
```

### 4.4 HTTP控制器

```python
# src/api/http/v1/auth/controllers.py
from fastapi import Depends, HTTPException, status
from uuid import UUID

from src.application.dtos.auth_dtos import UserResponse
from src.application.usecases.auth.commands.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase
)
from src.bootstrap.di.container import get_container


class AuthController:
    """认证控制器"""
    
    def __init__(self):
        self.container = get_container()
    
    async def register(
        self,
        email: str,
        password: str,
        tenant_id: UUID
    ) -> UserResponse:
        """用户注册端点"""
        try:
            # 解析依赖
            usecase = self.container.resolve(RegisterUserUseCase)
            
            # 执行命令
            command = RegisterUserCommand(
                email=email,
                plain_password=password,
                tenant_id=tenant_id
            )
            user = await usecase.execute(command)
            
            # 转换为DTO
            return UserResponse.from_domain(user)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="内部服务器错误"
            )
```

## 5. 基础设施层抽象

### 5.1 可插拔实现策略

```python
# src/infrastructure/persistence/sqlmodel/repositories/user_repository_impl.py
from typing import Optional, List
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.persistence.sqlmodel.models.user_model import UserModel
from src.infrastructure.persistence.sqlmodel.mappers.user_mapper import (
    UserMapper
)


class SQLModelUserRepository(UserRepository):
    """SQLModel用户仓储实现"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserMapper()
    
    async def save(self, user: User) -> User:
        """保存用户"""
        user_model = self.mapper.to_model(user)
        
        # 检查是否已存在
        existing = await self.session.get(UserModel, user.id)
        if existing:
            # 更新
            for key, value in user_model.dict(exclude={"id"}).items():
                setattr(existing, key, value)
            user_model = existing
        else:
            # 新增
            self.session.add(user_model)
        
        await self.session.commit()
        await self.session.refresh(user_model)
        
        return self.mapper.to_entity(user_model)
    
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID查找用户"""
        model = await self.session.get(UserModel, user_id)
        return self.mapper.to_entity(model) if model else None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户"""
        statement = select(UserModel).where(UserModel.email == email)
        result = await self.session.exec(statement)
        model = result.first()
        return self.mapper.to_entity(model) if model else None
    
    async def find_by_tenant(
        self, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """查找租户下的用户"""
        statement = (
            select(UserModel)
            .where(UserModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        models = result.all()
        return [self.mapper.to_entity(model) for model in models]
    
    async def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        model = await self.session.get(UserModel, user_id)
        if model:
            await self.session.delete(model)
            await self.session.commit()
            return True
        return False
```

### 5.2 内存实现（测试用）

```python
# src/infrastructure/persistence/in_memory/user_repository_impl.py
from typing import Dict, Optional, List
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    """内存用户仓储实现（用于测试）"""
    
    def __init__(self):
        self._storage: Dict[UUID, User] = {}
        self._email_index: Dict[str, UUID] = {}
    
    async def save(self, user: User) -> User:
        """保存用户"""
        self._storage[user.id] = user
        self._email_index[str(user.email)] = user.id
        return user
    
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """通过ID查找用户"""
        return self._storage.get(user_id)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """通过邮箱查找用户"""
        user_id = self._email_index.get(email)
        return self._storage.get(user_id) if user_id else None
    
    async def find_by_tenant(
        self, 
        tenant_id: UUID, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """查找租户下的用户"""
        users = [
            user for user in self._storage.values() 
            if user.tenant_id == tenant_id
        ]
        return users[skip:skip + limit]
    
    async def delete(self, user_id: UUID) -> bool:
        """删除用户"""
        user = self._storage.get(user_id)
        if user:
            del self._storage[user_id]
            if str(user.email) in self._email_index:
                del self._email_index[str(user.email)]
            return True
        return False
```

### 5.3 配置驱动的实现选择

```python
# src/bootstrap/config/database.py
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class DatabaseType(str, Enum):
    """数据库类型枚举"""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    MEMORY = "memory"  # 仅用于测试


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    type: DatabaseType = DatabaseType.POSTGRESQL
    host: Optional[str] = None
    port: Optional[int] = None
    name: str = "fastapi_app"
    user: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def connection_string(self) -> str:
        """生成连接字符串"""
        if self.type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql+asyncpg://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.name}"
            )
        elif self.type == DatabaseType.SQLITE:
            return f"sqlite+aiosqlite:///./{self.name}.db"
        elif self.type == DatabaseType.MEMORY:
            return "sqlite+aiosqlite:///:memory:"
        else:
            raise ValueError(f"不支持的数据库类型: {self.type}")
```

## 6. 应用启动与生命周期管理

### 6.1 依赖注入容器

```python
# src/bootstrap/di/container.py
from typing import Any, Type, Dict
from uuid import UUID

from src.bootstrap.config.settings import Settings
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.persistence.sqlmodel.repositories.user_repository_impl import (
    SQLModelUserRepository
)
from src.infrastructure.persistence.in_memory.user_repository_impl import (
    InMemoryUserRepository
)


class Container:
    """依赖注入容器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._instances: Dict[Type, Any] = {}
        self._setup()
    
    def _setup(self):
        """设置容器绑定"""
        # 根据配置选择仓储实现
        if self.settings.database.type == "memory":
            self.bind(UserRepository, InMemoryUserRepository())
        else:
            # 实际项目中需要注入session
            # 示例：self.bind(UserRepository, SQLModelUserRepository(session_factory()))
            self.bind(UserRepository, SQLModelUserRepository(session_factory()))
    
    def bind(self, interface: Type, implementation: Any):
        """绑定接口到实现"""
        self._instances[interface] = implementation
    
    def resolve(self, dependency: Type) -> Any:
        """解析依赖"""
        if dependency not in self._instances:
            raise ValueError(f"未找到依赖: {dependency}")
        return self._instances[dependency]


# 全局容器实例
_container: Optional[Container] = None

def init_container(settings: Settings) -> Container:
    """初始化容器"""
    global _container
    _container = Container(settings)
    return _container

def get_container() -> Container:
    """获取容器实例"""
    if _container is None:
        raise RuntimeError("容器未初始化")
    return _container
```

### 6.2 应用生命周期管理

```python
# src/bootstrap/lifespan/lifespan.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.bootstrap.config.settings import Settings
from src.bootstrap.di.container import init_container
from src.bootstrap.lifespan.startup_handlers import (
    setup_database,
    setup_cache,
    setup_event_bus
)
from src.bootstrap.lifespan.shutdown_handlers import (
    close_database,
    close_cache,
    close_event_bus
)


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI应用生命周期管理器
    
    负责：
    1. 启动阶段：初始化所有基础设施
    2. 运行阶段：应用正常运行
    3. 关闭阶段：优雅关闭所有资源
    """
    # 加载配置
    settings = Settings()
    
    # 初始化依赖注入容器
    container = init_container(settings)
    app.state.container = container
    
    # 启动阶段
    print("🚀 启动应用...")
    
    # 初始化数据库
    database = await setup_database(settings)
    app.state.database = database
    
    # 初始化缓存
    cache = await setup_cache(settings)
    app.state.cache = cache
    
    # 初始化事件总线
    event_bus = await setup_event_bus(settings)
    app.state.event_bus = event_bus
    
    # 注册健康检查
    await setup_health_checks(app)
    
    print("✅ 应用启动完成")
    
    # 运行阶段
    yield
    
    # 关闭阶段
    print("🛑 关闭应用...")
    
    # 关闭事件总线
    if hasattr(app.state, 'event_bus'):
        await close_event_bus(app.state.event_bus)
    
    # 关闭缓存
    if hasattr(app.state, 'cache'):
        await close_cache(app.state.cache)
    
    # 关闭数据库
    if hasattr(app.state, 'database'):
        await close_database(app.state.database)
    
    print("✅ 应用关闭完成")
```

### 6.3 健康检查系统

```python
# src/api/http/health/controllers.py
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.bootstrap.di.container import get_container
from src.infrastructure.cache.redis_cache import RedisCache


router = APIRouter(tags=["health"])


@router.get("/health/liveness")
async def liveness_probe():
    """
    存活探针
    
    检查应用是否正在运行。
    应始终返回200 OK，除非应用完全崩溃。
    """
    return {
        "status": "healthy",
        "service": "fastapi-enterprise-scaffold",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/readiness")
async def readiness_probe(
    session: AsyncSession = Depends(get_db_session),
    cache: RedisCache = Depends(get_cache)
):
    """
    就绪探针
    
    检查应用是否准备好接收流量。
    验证所有关键依赖（数据库、缓存等）是否可用。
    """
    checks = []
    
    # 检查数据库连接
    try:
        await session.execute("SELECT 1")
        checks.append({"database": "healthy"})
    except Exception as e:
        checks.append({"database": "unhealthy", "error": str(e)})
    
    # 检查缓存连接
    try:
        await cache.ping()
        checks.append({"cache": "healthy"})
    except Exception as e:
        checks.append({"cache": "unhealthy", "error": str(e)})
    
    # 判断整体状态
    all_healthy = all(
        check.get("database") == "healthy" 
        or check.get("cache") == "healthy" 
        for check in checks
    )
    
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }, status_code
```

## 7. 测试策略

### 7.1 测试金字塔

```
        ┌─────────────────┐
        │    E2E测试       │  ~10%
        │  (端到端流程)     │
        └─────────┬───────┘
                  │
        ┌─────────┴───────┐
        │   集成测试       │  ~20%
        │  (组件间交互)     │
        └─────────┬───────┘
                  │
        ┌─────────┴───────┐
        │   单元测试       │  ~70%
        │  (独立单元)      │
        └─────────────────┘
```

### 7.2 测试覆盖率要求
- **总体覆盖率**: ≥80%
- **领域层**: ≥90%（核心业务逻辑）
- **应用层**: ≥85%（用例服务）
- **基础设施层**: ≥70%（外部集成）

### 7.3 测试数据管理
```python
# tests/fixtures/user_fixtures.py
import pytest
from uuid import UUID, uuid4

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword


@pytest.fixture
def sample_user() -> User:
    """测试用户夹具"""
    return User(
        id=uuid4(),
        email=Email("test@example.com"),
        password=HashedPassword("hashed_password"),
        tenant_id=uuid4(),
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def in_memory_user_repository():
    """内存用户仓储夹具"""
    from src.infrastructure.persistence.in_memory.user_repository_impl import (
        InMemoryUserRepository
    )
    return InMemoryUserRepository()
```

## 8. 部署与运维

### 8.1 环境配置

```yaml
# config/
#   ├── .env.local          # 本地开发
#   ├── .env.test           # 测试环境  
#   ├── .env.staging        # 预发布环境
#   └── .env.production     # 生产环境

# .env.production 示例
DATABASE_TYPE=postgresql
DATABASE_HOST=postgres-primary
DATABASE_PORT=5432
DATABASE_NAME=fastapi_prod
DATABASE_USER=fastapi_user
DATABASE_PASSWORD=${DB_PASSWORD}

REDIS_HOST=redis-cluster
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD}

JWT_SECRET_KEY=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 8.2 Docker配置

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY pyproject.toml .

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/liveness', timeout=2)"

# 启动命令
CMD ["uvicorn", "src.bootstrap.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.3 Kubernetes部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi
        image: registry.example.com/fastapi-app:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: fastapi-secrets
        - configMapRef:
            name: fastapi-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 10
```

## 9. 开发工作流

### 9.1 本地开发

```bash
# 1. 安装依赖
pip install -r requirements-dev.txt

# 2. 设置环境变量
cp .env.example .env.local

# 3. 启动开发服务器（热重载）
uvicorn src.bootstrap.main:app --reload --host 0.0.0.0 --port 8000

# 4. 运行测试
pytest tests/ -v --cov=src --cov-report=term-missing

# 5. 代码质量检查
black src/ tests/
isort src/ tests/
mypy src/
ruff check src/ tests/
```

### 9.2 CI/CD流水线

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
    
    - name: Run security scan
      run: |
        bandit -r src/
    
    - name: Run type checking
      run: |
        mypy src/
```

## 10. 成功标准与验收条件

### 10.1 技术验收条件
- [ ] **架构分层清晰**：四层架构明确分离，依赖流向正确
- [ ] **领域层纯净**：领域实体不依赖任何外部框架
- [ ] **依赖注入完善**：所有外部依赖通过接口注入
- [ ] **基础设施可插拔**：数据库、缓存等实现可配置切换
- [ ] **测试覆盖达标**：总体覆盖率≥80%，核心领域≥90%
- [ ] **健康检查完整**：liveness/readiness探针工作正常
- [ ] **配置管理完善**：多环境配置支持，密钥安全存储
- [ ] **文档完整**：架构文档、API文档、部署指南齐全

### 10.2 业务验收条件
- [ ] **用户注册流程**：支持邮箱验证、密码强度校验
- [ ] **多租户隔离**：数据按租户严格隔离
- [ ] **RBAC权限控制**：角色-权限模型工作正常
- [ ] **JWT认证**：访问令牌与刷新令牌机制完善
- [ ] **API版本管理**：支持API版本演进
- [ ] **错误处理友好**：统一的错误响应格式

### 10.3 运维验收条件
- [ ] **监控指标**：关键业务指标与系统指标可观测
- [ ] **日志聚合**：结构化日志，支持集中查询
- [ ] **部署自动化**：CI/CD流水线工作正常
- [ ] **回滚机制**：支持快速回滚到上一版本
- [ ] **容量规划**：资源使用可预测，支持自动扩缩容

## 11. 风险与缓解措施

### 11.1 技术风险
| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 领域层与ORM映射复杂 | 中 | 高 | 使用专门Mapper层，保持领域纯净 |
| 异步代码调试困难 | 中 | 中 | 完善日志记录，使用结构化日志 |
| 依赖注入配置复杂 | 低 | 中 | 提供默认配置，支持逐步定制 |
| 测试数据管理复杂 | 中 | 低 | 使用夹具工厂，统一测试数据生成 |

### 11.2 迁移风险
| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 数据库模式变更 | 高 | 高 | 使用Alembic迁移，保持向后兼容 |
| API接口变更 | 中 | 中 | 支持多版本API，提供迁移指南 |
| 性能回归 | 低 | 高 | 性能测试套件，关键路径压测 |

### 11.3 运维风险
| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 配置泄露 | 低 | 高 | 使用密钥管理服务，环境变量加密 |
| 依赖服务故障 | 中 | 高 | 断路器模式，降级策略，健康检查 |
| 内存泄漏 | 低 | 高 | 内存监控，定期压力测试 |

## 12. 后续演进路线

### 12.1 近期（1-3个月）
1. **核心认证流程**：完成用户注册、登录、令牌刷新
2. **多租户管理**：租户创建、配置、用户管理
3. **RBAC基础**：角色与权限管理，权限验证中间件
4. **基本监控**：健康检查、基础指标收集

### 12.2 中期（3-6个月）
1. **高级安全特性**：MFA、IP白名单、会话管理
2. **审计日志**：关键操作审计，合规性支持
3. **性能优化**：查询优化，缓存策略，连接池管理
4. **开发者体验**：OpenAPI文档完善，SDK生成

### 12.3 长期（6-12个月）
1. **微服务化**：按领域拆分微服务，服务网格集成
2. **事件驱动架构**：领域事件，事件溯源，CQRS
3. **国际化支持**：多语言，多时区，本地化配置
4. **AI集成**：异常检测，智能审计，预测性扩缩容

---

## 附录A：术语表

| 术语 | 解释 |
|------|------|
| DDD | 领域驱动设计，一种软件设计方法论 |
| 实体 | 具有唯一标识和生命周期的领域对象 |
| 值对象 | 不可变、无标识的领域对象 |
| 仓储 | 领域对象的持久化抽象 |
| 用例 | 应用层服务，实现特定的用户目标 |
| 端口 | 领域层定义的接口（输入/输出） |
| 适配器 | 基础设施层对端口的实现 |
| CQRS | 命令查询职责分离，读写模型分离 |
| 事件总线 | 领域事件发布订阅的基础设施 |

## 附录B：决策记录

| 决策编号 | 决策内容 | 决策日期 | 决策理由 |
|----------|----------|----------|----------|
| ADR-001 | 采用四层架构而非传统MVC | 2026-04-01 | 更好的关注点分离，支持复杂业务逻辑 |
| ADR-002 | 使用SQLModel而非纯SQLAlchemy | 2026-04-01 | 类型安全，Pydantic集成，开发体验更好 |
| ADR-003 | 异步优先架构 | 2026-04-01 | 更好的IO性能，现代Python生态趋势 |
| ADR-004 | 依赖注入而非全局单例 | 2026-04-01 | 更好的可测试性，明确的依赖关系 |
| ADR-005 | 配置驱动而非硬编码 | 2026-04-01 | 环境无关，部署灵活性，安全性 |

---

**文档版本**: 1.0  
**最后更新**: 2026-04-01  
**下次评审**: 2026-07-01  
**状态**: ✅ 已批准 (用户确认：符合要求，暂时没有需要调整的)