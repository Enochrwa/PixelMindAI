# Frontend Deployment — Vercel

The React + Vite frontend is deployed to [Vercel](https://vercel.com).

## One-time setup

1. **Import the project** in Vercel and set:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `pnpm build` (default for Vite preset)
   - **Output Directory:** `dist` (default for Vite preset)
   - **Install Command:** `pnpm install`

2. **Environment variables** — In the Vercel project's **Settings →
   Environment Variables**, set:
   - `VITE_API_URL` — the deployed backend URL (Render), e.g.
     `https://pixelmind-api.onrender.com/api/v1`

   See [`.env.example`](../.env.example) for local-dev defaults.

3. **Routing & headers** — handled by [`vercel.json`](../vercel.json):
   SPA fallback rewrite to `index.html`, security headers, and long-cache
   `Cache-Control` for static assets.

4. **CI-gated deploys** — `frontend.yml`'s `deploy` job runs after lint,
   tests, and build all pass on `main`, then deploys via `vercel --prod`
   using the `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID`
   repository secrets. (Vercel's own git integration can also auto-deploy
   preview builds for PRs independently of this workflow.)

## Local development

```bash
cd frontend
pnpm install
cp .env.example .env.local   # fill in real values
pnpm dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api` to
`http://localhost:8000` (see `vite.config.ts`) for local backend testing.

## Notes

- `packages/ui` and `packages/shared-types` are scaffolded for future shared
  component/type use (e.g. a future API SDK or micro-frontend) but are not
  currently imported anywhere in `src/`. They're plain local folders, not a
  pnpm workspace — add them back as workspace packages if/when they're
  actually consumed.
