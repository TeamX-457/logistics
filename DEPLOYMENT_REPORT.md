# Deployment Report — Render

**Repo:** `github.com/TeamX-457/logistics`
**Date:** 2026-08-01
**Current live status:** BROKEN — every URL returns HTTP 400

---

## Verified branch state

Confirmed against the remote just now (`git ls-remote --heads origin`):

| Branch | Commit | Contents |
|---|---|---|
| `main` | `b00799f3` | `backend/` only. **This is what is deployed now, and it is broken.** |
| `fix-render-deploy` | `424bc0c5` | `main` + the Render fix. 3 files, +33 lines. |
| `logistica-tracking-api` | `fa82e146` | `main` + the same Render fix + the whole `logistica_tracking/` app + docs. 90 files, +5123 lines. |

**Important:** I verified with a diff that the backend fix on `logistica-tracking-api`
is **byte-identical** to the one on `fix-render-deploy`, and that
`logistica-tracking-api` still contains the full `backend/` folder. It is a strict
superset of `fix-render-deploy`, not a divergent rewrite.

---

## What is actually wrong right now

The live service returns **HTTP 400 `DisallowedHost`** on every path — `/`,
`/api/schema/`, `/api/docs/`. `/api/health` does not exist in the deployed code.

Cause: `backend/config/settings.py` only auto-allowed hosts inside an
`if ON_VERCEL:` branch. Render never sets `VERCEL`, so `ALLOWED_HOSTS` stayed
`["localhost", "127.0.0.1"]` and Django rejected every request before it reached
any view.

Two things follow from that, and they are separate problems:

1. The host config is wrong. Fixed on `fix-render-deploy`.
2. **`DEBUG=True` is on in production.** That is why you are seeing the yellow
   Django error page publicly. It leaks settings, file paths and tracebacks to
   anyone who visits. This one is a security issue, not just a broken deploy.

---

## Task 1 — Fix the live site (do this first)

**Deploy from: `fix-render-deploy` (`424bc0c5`)**

Merge it to `main` and redeploy, or point the existing service at the branch.

It changes 3 files, all in `backend/config/`:

- `settings.py` — detect Render via `RENDER` / `RENDER_EXTERNAL_HOSTNAME`, allow
  `.onrender.com`, and set `SECURE_PROXY_SSL_HEADER` so Django knows the request
  arrived over HTTPS (Render terminates TLS at its edge and forwards plain HTTP).
- `urls.py` — route `/api/health`.
- `views.py` — the health view itself.

Settings and routing only. **No migrations, no models, no data access.** It cannot
affect the live database.

### Env vars to set on the service

| Variable | Value | Why |
|---|---|---|
| `DEBUG` | `False` | **Set this explicitly.** Turns off the public error page. |
| `SECRET_KEY` | your existing secret | Do not regenerate — it invalidates active sessions. |

`RENDER` and `RENDER_EXTERNAL_HOSTNAME` are injected by Render automatically. You
do not need to set `ALLOWED_HOSTS` by hand; the fix derives it.

### Health check path

Set it to `/api/health`. It returns `{"status": "ok"}` with no auth and no DB
query, so it stays green even if Postgres is down — which is what you want from a
liveness probe.

### How to confirm it worked

```
curl -i https://<service>.onrender.com/api/health
```

Expect `200` and `{"status": "ok"}`. If you still get `400`, the new commit did not
actually deploy — check the deploy log for the commit SHA.

---

## Task 2 — Deploy the tracking API

**Deploy from: `logistica-tracking-api` (`fa82e146`)**

This is a **second, separate service**. Do not point the existing service at it.
The two apps have different roots, different servers and different dependencies.

| | Existing backend | Tracking API |
|---|---|---|
| Root directory | `backend/` | `logistica_tracking/` |
| Server | gunicorn (WSGI) | **daphne (ASGI)** |
| Needs Redis | no | **yes** |
| Needs a worker | no | **yes** |

### Service settings

- **Root directory:** `logistica_tracking`
- **Build:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- **Start:** `daphne -b 0.0.0.0 -p $PORT logistica_tracking.asgi:application`
- **Health check path:** `/api/schema/`

It **must** be daphne, not gunicorn. The app serves WebSockets for live GPS
tracking and job dispatch; gunicorn will serve the REST endpoints fine and then
silently fail every WebSocket connection. A `Procfile` with the correct command is
already committed at the app root.

### Required env vars

All of these are mandatory — `production.py` raises `ImproperlyConfigured` and
refuses to boot if any is missing. That is deliberate, so a misconfigured deploy
fails loudly instead of running on defaults.

| Variable | Notes |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `logistica_tracking.settings.production` |
| `SECRET_KEY` | Generate a **new** one. Do not reuse the backend's. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` | See the database note below. |
| `DB_PORT` | Optional, defaults to `5432`. |
| `REDIS_URL` | Required. Used for both Channels and Celery. |
| `DJANGO_ALLOWED_HOSTS` | Set to the service hostname. Defaults to `*` — tighten it. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated origins for the mobile app. |

### Also needs a worker

Job-accept conflict resolution runs on Celery, not in the request. Without a
worker, a driver tapping "accept" gets a `202` and then **nothing ever happens** —
the job is never assigned.

Start command: `celery -A logistica_tracking worker --loglevel=info`

Same env vars, same Redis instance.

---

## Blocker to fix before Task 2 goes live

`production.py` sets `SECURE_SSL_REDIRECT = True`, but **`SECURE_PROXY_SSL_HEADER`
is not set anywhere in the tracking app** — I grepped the whole settings package to
confirm.

On Render this causes an infinite redirect loop: TLS terminates at the edge, Django
sees plain HTTP, decides the request is insecure, and 301s to HTTPS forever. The
service will look deployed and answer nothing. Browsers report
`ERR_TOO_MANY_REDIRECTS`.

Fix — add to `logistica_tracking/settings/production.py`:

```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

This is the same one-liner already in the backend fix. It is not yet applied to the
tracking app. **Tell me and I will commit it**, or apply it directly — either way it
needs to be in before the first deploy, or the service will not respond.

---

## Database

The backend's live Postgres holds real user data. The tracking app defines its own
models (`User`, `Delivery`, `Location`, `TripSummary`) and running its migrations
against that database **would create tables and could collide with existing ones.**

Do not point `DB_*` at the live database until this is decided. Two safe options:

- **Separate database** — cleanest, zero risk to existing data.
- **Same instance, separate schema** — if a new database is not available.

This decision has not been made yet. Owner's instruction stands: do not touch the
live DB. Confirm with them before running any migration.

---

## Order of work

1. Merge `fix-render-deploy` → redeploy → verify `/api/health` returns `200`.
2. Set `DEBUG=False`. Confirm the Django error page is gone.
3. Decide the database question for the tracking app.
4. Add `SECURE_PROXY_SSL_HEADER` to the tracking app's `production.py`.
5. Create the tracking web service (daphne) + worker service (celery) from
   `logistica-tracking-api`.
6. Verify `/api/docs/` loads, then verify a WebSocket connects to
   `wss://<host>/ws/driver/?token=<jwt>`.

Steps 1–2 fix the outage and are independent of everything else. They can ship now.

---

## API documentation

Full reference for all 26 REST endpoints and 3 WebSocket channels is committed at
`logistica_tracking/docs/index.html` on `logistica-tracking-api`. Self-contained —
open it in a browser, no build step. Give this to the React Native developer.

Once deployed, live schema is at `/api/schema/` and a Swagger console at
`/api/docs/`.
