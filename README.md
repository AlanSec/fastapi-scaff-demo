<div align="center">

[**English**](./README.md) | [**中文**](./README.zh.md)

</div>

<br>

# FastAPI Scaff Demo

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

A multi-tenant RBAC authentication scaffold built with FastAPI, using a **DDD four-layer architecture with a manual DI container**. Batteries included: JWT auth with refresh-token rotation, **mandatory tenant isolation**, user ↔ role ↔ permission RBAC, user administration, rate limiting, email verification, Alembic migrations, Docker and CI.

## Feature Highlights

| Capability | Details |
|---|---|
| **Authentication** | JWT HS256: access 30 min + refresh 7 days (`jti`/`iat`/`tenant_id` claims); `/auth/refresh` rotates tokens and **revokes the old one server-side**; access/refresh types are strictly separated |
| **Multi-tenant isolation** | The JWT `tenant_id` is enforced all the way through routes → use cases → repositories; **superusers bypass permission-string checks only, never tenant filtering**; cross-tenant access always returns 404 (no enumeration); emails are unique per `(email, tenant_id)` |
| **RBAC** | User ↔ role ↔ permission associations persisted for real; `require_permissions("resource:action")` endpoint-level checks; permission sets cached in-process for 60s (one DB round-trip per request instead of 4–5), invalidated immediately on assignment changes |
| **Login hardening** | Per-email + per-IP failed-attempt counters (atomic Redis Lua counters); failures always return `Invalid credentials`; unknown accounts still run a dummy bcrypt verify (constant time, no timing enumeration); open endpoints additionally rate-limited per IP |
| **Rate-limit degradation** | Development: Redis unavailable → in-memory fallback + warning; **production: fail-closed** (requests rejected instead of letting an attacker take Redis down to bypass limits) |
| **Error handling** | Domain exceptions mapped globally: not found → 404, conflict → 409, invalid credentials → 401, domain/validation error → 400, rate limit → 429, unhandled → 500; every response carries a `code` field |
| **Time handling** | Entities, models and use cases all use timezone-aware UTC datetimes (`DateTime(timezone=True)` columns), eliminating naive/aware mix-ups |
| **Refresh-token cleanup** | Expired rows are purged by a background lifespan task every hour, off the request hot path (no write amplification) |
| **Engineering** | Alembic baseline + incremental migrations, Docker Compose, GitHub Actions CI, pre-commit, ruff, 289 passing tests |

## Architecture

```
main.py                                 → Entry point (uvicorn factory mode)
│
├── src/                                → DDD four-layer architecture
│   ├── domain/                         →   Domain layer (pure Python, zero deps)
│   │   ├── entities/                   →   Entities (User, Tenant, Role, Permission)
│   │   ├── value_objects/              →   Value objects (Email, Password, HashedPassword)
│   │   ├── repositories/               →   Repository interfaces (tenant-aware: find_by_id requires tenant_id)
│   │   ├── services/                   →   Service interfaces (PasswordHasher, JWTProvider, RateLimiter, EmailSender)
│   │   └── exceptions.py               →   Domain exception hierarchy (→ 4xx global mapping)
│   ├── application/                    →   Application layer (DTOs + Use Cases)
│   │   ├── dto/                        →   Input/output DTOs
│   │   └── use_cases/                  →   Register, login, refresh, passwords, tenant/role/permission, RBAC associations
│   ├── infrastructure/                 →   Infrastructure layer (implementations)
│   │   ├── persistence/
│   │   │   ├── database.py             →     Async engine + session factory + init_db + session_scope
│   │   │   ├── sqlmodel/               →     ORM models / mappers / repositories (session-factory pattern)
│   │   │   │   └── models/time.py      →     UTC time helper (utcnow)
│   │   │   └── in_memory/              →     In-memory repositories (unit-test use cases)
│   │   ├── security/                   →     JWT, bcrypt, Redis/in-memory rate limiting, permission cache
│   │   └── email/                      →     ConsoleEmailSender (emails written to logs)
│   ├── api/                            →   API adapter layer
│   │   ├── controllers/                →     Controllers (schema ↔ DTO)
│   │   ├── routes/                     →     Routers + API version registry
│   │   ├── schemas/                    →     Pydantic schemas (write requests use extra="forbid")
│   │   └── middleware/                 →     Auth/permission dependencies, exception handlers
│   └── bootstrap/                      →   Bootstrap layer
│       ├── config.py                   →     Pydantic Settings (.env / env vars)
│       ├── container.py                →     Manual singleton DI container (cached_property)
│       ├── lifespan.py                 →     App factory: create tables + admin bootstrap + route registration + cleanup task
│       └── ensure_admin.py             →     Default tenant + admin superuser (failure aborts startup)
├── alembic/                            → Database migrations (baseline + 3 incremental)
├── tests/                              → 289 tests (unit + integration, in-memory SQLite / TestClient full stack)
├── scripts/                            → smoke_test_rbac.py (full-stack smoke), verify_alembic.py (migration check)
├── Dockerfile / docker-compose.yml     → Containerization (api + redis)
└── pyproject.toml                      → Dependencies & ruff/pytest config
```

**Request flow** (dependencies point strictly inward):

```
HTTP request
  → Router (Depends pulls the controller from the DI container; auth deps verify the JWT and inject current_user/tenant_id)
  → Controller (schema ↔ DTO)
  → UseCase (business rules; tenant_id is an explicit parameter, never trusted from the request body)
  → Repository (SQLModel implementation, independent session per operation)
```

**Design constraints**:

- Routers hold no module-level mutable globals — endpoints resolve their controller from the container via `Depends(get_xxx_controller())`;
- Tenant context is passed explicitly everywhere (no contextvars): JWT `tenant_id` → `get_current_user` verification → router → use case → repository;
- `tenant_id` for tenant-scoped resources always comes from the auth context; request schemas such as `RoleCreateRequest` / `AdminCreateUserRequest` use `extra="forbid"`, so clients cannot supply `tenant_id`;
- `domain/entities` and `sqlmodel/models` are separate, converted via `mappers/`; models must not import `database.py` (avoids creating the async engine inside Alembic's sync context).

## Quick Start

```bash
# Install dependencies
pip install -e .

# Copy and fill in configuration (SECRET_KEY / ADMIN_PASSWORD are required)
cp .env.example .env

# Run the dev server (hot reload, auto create tables + admin)
python main.py

# Or run directly with uvicorn
uvicorn src.bootstrap.lifespan:create_app --reload --factory
```

Open <http://localhost:8000/docs> for Swagger UI. Click **Authorize** and log in through `POST /api/v1/auth/token` (OAuth2 password-mode form) to try the API.

## Commands

```bash
# Run all tests (289)
python run_tests.py
python -m pytest tests/ -v --tb=short

# Unit / integration tests
python -m pytest tests/unit/ -v --tb=short
python -m pytest tests/integration/ -v --tb=short

# Coverage
python -m pytest --cov=src --cov-report=term-missing tests/

# Lint and auto-fix
python -m ruff check src/ tests/
python -m ruff check src/ tests/ --fix

# Database migrations
alembic upgrade head                    # apply all migrations
python scripts/verify_alembic.py        # assert migrations match SQLModel metadata (self-contained)

# Full-stack smoke (register/login/refresh/RBAC/token revocation)
python scripts/smoke_test_rbac.py
```

## API Endpoints

All business routes are prefixed with `/api/v1` (version registry in `src/api/routes/__init__.py`).

| Method & Path | Auth | Description |
|---|---|---|
| GET `/health` | none | Health check (deployment probe) |
| POST `/api/v1/auth/register` | IP rate limit 10/h | Register; `tenant_id` optional — auto-creates a personal tenant; a provided tenant must exist and be active |
| POST `/api/v1/auth/login` | email + IP rate limit | Login, returns access + refresh tokens; inactive tenants/users rejected generically |
| POST `/api/v1/auth/login/json` | same | Login (OAuth2-compatible response) |
| POST `/api/v1/auth/token` | same (form) | OAuth2 password-mode token (used by Swagger Authorize) |
| POST `/api/v1/auth/refresh` | server-side revocation check | Rotate the refresh token; the old one is invalidated immediately; `tenant_id` claim checked against the user |
| POST `/api/v1/password/forgot` | IP rate limit 5/h | Forgot password (token sent via email, never in the response) |
| POST `/api/v1/password/reset` | none | Reset password with a token |
| POST `/api/v1/password/change` | authenticated | Change **your own** password (identity from JWT; no `user_id` accepted) |
| POST `/api/v1/verify/email` | none | Verify email |
| POST `/api/v1/verify/resend` | IP rate limit 5/h | Resend verification email |
| GET `/api/v1/tenants`, `GET /tenants/{id}` | superuser | Tenant reads (platform-level resources, no anonymous enumeration) |
| POST/PUT/DELETE `/api/v1/tenants` | `tenant:*` | Tenant management |
| GET/POST/PUT/DELETE `/api/v1/roles` | read: authenticated; write: `role:*` | Role management — **scoped to the caller's tenant**; cross-tenant returns 404 |
| POST `/api/v1/roles/{role_id}/users/{user_id}` | `role:update` | Assign role to user (both must belong to the caller's tenant) |
| GET/POST/PUT/DELETE `/api/v1/permissions` | read: authenticated; write: `permission:*` | Permission management (global catalog) |
| POST `/api/v1/permissions/{permission_id}/roles/{role_id}` | `permission:update` | Assign permission to role (role must belong to the caller's tenant) |
| GET/PUT `/api/v1/user/me` | authenticated | Current user info / update email |
| GET/POST/PUT/DELETE `/api/v1/user` | superuser | User administration — **scoped to the caller's tenant** |

## Tenant Isolation (Mandatory Constraints)

This is the project's core design; every tenant-scoped resource follows it:

1. **Explicit context propagation**: JWT `tenant_id` → `get_current_user` (verified against the stored user) → router → controller → use case → repository, always as explicit parameters — no contextvars;
2. **Isolation applies to everyone**: superusers bypass permission-string checks only, not tenant filtering; cross-tenant reads/writes return **404** (same semantics as "resource not found", preventing enumeration);
3. **Tenant-aware repositories**: `UserRepository.find_by_id(user_id, tenant_id)`, `RoleRepository.find_by_id(role_id, tenant_id)` etc. require the tenant; user/role listings use `find_by_tenant` — no unfiltered `find_all`;
4. **Database-level backstop**: `users` has a `(email, tenant_id)` unique constraint; `user_roles` / `role_permissions` have unique constraints + indexes (prevents concurrent duplicate assignments);
5. **Two-sided validation on associations**: assigning a role checks the user and role belong to the same tenant; assigning a permission checks the role belongs to the caller's tenant.

## Authentication & Security

- **JWT**: HS256, access 30 min + refresh 7 days (`jti`/`iat`/`tenant_id`); `get_current_user` accepts only `type=access` tokens and looks the user up by `(user_id, tenant_id)` to verify consistency;
- **Refresh-token rotation**: each refresh revokes the old `jti` and records the new one; the old token immediately returns 401; expired rows are purged hourly by a background task;
- **Rate limiting**:
  - Failed logins counted **per email** (inside the use case) + **per IP** (route layer); exceeding returns 429;
  - Backed by local **Redis** (atomic Lua counters, shared across processes, survives restarts);
  - Development: degrades to in-memory with a warning when Redis is unavailable; **production: fail-closed**;
  - Open endpoints are IP rate-limited: register 10/h, forgot-password and resend-verification 5/h;
- **Anti-enumeration**: login failures always return `Invalid credentials` (account missing / wrong password / inactive / unverified are indistinguishable); unknown accounts still run one bcrypt verify against a dummy hash (constant time);
- **Permission cache**: `require_permissions` uses an in-process 60s TTL cache (capped at 10,000 entries to bound memory); role/permission assignment routes clear it immediately;
- **Error responses**: a global handler maps everything to `{"detail": ..., "code": <status>}`; routes no longer try/except per endpoint (the only exception: the login route catches `InvalidCredentialsError` to count the IP failure, then re-raises);
- **Production safety**: `ENVIRONMENT=production` refuses to start without an explicit `SECRET_KEY`; table creation failure and admin bootstrap failure both **abort startup** (no half-broken deployments);
- **Tokens never in responses**: reset/verification tokens go only through `EmailSender` (currently ConsoleEmailSender writing to logs; swap in an SMTP implementation).

## Configuration

Configured via environment variables or a `.env` file (auto-loaded by `main.py`; unlisted variables are ignored):

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment (`production` enforces `SECRET_KEY` and fail-closed rate limiting) |
| `SECRET_KEY` | dev default | JWT signing key; must be explicit in production (`openssl rand -hex 32`) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | Database URL (PostgreSQL + asyncpg recommended for production) |
| `REDIS_URL` | `redis://localhost:6379/0` | Rate-limit storage |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `MAX_LOGIN_ATTEMPTS` | `5` | Login rate-limit threshold |
| `LOGIN_LOCKOUT_MINUTES` | `30` | Login lockout window |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Require email verification before login |
| `SERVER_HOST` / `SERVER_PORT` | `0.0.0.0` / `8000` | Bind address/port for `python main.py` |
| `SERVER_RELOAD` | `true` | Dev hot reload (set `false` in production) |
| `LOG_LEVEL` / `LOG_FILE` | `INFO` / unset | Logging level; optional log file path (unset = console only) |
| `CORS_ORIGINS` | localhost set | Allowed CORS origins (comma-separated) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | `admin@example.com` / `Admin123456` | Admin account created at startup (change in production) |
| `ADMIN_IS_SUPERUSER` | `true` | Whether the admin is a superuser |

## Database & Migrations

- Default SQLite (`sqlite+aiosqlite:///./test.db`); production switches to PostgreSQL + asyncpg via `DATABASE_URL`;
- `init_db()` creates tables at startup (convenient for development); formal changes go through Alembic:

| Migration | Contents |
|---|---|
| `742419bf3b87` baseline | 7 tables: users / tenants / roles / permissions / user_roles / role_permissions / refresh_tokens |
| `8f3c2a1b9d4e` tenant_isolation_constraints | `(email, tenant_id)` unique, association unique constraints and indexes |
| `4c1e9d7f2a58` utc_datetime_columns | time columns migrated to `DateTime(timezone=True)` |
| `9e5b3c8d1f27` drop_user_legacy_columns | drop legacy `username`, `failed_login_attempts`, `locked_until` |

```bash
alembic upgrade head               # apply to latest
python scripts/verify_alembic.py   # assert migration tables == SQLModel metadata
```

## Testing & Quality

- **289 tests, all passing**: unit tests use **real in-memory repositories + deterministic fakes** (not MagicMock, so entity/field mismatches can't hide); integration tests use in-memory SQLite + `StaticPool`, with a `TestClient` exercising the full stack;
- Coverage: entities/value objects, repositories (in-memory + SQLModel), use cases, route auth and error formats, rate limiting, JWT, permission cache, tenant isolation (two-tenant IDOR scenarios), refresh-token revocation and expired-row cleanup;
- **Lint**: `ruff` (`E/F/I/W`, line length 120); **pre-commit** hook configured;
- **CI** (`.github/workflows/ci.yml`): ruff → pytest → coverage → migration consistency check → full-stack smoke;
- Reference: [`docs/architecture-audit.md`](docs/architecture-audit.md) (architecture audit and phased hardening plan).

## Adding New Features

Follow the DDD four-layer flow:

1. **Domain** (`src/domain/`) — entities, value objects, repository interfaces, domain exceptions
2. **Infrastructure** (`src/infrastructure/`) — repository implementations (SQLModel + InMemory), security services
3. **Application** (`src/application/`) — DTOs and use cases (business failures raise `DomainError` subclasses)
4. **API** (`src/api/`) — schemas, controllers, routes (permission endpoints get `require_permissions`)
5. **Bootstrap** (`src/bootstrap/`) — register dependencies in `container.py`, register routers in `routes/__init__.py`
6. **Tests** (`tests/`) — unit tests (real in-memory repositories) + integration tests (in-memory SQLite)

## Docker

```bash
docker compose up --build   # api (port 8000) + redis, production mode
```

The compose file runs the API with `ENVIRONMENT=production` (fail-closed rate limiting, requires `SECRET_KEY`), persists SQLite data on a `/data` volume, and starts the API only after Redis passes its health check.

## Known Limitations

- No real SMTP sending (tokens go to logs); swap in an `EmailSender` implementation;
- JWTs carry no `iss`/`aud`/`pwd_version` claim, so an old access token remains valid for up to 30 minutes after a password change;
- Cross-repository operations are not atomic (e.g. register's "create personal tenant + create user" are two transactions, mitigated by compensating rollback; login's "persist refresh token + update last_login" likewise) — no Unit of Work yet;
- The permission cache is per-process, so with multiple workers each process has its own copy (changes apply immediately in the process that made them, up to TTL elsewhere);
- Refresh-token cleanup runs as one background task per process (duplicated across workers, but the deletes are idempotent).

## Tech Stack

FastAPI + Uvicorn · SQLModel/SQLAlchemy async · JWT (PyJWT) + bcrypt · Pydantic Settings · Redis · Alembic · pytest + pytest-asyncio + httpx · ruff · Docker / GitHub Actions

## License

MIT
