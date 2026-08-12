# Curos — Cortex OI

> **Organizational Intelligence for modern institutions.**  
> Cortex OI is the first product from [Curos](https://curos.io) — a platform designed to help organizations operate with clarity, speed, and intelligence.

---

## Repository Structure

```
curos/
├── apps/
│   ├── cortex-api/        # FastAPI backend (Python 3.13)
│   ├── cortex-web/        # Next.js 14 frontend (TypeScript)
│   └── cortex-worker/     # Background worker skeleton
├── packages/
│   ├── types/             # Auto-generated API types (openapi-typescript)
│   ├── ui/                # Shared React components
│   ├── config/            # Shared config helpers
│   └── eslint-config/     # Shared ESLint configuration
├── infrastructure/
│   ├── docker/            # Docker support files
│   └── scripts/           # Setup and seed scripts
├── docs/                  # Architecture and development documentation
├── tests/                 # E2E and integration test suites
└── .github/workflows/     # CI/CD pipelines
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.13 |
| Backend framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Validation | Pydantic 2.x |
| Migrations | Alembic |
| Python package manager | uv |
| Database | PostgreSQL 16 |
| Cache / Broker | Redis 7 |
| Frontend framework | Next.js 14 (App Router) |
| Frontend language | TypeScript (strict) |
| Styling | Tailwind CSS v3 |
| Frontend state | Zustand |
| Frontend package manager | pnpm workspaces |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Lint (Python) | Ruff |
| Type-check (Python) | MyPy |
| Tests (Python) | Pytest + pytest-asyncio |
| API types (frontend) | openapi-typescript (generated) |

---

## Prerequisites

- **Docker** ≥ 24 and **Docker Compose** ≥ 2.20
- **Python** 3.13 (via `pyenv` or system)
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js** ≥ 20 (LTS)
- **pnpm** ≥ 9 — `npm install -g pnpm`

---

## Quick Start (Local Development)

### 1. Clone & configure environment

```bash
git clone https://github.com/curos/cortex.git
cd cortex

# Copy root env file
cp .env.example .env

# Copy API env file
cp apps/cortex-api/.env.example apps/cortex-api/.env

# Copy web env file
cp apps/cortex-web/.env.local.example apps/cortex-web/.env.local
```

### 2. Start all services with Docker Compose

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`
- **cortex-api** on `localhost:8000` (hot-reload)
- **cortex-web** on `localhost:3000` (hot-reload)
- **cortex-worker** (no port; background process)

### 3. Verify health

```bash
# Liveness
curl http://localhost:8000/api/v1/health

# Readiness (checks DB + Redis)
curl http://localhost:8000/api/v1/health/ready

# Frontend
open http://localhost:3000
```

### 4. Install dependencies (for local development outside Docker)

```bash
# Python backend
cd apps/cortex-api
uv sync

# Frontend
cd ../..
pnpm install
```

### 5. Run database migrations

```bash
cd apps/cortex-api
uv run alembic upgrade head
```

---

## Development Commands

### Backend

```bash
cd apps/cortex-api

# Run dev server
uv run uvicorn app.main:app --reload --port 8000

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type-check
uv run mypy .

# Tests
uv run pytest

# Tests with coverage
uv run pytest --cov=app --cov-report=html

# New migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

### Frontend

```bash
# Dev server
pnpm --filter cortex-web dev

# Type-check
pnpm --filter cortex-web type-check

# Lint
pnpm --filter cortex-web lint

# Build
pnpm --filter cortex-web build

# Generate API types from backend OpenAPI spec
# (requires cortex-api running on localhost:8000)
pnpm --filter @curos/types generate
```

---

## Architecture

See [`docs/architecture/`](./docs/architecture/) for detailed documentation:

- [Backend Architecture](./docs/architecture/backend.md) — Clean Architecture, module structure, dependency rules
- [Frontend Architecture](./docs/architecture/frontend.md) — Feature-driven structure, state management, type generation

---

## Documentation

- [Getting Started](./docs/development/getting-started.md)
- [Environment Variables](./docs/development/environment.md)
- [Contributing](./docs/development/contributing.md)
- [API Conventions](./docs/api/conventions.md)

---

## Product

**Cortex OI Campus Operations** — Event & Workflow Management  

The first release covers the complete event lifecycle:  
Create → Approve → Publish → Register → Execute → Attendance → Feedback → Certificate → Analytics → Archive

---

## License

MIT © 2026 Curos
