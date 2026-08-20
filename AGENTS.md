# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

FastAPI 多租户 RBAC 认证系统脚手架，采用 **DDD 四层架构 + 手动 DI 容器**（`src/` 层，无遗留代码）。

## Commands

```bash
# 启动开发服务器（热重载，uvicorn factory 模式；自动建表 + 初始化 admin）
python main.py

# 运行全部测试（单元 + 集成）
python run_tests.py
python -m pytest tests/ -v --tb=short

# 单元测试（无数据库依赖，UseCase 用真实 InMemory 仓储）
python -m pytest tests/unit/ -v --tb=short

# 集成测试（SQLite 内存库，验证 SQLModel 仓储）
python -m pytest tests/integration/ -v --tb=short

# 覆盖率
python -m pytest --cov=src --cov-report=term-missing tests/

# Lint（ruff）
python -m ruff check src/ tests/
python -m ruff check src/ tests/ --fix

# 冒烟测试（全链路：注册/登录/刷新令牌/RBAC，走真实 SQLite 文件库）
python scripts/smoke_test_rbac.py
```

## Architecture

```
main.py                                 → 入口，uvicorn factory 模式
│
├── src/                                → DDD 四层架构
│   ├── domain/                         →   领域层（纯 Python，零依赖）
│   │   ├── entities/                   →   领域实体（User, Tenant, Role, Permission）
│   │   ├── value_objects/              →   值对象（Email, Password, HashedPassword）
│   │   ├── repositories/               →   仓储接口（抽象协议）
│   │   └── services/                   →   服务接口（PasswordHasher, JWTProvider, RateLimiter, EmailSender）
│   ├── application/                    →   应用层（用例编排）
│   │   ├── dto/                        →   输入/输出 DTO
│   │   └── use_cases/                  →   注册、登录、刷新令牌、改密、租户/角色/权限、RBAC 关联
│   ├── infrastructure/                 →   基础设施层（技术实现）
│   │   ├── persistence/
│   │   │   ├── database.py             →     异步 engine + session factory + init_db + session_scope
│   │   │   ├── sqlmodel/               →     SQLModel ORM 模型 / mapper / 仓储（session-factory 模式）
│   │   │   └── in_memory/              →     仓储内存实现（UseCase 单元测试用）
│   │   ├── security/                   →     JWT、bcrypt、内存限流
│   │   └── email/                      →     ConsoleEmailSender（token 邮件写入日志）
│   ├── api/                            →   API 适配层
│   │   ├── controllers/                →     Controller（请求/响应转 DTO）
│   │   ├── routes/                     →     FastAPI Router 定义
│   │   ├── schemas/                    →     Pydantic 请求/响应 Schema
│   │   └── middleware/                 →     认证/权限依赖（get_current_user, require_permissions）
│   └── bootstrap/                      →   启动层
│       ├── config.py                   →     Pydantic Settings（ENVIRONMENT 生产强校验 SECRET_KEY）
│       ├── container.py                →     手动单例 DI 容器（懒加载属性）
│       ├── lifespan.py                 →     App 工厂：init_db 建表 + ensure_admin + 路由注册
│       └── ensure_admin.py             →     默认租户 + admin 超级用户
│
└── tests/                              → 单元测试（真实 InMemory 仓储）+ 集成测试（SQLite 内存库）
```

### 路由注册机制

所有路由在 `src/bootstrap/lifespan.py:create_app()` 中手动注册：

```python
app.include_router(auth_router, prefix="/api/v1")
app.include_router(password_router, prefix="/api/v1")
...
```

路由端点通过 `Depends(get_xxx_controller())` 直接向 DI 容器取 Controller（如 `get_role_controller() -> get_container().role_controller`），**无模块级可变全局**；lifespan 只负责建表与初始化 admin，不再注入 Controller。

### DI 容器模式

`src/bootstrap/container.py` 实现**手动单例容器**：

- `Container` 类：懒加载属性，`get_container()` 返回全局单例
- 依赖链：UseCase 依赖 Repository + Hasher/JWT/RateLimiter/EmailSender → Controller 依赖 UseCase → 路由通过 `Depends` 从容器取 Controller
- 持久化：SQLModel 仓储绑定 `async_session_maker`，**每次操作独立会话**（`session_scope`），适配单例容器
- 认证：`get_current_user`（只接受 type=access 的 JWT）→ `require_permissions("resource:action")`（superuser 放行）

### 持久化

- `src/infrastructure/persistence/database.py`：`engine` / `async_session_maker` / `init_db()`（启动建表）/ `session_scope()`
- SQLModel 仓储 `save()` 为"存在则更新、不存在则插入"（先 `session.get` 判断）
- `src/domain/entities/` 纯 Python 实体与 `sqlmodel/models/` ORM 模型分离，通过 `mappers/` 转换
- 默认数据库 `sqlite+aiosqlite:///./test.db`，生产通过 `DATABASE_URL` 换 PostgreSQL

### 认证与安全

- JWT HS256：access 30 分钟 + refresh 7 天，含 `jti`/`iat` claim；`/auth/refresh` 轮换令牌
- 登录限流：按邮箱（UseCase 内）与按 IP（路由层）计数失败尝试，超出抛 `RateLimitExceeded` → 429
- 重置/验证 token 通过 `EmailSender` 发送（ConsoleEmailSender 写日志），不落 API 响应体
- `ENVIRONMENT=production` 时未显式设置 `SECRET_KEY` 拒绝启动

## Adding New Features

新增 API 端点的四层流程：

1. **领域层** `src/domain/` — 定义实体、值对象、仓储接口
2. **基础设施层** `src/infrastructure/` — 实现仓储（SQLModel + InMemory 双实现）、安全服务
3. **应用层** `src/application/` — 创建 DTO 和 UseCase
4. **API 层** `src/api/` — 创建 Schema、Controller、Routes（权限端点挂 `require_permissions`）
5. **启动层**：在 `container.py` 注册新依赖，在 `lifespan.py` 注册路由（路由端点用 `Depends(get_xxx_controller())` 从容器取 Controller）
6. 在 `tests/unit/`（真实 InMemory 仓储）和 `tests/integration/` 中编写测试

## Testing Notes

- 单元测试用**真实 InMemory 仓储 + 确定性假 hasher**（如 `FakePasswordHasher`、`RecordingEmailSender`），**避免用 MagicMock 掩盖实体字段不匹配类 bug**
- 集成测试（`tests/integration/`）用 `sqlite+aiosqlite:///:memory:` + StaticPool，每个测试函数自动建表/删表
- `tests/integration/conftest.py` 提供 `db_session` / `default_tenant` / `test_user` / `admin_role` fixtures
- 冒烟脚本 `scripts/smoke_test_rbac.py`：TestClient 全链路（注册/登录/刷新/RBAC/持久化），先删 `smoke_test.db` 再跑
- 数据库表变更：启动时 `init_db()` 用 `create_all` 自动建表；正式迁移用 Alembic（`alembic/env.py` 已指向 `src` 模型，baseline 迁移已生成，`alembic upgrade head` 可用）

## API 版本管理

项目采用 URL 版本管理，统一 `/api/v1/` 前缀。未来扩展 v2：创建新路由模块，注册到 `/api/v2/` 下。
