# PixelMind AI — Backend

FastAPI backend for PixelMind AI, a multi-tenant SaaS platform delivering
computer-vision tools (OCR, photo intelligence, creator tools, business
intelligence, agriculture AI, entertainment) through a unified REST API.

Deployed on [Render](https://render.com). See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
for deployment setup and [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
for the full system architecture.

## Stack

FastAPI · Python 3.11 · Pydantic v2 · SQLAlchemy (async) + Alembic ·
PostgreSQL (Neon) · Redis (Upstash) + ARQ workers · Cloudflare R2 ·
OpenCV + ONNX Runtime + MediaPipe · EasyOCR/PaddleOCR/Tesseract · Groq LLM API

## Local development

```bash
cp .env.example .env          # fill in real values
python3 -m pip install -r requirements.txt --break-system-packages
alembic upgrade head
uvicorn main:app --reload
```

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs (development only)

Or start the full local stack (Postgres + Redis + API + worker) from the
repo root: `docker compose up -d`.

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
