#!/usr/bin/env bash
# ============================================================
# setup.sh — First-run local development setup
# ============================================================
set -euo pipefail

echo "🚀 Setting up Curos development environment..."

# ---- Check prerequisites ----
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required. Install from https://docker.com"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm is required. Run: npm install -g pnpm"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "❌ uv is required. Run: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# ---- Environment files ----
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "📋 Copying environment files..."
[ -f "$ROOT_DIR/.env" ] || cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
[ -f "$ROOT_DIR/apps/cortex-api/.env" ] || cp "$ROOT_DIR/apps/cortex-api/.env.example" "$ROOT_DIR/apps/cortex-api/.env"
[ -f "$ROOT_DIR/apps/cortex-web/.env.local" ] || cp "$ROOT_DIR/apps/cortex-web/.env.local.example" "$ROOT_DIR/apps/cortex-web/.env.local" 2>/dev/null || true

# ---- Install frontend deps ----
echo "📦 Installing frontend dependencies..."
cd "$ROOT_DIR" && pnpm install

# ---- Install Python deps ----
echo "🐍 Installing Python dependencies..."
cd "$ROOT_DIR/apps/cortex-api" && uv sync
cd "$ROOT_DIR/apps/cortex-worker" && uv sync

# ---- Start services ----
echo "🐳 Starting Docker services..."
cd "$ROOT_DIR" && docker compose up -d postgres redis

# ---- Wait for postgres ----
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U cortex -d cortex_dev >/dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL ready"

# ---- Run migrations ----
echo "🗄️  Running database migrations..."
cd "$ROOT_DIR/apps/cortex-api" && uv run alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "Run the full stack with:"
echo "  docker compose up --build"
echo ""
echo "Or run services individually:"
echo "  Backend:  cd apps/cortex-api && uv run uvicorn app.main:app --reload"
echo "  Frontend: pnpm --filter cortex-web dev"
