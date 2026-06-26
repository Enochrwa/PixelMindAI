# Backend Deployment — Render.com

The FastAPI backend is deployed to [Render](https://render.com) as a Docker-based
Web Service, built from `backend/Dockerfile`.

## One-time setup

1. **Create the service** — In the Render dashboard, choose
   **New → Blueprint** and point it at this repository, or **New → Web
   Service** and set:
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Dockerfile Path:** `./Dockerfile`
   - **Health Check Path:** `/health`

   Alternatively, run `render blueprint launch` from the repo root — Render
   will read [`render.yaml`](../render.yaml) and provision the service
   automatically.

2. **Environment variables** — Set the following in the service's
   **Environment** tab (see [`.env.example`](../.env.example) for the full
   list and local-dev defaults):
   - `SECRET_KEY`
   - `DATABASE_URL` / `DATABASE_URL_POOLED` (Aiven Postgres)
   - `REDIS_URL` (Upstash)
   - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
     `R2_BUCKET_NAME`, `R2_PUBLIC_URL`
   - `GROQ_API_KEY`
   - `RESEND_API_KEY`, `BREVO_API_KEY`
   - `ALLOWED_ORIGINS` — the deployed Vercel frontend URL(s)

   `PORT`, `HOST`, and `ENVIRONMENT` are pre-set in `render.yaml`. The
   container reads `$PORT` at runtime (Render assigns this dynamically), so
   no manual port configuration is required.

3. **Database migrations** — `render.yaml` sets `alembic upgrade head` as
   the `preDeployCommand`, so migrations run automatically before each new
   release starts serving traffic.

4. **CI-gated deploys (optional but recommended)** — Render auto-deploys on
   every push to the connected branch by default. To gate deploys on CI
   passing (lint + tests) instead, disable Render's auto-deploy for the
   service and create a **Deploy Hook** (Service → Settings → Deploy Hook),
   then store its URL as the `RENDER_DEPLOY_HOOK_URL` secret in this GitHub
   repo. The `backend.yml` workflow's `deploy` job will call it after tests
   pass on `main`.

## Local development

```bash
cd backend
cp .env.example .env   # fill in real values
python3 -m pip install -r requirements.txt --break-system-packages
alembic upgrade head
uvicorn main:app --reload
```

Or via Docker Compose from the repo root: `docker compose up -d`.

## Notes

- The backend previously targeted Fly.io (see `docs/ARCHITECTURE.md` history
  in git log); Render replaces that as of the `feature/folder-restructure`
  branch.
- Render's free tier spins down idle instances; if always-on behavior is
  required, upgrade the service plan in `render.yaml` (`plan: starter` or
  higher).
