# 架构审计报告 — fastapi-scaff-demo

> 审计日期：本次会话 | 基线：`a0ca66b` | 验证：253 个测试全绿、`ruff check` 零告警
>
> 严重程度：**P0 = 阻断/高危（安全、数据完整性、可运行性）** ｜ P1 = 高（安全/正确性） ｜ P2 = 中（设计/性能/一致性） ｜ P3 = 低（工程化/体验）

---

## 一、总体评价

**优点（值得保留的做法）：**

1. **DDD 四层划分干净**：`domain/` 层纯 Python 零依赖（实体 + 值对象 + 仓储/服务接口），依赖方向严格向内，是教科书式骨架。
2. **双仓储实现策略正确**：单元测试用真实 `InMemory` 仓储而非 MagicMock，能抓住"实体字段不匹配"类 bug；集成测试用 SQLite 内存库 + StaticPool。
3. **无模块级可变全局**：路由通过 `Depends(get_xxx_controller())` 从容器取依赖，`lifespan` 只做建表和初始化。
4. **测试覆盖扎实**：253 个用例覆盖实体、值对象、仓储、UseCase、路由、限流、JWT、容器，且全部通过。
5. **安全基础动作到位**：refresh token 轮换 + 服务端吊销、access/refresh 类型隔离、登录限流（邮箱 + IP）、生产强制 `SECRET_KEY`、错误响应统一带 `code`。
6. **工程化就绪**：Alembic 基线迁移可用、ruff 配置、冒烟脚本、中文/英文文档。

**核心结论：**

> 骨架质量高，但 **"多租户"目前只是 `tenant_id` 字段，没有真正的租户隔离**；同时存在 **5 个 P0 级问题**（其中 2 个是公开安全漏洞、1 个依赖缺口会导致干净环境无法启动、1 个会产生脏数据/生产 500、1 个是架构级 IDOR 缺陷）。上线前必须先修 P0。

---

## 二、P0 — 紧急修复（安全 / 数据完整性 / 可运行性）

### P0-1 依赖缺口：PyJWT 未声明，干净环境 ImportError 🔴

- **位置**：`src/infrastructure/security/jwt_provider.py:6`（`import jwt`）
- **问题**：代码使用 PyJWT，但 `pyproject.toml` 与 `requirements.txt` 均无 PyJWT；`requirements.txt` 中的 `python-jose==3.5.0` 是未使用的遗留依赖。当前机器恰好装有 PyJWT 2.10.1 才未暴露。**`pip install -r requirements.txt` 后在干净环境启动即 `ModuleNotFoundError`**。
- **修复**：`pyproject.toml` 加 `pyjwt>=2.10`，移除 `python-jose`；重新生成 `requirements.txt` / `uv.lock`；CI 中用全新 venv 验证。

### P0-2 公开漏洞：`/api/v1/password/change` 未鉴权，`user_id` 客户端可控 🔴

- **位置**：`src/api/routes/password_routes.py:49-55`
- **问题**：`change_password` 端点**没有任何认证依赖**，且 `user_id` 是客户端可指定的 **query 参数**（路径中没有 `{user_id}`）。虽然 UseCase 会校验 `current_password`，但"修改谁的密码"完全由调用方决定——身份上下文本应来自 JWT。一旦攻击者掌握受害者当前密码（撞库、社工），该端点即成为任意账号密码修改入口。
- **修复**：
  ```python
  @password_router.post("/change", response_model=ChangePasswordResponse)
  async def change_password(
      request: ChangePasswordRequest,
      current_user: User = Depends(get_current_active_user),
      controller: PasswordController = Depends(get_password_controller),
  ):
      return await controller.change_password(request, current_user.id)
  ```
  控制器签名去掉 `user_id` 参数，UseCase 保持不变。补集成测试：未登录调用返回 401。

### P0-3 公开漏洞：租户/角色/权限**读端点匿名可访问** 🔴

- **位置**：`src/api/routes/tenant_routes.py:35-52`、`role_routes.py:35-52`、`permission_routes.py:35-52`
- **问题**：`GET /api/v1/tenants`、`GET /api/v1/tenants/{id}`、`GET /api/v1/roles...`、`GET /api/v1/permissions...` **无任何认证**。任何匿名访客可枚举全部租户（名称、域名）、角色、权限——多租户系统的租户清单本身就是敏感信息。
- **根因**：`tests/integration/api/conftest.py:50-55` 的 `get_default_tenant_id` 与 `scripts/smoke_test_rbac.py:22` 都在**匿名调用该端点**，测试固化了不安全行为。
- **修复**：
  1. 读端点至少挂 `Depends(get_current_active_user)`；跨租户管理类读端点挂 `require_permissions("tenant:read")` 等。
  2. 测试辅助函数改为直接查仓储取默认租户 ID（或用 admin 令牌），不再匿名调用 API。

### P0-4 数据完整性：`CreateRoleUseCase` 丢失 `tenant_id` 🔴

- **位置**：`src/application/use_cases/role_use_case.py:27` → `src/domain/entities/role.py:24-33`
- **问题**：`Role.create(name=name, description=dto.description)` **没有传入 `dto.tenant_id`**，而 `Role.create` 在 `tenant_id=None` 时执行 `tenant_id or uuid4()` **随机生成一个不存在的租户 ID**。结果：
  - SQLite（默认不启用外键约束）：静默写入指向不存在租户的角色 → **脏数据**；
  - PostgreSQL：外键约束直接 `ForeignKeyViolation` → **500**。
  - 且 `find_by_name(name, dto.tenant_id)` 按租户查重、创建却不按租户，行为自相矛盾。冒烟测试恰好传了 `tenant_id`，掩盖了 bug。
- **修复**：
  1. `CreateRoleUseCase.execute` 改为 `Role.create(name=name, description=dto.description, tenant_id=dto.tenant_id)`；
  2. **删除 `Role.create` 的 `tenant_id or uuid4()` 兜底**——域对象不应生成指向不存在实体的外键，`tenant_id` 改为必填（或由调用方显式传入）；
  3. 补单元测试：创建角色后断言 `role.tenant_id == dto.tenant_id`；补集成测试：SQLite 下验证角色属于指定租户。

### P0-5 架构级：多租户数据隔离（IDOR）缺失 🔴

- **位置**：`src/api/middleware/auth_dependencies.py:76-91`（`require_permissions`）及全部 tenant/role/permission/user-admin 管理端点
- **问题**：`require_permissions("role:update")` 只校验**权限字符串**，不校验目标资源是否属于调用者所在租户。租户 A 的角色管理员（拥有 `role:update`）只要知道 UUID，就能 `PUT /api/v1/roles/{tenantB_role_id}` 修改租户 B 的角色、把租户 B 的用户分配给自己租户的角色（`POST /roles/{role_id}/users/{user_id}`）等。**这是多租户系统最核心的架构缺陷**：DDD 层到 API 层都没有"当前租户上下文"的概念。
- **修复方案（建议分两步）**：
  1. **短期（端点级防护）**：管理类端点全部改为 superuser-only（`get_current_active_superuser`），或显式从 JWT 取 `tenant_id` 并在 Controller/UseCase 中校验资源归属；
  2. **长期（租户上下文贯穿）**：
     - `get_current_user` 返回携带 `tenant_id` 的请求上下文（或新增 `get_current_tenant` 依赖）；
     - 仓储接口改为租户感知：`find_by_id(tenant_id, id)` / 内部强制 `WHERE tenant_id = ?`，杜绝跨租户查询；
     - UseCase 显式接收 `tenant_id` 参数（禁止从 DTO 盲信）；
     - 每个管理端点补"跨租户访问返回 404/403"的集成测试。

---

## 三、P1 — 高优先级（安全 / 正确性）

### P1-1 邮箱唯一性语义矛盾（领域 vs 持久化）

- **位置**：`src/domain/repositories/user_repository.py:19`（`find_by_email(email, tenant_id)`）vs `src/infrastructure/persistence/sqlmodel/models/user.py:19`（`email: str = Field(index=True, unique=True)`）
- **问题**：应用层按 **(email, tenant_id)** 判重（多租户内邮箱唯一），但数据库层 `email` **全局唯一** → 同一邮箱无法注册到第二个租户，与领域语义冲突；`find_by_email(email, None)` 在 InMemory 实现（取第一个匹配）与 SQL 实现（依赖全局唯一不会多行）之间行为不一致。
- **修复**：明确产品语义后统一。若按租户唯一：`UniqueConstraint(email, tenant_id)`（SQLite 注意唯一索引与 NULL 的行为）+ `find_by_email(email, None)` 显式禁止（改为按租户必传）；若全局唯一：删除仓储的 `tenant_id` 参数。**同时补 Alembic 迁移**（`alembic revision --autogenerate`）。

### P1-2 限流 fail-open + 多进程绕过 + 关键端点无限流

- **位置**：`src/infrastructure/security/redis_rate_limiter.py:45-69`
- **问题**：
  1. Redis 不可用时**静默降级为进程内 InMemory 限流**（fail-open）：多 worker 部署下每个进程独立计数，限流可被轻易绕过；攻击者甚至可以打挂 Redis 来解除限流；
  2. `POST /auth/register`、`/password/forgot`、`/verify/resend` **完全无限流** → 可批量注册垃圾账号、邮件轰炸。
- **修复**：
  1. 降级策略改为：仅开发环境允许降级；生产环境 fail-closed（限流器不可用 → 拒绝登录类请求）或至少显著调低进程内限额；
  2. 为 register / forgot / resend 增加 IP 级限流（复用现有 `_record_failed_login_from_ip` 模式，抽象成通用依赖）；
  3. 补测试：Redis 客户端抛错时行为符合所选策略。

### P1-3 登录用户枚举（计时侧信道 + 状态区分消息）

- **位置**：`src/application/use_cases/login_user_use_case.py:32-45`
- **问题**：用户不存在时**直接返回**（不执行 bcrypt verify），存在时执行 verify —— 响应时间差异可枚举账号；且 `"User is inactive"` / `"Email not verified"` / `"Invalid credentials"` 三种消息区分了账号状态（注册信息泄露）。
- **修复**：用户不存在时对**预计算 dummy hash** 执行一次 verify（恒时）；所有失败统一返回 `"Invalid credentials"`（或相同文案）；`is_active` / `is_verified` 检查合并进统一失败路径。补测试：不存在用户与密码错误用户的执行路径耗时/行为不可区分（可用 verify 调用次数断言）。

### P1-4 `PermissionMapper.to_entity` 静默兜底掩盖数据错误

- **位置**：`src/infrastructure/persistence/sqlmodel/mappers/permission_mapper.py:32-37`
- **问题**：数据库中出现未知 `action`/`resource` 时**静默映射为 `READ`/`USER`**——把数据错误伪装成正常数据，RBAC 校验可能因此误放行。
- **修复**：改为抛 `ValueError`（或领域异常），启动时/读取时暴露问题。

### P1-5 `ensure_admin` 启动失败被吞 + 遗留命名

- **位置**：`src/bootstrap/lifespan.py:33-36`、`src/bootstrap/ensure_admin.py:3-8`
- **问题**：`ensure_admin_user()` 异常只 `logger.error` 后继续启动——init_db 失败会直接暴露（注释明确"数据库不可用时应用不应带病启动"），admin 初始化失败却带病启动，**自相矛盾**；admin 缺失时登录入口对 superuser 完全不可用，且限流/验证功能依赖 admin。另有遗留命名 `settings as new_settings`、过时 docstring（"currently InMemory"）。
- **修复**：`ensure_admin` 失败同样让启动失败（或提供 `SKIP_ADMIN_BOOTSTRAP` 显式开关）；清理命名与 docstring。

### P1-6 JWT 加固

- **位置**：`src/infrastructure/security/jwt_provider.py:26-52`、`src/api/middleware/auth_dependencies.py:10-42`
- **建议**：
  1. 增加 `iss`/`aud` claim 并校验（防止跨应用重用令牌）；
  2. refresh token 与 access token 载荷对齐（refresh 目前缺 `tenant_id`/`email`）；
  3. 增加 `pwd_version`（用户密码哈希版本/变更计数）claim，改密后旧 access token 立即失效；
  4. `verify_token` 区分过期与无效（过期可返回特定信号，刷新链路可友好处理）；
  5. `sub` 校验使用 UUID 严格解析（当前 `UUID(user_id)` 失败被兜底为 401，可接受但可显式处理）。

---

## 四、P2 — 中优先级（设计 / 性能 / 一致性）

| # | 问题 | 位置 | 说明与建议 |
|---|------|------|-----------|
| P2-1 | **时间使用不一致**（naive vs UTC） | `domain/entities/*.py`（`datetime.now()`）、`login_user_use_case.py`（aware UTC）、`refresh_token_use_case.py:34-36`（手工补 tzinfo） | 统一为 `datetime.now(timezone.utc)`；SQLModel 列用 `DateTime(timezone=True)`；PostgreSQL 部署后避免时区灾难。需 Alembic 迁移 + 全量测试回归。 |
| P2-2 | **Password 无最大长度**（bcrypt 72 字节截断） | `src/domain/value_objects/password.py:12-24` | 加 `len(password) <= 72` 校验；API Schema 加 `min_length=8, max_length=72`（把 400 提前到 422，体验一致）。 |
| P2-3 | **UserModel 遗留字段** | `models/user.py:20,33-34`（`username`、`failed_login_attempts`、`locked_until`） | 旧版限流/模型残留，领域实体无对应字段，mapper 靠派生/忽略维持。清理字段或明确标注 deprecated + Alembic 迁移。 |
| P2-4 | **缺索引与唯一约束** | `models/user_role.py`、`role_permission.py`、`refresh_token.py`、`user.py`、`tenant.py` | ① `user_roles(role_id)`、`role_permissions(permission_id)`、`refresh_tokens(user_id)`、`users(tenant_id)` 加索引（JOIN 全表扫）；② 关联表加 `UniqueConstraint(user_id, role_id)` / `(role_id, permission_id)`（当前依赖"先查后插"有竞态，DB 层应兜底）；③ `tenants.domain` 唯一索引（域名路由场景）；④ 外键 `ondelete`（当前级联仅靠 ORM relationship，换 ORM/直连 SQL 即断）。 |
| P2-5 | **RBAC 校验每请求 4~5 次 DB 往返** | `auth_dependencies.py:67-91` → `association_use_case.py:60-70` | `require_permissions` 每次请求：查用户 + 查角色 ID + 查权限 ID + 查权限明细。建议：access token 内嵌权限快照（签发时计算，`resource:action` 集合）+ 定期失效/角色变更时强制重新登录；或加短 TTL 缓存。 |
| P2-6 | **跨仓储操作无原子性（缺 UoW）** | `register_user_use_case.py:26-42`（建租户 + 建用户两个独立事务）、`login_user_use_case.py:49-52`（存 refresh token + 存 user 两个事务） | 任一步失败会留下部分数据（孤儿租户/无 token 记录）。建议引入请求级会话 + 仓储共享会话（UoW），或至少为注册流程加补偿/重试。这是"每个仓储独立 session_scope"架构的固有代价，需权衡。 |
| P2-7 | **`AdminUpdateUserUseCase` 重复构造 + `updated_at` 不更新** | `user_admin_use_case.py:80-99,133-138` | 大段 `User(...)` 手工重排，且更新后 `updated_at` 不变（与 `deactivate()` 等行为不一致）。补实体方法 `with_email()`/`with_superuser()`/`with_tenant()`（复用 `replace`）。 |
| P2-8 | **refresh token 清理写放大** | `sqlmodel_refresh_token_repository.py:22-27` | 每次登录/轮换都执行一次 `DELETE ... WHERE expires_at < now`（无索引全表扫）。改为独立后台任务/定时清理（`delete_expired` 已存在但无人调用）。 |
| P2-9 | **Container 样板代码 + 双重单例** | `src/bootstrap/container.py` | ① 551 行手写懒加载属性，每加依赖要改 3 处（前缀变量 + 属性 + 构造）；可抽 `_lazy(factory)` 辅助泛型或引入轻量 DI 库；② `Container._instance` 类属性与模块级 `_container_instance` **两套单例并存**，`Container()` 直建与 `get_container()` 混用会得到不同实例。保留一个入口。 |
| P2-10 | **测试用反射重置容器** | `tests/integration/api/conftest.py:36-38` | `vars(container)` 遍历私有属性置 None，脆弱且依赖实现细节。给 `Container` 加显式 `reset()` / 测试专用 `build_test_container()` 工厂。 |
| P2-11 | **业务异常体系不统一** | 各 UseCase 抛 `ValueError`，路由逐个 try/except 映射 400/404/401 | 建议引入领域异常层级（`DomainError` → 4xx 基类，`NotFoundError` → 404，`ConflictError` → 409，`UnauthorizedError` → 401），路由只保留一个全局映射，删掉每个端点的 try/except 样板。 |
| P2-12 | **死代码** | `role.py:7-10`（`RoleName` 枚举已废弃）、`tests/conftest.py:44-46`（`hashed_password` fixture 构造 `HashedPassword("")`，而 VO 校验非空——**一旦被使用立即炸**） | 删除 `RoleName`；删除/修正坏 fixture。 |

---

## 五、P3 — 低优先级（工程化 / 体验）

1. **CI 缺失**：无 GitHub Actions/其他流水线。建议最小 CI：`ruff check` + `pytest` + 冒烟脚本 + 干净 venv 安装验证（可防 P0-1 复发）。
2. **容器化缺失**：无 Dockerfile/docker-compose；`redis` 是运行时依赖，本地开发需手动起。建议 compose 编排 `api + redis`，生产 Dockerfile 多阶段构建。
3. **日志配置硬编码**：`main.py:12-19` 固定 `app.log` 相对路径 + StreamHandler，多 worker/容器下互踩。建议由 `Settings` 驱动（LOG_LEVEL / LOG_FILE / JSON 格式开关）。
4. **API 版本注册表**：`lifespan.py:74-82` 8 个 `include_router` 手写，v2 将复制粘贴。建议 `API_VERSIONS = {"v1": [auth_router, ...]}` 循环注册。
5. **pre-commit**：加 ruff + 格式化的 pre-commit hook。
6. **文档同步**：README 声称 "~200 unit tests"（实际 253）；`AGENTS.md` 与 `CLAUDE.md` 内容重复度高，可合并为单一 `docs/` 体系。
7. **依赖声明三处漂移**：`pyproject.toml` / `requirements.txt` / `uv.lock` 并存（P0-1 即由此产生）。建议统一为单一来源（uv 或 pip-tools），CI 校验三者一致。

---

## 六、分阶段优化计划

### 阶段 1：止血（约 1~2 天）— 全部 P0
| 任务 | 产出 | 验证 |
|------|------|------|
| 修复 P0-1 依赖声明 | `pyproject.toml` + `requirements.txt` + `uv.lock` | 干净 venv `pip install -r requirements.txt` 后启动冒烟 |
| 修复 P0-2 change 端点鉴权 | `password_routes.py` + 控制器签名 | 新增集成测试：未认证 401、他人 user_id 无效 |
| 修复 P0-3 读端点鉴权 | 三个 routes 文件 + 测试辅助函数改造 | 匿名访问 401/403；测试与冒烟脚本全绿 |
| 修复 P0-4 角色租户丢失 | `role_use_case.py` + `role.py`（必填 tenant_id） | 新增单元 + 集成测试断言租户归属 |
| P0-5 短期防护 | 管理端点 superuser-only 或租户校验 | 跨租户访问测试 |

### 阶段 2：安全加固（约 2~3 天）— 全部 P1
邮箱唯一性统一（含 Alembic 迁移）→ 限流 fail-closed + 关键端点补限流 → 登录恒时比较 → mapper 严格校验 → admin 启动失败策略 → JWT 加固（iss/aud/pwd_version）。

### 阶段 3：租户隔离架构改造（约 1 周）— P0-5 长期方案 + P2-6
1. 引入 `TenantContext`（请求级，从 JWT `tenant_id` 注入）；
2. 仓储接口租户感知化（`find_by_id(tenant_id, id)`、强制 `WHERE tenant_id`）；
3. UseCase 显式接收租户参数；4. 逐端点补隔离测试；5. 评估 UoW 引入。

### 阶段 4：工程化收敛（持续）— P2/P3
UTC 统一与字段清理（合并进一次 Alembic 迁移）→ 索引/唯一约束迁移 → RBAC 权限快照缓存 → Container/异常体系重构 → CI/Docker/pre-commit。

---

## 七、附：建议优先验证的两个高风险行为（修复后回归）

1. `POST /api/v1/password/change?user_id=<any>`：未登录调用 → 应 401；
2. `GET /api/v1/tenants`（匿名）→ 应 401/403；admin 跨租户 `PUT /api/v1/roles/{other_tenant_role}` → 应 404/403。
