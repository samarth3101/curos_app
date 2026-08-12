# ============================================================
# cortex-api — Multi-stage Dockerfile
# ============================================================
# Stages:
#   builder     — installs deps with uv
#   development — hot-reload dev server
#   production  — slim runtime image
# ============================================================

# ---- Base ----
FROM python:3.13-slim AS base

# Prevent Python from writing .pyc files and enable stdout buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ---- Builder ----
FROM base AS builder

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
COPY .python-version ./

# Install production dependencies into a virtual environment
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# ---- Development ----
FROM base AS development

COPY pyproject.toml ./
COPY .python-version ./

# Install all dependencies (including dev) for hot-reload
RUN uv sync 2>/dev/null || uv sync

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- Production ----
FROM python:3.13-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy the pre-built virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Run as non-root user for security
RUN addgroup --system cortex && adduser --system --group cortex
USER cortex

EXPOSE 8000

# Use gunicorn + uvicorn workers in production
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
