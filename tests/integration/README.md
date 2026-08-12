# Integration Tests

Cross-service integration tests (to be configured alongside feature implementation).

## Status

⏳ Placeholder — integration tests are added as modules are built.

## Approach

Integration tests live in each module's `tests/` directory (marked with `@pytest.mark.integration`).
This folder houses cross-service tests that span multiple modules or external dependencies.

## Running Integration Tests

```bash
cd apps/cortex-api

# Requires running PostgreSQL and Redis (or use Docker Compose)
uv run pytest -m integration -v
```
