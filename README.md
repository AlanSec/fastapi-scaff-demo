# FastAPI Scaff Demo

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

基于FastAPI构建，提供用户认证、鉴权、支持多租户、日志记录，支持响应&错误响应格式统一、异常处理中间件、数据库迁移、API文档、CORS等。

## 功能特性

- **用户认证**：基于JWT的身份验证系统
- **多租户支持**：支持多租户架构
- **异常处理中间件**：自动处理异常并返回错误信息
- **数据库迁移**：使用Alembic进行数据库迁移
- **响应&错误响应格式统一**：自动返回错误信息
- **RBAC**: 基于RBAC的权限控制
- **API文档**：自动生成的交互式API文档

## 技术栈

- **框架**：FastAPI
- **数据库**：PostgreSQL (SQLAlchemy ORM)
- **缓存**：Redis
- **数据库迁移**：Alembic
- **API文档**：Swagger UI & ReDoc
## 项目结构

```
fastapi-scaff-demo/
├── alembic/                  # 数据库迁移
│   ├── versions/             # 迁移版本
│   ├── env.py                  # Alembic环境配置
│   └── script.py.mako          # 迁移脚本模板
├── app/                        # 应用主目录
│   ├── api/                    # API路由
│   │   └── exception.py        # 自定义异常
│   │   └── repsonse.py         # 接口返回值格式统一
│   │   └── status.py           # 异常状态码
│   │   ├── v1/                 # API版本
│   │   │   ├──  users.py       # 用户API
│   │   │   ├──  auth.py        # 鉴权认证API
│   │   │   ├──  permissions.py # 权限 API
│   │   │   ├──  roles.py       # 角色 API
│   │   │   └──  tenants.py     # 多租户 API
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置
│   │   ├── security.py         # 安全相关
│   │   └── logging.py          # 日志配置
│   ├── db/                     # 数据库
│   │   ├── base.py             # 数据库基础设置
│   │   ├── session.py          # 会话管理
│   │   └── init_db.py          # 数据库初始化
│   ├── middleware/             # 中间件
│   │   ├── __init_.py          # 注册中间件
│   │   ├── cors.py             # CORS
│   │   └── exception.py        # 异常处理
│   ├── models/                 # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── tenant.py           # 租户模型
│   │   ├── role.py             # 角色模型
│   │   ├── permission.py       # 权限模型
│   │   ├── role_permission.py  # 角色与权限关联模型
│   │   └── user_role.py        # 用户与角色关联模型
│   ├── router/                 # 路由相关
│   │   ├── __init__.py         # 路由自动注册
│   ├── schemas/                # Pydantic模式
│   │   ├── user.py             # 用户模式
│   │   ├── tenant.py           # 租户模式
│   │   ├── role.py             # 角色模式
│   │   ├── permission.py       # 权限模式
│   │   ├── role_permission.py  # 角色与权限模式
│   │   ├── user_role.py        # 用户与角色模式
│   │   └── token.py            # token模式
│   ├── services/               # 业务逻辑
│   │   ├── user.py             # 用户业务逻辑
│   │   ├── tenants.py          # 租户业务逻辑
│   │   ├── permissions.py      # 权限业务逻辑
│   │   ├── roles.py            # 角色业务逻辑
│   │   └── auth.py             # 登陆认证、权限验证、鉴权 业务逻辑
│   ├── utils/                  # 工具函数
│   │   ├── dependencies.py     # 依赖项
│   │   └── helpers.py          # 辅助函数
│   └── main.py                 # 应用入口
├── tests/                      # 测试
│   ├── api/                    # API测试
│   ├── services/               # 服务测试
│   └── conftest.py             # 测试配置
├── deploy/                     # CICD、镜像相关
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略文件
├── alembic.ini                 # Alembic配置文件
├── pyproject.toml              # 项目配置
├── README.md                   # 项目说明
└── main.py                     # 项目启动脚本
```
## 开发指南

### 业务逻辑开发流程

1. **业务逻辑位置**：所有业务逻辑应放在`app/services/`目录下
2. **服务模块划分**：
   - 每个主要业务领域应有独立的服务文件
   - 例如：用户相关逻辑放在`user.py`
3. **服务层职责**：
   - 处理核心业务规则
   - 协调多个模型的操作
   - 处理事务
   - 调用外部服务
4. **最佳实践**：
   - 保持服务函数小而专注
   - 避免在服务层直接处理HTTP相关逻辑
   - 使用依赖注入提高可测试性

### API接口开发规范

1. **路由组织**：
   - API路由放在`app/api/v1/`目录下
   - 按业务领域组织路由文件
2. **端点设计**：
   - 遵循RESTful原则
   - 使用适当的HTTP方法(GET, POST, PUT, DELETE等)
3. **请求/响应处理**：
   - 使用Pydantic模型进行数据验证
   - 响应格式统一使用`app/api/response.py`中的工具
4. **错误处理**：
   - 使用`app/api/exception.py`中的自定义异常
   - 错误响应格式统一

### Models分层设计原则

1. **数据库模型**：
   - 位于`app/models/`目录
   - 使用SQLAlchemy ORM定义
   - 只包含数据库相关属性和方法
2. **Pydantic模型**：
   - 位于`app/schemas/`目录
   - 用于API请求/响应验证
   - 不应包含业务逻辑
3. **分层关系**：
   - 服务层调用数据库模型
   - API层使用Pydantic模型验证数据
   - 避免在模型层包含业务逻辑

### 代码组织最佳实践

1. **模块化设计**：
   - 每个功能模块应包含完整的业务逻辑
   - 模块间通过明确定义的接口通信
2. **依赖管理**：
   - 使用`app/utils/dependencies.py`管理公共依赖
   - 避免隐式依赖
3. **测试策略**：
   - 单元测试覆盖服务层
   - 集成测试覆盖API端点
   - 测试数据使用工厂模式生成

## 安装指南

### 前置要求

- Python 3.9+
- PostgreSQL 13+
- Redis 6+

### 1. 克隆仓库

```bash
git clone https://gitlab.foda.ai/zhangjin/fastapi-scaff-demo.git
cd fastapi-scaff-demo
```

### 2. 创建虚拟环境并安装依赖

```bash
uv venv myenv --python=3.13
uv activate myenv

```
使用uv安装依赖
```bash
uv pip install -e .
```

### 3. 配置环境变量

复制`.env.example`文件并重命名为`.env`，然后根据实际情况修改配置：

```bash
cp .env.example .env
```
### 4.运行数据迁移
```angular2html
alembic upgrade head
```
### 5.初始化数据库
```bash
python -m app.db.init_db
```

主要配置项说明：

```ini
# 数据库配置
POSTGRES_SERVER=localhost       # PostgreSQL服务器地址
POSTGRES_PORT=5432              # PostgreSQL端口
POSTGRES_USER=postgres          # 数据库用户名
POSTGRES_PASSWORD=postgres      # 数据库密码
POSTGRES_DB=aigc_db            # 数据库名称

# 安全配置
SECRET_KEY=your-secret-key-here # JWT加密密钥
ALGORITHM=HS256                # 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Token过期时间(分钟)

# 存储配置
MEDIA_ROOT=./media             # 媒体文件存储根目录
GALLERY_PATH=./media/gallery   # 画廊图片存储目录

# Redis配置
REDIS_HOST=localhost           # Redis服务器地址
REDIS_PORT=6379               # Redis端口
REDIS_DB=0                    # Redis数据库编号
REDIS_PASSWORD=               # Redis密码(可选)

# 日志配置
LOG_LEVEL=INFO                # 日志级别(DEBUG/INFO/WARNING/ERROR/CRITICAL)
```


## API文档

应用启动后，可以通过以下URL访问API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`


## 代码风格与格式化

项目使用以下工具保持代码风格一致:

- **Black**: 自动格式化Python代码
  ```bash
  uv pip install black
  black .
  ```

- **isort**: 自动排序import语句
  ```bash
  uv pip install isort
  isort .
  ```

- **flake8**: 代码风格检查
  ```bash
  uv pip install flake8
  flake8 .
  ```

## 测试指南

### 运行测试

1. 安装测试依赖:
```bash
uv pip install pytest pytest-cov
```

2. 运行全部测试:
```bash
pytest tests/ -v
```

3. 生成测试覆盖率报告:
```bash
pytest --cov=app tests/
```

### 编写测试最佳实践

- 测试文件应放在与被测代码对应的`tests/`子目录中
- 测试函数名应描述测试场景，如`test_create_user_with_valid_data`
- 使用pytest fixtures管理测试资源
- 每个测试应独立运行，不依赖其他测试的状态

## 开发工作流示例

### 1. 创建新API端点的完整流程

1. **定义数据模型**:
```python
# app/models/sample.py
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel

class Sample(SQLModel):
    __tablename__ = "samples"
    id = Column(String, primary_key=True)
    name = Column(String)
```

2. **创建Pydantic模型**:
```python
# app/schemas/sample.py
from pydantic import BaseModel

class SampleCreate(BaseModel):
    name: str

class SampleResponse(BaseModel):
    id: str
    name: str
```

3. **实现服务层**:
```python
# app/services/sample_services.py
from sqlalchemy.orm import Session
from app.models.sample import Sample

def create_sample(db: Session, sample_data):
    db_sample = Sample(**sample_data.dict())
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample
```

4. **创建API路由**:
```python
# app/api/v1/samples.py
from fastapi import APIRouter, Depends
from app.schemas.sample import SampleCreate, SampleResponse
from app.services import sample_services

samples_router = APIRouter()
_active = True  # 激活状态（默认激活）
_tag = "smples"  # 标签（默认模块名或子目录名）

@samples_router.post("/", response_model=SampleResponse)
def create_sample(sample: SampleCreate):
    return sample_services.create_sample(db, sample)
```

5. **测试API**:
```python
# tests/api/v1/test_samples.py
def test_create_sample(client):
    response = client.post("/v1/samples/", json={"name": "Test"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```

### 2. 常见问题解答（FAQ）

**Q: 如何添加新的数据库表?**

A: 1. 在app/models/创建模型

   2. 生成迁移: `alembic revision --autogenerate -m "add new table"`

   3. 应用迁移: `alembic upgrade head`

**Q: 如何添加中间件?**

A: 1. 在app/middleware/创建中间件

   2. 在app/middleware/__init__.py中注册


## 数据库迁移
项目使用 Alembic 进行数据库迁移管理。以下是常用的迁移命令：

### 创建新的迁移版本
当您修改数据模型后，需要创建新的迁移版本：
```bash
alembic revision --autogenerate -m "迁移描述"
```
### 回滚迁移
回滚到上一个版本：
```bash
alembic downgrade -1
```

### 查看迁移状态
查看当前的迁移版本：
```bash
alembic current
```

查看迁移历史：
```bash
alembic history
```

### 初始化数据库
如果需要初始化基础数据（如默认租户和管理员用户），可以运行：
```bash
python -m app.db.init_db
```

## 贡献指南

欢迎为项目贡献代码！以下是贡献流程：

1. **创建分支**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **提交变更**:
   - 保持提交信息清晰简洁
   - 遵循[约定式提交](https://www.conventionalcommits.org/)规范

3. **运行测试**:
   - 确保所有测试通过
   - 添加新功能的测试用例

4. **创建Pull Request**:
   - 描述变更内容和动机
   - 关联相关issue(如果有)

## 部署基础

### 本地开发部署

1. 启动FastAPI服务:
```bash
uvicorn app.main:app --reload
```

2. 启动Celery worker(可选):
```bash
celery -A app.core.celery_app worker --loglevel=info
```

### 生产环境部署建议

- 使用Gunicorn作为WSGI服务器:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

- 配置Nginx作为反向代理
- 使用Supervisor管理进程
- 配置日志轮转
- 设置定期数据库备份

```


