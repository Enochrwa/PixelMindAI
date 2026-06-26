# PixelMind AI — Frontend

React + Vite + TypeScript frontend for PixelMind AI.

Deployed on [Vercel](https://vercel.com). See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
for deployment setup and [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md)
for the full system architecture.

## Stack

React 18 · Vite 6 · TypeScript (strict) · Tailwind CSS · TanStack Query/Router ·
Zustand · Axios (with auto-refresh interceptor) · Vitest + Testing Library

## Local development

```bash
pnpm install
cp .env.example .env.local   # fill in real values
pnpm dev
```

Visit http://localhost:5173. The dev server proxies `/api` requests to
`http://localhost:8000` — make sure the backend is running locally too (see
`../backend/README.md`).

## Code quality & tests

```bash
pnpm typecheck   # tsc --noEmit
pnpm lint        # ESLint
pnpm test        # Vitest
pnpm build       # Production build (tsc --noEmit && vite build)
```

## Project layout

```
src/
├── components/   # UI, layout, tool-specific components
├── pages/        # Route pages
├── hooks/        # useJobPoller, useCurrentUser, etc.
├── stores/       # Zustand (auth, UI state)
├── lib/          # Axios client with auto-refresh
└── types/        # TypeScript types
packages/         # @pixelmind/ui and @pixelmind/shared-types — scaffolded
                   # for future shared use, not currently imported anywhere
docs/             # Deployment docs
vercel.json       # Routing/header config for Vercel
```
