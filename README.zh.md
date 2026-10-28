<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

# FastAPI Scaff Demo

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

基于 FastAPI 的多租户 RBAC 认证系统脚手架，采用 **DDD 四层架构 + 手动 DI 容器**。开箱即用：JWT 认证与刷新令牌轮换、**强制租户隔离**、用户↔角色↔权限三级 RBAC、用户管理、限流、邮箱验证、Alembic 迁移、Docker 与 CI。

## 特性亮点

| 能力 | 说明 |
|---|---|
| **认证** | JWT HS256：access 30 分钟 + refresh 7 天（`jti`/`iat`/`tenant_id` claim）；`/auth/refresh` 轮换令牌并**服务端吊销旧令牌**；access/refresh 类型严格隔离 |
| **多租户隔离** | JWT `tenant_id` 贯穿 路由 → 用例 → 仓储 强制过滤；**superuser 只豁免权限字符串检查，不豁免租户过滤**；跨租户访问一律 404（防枚举）；邮箱按 `(email, tenant_id)` 组合唯一 |
| **RBAC** | 用户↔角色↔权限真实持久化；`require_permissions("resource:action")` 端点级校验；权限集合进程内 60s TTL 缓存（单请求 DB 往返从 4~5 次降为 1 次），关联变更后立即失效 |
| **登录安全** | 按邮箱 + 按 IP 双重失败计数（Redis Lua 原子计数）；失败统一返回 `Invalid credentials`，账号不存在时执行占位 bcrypt 校验（恒时比较，防计时枚举）；开放端点另有 IP 限流 |
| **限流降级策略** | 开发环境 Redis 不可用 → 内存降级 + 告警；**生产环境 fail-closed**（拒绝放行，防止打挂 Redis 绕过限流） |
| **错误处理** | 领域异常全局映射：不存在→404、冲突→409、凭证无效→401、业务/校验错误→400、限流→429、未处理→500；响应统一带 `code` 字段 |
| **时间处理** | 实体、模型、用例统一 UTC aware（`DateTime(timezone=True)` 列），杜绝 naive/aware 混用 |
| **刷新令牌清理** | 过期记录由 lifespan 后台任务每小时清理，已移出请求热路径（无写放大） |
| **工程化** | Alembic 基线 + 增量迁移、Docker Compose、GitHub Actions CI、pre-commit、ruff、289 个测试全绿 |

## 架构

```
main.py                                 → 入口（uvicorn factory 模式）
│
├── src/                                → DDD 四层架构
│   ├── domain/                         →   领域层（纯 Python，零依赖）
│   │   ├── entities/                   →   实体（User, Tenant, Role, Permission）
│   │   ├── value_objects/              →   值对象（Email, Password, HashedPassword）
│   │   ├── repositories/               →   仓储接口（租户感知：find_by_id 强制 tenant_id）
│   │   ├── services/                   →   服务接口（PasswordHasher, JWTProvider, RateLimiter, EmailSender）
│   │   └── exceptions.py               →   领域异常体系（→ 4xx 全局映射）
│   ├── application/                    →   应用层（DTO + UseCase）
│   │   ├── dto/                        →   输入/输出 DTO
│   │   └── use_cases/                  →   注册、登录、刷新、改密、租户/角色/权限、RBAC 关联
│   ├── infrastructure/                 →   基础设施层（技术实现）
│   │   ├── persistence/
│   │   │   ├── database.py             →     异步 engine + session factory + init_db + session_scope
│   │   │   ├── sqlmodel/               →     ORM 模型 / 映射器 / 仓储（session-factory 模式）
│   │   │   │   └── models/time.py      →     UTC 时间工具（utcnow）
│   │   │   └── in_memory/              →     内存仓储（UseCase 单元测试用）
│   │   ├── security/                   →     JWT、bcrypt、Redis/内存限流、权限缓存
│   │   └── email/                      →     ConsoleEmailSender（token 邮件写入日志）
│   ├── api/                            →   API 适配层
│   │   ├── controllers/                →     Controller（Schema ↔ DTO）
│   │   ├── routes/                     →     Router + API 版本注册表
│   │   ├── schemas/                    →     Pydantic Schema（写请求 extra="forbid"）
│   │   └── middleware/                 →     认证/权限依赖、异常处理器
│   └── bootstrap/                      →   启动层
│       ├── config.py                   →     Pydantic Settings（.env / 环境变量）
│       ├── container.py                →     手动单例 DI 容器（cached_property 懒加载）
│       ├── lifespan.py                 →     App 工厂：建表 + admin 初始化 + 路由注册 + 后台清理任务
│       └── ensure_admin.py             →     默认租户 + admin 超级用户（失败即拒绝启动）
├── alembic/                            → 数据库迁移（baseline + 3 个增量）
├── tests/                              → 289 个测试（单元 + 集成，SQLite 内存库 / TestClient 全链路）
├── scripts/                            → smoke_test_rbac.py（全链路冒烟）、verify_alembic.py（迁移校验）
├── Dockerfile / docker-compose.yml     → 容器化（api + redis）
└── pyproject.toml                      → 依赖 & ruff/pytest 配置
```

**请求流转**（依赖方向严格向内）：

```
HTTP 请求
  → 路由（Depends 从 DI 容器取 Controller；认证依赖校验 JWT 并注入 current_user/tenant_id）
  → Controller（Schema ↔ DTO）
  → UseCase（业务规则；tenant_id 为显式参数，不从请求体盲信）
  → Repository（SQLModel 持久化实现，每操作独立会话）
```

**设计约束**：

- 路由不持有模块级可变全局——端点通过 `Depends(get_xxx_controller())` 直接向容器取 Controller；
- 租户上下文全程显式传递（不使用 contextvar）：JWT `tenant_id` → `get_current_user` 校验 → 路由 → UseCase → Repository；
- 创建租户内资源时 `tenant_id` 来自认证上下文，`RoleCreateRequest` / `AdminCreateUserRequest` 等 Schema 使用 `extra="forbid"`，禁止客户端指定 `tenant_id`；
- `domain/entities` 与 `sqlmodel/models` 分离，通过 `mappers/` 转换；模型不得反向依赖 `database.py`（避免 Alembic 同步上下文连带创建异步 engine）。

## 快速开始

```bash
# 安装依赖
pip install -e .

# 复制并填写配置（SECRET_KEY / ADMIN_PASSWORD 必填）
cp .env.example .env

# 启动开发服务器（热重载，自动建表 + 初始化 admin）
python main.py

# 或直接用 uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

访问 <http://localhost:8000/docs> 查看 Swagger UI，点击 **Authorize** 可用 `POST /api/v1/auth/token`（OAuth2 密码模式表单）登录调试。

## 常用命令

```bash
# 运行全部测试（289 个）
python run_tests.py
python -m pytest tests/ -v --tb=short

# 单元测试 / 集成测试
python -m pytest tests/unit/ -v --tb=short
python -m pytest tests/integration/ -v --tb=short

# 覆盖率
python -m pytest --cov=src --cov-report=term-missing tests/

# Lint 与自动修复
python -m ruff check src/ tests/
python -m ruff check src/ tests/ --fix

# 数据库迁移
alembic upgrade head                    # 应用迁移
python scripts/verify_alembic.py        # 校验迁移与 SQLModel 模型一致（自包含）

# 全链路冒烟（注册/登录/刷新令牌/RBAC/令牌吊销）
python scripts/smoke_test_rbac.py
```

## API 接口

所有业务路由前缀为 `/api/v1`（版本注册表见 `src/api/routes/__init__.py`）。

| 方法与路径 | 鉴权 | 说明 |
|---|---|---|
| GET `/health` | 无 | 健康检查（部署探活） |
| POST `/api/v1/auth/register` | IP 限流 10 次/小时 | 注册；`tenant_id` 可选，为空自动创建独立租户；指定租户必须存在且激活 |
| POST `/api/v1/auth/login` | 邮箱 + IP 限流 | 登录，返回 access + refresh token；停用租户/失活用户统一拒绝 |
| POST `/api/v1/auth/login/json` | 同上 | 登录（OAuth2 兼容响应） |
| POST `/api/v1/auth/token` | 同上（表单） | OAuth2 密码模式令牌（Swagger Authorize 使用） |
| POST `/api/v1/auth/refresh` | 服务端吊销校验 | 轮换刷新令牌；旧令牌立即失效；token 内 `tenant_id` 与用户校验 |
| POST `/api/v1/password/forgot` | IP 限流 5 次/小时 | 忘记密码（token 经邮件发送，不落响应体） |
| POST `/api/v1/password/reset` | 无 | 使用 token 重置密码 |
| POST `/api/v1/password/change` | 登录 | 修改**自己的**密码（身份取自 JWT，不接受 `user_id`） |
| POST `/api/v1/verify/email` | 无 | 邮箱验证 |
| POST `/api/v1/verify/resend` | IP 限流 5 次/小时 | 重发验证邮件 |
| GET `/api/v1/tenants`、`GET /tenants/{id}` | superuser | 租户读取（平台级资源，防匿名枚举） |
| POST/PUT/DELETE `/api/v1/tenants` | `tenant:*` 权限 | 租户管理 |
| GET/POST/PUT/DELETE `/api/v1/roles` | 读：登录；写：`role:*` | 角色管理——**仅限调用者租户**；跨租户返回 404 |
| POST `/api/v1/roles/{role_id}/users/{user_id}` | `role:update` | 分配角色给用户（角色与用户须同属调用者租户） |
| GET/POST/PUT/DELETE `/api/v1/permissions` | 读：登录；写：`permission:*` | 权限管理（全局目录） |
| POST `/api/v1/permissions/{permission_id}/roles/{role_id}` | `permission:update` | 分配权限给角色（角色须属于调用者租户） |
| GET/PUT `/api/v1/user/me` | 登录 | 当前用户信息 / 更新邮箱 |
| GET/POST/PUT/DELETE `/api/v1/user` | superuser | 用户管理——**仅限调用者租户** |

## 租户隔离（强制约束）

这是本项目的核心设计，所有租户内资源都遵循：

1. **上下文显式传递**：JWT `tenant_id` → `get_current_user`（校验与数据库用户一致）→ 路由 → Controller → UseCase → Repository，全程显式参数，不使用 contextvar；
2. **隔离对所有人生效**：superuser 只豁免权限字符串检查，不豁免租户过滤；跨租户读写返回 **404**（与"资源不存在"语义一致，防止枚举探测）；
3. **仓储租户感知**：`UserRepository.find_by_id(user_id, tenant_id)`、`RoleRepository.find_by_id(role_id, tenant_id)` 等强制租户参数；用户/角色列表走 `find_by_tenant`，不存在无租户过滤的 `find_all`；
4. **数据库层兜底**：`users` 表 `(email, tenant_id)` 组合唯一；`user_roles`、`role_permissions` 关联表唯一约束 + 索引（防并发重复分配）；
5. **关联操作双端校验**：分配角色时校验用户与角色同租户；分配权限时校验角色归属当前租户。

## 认证与安全

- **JWT**：HS256，access 30 分钟 + refresh 7 天（`jti`/`iat`/`tenant_id`）；`get_current_user` 只接受 `type=access` 的令牌，并按 `(user_id, tenant_id)` 查库校验一致性；
- **刷新令牌轮换**：每次刷新吊销旧 `jti` 并登记新 `jti`；旧令牌立即返回 401；过期记录由后台任务每小时清理；
- **限流**：
  - 登录失败按**邮箱**（UseCase 内）+ 按 **IP**（路由层）双维度计数，超出返回 429；
  - 存储基于本地 **Redis**（Lua 原子计数，多进程共享，重启不清零）；
  - 开发环境 Redis 不可用时降级为内存实现并告警；**生产环境 fail-closed**；
  - 开放端点 IP 限流：注册 10 次/小时、忘记密码与重发验证 5 次/小时；
- **防枚举**：登录失败统一 `Invalid credentials`（不区分账号不存在/密码错误/账号失活/邮箱未验证）；账号不存在时对占位哈希执行一次 bcrypt 校验（恒时比较）；
- **权限缓存**：`require_permissions` 使用进程内 60s TTL 权限缓存（上限 1 万条，防随机 key 撑爆内存）；角色/权限分配接口在路由层立即清空缓存；
- **错误响应**：全局异常处理器统一映射为 `{"detail": ..., "code": <status>}`，路由层不再逐端点 try/except（唯一例外：登录路由捕获 `InvalidCredentialsError` 做按 IP 失败计数后重抛）；
- **生产安全**：`ENVIRONMENT=production` 时未显式设置 `SECRET_KEY` 拒绝启动；建表失败与 admin 初始化失败均**直接终止启动**（不允许带病启动）；
- **Token 不落响应体**：重置/验证 token 只通过 `EmailSender` 发送（当前为 ConsoleEmailSender 写日志，可替换为 SMTP 实现）。

## 配置说明

通过环境变量或 `.env` 文件配置（`main.py` 启动时自动加载；未列出的变量会被忽略）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ENVIRONMENT` | `development` | 运行环境（`production` 强制校验 `SECRET_KEY`、限流 fail-closed） |
| `SECRET_KEY` | dev 默认值 | JWT 签名密钥，生产必须显式设置（`openssl rand -hex 32`） |
| `ALGORITHM` | `HS256` | JWT 算法 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | 数据库连接（生产建议 PostgreSQL + asyncpg） |
| `REDIS_URL` | `redis://localhost:6379/0` | 限流存储 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | access token 有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | refresh token 有效期 |
| `MAX_LOGIN_ATTEMPTS` | `5` | 登录限流阈值 |
| `LOGIN_LOCKOUT_MINUTES` | `30` | 登录锁定窗口 |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | 是否强制邮箱验证（开启后未验证用户不能登录） |
| `SERVER_HOST` / `SERVER_PORT` | `0.0.0.0` / `8000` | `python main.py` 监听地址/端口 |
| `SERVER_RELOAD` | `true` | 开发热重载（生产建议 `false`） |
| `LOG_LEVEL` / `LOG_FILE` | `INFO` / 空 | 日志级别；可选日志文件路径（空则仅控制台） |
| `CORS_ORIGINS` | 本地 localhost 集合 | 允许的 CORS 来源（逗号分隔） |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | `admin@example.com` / `Admin123456` | 启动时自动创建的 admin 账号（生产务必修改） |
| `ADMIN_IS_SUPERUSER` | `true` | admin 是否超级用户 |

## 数据库与迁移

- 默认 SQLite（`sqlite+aiosqlite:///./test.db`），生产通过 `DATABASE_URL` 切换 PostgreSQL + asyncpg；
- 启动时 `init_db()` 用 `create_all` 建表（开发便捷）；正式变更走 Alembic：

| 迁移 | 内容 |
|---|---|
| `742419bf3b87` baseline | 7 张表：users / tenants / roles / permissions / user_roles / role_permissions / refresh_tokens |
| `8f3c2a1b9d4e` tenant_isolation_constraints | `(email, tenant_id)` 唯一、关联表唯一约束与索引 |
| `4c1e9d7f2a58` utc_datetime_columns | 时间列统一为 `DateTime(timezone=True)` |
| `9e5b3c8d1f27` drop_user_legacy_columns | 删除 `username`、`failed_login_attempts`、`locked_until` 等遗留字段 |

```bash
alembic upgrade head               # 应用到最新
python scripts/verify_alembic.py   # 断言迁移建表 == SQLModel 元数据
```

## 测试与质量保障

- **289 个测试全部通过**：单元测试使用**真实 InMemory 仓储 + 确定性假依赖**（而非 MagicMock，避免掩盖实体字段不匹配类 bug）；集成测试使用 SQLite 内存库 + `StaticPool`，API 层用 `TestClient` 走全链路；
- 覆盖：实体/值对象、仓储（内存 + SQLModel）、UseCase、路由鉴权与错误格式、限流、JWT、权限缓存、租户隔离（双租户 IDOR 场景）、refresh token 吊销与过期清理；
- **Lint**：`ruff`（`E/F/I/W`，行宽 120）；**pre-commit** 钩子已配置；
- **CI**（`.github/workflows/ci.yml`）：ruff → pytest → 覆盖率 → 迁移一致性校验 → 全链路冒烟；
- 参考：[`docs/architecture-audit.md`](docs/architecture-audit.md)（架构审计报告与分阶段加固计划）。

## 新增功能

遵循 DDD 四层流程：

1. **领域层** `src/domain/` — 定义实体、值对象、仓储接口、领域异常
2. **基础设施层** `src/infrastructure/` — 实现仓储（SQLModel + InMemory 双实现）、安全服务
3. **应用层** `src/application/` — 创建 DTO 和 UseCase（业务失败抛 `DomainError` 子类）
4. **API 层** `src/api/` — 创建 Schema、Controller、Routes（权限端点挂 `require_permissions`）
5. **启动层** `src/bootstrap/` — 在 `container.py` 注册依赖、在 `routes/__init__.py` 注册路由
6. **测试** `tests/` — 单元测试（真实 InMemory 仓储）+ 集成测试（SQLite 内存库）

## Docker

```bash
docker compose up --build   # api（8000 端口）+ redis，production 模式
```

compose 以 `ENVIRONMENT=production` 运行 API（限流 fail-closed，需提供 `SECRET_KEY`），SQLite 数据挂载到 `/data` 持久化卷，并在 Redis 健康检查通过后才启动 API。

## 已知限制

- 无真实 SMTP 邮件发送（token 写入日志），可替换 `EmailSender` 实现；
- JWT 未包含 `iss`/`aud`/`pwd_version` claim，修改密码后旧 access token 在有效期内（≤30 分钟）仍可用；
- 跨仓储操作非原子（如注册时"自动建租户 + 建用户"为两个独立事务，已做补偿回滚；登录时"登记 refresh token + 更新 last_login"同理），未引入 Unit of Work；
- 权限缓存为进程内实现，多 worker 部署时各进程独立（权限变更在本进程立即生效，其他进程最多延迟 TTL）；
- refresh token 过期清理为每进程一个后台任务（多 worker 下重复执行，但删除操作幂等）。

## 技术栈

FastAPI + Uvicorn · SQLModel/SQLAlchemy async · JWT（PyJWT）+ bcrypt · Pydantic Settings · Redis · Alembic · pytest + pytest-asyncio + httpx · ruff · Docker / GitHub Actions

## 许可证

MIT
