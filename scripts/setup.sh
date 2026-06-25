#!/usr/bin/env bash
# PixelMind AI — One-shot local setup script
set -euo pipefail

echo "🧠 PixelMind AI — Local Setup"
echo "================================"

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install v20+"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { npm install -g pnpm; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required for local DB/Redis"; exit 1; }

echo "✅ Prerequisites OK"

# Install Node dependencies
echo "📦 Installing Node dependencies..."
pnpm install

# Copy env files
if [ ! -f apps/api/.env ]; then
  cp apps/api/.env.example apps/api/.env
  echo "⚠️  Created apps/api/.env — fill in real values before running"
fi

if [ ! -f apps/web/.env.local ]; then
  cp apps/web/.env.example apps/web/.env.local
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd apps/api
python3 -m pip install -r requirements.txt --break-system-packages --quiet
cd ../..

# Start Docker services
echo "🐳 Starting PostgreSQL + Redis..."
docker compose up -d postgres redis

# Wait for Postgres
echo "⏳ Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U pixelmind >/dev/null 2>&1; do
  sleep 1
done

# Run migrations
echo "🗄️  Running database migrations..."
cd apps/api && alembic upgrade head && cd ../..

echo ""
echo "✅ Setup complete!"
echo ""
echo "Start dev servers: pnpm dev"
echo "  API: http://localhost:8000"
echo "  Web: http://localhost:5173"
echo "  Docs: http://localhost:8000/docs"
