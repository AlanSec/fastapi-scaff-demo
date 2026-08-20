<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

# FastAPI Scaff Demo

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

基于 FastAPI 的多租户 RBAC 认证系统脚手架，采用 **DDD 四层架构 + 手动 DI 容器**，开箱即用地提供认证、租户隔离、角色权限管理与用户管理能力。

## 架构

```
main.py                                 → 入口（uvicorn factory 模式）
│
├── src/                                → DDD 四层架构
│   ├── domain/                         →   领域层（纯 Python，零依赖）
│   │   ├── entities/                   →   实体（User, Tenant, Role, Permission）
│   │   ├── value_objects/              →   值对象（Email, Password, HashedPassword）
│   │   ├── repositories/               →   仓储接口（抽象协议）
│   │   └── services/                   →   服务接口（PasswordHasher, JWTProvider, RateLimiter, EmailSender）
│   ├── application/                    →   应用层（DTO + UseCase）
│   │   ├── dto/                        →   输入/输出 DTO
│   │   └── use_cases/                  →   注册、登录、刷新令牌、改密、租户/角色/权限管理、RBAC 关联
│   ├── infrastructure/                 →   基础设施层（技术实现）
│   │   ├── persistence/                →     持久化（SQLModel 仓储 + InMemory 测试实现）
│   │   │   ├── database.py             →     异步 engine + session factory + init_db
│   │   │   ├── sqlmodel/               →     SQLModel ORM 模型/映射器/仓储
│   │   │   └── in_memory/              →     内存仓储（UseCase 单元测试用）
│   │   ├── security/                   →     JWT、bcrypt、限流
│   │   └── email/                      →     ConsoleEmailSender（邮件写入日志）
│   ├── api/                            →   API 适配层
│   │   ├── controllers/                →     Controller（请求/响应 ↔ DTO）
│   │   ├── routes/                     →     FastAPI Router
│   │   ├── schemas/                    →     Pydantic Schema
│   │   └── middleware/                 →     认证/权限依赖（get_current_user, require_permissions）
│   └── bootstrap/                      →   启动层
│       ├── config.py                   →     Pydantic Settings（.env / 环境变量）
│       ├── container.py                →     手动单例 DI 容器
│       ├── lifespan.py                 →     App 工厂 + 建表 + 初始化 admin
│       └── ensure_admin.py             →     默认租户 + admin 超级用户
├── tests/                              → 单元测试（~200）+ 集成测试（SQLite 内存库）
├── scripts/smoke_test_rbac.py          → 全链路冒烟测试脚本
└── pyproject.toml                      → 项目元数据 & ruff/pytest 配置
```

## 快速开始

```bash
# 安装依赖
pip install -e .

# 启动开发服务器（热重载，自动建表 + 初始化 admin）
python main.py

# 或直接用 uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

## 常用命令

```bash
# 运行全部测试
python run_tests.py
python -m pytest tests/ -v --tb=short

# 单元测试 / 集成测试
python -m pytest tests/unit/ -v --tb=short
python -m pytest tests/integration/ -v --tb=short

# 覆盖率
python -m pytest --cov=src --cov-report=term-missing tests/

# Lint
python -m ruff check src/ tests/
```

## API 接口

所有路由以 `/api/v1` 为前缀。

| 端点 | 说明 |
|---|---|
| GET `/health` | 健康检查（部署探活，不鉴权） |
| POST `/api/v1/auth/register` | 用户注册（tenant_id 可选，为空自动创建独立租户） |
| POST `/api/v1/auth/login` | 登录，返回 JWT access + refresh token |
| POST `/api/v1/auth/token` | OAuth2 密码模式令牌（表单，支持 Swagger Authorize） |
| POST `/api/v1/auth/login/json` | 登录（OAuth2 兼容响应） |
| POST `/api/v1/auth/refresh` | 刷新令牌（refresh token 换新令牌） |
| POST `/api/v1/password/forgot` \| `/reset` \| `/change` | 忘记/重置/修改密码（token 通过邮件发送，不落响应体） |
| POST `/api/v1/verify/email` \| `/resend` | 邮箱验证 / 重发验证邮件 |
| GET/POST/PUT/DELETE `/api/v1/tenants` | 租户管理（写操作需 `tenant:create` 等权限） |
| GET/POST/PUT/DELETE `/api/v1/roles` | 角色管理（写操作需 `role:*` 权限） |
| POST `/api/v1/roles/{role_id}/users/{user_id}` | 角色分配给用户（需 `role:update`） |
| GET/POST/PUT/DELETE `/api/v1/permissions` | 权限管理（写操作需 `permission:*` 权限） |
| POST `/api/v1/permissions/{permission_id}/roles/{role_id}` | 权限分配给角色（需 `permission:update`） |
| GET/PUT `/api/v1/user/me` | 当前用户信息（需登录） |
| GET/POST/PUT/DELETE `/api/v1/user` | 管理员用户管理（需 superuser） |

## 安全特性

- **认证**：JWT HS256，access 30 分钟 + refresh 7 天（含 `jti`/`iat` claim）；refresh token 不能当 access token 使用；`/auth/refresh` 轮换令牌并**服务端吊销旧令牌**（落库 `refresh_tokens` 表，每次写入顺带清理过期记录，防止表无限增长）
- **密码**：bcrypt 哈希 + 强度校验（8 位以上、含大小写与数字）
- **登录限流**：按邮箱 + 按 IP 计数失败尝试，超出返回 429；基于**本地 Redis**（Lua 原子计数，多进程共享，重启不清零），Redis 不可用时自动降级为内存实现并告警（`MAX_LOGIN_ATTEMPTS` / `LOGIN_LOCKOUT_MINUTES` / `REDIS_URL` 可配置）
- **RBAC**：用户↔角色↔权限三级关联，`require_permissions("resource:action")` 依赖做端点级校验（superuser 放行）
- **生产安全**：`ENVIRONMENT=production` 时未显式设置 `SECRET_KEY` 拒绝启动
- **Token 不落响应体**：重置/验证 token 通过 `EmailSender` 发送（当前为 ConsoleEmailSender 写日志，可替换为 SMTP 实现）

## 配置说明

通过环境变量或 `.env` 文件配置（`main.py` 启动时自动加载 `.env`）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ENVIRONMENT` | `development` | 运行环境（production 强制校验 SECRET_KEY） |
| `SECRET_KEY` | dev 默认值 | JWT 密钥，生产必须显式设置 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | 数据库连接（生产建议 PostgreSQL asyncpg） |
| `REDIS_URL` | `redis://localhost:6379/0` | 限流存储（不可用时自动降级内存） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | access token 有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | refresh token 有效期 |
| `MAX_LOGIN_ATTEMPTS` | `5` | 登录限流阈值 |
| `LOGIN_LOCKOUT_MINUTES` | `30` | 登录锁定窗口 |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | 是否强制邮箱验证（开启后未验证用户不能登录） |
| `SERVER_HOST` / `SERVER_PORT` | `0.0.0.0` / `8000` | `python main.py` 监听地址/端口 |
| `SERVER_RELOAD` | `true` | 开发热重载（生产建议 `false`） |
| `CORS_ORIGINS` | 本地 localhost 集合 | 允许的 CORS 来源（逗号分隔） |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | - | 启动时自动创建的 admin 账号 |

## 新增功能

遵循 DDD 四层流程：

1. **领域层**（`src/domain/`）— 定义实体、值对象、仓储接口
2. **基础设施层**（`src/infrastructure/`）— 实现仓储、安全服务
3. **应用层**（`src/application/`）— 创建 DTO 和 UseCase
4. **API 层**（`src/api/`）— 创建 Schema、Controller、路由
5. **启动层**（`src/bootstrap/`）— 在容器中注册依赖；路由通过 `Depends` 直接向容器取 Controller，无需手动注入
6. **测试**（`tests/`）— 单元测试（真实仓储实现，避免 mock 掩盖 bug）+ 集成测试

## 已知限制

- 无真实 SMTP 邮件发送（token 写入日志），可替换 `EmailSender` 实现

## 技术栈

FastAPI + Uvicorn · SQLModel/SQLAlchemy async · JWT + bcrypt · Pydantic Settings · pytest + pytest-asyncio + httpx · ruff

## 许可证

MIT
