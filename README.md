<div align="center">

# PixelMind AI 🧠✨

**The World's First Unified Visual Intelligence Operating System**

[![Backend CI](https://github.com/Enochrwa/PixelMindAI/actions/workflows/backend.yml/badge.svg)](https://github.com/Enochrwa/PixelMindAI/actions/workflows/backend.yml)
[![Frontend CI](https://github.com/Enochrwa/PixelMindAI/actions/workflows/frontend.yml/badge.svg)](https://github.com/Enochrwa/PixelMindAI/actions/workflows/frontend.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*43 AI-powered computer vision tools · $0 infrastructure · Built for Africa, used worldwide*

</div>

---

## 🌟 What is PixelMind AI?

PixelMind AI is a multi-tenant SaaS platform delivering 43 professional computer vision tools through a single, unified interface. From OCR and passport photo generation to deepfake detection and crop disease diagnosis — all running on a zero-cost infrastructure stack.

Built with FastAPI + React/TypeScript, deployed on Fly.io + Vercel, powered by OpenCV, ONNX Runtime, and Groq's free LLM API.

## 🗂️ Repository Structure

```
pixelmind-ai/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/           # Config, security, storage, queue
│   │   │   ├── api/v1/         # REST endpoints (auth, files, jobs, tools)
│   │   │   ├── cv/             # Computer vision modules
│   │   │   │   ├── ocr/        # EasyOCR + PaddleOCR + Tesseract
│   │   │   │   ├── photo/      # Background removal, upscaling, face AI
│   │   │   │   ├── creator/    # CLIP, Groq captions, memes
│   │   │   │   ├── business/   # Counting, crowd analysis, PPE
│   │   │   │   ├── agriculture/# Plant disease, crop health, soil
│   │   │   │   └── entertainment/ # Age, emotion, deepfake, pets
│   │   │   ├── db/             # SQLAlchemy models + Alembic migrations
│   │   │   ├── middleware/     # Rate limiting
│   │   │   ├── workers/        # ARQ async job workers
│   │   │   └── services/       # Business logic services
│   │   ├── tests/              # pytest (unit + integration)
│   │   ├── pyproject.toml      # Dependencies, ruff, mypy, pytest config
│   │   ├── Dockerfile          # Multi-stage production image
│   │   └── alembic.ini
│   └── web/                    # React + Vite + TypeScript + Tailwind
│       └── src/
│           ├── components/     # UI, layout, tool-specific components
│           ├── pages/          # Route pages
│           ├── hooks/          # useJobPoller, useCurrentUser, etc.
│           ├── stores/         # Zustand (auth, UI state)
│           ├── lib/            # Axios client with auto-refresh
│           └── types/          # TypeScript types
├── packages/
│   ├── shared-types/           # Types shared across apps
│   └── ui/                     # Shared React component library
├── infra/
│   ├── fly/fly.toml            # Fly.io deployment (no-sleep, Johannesburg)
│   ├── docker/docker-compose.yml # Local dev stack
│   └── models/                 # ONNX model weights (.gitignored, add manually)
├── .github/workflows/          # CI/CD: backend, frontend, security
├── turbo.json                  # Turborepo pipeline
└── pnpm-workspace.yaml
```

## 🚀 Quick Start (Local Dev)

### Prerequisites
- Node.js ≥ 20, pnpm ≥ 9
- Python ≥ 3.11
- Docker & Docker Compose

### 1. Clone & install

```bash
git clone https://github.com/Enochrwa/PixelMindAI.git
cd PixelMindAI
pnpm install
```

### 2. Environment setup

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
# Fill in real values in apps/api/.env
```

### 3. Start infrastructure

```bash
docker compose up -d postgres redis
```

### 4. Run database migrations

```bash
cd apps/api
alembic upgrade head
```

### 5. Start dev servers

```bash
# From repo root — starts both API and web concurrently
pnpm dev
```

- **API:** http://localhost:8000
- **Web:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs (development only)

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + TypeScript (strict) + Tailwind CSS |
| API | FastAPI + Python 3.11 + Pydantic v2 |
| Database | PostgreSQL via Neon (free) — SQLAlchemy async + Alembic |
| Cache / Queue | Upstash Redis + ARQ async workers |
| File Storage | Cloudflare R2 (10GB free, zero egress) |
| CV Inference | OpenCV + ONNX Runtime + MediaPipe + rembg (U2Net) |
| OCR | EasyOCR + PaddleOCR + Tesseract (multi-engine fallback) |
| Language AI | Groq API — LLaMA 3.1 8B (14,400 req/day free) |
| Auth | Custom JWT (access + refresh) + bcrypt |
| Email | Resend (primary) + Brevo (fallback) |
| Error Tracking | Sentry (5K errors/month free) |
| Analytics | PostHog (1M events/month free) |
| Deployment | Fly.io (backend, Johannesburg) + Vercel (frontend) |
| CI/CD | GitHub Actions — lint → test → build → deploy |

## 🔬 Code Quality

```bash
# Python
cd apps/api
ruff check .          # Lint
ruff format .         # Format
mypy app              # Type check
pytest tests/         # Tests

# TypeScript
cd apps/web
pnpm lint             # ESLint
pnpm typecheck        # tsc --noEmit
pnpm test             # Vitest

# From root
pnpm build            # Full turbo build
```

## 📋 Sprint Roadmap

| Sprint | Theme | Tools |
|--------|-------|-------|
| 0 | Foundation & DevOps | Auth, file upload, async queue, CI/CD |
| 1–2 | Document Intelligence | Receipt Scanner, Invoice, Handwriting OCR, Menu Scanner (+8) |
| 3–4 | Photo Intelligence | Background Remover, Passport Photo, Upscaler, Deepfake Detector (+7) |
| 5–6 | Creator Studio | Thumbnail Analyzer, Caption Lens, PixelStory (world-first) (+7) |
| 7–8 | Business Intelligence | Shelf Counter, CrowdMood (world-first), PPE Checker (+8) |
| 9–10 | Agriculture AI | Plant Disease, Crop Health, Vision Replay (world-first) (+6) |
| 11 | Entertainment | Age Predictor, Deepfake Detector, Vibe Check (+7) |
| 12–13 | Billing & Launch | Stripe, API access, Product Hunt launch |

## 📜 License

MIT © 2026 EnochLabs — Enock Uwumukiza
