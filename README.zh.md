<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

# FastAPI Scaff Demo

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

基于 FastAPI 构建的多租户 RBAC 认证系统，当前处于**架构过渡期**：遗留 `app/` 层（SQLModel + 扁平分层）与新 `src/` 层（DDD 四层架构）共存，共同注册在同一 FastAPI 实例上。

## 架构

项目正处于从遗留扁平分层向 DDD（领域驱动设计）四层架构的受控重构过程中。

### 遗留架构（`app/`）
- 扁平分层，SQLModel 即领域模型
- 自动扫描注册路由 `app/api/v1/`
- PostgreSQL + SQLAlchemy 异步

### 新架构（`src/`）
- DDD 四层架构：领域层 → 应用层 → 基础设施层 → API 层
- 手动 DI 容器（`src/bootstrap/container.py`）
- 内存仓储（测试用）+ SQLModel 仓储（开发中）
- 纯 Python 领域实体、带校验的值对象
- 124 个单元测试覆盖各层

## 项目结构

```
├── app/               遗留架构（扁平分层，迁移中）
│   ├── api/v1/        Legacy 路由
│   ├── core/          配置、安全、日志
│   ├── db/            数据库引擎与会话
│   ├── models/        SQLModel ORM 模型
│   ├── services/      业务逻辑
│   └── test/          Legacy 测试
├── src/               新 DDD 架构
│   ├── domain/        领域实体、值对象、仓储接口
│   ├── application/   UseCase、DTO
│   ├── infrastructure/ 持久化（SQLModel/InMemory）、安全（JWT/bcrypt）
│   ├── api/           Controller、路由、Pydantic Schema
│   └── bootstrap/     配置、DI 容器、App 工厂 & 生命周期
├── tests/             新架构单元测试 & 集成测试
│   ├── unit/          124 个测试覆盖各层
│   └── integration/   全链路 API 测试
├── scripts/           调试脚本（fix_db, test_login）
├── main.py            应用入口（uvicorn factory 模式）
├── run_tests.py       同时运行 legacy 和新架构测试
└── pyproject.toml     项目元数据 & 依赖
```

## 快速开始

```bash
# 安装依赖
pip install -e .

# 启动开发服务器（热重载）
python main.py

# 或直接使用 uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

## 常用命令

```bash
# 运行全部测试（legacy + 新架构）
python run_tests.py

# 运行新架构单元测试
python -m pytest tests/unit/ -v --tb=short

# 运行新架构集成测试
python -m pytest tests/integration/ -v --tb=short

# 运行遗留测试
python -m pytest app/test/ -v --tb=short

# 覆盖率报告
python -m pytest --cov=src --cov-report=term-missing tests/

# 数据库迁移（遗留）
alembic revision --autogenerate -m "迁移描述"
alembic upgrade head
```

## API 接口

所有路由以 `/api/v1` 为前缀。

| 端点 | 架构 | 说明 |
|---|---|---|
| POST `/api/v1/auth/register` | 新架构（src） | 用户注册 |
| POST `/api/v1/auth/login` | 新架构（src） | 登录，返回 JWT 令牌 |
| POST `/api/v1/auth/token` | 遗留（app） | OAuth2 令牌接口 |
| POST `/api/v1/password/forgot` | 新架构（src） | 忘记密码 |
| POST `/api/v1/roles/` | 遗留（app） | 角色管理 |
| POST `/api/v1/tenants/` | 遗留（app） | 租户管理 |

## 技术栈

- **框架**: FastAPI + Uvicorn
- **运行环境**: Python 3.13+
- **ORM**: SQLModel / SQLAlchemy 异步
- **认证**: JWT（HS256）+ bcrypt
- **配置**: Pydantic Settings（支持 .env 文件）
- **测试**: pytest + pytest-asyncio + httpx

## 新增功能

遵循 DDD 四层流程开发新功能：

1. **领域层**（`src/domain/`）— 定义实体、值对象、仓储接口
2. **基础设施层**（`src/infrastructure/`）— 实现仓储、安全服务
3. **应用层**（`src/application/`）— 创建 DTO 和 UseCase
4. **API 层**（`src/api/`）— 创建 Schema、Controller、路由
5. **启动层**（`src/bootstrap/`）— 在容器中注册依赖，注入路由
6. **测试**（`tests/`）— 编写单元测试和集成测试

## 配置说明

通过环境变量或 `.env` 文件配置，关键配置项：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `secret_key` | `dev-secret-key-change-in-production` | JWT 加密密钥 |
| `algorithm` | `HS256` | JWT 算法 |
| `access_token_expire_minutes` | `30` | 访问令牌过期时间 |
| `refresh_token_expire_days` | `7` | 刷新令牌过期时间 |
| `database_url` | `sqlite+aiosqlite:///./test.db` | 数据库连接 URL |
| `admin_email` | `admin@example.com` | 管理员邮箱 |
| `admin_password` | `Admin123456` | 管理员密码 |

## 开发分支规范

- 新功能分支：`feature/<描述>`
- Bug 修复分支：`fix/<描述>`
- 代码重构分支：`refactor/<描述>`
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范

## 许可证

MIT
