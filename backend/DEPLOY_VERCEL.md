# Deploying to Vercel

The Django app deploys to Vercel as a Python serverless function (WSGI). Static
assets are collected at build time and served from Vercel's CDN.

## Files involved

- `api/index.py` — exposes the WSGI `app` that Vercel serves.
- `vercel.json` — Python build for the app + static build for assets, plus routes.
- `build_files.sh` — installs requirements and runs `collectstatic`.

## One-time Vercel project setup

1. Import the Git repo into Vercel.
2. **Set the project's Root Directory to `backend`** (Settings → General →
   Root Directory). Everything above lives under `backend/`.
3. Add Environment Variables (Settings → Environment Variables):

   | Variable | Value |
   | --- | --- |
   | `SECRET_KEY` | a long random string |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | a hosted Postgres URL (see below) — **required** |
   | `ALLOWED_HOSTS` | your custom domain(s), comma-separated (optional; `*.vercel.app` is already allowed) |
   | `CSRF_TRUSTED_ORIGINS` | `https://your-domain.com` (optional; `https://*.vercel.app` is already trusted) |

   Vercel automatically sets `VERCEL=1`, which the settings use to switch to
   production-safe static storage and host/CSRF defaults.

4. Deploy.

## Database — required

Vercel's filesystem is read-only and ephemeral, so the bundled `db.sqlite3`
cannot be used (anything that writes — logins, sessions — would fail). Provision
a hosted Postgres (e.g. Neon, Supabase, or Vercel Postgres) and set
`DATABASE_URL`, e.g.:

```
DATABASE_URL=postgres://user:pass@host:5432/dbname?sslmode=require
```

Run migrations against it once (locally, pointed at the same `DATABASE_URL`):

```
DATABASE_URL=postgres://... python manage.py migrate
DATABASE_URL=postgres://... python manage.py createsuperuser
```

## Known limitation — WebSockets / Channels

Vercel serverless does not support long-lived WebSocket connections, so the
Channels/ASGI realtime features will not run on Vercel. The HTTP API, admin,
dashboards, and templated pages work normally over WSGI. For realtime, run the
ASGI server (Daphne/Uvicorn) on a platform that supports persistent connections.
