# PixelMind AI — Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT (React + Vite)                       │
│  Vercel CDN · TanStack Query · Zustand · React Router v6       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend (Render)                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌────────────┐   │
│  │ /auth/*  │  │ /files/* │  │ /tools/*   │  │ /jobs/*    │   │
│  │ JWT auth │  │ R2 upload│  │ CV enqueue │  │ status poll│   │
│  └──────────┘  └──────────┘  └─────┬──────┘  └────────────┘   │
│                                     │                           │
│  ┌──────────────────────────────────▼────────────────────────┐  │
│  │              ARQ Worker (same Render instance)            │  │
│  │  receipt_scanner | invoice_reader | background_remover   │  │
│  │  passport_photo | deepfake_detector | plant_disease ...  │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────┬──────────────────┬──────────────────┬───────────────┘
           │                  │                  │
    ┌──────▼──────┐   ┌───────▼──────┐   ┌──────▼──────┐
    │  Aiven PG   │   │ Upstash Redis │   │Cloudflare R2│
    │ (free tier) │   │ (500K/mo free)│   │(10GB total) │
    └─────────────┘   └──────────────┘   └─────────────┘
```

## CV Processing Pipeline (Universal Pattern)

```
User uploads image
      │
      ▼
POST /files/upload
  ├─ MIME type validation (python-magic)
  ├─ Pillow integrity check
  ├─ Size limit (25MB)
  └─ Upload to Cloudflare R2
      │
      ▼
POST /tools/{slug}/process
  └─ Deduct credits
  └─ INSERT processing_jobs (status=QUEUED)
  └─ ARQ enqueue_job()
      │
      ▼
GET /jobs/{job_id} (poll every 2s)
      │
      ▼
ARQ Worker picks job
  ├─ status=PROCESSING
  ├─ Download from R2
  ├─ CV pipeline (OpenCV → ONNX → result)
  └─ status=COMPLETED, result_json stored
      │
      ▼
Frontend renders ResultPanel
```

## Authentication Flow

```
Register/Login → JWT access_token (30min) + refresh_token (30 days)
  ↓
Axios interceptor attaches Bearer
  ↓
401 → auto-refresh → retry original request
  ↓
Refresh fails → logout → redirect /login
```

## File Retention Policy

| Plan     | Retention |
|----------|-----------|
| Free     | 24 hours  |
| Starter  | 7 days    |
| Pro      | 30 days   |

Daily ARQ cleanup job queries `files.expires_at < NOW()` → deletes from R2 → removes DB record.

## Rate Limiting

Sliding window per user_id or IP using Upstash Redis INCR+EXPIRE:
- Unauthenticated: 60 req/min
- Free users: 200 req/min
- Paid users: 1,000 req/min
- /health exempt (UptimeRobot pings)
