# Getting Started

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker | ≥ 24 | [docker.com](https://docker.com) |
| Docker Compose | ≥ 2.20 | Included with Docker Desktop |
| Python | 3.13 | `pyenv install 3.13` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | ≥ 20 LTS | [nodejs.org](https://nodejs.org) |
| pnpm | ≥ 9 | `npm install -g pnpm` |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/curos/cortex.git
cd cortex

# 2. First-time setup (copies .env files, installs deps, starts services, runs migrations)
./infrastructure/scripts/setup.sh

# 3. Start everything
docker compose up --build

# 4. Verify
curl http://localhost:8000/api/v1/health/ready
open http://localhost:3000
```

## Running Individually (without Docker)

**Backend:**
```bash
# Start PostgreSQL + Redis via Docker
docker compose up -d postgres redis

cd apps/cortex-api
cp .env.example .env   # edit DATABASE_URL and REDIS_URL to use localhost

uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd apps/cortex-web
cp .env.local.example .env.local

pnpm install
pnpm dev
```

## OpenAPI / Swagger

When running in development mode, the interactive API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Regenerate Frontend Types

After changing backend schemas:

```bash
# Requires cortex-api running on localhost:8000
pnpm --filter @curos/types generate
```
