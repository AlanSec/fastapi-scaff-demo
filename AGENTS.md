# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

FastAPI 多租户 RBAC 认证系统，处于**架构过渡期**：遗留 `app/` 层（SQLModel + 扁平结构）与新 `src/` 层（DDD 四层架构）共存，共同注册在同一 FastAPI 实例上。

- **旧架构** (`app/`)：扁平分层，SQLModel 即领域模型，自动路由注册
- **新架构** (`src/`)：DDD 四层架构，严格分层，手动 DI 注入

## Commands

```bash
# 启动开发服务器（热重载，uvicorn factory 模式）
python main.py

# 运行全部遗留测试（app/test/）
python run_tests.py

# 运行单个遗留测试文件
python run_tests.py app/test/test_register_api.py

# 直接用 pytest 运行遗留测试
python -m pytest app/test/ -v --tb=short
python -m pytest app/test/test_register_api.py -v
python -m pytest app/test/test_register_api.py::test_function_name -v

# 运行新架构单元测试（无数据库依赖）
python -m pytest tests/unit/ -v --tb=short

# 运行新架构集成测试（需 SQLite 内存库）
python -m pytest tests/integration/ -v --tb=short

# 运行全部新架构测试
python -m pytest tests/ -v --tb=short

# 覆盖率报告
python -m pytest --cov=src --cov-report=term-missing tests/

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## Architecture

### 两套体系共存

```
main.py                                → 入口，uvicorn factory 模式
│
├── src/                               → 新架构：DDD 四层 + 手动 DI
│   ├── domain/                        →   领域层（纯 Python，零依赖）
│   │   ├── entities/                  →   领域实体（User, Tenant, Role...）
│   │   ├── value_objects/             →   值对象（Email, Password, JwtToken）
│   │   ├── repositories/             →   仓储接口（抽象协议）
│   │   └── services/                  →   领域服务接口
│   ├── application/                   →   应用层（用例编排）
│   │   ├── dto/                       →   输入/输出 DTO
│   │   └── use_cases/                 →   用例（注册、登录、改密...）
│   ├── infrastructure/                →   基础设施层（技术实现）
│   │   ├── persistence/               →     持久化（SQLModel/InMemory 实现）
│   │   │   ├── sqlmodel/models/       →     SQLModel ORM 模型
│   │   │   ├── sqlmodel/repositories/ →     仓储 SQLModel 实现
│   │   │   └── in_memory/             →     仓储内存实现（测试用）
│   │   └── security/                  →     安全（JWT、bcrypt、限流）
│   ├── api/                           →   API 适配层
│   │   ├── controllers/               →     Controller（请求/响应转 DTO）
│   │   ├── routes/                    →     FastAPI Router 定义
│   │   └── schemas/                   →     Pydantic 请求/响应 Schema
│   └── bootstrap/                     →   启动层
│       ├── config.py                  →     启动配置
│       ├── container.py               →     DI 容器（手动单例）
│       └── lifespan.py                →     App 工厂 + 生命周期管理
│
└── app/                               → 旧架构：扁平分层，逐步迁移中
    ├── api/v1/                        →   遗留路由（未来移入 src/api/routes）
    ├── services/                      →   遗留业务逻辑
    ├── models/                        →   SQLModel 模型（与 src 层模型共存）
    ├── schemas/                       →   遗留 Pydantic Schema
    ├── db/                            →   数据库引擎与会话管理
    └── test/                          →   遗留测试
```

### 路由注册机制

新架构路由在 `src/bootstrap/lifespan.py:create_app()` 中手动注册：

```python
app.include_router(auth_router, prefix="/api/v1")
app.include_router(password_router, prefix="/api/v1")
```

旧架构路由由 `_register_legacy_routers()` 自动扫描 `app/api/v1/` 目录。
已迁移的模块名（auth、password、verify）会被跳过，避免重复注册。

### DI 容器模式

`src/bootstrap/container.py` 实现**手动单例容器**：

- `Container` 类：饿汉式单例，属性按需懒初始化
- 依赖链：`UseCase` 依赖 `Repository` + `Hasher`/`JWT` → `Controller` 依赖 `UseCase` → 路由层通过全局 `set_controller()` 注入
- 当前 `user_repository` 使用 `InMemoryUserRepository`（内存存储），未对接旧架构的 `app/db/session.py`

### 新旧模型分离

- `app/models/`：SQLModel ORM 模型（也是领域模型，符合旧架构惯例）
- `src/infrastructure/persistence/sqlmodel/models/`：SQLModel ORM 模型（基础设施层实现）
- `src/domain/entities/`：纯 Python 领域实体，不依赖 ORM
- `src/infrastructure/persistence/sqlmodel/mappers/user_mapper.py`：ORM ↔ 实体转换

两个模型体系**不共享**，各自独立建表。当前新架构的内存仓储不依赖数据库。
`app/db/init_db()` 初始化旧模型表，`auth_routes.py` 中 `/token` 端点仍依赖旧架构的 `authenticate_user`。

### 认证体系

- JWT HS256，access_token 30 分钟 + refresh_token 7 天（新架构）
- JWT HS256，access_token 7 天 + refresh_token 30 天（旧架构，通过 Settings 配置）
- 密码 bcrypt 哈希
- 当前两个认证体系共存：新架构用 `/login`，旧架构用 `/token`

## Adding New Features

### 新架构（推荐）

新增 API 端点的四层流程：

1. **领域层** `src/domain/` — 定义实体、值对象、仓储接口
2. **基础设施层** `src/infrastructure/` — 实现仓储、安全服务
3. **应用层** `src/application/` — 创建 DTO 和 UseCase
4. **API 层** `src/api/` — 创建 Schema、Controller、Routes
5. **启动层**：在 `container.py` 注册新依赖，在 `lifespan.py` 注入 Controller 并注册路由
6. 在 `tests/unit/` 和 `tests/integration/` 中编写测试

### 旧架构（遗留）

见原描述（`app/models/` → `app/schemas/` → `app/services/` → `app/api/v1/` 流程）。

## Testing Notes

### 新测试体系 (`tests/`)

```
tests/
├── conftest.py                          → 通用 mock fixtures
├── unit/                                → 纯单元测试，无需数据库
│   ├── domain/                          →   实体、值对象、仓储接口测试
│   ├── application/                     →   UseCase 测试（mock 仓储）
│   ├── infrastructure/                  →   安全、持久化实现测试
│   ├── api/                             →   Controller/Routes 测试
│   └── bootstrap/                       →   配置、容器测试
└── integration/                         → 集成测试，SQLite 内存库
    ├── conftest.py                      →   测试引擎、fixtures
    ├── api/                             →   全链路 API 测试
    └── persistence/                     →   仓储实现测试
```

- 单元测试使用 `tests/conftest.py` 中的 AsyncMock fixtures
- 集成测试使用 `tests/integration/conftest.py` 的 `sqlite+aiosqlite:///:memory:` 引擎
- `setup_test_database` fixture 每个函数自动建表/删表，完全隔离

### 遗留测试 (`app/test/`)

- 通过 `conftest.py` 中的 `test_client` fixture 获得 FastAPI TestClient
- `setup_database` fixture 每个测试函数自动建表/删表
- 使用 `dependency_overrides` 注入测试会话
- 测试用的 app 只注册了认证相关路由，非认证测试需自行添加路由

## API 版本管理

项目采用 URL 版本管理，统一 `/api/v1/` 前缀：

```
POST /api/v1/auth/register      → 注册（新架构）
POST /api/v1/auth/login         → 登录（新架构）
POST /api/v1/auth/token         → OAuth2 令牌（旧架构）
POST /api/v1/password/forgot    → 忘记密码（新架构）
GET  /api/v1/roles/             → 角色管理（旧架构）
POST /api/v1/tenants/           → 租户管理（旧架构）
```

**未来扩展 v2**：创建新路由模块，注册到 `/api/v2/` 下。
