# ---- cortex-worker Dockerfile ----
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# ---- development ----
FROM base AS development

COPY pyproject.toml .python-version* ./
RUN uv sync 2>/dev/null || uv sync

COPY . .
CMD ["uv", "run", "python", "-m", "worker.main"]

# ---- production ----
FROM base AS production

COPY pyproject.toml .python-version* ./
RUN uv sync --no-dev 2>/dev/null || uv sync --no-dev

COPY worker/ ./worker/

RUN addgroup --system cortex && adduser --system --group cortex
USER cortex

CMD ["uv", "run", "python", "-m", "worker.main"]
