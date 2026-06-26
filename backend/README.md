# PixelMind AI — Backend

FastAPI backend for PixelMind AI, a multi-tenant SaaS platform delivering
computer-vision tools (OCR, photo intelligence, creator tools, business
intelligence, agriculture AI, entertainment) through a unified REST API.

Deployed on [Render](https://render.com). See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
for deployment setup and [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
for the full system architecture.

## Stack

FastAPI · Python 3.11 · Pydantic v2 · SQLAlchemy (async) + Alembic ·
PostgreSQL (Aiven) · Redis (Upstash) + ARQ workers · Cloudflare R2 ·
OpenCV + ONNX Runtime + MediaPipe · EasyOCR/PaddleOCR/Tesseract · Groq LLM API

## Local development

This backend connects to **hosted** Aiven PostgreSQL and Upstash Redis — there
are no local database/cache containers. The same `backend/.env` file is used
for both run modes below.

```bash
cp .env.example .env          # fill in your Aiven DATABASE_URL and Upstash REDIS_URL
```

### Option A — Run directly (uvicorn)

```bash
python3 -m pip install -r requirements.txt --break-system-packages
alembic upgrade head
uvicorn main:app --reload
```

### Option B — Run via Docker

```bash
docker compose -f ../infra/docker/docker-compose.yml up -d --build
# or, from the repo root:
docker compose up -d --build
```

This builds the API and worker images and runs them with `backend/.env`
loaded via `env_file`, so no values need to be duplicated in
`docker-compose.yml`.

Either way:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs (development only)

## Code quality & tests

```bash
ruff check .          # Lint
ruff format .         # Format
mypy app              # Type check
pytest tests/         # Tests (unit + integration)
```

## Project layout

```
app/
├── core/           # Config, security, storage, queue
├── api/v1/         # REST endpoints (auth, files, jobs, tools)
├── cv/             # Computer vision modules (ocr, photo, creator, business, agriculture, entertainment)
├── db/             # SQLAlchemy models + Alembic migrations
├── middleware/     # Rate limiting
├── workers/        # ARQ async job workers
└── services/       # Business logic services
tests/              # pytest (unit + integration)
docs/               # Deployment docs
render.yaml         # Render Blueprint
Dockerfile          # Multi-stage production image
```
