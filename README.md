<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

# FastAPI Scaff Demo

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

A multi-tenant RBAC authentication scaffold built with FastAPI, using a **DDD four-layer architecture with a manual DI container**. It provides authentication, tenant isolation, role/permission management, and user administration out of the box.

## Architecture

```
main.py                                 → Entry point (uvicorn factory mode)
│
├── src/                                → DDD four-layer architecture
│   ├── domain/                         →   Domain layer (pure Python, zero deps)
│   │   ├── entities/                   →   Entities (User, Tenant, Role, Permission)
│   │   ├── value_objects/              →   Value objects (Email, Password, HashedPassword)
│   │   ├── repositories/               →   Repository interfaces (protocols)
│   │   └── services/                   →   Service interfaces (PasswordHasher, JWTProvider, RateLimiter, EmailSender)
│   ├── application/                    →   Application layer (DTOs + Use Cases)
│   │   ├── dto/                        →   Input/Output DTOs
│   │   └── use_cases/                  →   Register, login, refresh, passwords, tenant/role/permission, RBAC associations
│   ├── infrastructure/                 →   Infrastructure layer (implementations)
│   │   ├── persistence/                →     Persistence (SQLModel repositories + InMemory for tests)
│   │   │   ├── database.py             →     Async engine + session factory + init_db
│   │   │   ├── sqlmodel/               →     SQLModel ORM models / mappers / repositories
│   │   │   └── in_memory/              →     In-memory repositories (unit-test use cases)
│   │   ├── security/                   →     JWT, bcrypt, rate limiting
│   │   └── email/                      →     ConsoleEmailSender (email written to logs)
│   ├── api/                            →   API adapter layer
│   │   ├── controllers/                →     Controllers (request/response ↔ DTO)
│   │   ├── routes/                     →     FastAPI routers
│   │   ├── schemas/                    →     Pydantic schemas
│   │   └── middleware/                 →     Auth/permission deps (get_current_user, require_permissions)
│   └── bootstrap/                      →   Bootstrap layer
│       ├── config.py                   →     Pydantic Settings (.env / env vars)
│       ├── container.py                →     Manual singleton DI container
│       ├── lifespan.py                 →     App factory + init_db + admin bootstrap
│       └── ensure_admin.py             →     Default tenant + admin superuser
├── tests/                              → ~200 unit tests + integration tests (in-memory SQLite)
├── scripts/smoke_test_rbac.py          → Full-stack smoke test script
└── pyproject.toml                      → Metadata & ruff/pytest config
```

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run dev server (hot reload, auto create tables + admin)
python main.py

# Or directly with uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

## Commands

```bash
# Run all tests
python run_tests.py
python -m pytest tests/ -v --tb=short

# Unit / integration tests
python -m pytest tests/unit/ -v --tb=short
python -m pytest tests/integration/ -v --tb=short

# Coverage
python -m pytest --cov=src --cov-report=term-missing tests/

# Lint
python -m ruff check src/ tests/
```

## API Endpoints

All routes are prefixed with `/api/v1`.

| Endpoint | Description |
|---|---|
| GET `/health` | Health check (for deployment probes, no auth) |
| POST `/api/v1/auth/register` | User registration (`tenant_id` optional — auto-creates a personal tenant) |
| POST `/api/v1/auth/login` | Login, returns JWT access + refresh tokens |
| POST `/api/v1/auth/token` | OAuth2 password-mode token (form-encoded, enables Swagger Authorize) |
| POST `/api/v1/auth/login/json` | Login (OAuth2-compatible response) |
| POST `/api/v1/auth/refresh` | Refresh tokens (rotate refresh token) |
| POST `/api/v1/password/forgot` / `/reset` / `/change` | Password flows (tokens sent via email, never in response) |
| POST `/api/v1/verify/email` / `/resend` | Email verification / resend |
| GET/POST/PUT/DELETE `/api/v1/tenants` | Tenant management (writes require `tenant:*`) |
| GET/POST/PUT/DELETE `/api/v1/roles` | Role management (writes require `role:*`) |
| POST `/api/v1/roles/{role_id}/users/{user_id}` | Assign role to user (requires `role:update`) |
| GET/POST/PUT/DELETE `/api/v1/permissions` | Permission management (writes require `permission:*`) |
| POST `/api/v1/permissions/{permission_id}/roles/{role_id}` | Assign permission to role (requires `permission:update`) |
| GET/PUT `/api/v1/user/me` | Current user info (authenticated) |
| GET/POST/PUT/DELETE `/api/v1/user` | Admin user management (superuser only) |

## Security Features

- **Auth**: JWT HS256, access 30min + refresh 7d (with `jti`/`iat` claims); refresh tokens cannot be used as access tokens; `/auth/refresh` rotates tokens and **revokes the old one server-side** (persisted in the `refresh_tokens` table; expired rows are purged opportunistically on each write so the table never grows unbounded)
- **Passwords**: bcrypt hashing + strength validation (8+ chars, upper/lower/digit)
- **Login rate limiting**: per-email + per-IP failed-attempt counters, 429 on exceed; backed by **local Redis** (atomic Lua counters, shared across processes, survives restarts), auto-degrades to in-memory with a warning if Redis is unavailable (`MAX_LOGIN_ATTEMPTS` / `LOGIN_LOCKOUT_MINUTES` / `REDIS_URL`)
- **RBAC**: user ↔ role ↔ permission associations; `require_permissions("resource:action")` dependency for endpoint-level checks (superusers bypass)
- **Production safety**: `ENVIRONMENT=production` refuses to start without an explicit `SECRET_KEY`
- **Tokens never in responses**: reset/verification tokens go through `EmailSender` (currently ConsoleEmailSender writing to logs; swap in an SMTP implementation)

## Configuration

Configured via environment variables or a `.env` file (auto-loaded by `main.py`):

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (production enforces SECRET_KEY) |
| `SECRET_KEY` | dev default | JWT signing key; must be set explicitly in production |
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | Database URL (PostgreSQL asyncpg recommended for prod) |
| `REDIS_URL` | `redis://localhost:6379/0` | Rate-limit storage (auto-degrades to in-memory if unavailable) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `MAX_LOGIN_ATTEMPTS` | `5` | Login rate-limit threshold |
| `LOGIN_LOCKOUT_MINUTES` | `30` | Login lockout window |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Require email verification before login |
| `SERVER_HOST` / `SERVER_PORT` | `0.0.0.0` / `8000` | Bind address/port for `python main.py` |
| `SERVER_RELOAD` | `true` | Dev hot reload (set `false` in production) |
| `CORS_ORIGINS` | localhost set | Allowed CORS origins (comma-separated) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | - | Admin account created at startup |

## Adding New Features

Follow the DDD four-layer flow:

1. **Domain** (`src/domain/`) — entities, value objects, repository interfaces
2. **Infrastructure** (`src/infrastructure/`) — repository & security implementations
3. **Application** (`src/application/`) — DTOs and use cases
4. **API** (`src/api/`) — schemas, controllers, routes
5. **Bootstrap** (`src/bootstrap/`) — register in the DI container; routes pull their controllers straight from the container via `Depends` (no manual wiring)
6. **Tests** (`tests/`) — unit tests with real repository implementations (so mocks can't hide bugs) + integration tests

## Known Limitations

- No real SMTP sending (tokens go to logs); swap in an `EmailSender` implementation

## Tech Stack

FastAPI + Uvicorn · SQLModel/SQLAlchemy async · JWT + bcrypt · Pydantic Settings · pytest + pytest-asyncio + httpx · ruff

## License

MIT
