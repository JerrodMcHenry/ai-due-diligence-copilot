# SIE Core Platform — Staging Deployment Runbook

Target architecture: **Vercel** (frontend) + **Render** (backend + managed Postgres).
Render was chosen over Railway because it offers a genuinely free-tier Postgres
option suited to a staging environment, and its `render.yaml` Blueprint format
(see `render.yaml` at the repo root) lets one file define both the web service
and the database together.

This document describes how to deploy staging. **No deployment has been
performed** — this is preparation only.

## Hosts

- **Frontend**: Vercel (Next.js 16, App Router — zero custom build config needed)
- **Backend**: Render Web Service (Python/FastAPI, `render.yaml` at repo root)
- **Database**: Render managed PostgreSQL (same provider as the backend, defined
  in the same `render.yaml`)

## Required environment variables

### Backend (Render)

| Variable | Source | Notes |
|---|---|---|
| `DATABASE_URL` | Auto-populated by Render from the linked Postgres resource | Do not set manually |
| `OPENAI_API_KEY` | Set manually in the Render dashboard | Secret — never commit |
| `TAVILY_API_KEY` | Set manually in the Render dashboard | Secret — never commit |
| `CORS_ALLOWED_ORIGINS` | Set manually in the Render dashboard | Comma-separated list of allowed frontend origins, e.g. `https://sie-staging.vercel.app`. Unset = local-dev-only origins (see `app/api.py`) |
| `PYTHON_VERSION` | Set in `render.yaml` | Pinned to `3.12.5` to match the version this app has been tested against locally |

### Frontend (Vercel)

| Variable | Value | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | The deployed Render backend's public URL, e.g. `https://sie-backend-staging.onrender.com` | Must be set before the first Vercel build that needs to talk to staging data — it's baked in at build time as a `NEXT_PUBLIC_` var |

## Backend build/start commands

```
Build:  pip install -r requirements.txt
Start:  uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

No `--reload` in production. `$PORT` is injected by Render at runtime — do not
hardcode a port. Both commands are already encoded in `render.yaml`.

## Frontend environment settings

Vercel auto-detects Next.js — no custom build/output settings are required.
The only setting to configure is the `NEXT_PUBLIC_API_URL` environment variable
above, set per-environment (Preview/Production) in the Vercel project settings.

## CORS setup

`app/api.py` now resolves allowed origins from `CORS_ALLOWED_ORIGINS`
(comma-separated), falling back to the two local-dev origins
(`http://localhost:3000`, `http://127.0.0.1:3000`) when unset — local
development behavior is unchanged. **Never set this to `*`.** Once the Vercel
staging URL is known, set it as `CORS_ALLOWED_ORIGINS` on the Render service
and redeploy (or Render will pick it up on the next deploy/restart).

## Expected deployment order

1. **Create the Render Blueprint** from `render.yaml` (Render dashboard → New →
   Blueprint → point at this repo). This provisions the Postgres database and
   the (not-yet-working) web service.
2. **Set `OPENAI_API_KEY` and `TAVILY_API_KEY`** on the web service in the
   Render dashboard (Blueprint intentionally leaves these blank).
3. **Deploy the backend.** Confirm it starts and the startup migrations run
   cleanly against the fresh, empty staging database (see "Database
   readiness" below).
4. **Note the backend's public URL** (e.g. `https://sie-backend-staging.onrender.com`).
5. **Deploy the frontend to Vercel**, setting `NEXT_PUBLIC_API_URL` to that URL
   before the build.
6. **Set `CORS_ALLOWED_ORIGINS`** on the Render backend to the Vercel URL from
   step 5, then redeploy the backend so it picks up the new origin.
7. Run the health verification steps below.

## Health verification steps

1. `GET {backend_url}/health` → `{"status": "healthy"}`
2. `GET {backend_url}/version` → confirms `methodology_version` is stamped
   and matches the current constant.
3. Open the deployed frontend → Dashboard loads with an empty/zero state
   (fresh staging DB has no analyses yet — this is expected, not a bug).
4. Analyze Startup → submit a real company → confirm the analysis completes,
   redirects to its Startup Profile, and the profile renders (six pillars,
   SPS, evidence).
5. Confirm that company now appears in Rankings and Search on the deployed
   frontend.
6. Check the browser console for CORS errors specifically — a misconfigured
   `CORS_ALLOWED_ORIGINS` shows up immediately here as blocked requests.

## Rollback basics

- **Frontend**: Vercel keeps every previous deployment; "Promote to Production"
  (or "Redeploy") any prior working deployment from the Vercel dashboard —
  effectively instant, no data implications.
- **Backend**: Render keeps a deploy history per service; roll back to a
  previous deploy from the Render dashboard. Because startup migrations are
  additive-only (`CREATE TABLE IF NOT EXISTS` / `ADD COLUMN`, each wrapped in
  its own try/except), rolling the backend back to an older commit is safe —
  older code simply won't reference newer columns, and no migration ever
  drops or destructively alters existing data.
- **Database**: this is a staging database with no production data to protect;
  if it ever needs to be reset, delete and recreate the Render Postgres
  resource rather than attempting to hand-edit it. Do not do this to the
  production database once one exists.
