# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI 多租户 RBAC 认证系统脚手架，基于 SQLModel（SQLAlchemy + Pydantic），异步架构，采用 **DDD 四层架构 + 手动 DI 容器**（`src/` 层）。

## Commands

```bash
# 启动开发服务器（热重载；自动建表 + 初始化 admin）
python main.py

# 运行全部测试
python run_tests.py
python -m pytest tests/ -v --tb=short

# 单元测试 / 集成测试
python -m pytest tests/unit/ -v --tb=short
python -m pytest tests/integration/ -v --tb=short

# Lint
python -m ruff check src/ tests/

# 冒烟测试
python scripts/smoke_test_rbac.py
```

## Architecture

### 分层结构

```
main.py                 → 入口，启动 uvicorn（factory 模式）
src/
├── domain/             → 领域层：实体、值对象、仓储接口、服务接口
├── infrastructure/     → 基础设施层：持久化（SQLModel/InMemory）、安全（JWT/bcrypt/限流）、邮件
├── application/        → 应用层：DTO、Use Cases
├── api/                → API 层：Schema、Controller、Routes、认证/权限依赖
└── bootstrap/          → 启动层：DI 容器、配置、App 工厂 & 生命周期
```

### DI 容器

`src/bootstrap/container.py` 手动单例容器（`@cached_property` 懒加载）。仓储绑定 `async_session_maker`，每次操作独立会话（`session_scope`），适配单例容器。测试注入 `container.user_repository = X`，`container.reset()` 清空缓存。

### 认证与 RBAC

- JWT HS256：access 30 分钟 + refresh 7 天（`jti`/`iat`/`tenant_id` claim），`POST /api/v1/auth/refresh` 轮换
- `get_current_user` 只接受 `type=access` 令牌并校验 token 内 `tenant_id` 与用户一致；`require_permissions("resource:action")` 端点级权限校验（superuser 放行但不豁免租户隔离）
- 登录限流：按邮箱 + 按 IP 计数失败尝试，超出返回 429；开放端点 IP 限流（注册 10/h、forgot/resend 5/h）；生产环境 Redis 不可用限流 fail-closed
- 登录防枚举：失败统一 "Invalid credentials" + 占位哈希恒时比较
- 重置/验证 token 经 `EmailSender`（ConsoleEmailSender 写日志）发送，不落响应体
- 生产环境（`ENVIRONMENT=production`）未显式设置 `SECRET_KEY` 拒绝启动

### 租户隔离（强制约束）

- 租户上下文显式传递：JWT `tenant_id` → 路由 → Controller → UseCase → Repository，全程显式参数（不使用 contextvar）
- 隔离对所有人生效（superuser 不豁免）；跨租户访问返回 404（防枚举）
- 仓储接口租户感知：`find_by_id(user_id, tenant_id)` 等强制租户参数；无租户的 `find_all` 不存在（列表走 `find_by_tenant`）
- 创建资源租户来自认证上下文（Role/User 请求体不接受 `tenant_id`，Schema `extra="forbid"`）
- 邮箱按租户唯一（`UniqueConstraint(email, tenant_id)`）
- 关联操作双端校验（`AssignRoleToUserUseCase` 校验 user 与 role 同属当前租户）

### 业务异常体系

`src/domain/exceptions.py`：`DomainError`（继承 `ValueError`）→ `EntityNotFoundError`(404) / `ConflictError`(409) / `InvalidCredentialsError`(401) / `InvalidInputError`(400)；全局 handler 统一映射，路由不做逐端点 try/except。

### 数据库

- 默认 SQLite（`sqlite+aiosqlite:///./test.db`），生产通过 `DATABASE_URL` 换 PostgreSQL + asyncpg
- `init_db()` 启动建表；`src/domain/entities/` 与 `sqlmodel/models/` 通过 `mappers/` 转换
- 时间统一 UTC aware（`models/time.py:utcnow()`，列 `DateTime(timezone=True)`）；迁移用 Alembic（`alembic upgrade head`）

## Adding New Features

新增 API 端点的标准流程（DDD 四层）：

1. `src/domain/` — 定义实体、值对象、仓储接口
2. `src/infrastructure/` — 实现仓储（SQLModel + InMemory 双实现）、安全服务
3. `src/application/` — 创建 DTO 和 UseCase
4. `src/api/` — 创建 Schema、Controller、Routes
5. `src/bootstrap/` — 在 `container.py` 注册依赖，在 `lifespan.py` 注入 Controller 并注册路由
6. `tests/unit/`（真实 InMemory 仓储）与 `tests/integration/` 编写测试

## Testing Notes

- 单元测试使用**真实 InMemory 仓储 + 确定性假依赖**（`FakePasswordHasher`、`RecordingEmailSender`），避免 MagicMock 掩盖 bug
- 集成测试使用 SQLite 内存库 + StaticPool，每个测试函数自动建表/删表（`tests/integration/conftest.py`）
- 冒烟脚本 `scripts/smoke_test_rbac.py` 覆盖注册/登录/刷新令牌/RBAC/持久化全链路
- Lint 用 ruff（配置见 `pyproject.toml`）
