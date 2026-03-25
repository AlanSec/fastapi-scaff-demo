# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI 多租户 RBAC 认证系统，基于 SQLModel（SQLAlchemy + Pydantic），异步架构。

## Commands

```bash
# 启动开发服务器（热重载）
python main.py

# 运行全部测试（含 80% 覆盖率要求）
python run_tests.py

# 运行单个测试文件
python run_tests.py app/test/test_register_api.py

# 直接用 pytest（更灵活）
python -m pytest app/test/ -v --tb=short
python -m pytest app/test/test_register_api.py -v
python -m pytest app/test/test_register_api.py::test_function_name -v

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

## Architecture

### 分层结构

```
main.py                 → 入口，启动 uvicorn
app/main.py             → FastAPI 工厂，注册路由与中间件
app/api/v1/             → 路由层（HTTP 端点），文件名即模块名
app/services/           → 业务逻辑层，路由不应包含业务逻辑
app/models/             → SQLModel 数据模型，每个模型一个文件
app/schemas/            → Pydantic 请求/响应 Schema
app/core/               → 配置(config)、安全(security)、异常(exceptions)
app/db/session.py       → 异步数据库引擎与 get_session 依赖
app/router/__init__.py  → 自动路由注册（递归扫描 app/api/）
app/middleware/          → 全局中间件（异常处理等）
app/test/               → pytest 测试，使用 SQLite 内存数据库
```

### 自动路由注册机制

`app/router/__init__.py` 递归扫描 `app/api/` 目录。新增路由只需：
1. 在 `app/api/v1/` 下创建 `.py` 文件
2. 定义 `{filename}_router` 对象（如 `auth.py` 中定义 `auth_router`）
3. 可选定义 `_prefix`、`_tag`、`_active` 模块级变量

无需手动注册，系统自动发现。

### 多租户 RBAC 模型

```
Tenant (1:N) User (M:N) Role (M:N) Permission
              ↑            ↑
           UserRole    RolePermission
```

- 用户通过 `tenant_id` 实现租户隔离
- 预置角色：admin、user
- 预置 12 个 CRUD 权限

### 数据库

- 生产：PostgreSQL + asyncpg（通过 `SQLALCHEMY_DATABASE_URI` 配置）
- 测试：SQLite 内存库 + aiosqlite（`conftest.py` 自动切换）
- 每个测试函数自动创建/清理表，通过 `dependency_overrides` 注入测试会话

### 认证

- JWT HS256，默认 7 天有效期
- 密码 bcrypt 哈希
- 邮箱验证（verification token）与密码重置（reset token，带过期）

## Adding New Features

新增 API 端点的标准流程：

1. `app/models/` 中定义 SQLModel 模型
2. `app/schemas/` 中定义 Pydantic 请求/响应 Schema
3. `app/services/` 中实现业务逻辑
4. `app/api/v1/` 中创建路由文件，导出 `{name}_router`
5. 在 `app/test/` 中编写测试
6. 如需数据库变更：`alembic revision --autogenerate -m "描述"`

## Testing Notes

- 测试通过 `conftest.py` 中的 `test_client` fixture 获得 FastAPI TestClient
- `setup_database` fixture 为每个测试函数自动建表/删表，测试间完全隔离
- 测试用的 app 只注册了认证相关路由（register、password、verify），非认证测试需自行添加路由
