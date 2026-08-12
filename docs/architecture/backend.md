# Backend Architecture

## Overview

Cortex OI uses a **modular monolith** architecture following Clean Architecture principles. The system is designed to be split into services in the future if needed, but starts as a single deployable unit.

## Dependency Rule

```
API Layer
    ↓
Application Layer
    ↓
Domain Layer

Infrastructure Layer (implements interfaces defined by Domain/Application)
```

**Rule**: Dependencies always point inward. The Domain layer has zero external dependencies. Infrastructure implements interfaces — it never contaminates the domain.

## Module Structure

Every module follows this layout:

```
modules/<module_name>/
├── api/                    # FastAPI routes — marshal/unmarshal only, no logic
├── application/            # Use cases, commands, queries, application services
├── domain/
│   ├── entities/           # Pure Python domain objects (identified by ID)
│   ├── value_objects/      # Immutable, validated domain values
│   └── events/             # Domain events (raised by domain, consumed elsewhere)
├── infrastructure/
│   ├── models/             # SQLAlchemy ORM models (NOT domain entities)
│   └── repositories/       # Concrete async repository implementations
├── schemas/                # Pydantic request/response schemas (API boundary)
└── tests/                  # Module-scoped tests
```

## Current Modules

| Module | Status | Description |
|---|---|---|
| `identity` | Skeleton | JWT auth, user management, OIDC-ready |
| `organization` | Stub | Multi-tenant organization management |

## Key Design Decisions

### No business logic in API routes
Routes only: parse input → call application service → return response.

### Domain entities are pure Python
`BaseEntity` is a Python dataclass. It knows nothing about SQLAlchemy, FastAPI, or Redis.

### ORM models are separate from domain entities
`infrastructure/models/` contains SQLAlchemy models. Repositories map between ORM models and domain entities.

### OIDC abstraction boundary
`IdentityService.verify_access_token()` is the single point where JWT verification happens. Replace the body of this method to integrate an external OIDC provider without touching any business logic.

### Multi-tenant from day one
Every entity carries a `tenant_id`. All queries are scoped to the current tenant.

## Shared Infrastructure

| Component | Location | Purpose |
|---|---|---|
| Database | `app/infrastructure/database.py` | Async SQLAlchemy engine + session |
| Cache | `app/infrastructure/cache.py` | Redis async client |
| Config | `app/core/config.py` | Pydantic settings |
| Logging | `app/core/logging.py` | structlog (JSON in prod) |
| Exceptions | `app/core/exceptions.py` | Structured error responses |
| Dependencies | `app/core/dependencies.py` | FastAPI DI providers |
