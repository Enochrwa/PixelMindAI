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

# Install frontend (Node) dependencies
echo "📦 Installing frontend dependencies..."
(cd frontend && pnpm install)

# Copy env files
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "⚠️  Created backend/.env — fill in real values before running"
fi

if [ ! -f frontend/.env.local ]; then
  cp frontend/.env.example frontend/.env.local
fi

# Install Python dependencies
echo "🐍 Installing backend (Python) dependencies..."
(cd backend && python3 -m pip install -r requirements.txt --break-system-packages --quiet)

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
(cd backend && alembic upgrade head)

echo ""
echo "✅ Setup complete!"
echo ""
echo "Start the backend:  cd backend && uvicorn main:app --reload"
echo "Start the frontend: cd frontend && pnpm dev"
echo "  API:  http://localhost:8000"
echo "  Web:  http://localhost:5173"
echo "  Docs: http://localhost:8000/docs"
