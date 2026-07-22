# FastAPI Scaff Demo

# FastAPI Scaff Demo
<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

Multi-tenant RBAC authentication system built with FastAPI, currently in a transitional architecture phase — the legacy `app/` layer (SQLModel + flat structure) coexists with the new `src/` layer (DDD four-layer architecture), both registered on the same FastAPI instance.

## Architecture

The project is undergoing a controlled refactoring from legacy flat-layered architecture to DDD (Domain-Driven Design) four-layer architecture.

### Legacy (`app/`)
- Flat layering, SQLModel as domain model
- Auto router registration via `app/api/v1/` scanning
- PostgreSQL + SQLAlchemy async

### New Architecture (`src/`)
- DDD four-layer: domain → application → infrastructure → api
- Manual DI container (`src/bootstrap/container.py`)
- In-memory repository (testing) + SQLModel repository in development
- Pure Python domain entities, value objects with validation
- 124 unit tests covering all layers

## Project Structure

```
├── app/               Legacy architecture (flat, migrating)
│   ├── api/v1/        Legacy routes
│   ├── core/          Config, security, logging
│   ├── db/            Database engine & session
│   ├── models/        SQLModel ORM models
│   ├── services/      Business logic
│   └── test/          Legacy tests
├── src/               New DDD architecture
│   ├── domain/        Entities, value objects, repository interfaces
│   ├── application/   Use cases, DTOs
│   ├── infrastructure/ Persistence (SQLModel/InMemory), security (JWT/bcrypt)
│   ├── api/           Controllers, routes, Pydantic schemas
│   └── bootstrap/     Config, DI container, app factory & lifespan
├── tests/             Unit & integration tests for new architecture
│   ├── unit/          124 tests covering all layers
│   └── integration/   Full-stack API tests
├── scripts/           Debug scripts (fix_db, test_login)
├── main.py            App entry point (uvicorn factory mode)
├── run_tests.py       Runs both legacy and new test suites
└── pyproject.toml     Project metadata & dependencies
```

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run with hot-reload
python main.py

# Or directly with uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

## Commands

```bash
# Run all tests (legacy + new architecture)
python run_tests.py

# Run new architecture unit tests
python -m pytest tests/unit/ -v --tb=short

# Run new architecture integration tests
python -m pytest tests/integration/ -v --tb=short

# Run legacy tests
python -m pytest app/test/ -v --tb=short

# Coverage report
python -m pytest --cov=src --cov-report=term-missing tests/

# Database migration (legacy)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## API Endpoints

All routes prefixed with `/api/v1`.

| Endpoint | Architecture | Description |
|---|---|---|
| POST `/api/v1/auth/register` | New (src) | User registration |
| POST `/api/v1/auth/login` | New (src) | Login, returns JWT tokens |
| POST `/api/v1/auth/token` | Legacy (app) | OAuth2 token endpoint |
| POST `/api/v1/password/forgot` | New (src) | Forgot password |
| POST `/api/v1/roles/` | Legacy (app) | Role management |
| POST `/api/v1/tenants/` | Legacy (app) | Tenant management |

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Runtime**: Python 3.13+
- **ORM**: SQLModel / SQLAlchemy async
- **Auth**: JWT (HS256) + bcrypt
- **Config**: Pydantic Settings (env file support)
- **Testing**: pytest + pytest-asyncio + httpx

## Adding New Features

Follow the DDD four-layer flow for new features:

1. **Domain** (`src/domain/`) — Define entities, value objects, repository interfaces
2. **Infrastructure** (`src/infrastructure/`) — Implement repositories, security services
3. **Application** (`src/application/`) — Create DTOs and use cases
4. **API** (`src/api/`) — Create schemas, controllers, routes
5. **Bootstrap** (`src/bootstrap/`) — Register dependencies in container, wire routes
6. **Tests** (`tests/`) — Unit + integration tests
