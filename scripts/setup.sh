#!/usr/bin/env bash
# PixelMind AI — One-shot local setup script
set -euo pipefail

echo "🧠 PixelMind AI — Local Setup"
echo "================================"

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install v20+"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { npm install -g pnpm; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required"; exit 1; }

echo "✅ Prerequisites OK"

# Install frontend (Node) dependencies
echo "📦 Installing frontend dependencies..."
(cd frontend && pnpm install)

# Copy env files
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
  echo "⚠️  Created backend/.env — fill in your Aiven (DATABASE_URL) and"
  echo "    Upstash (REDIS_URL) credentials before running."
  exit 1
fi

if [ ! -f frontend/.env.local ]; then
  cp frontend/.env.example frontend/.env.local
fi

# Install Python dependencies
echo "🐍 Installing backend (Python) dependencies..."
(cd backend && python3 -m pip install -r requirements.txt --break-system-packages --quiet)

# Run migrations against the hosted Aiven database
echo "🗄️  Running database migrations against Aiven..."
(cd backend && alembic upgrade head)

echo ""
echo "✅ Setup complete!"
echo ""
echo "This backend connects to hosted Aiven PostgreSQL + Upstash Redis —"
echo "no local DB/Redis containers needed. Pick either run mode:"
echo ""
echo "  Direct:  cd backend && uvicorn main:app --reload"
echo "  Docker:  docker compose -f infra/docker/docker-compose.yml up -d --build"
echo ""
echo "  API:  http://localhost:8000"
echo "  Web:  http://localhost:5173"
echo "  Docs: http://localhost:8000/docs"

