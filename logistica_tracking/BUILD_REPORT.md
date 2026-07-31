# Logistica Tracking — Build Report

Date: 2026-07-21 (updated same day after user testing feedback)
Scope: Backend (Django + DRF + Channels + Redis) and a Tailwind/HTML/JS test console. The React Native app is being built separately by another engineer — nothing here is meant to replace it.

**Revision note**: sections 10 and 13 were updated after initial user testing surfaced two things — a real bug (§11) and a design change requested by the user: separate per-role dashboard URLs instead of one shared page (§10). Both are reflected below as the current state, not as a changelog. §14 covers a full visual redesign done afterward per a detailed design spec — file-by-file, as that spec requested.

---

## 1. Stack actually installed

| Piece | Package | Version |
|---|---|---|
| Web framework | Django | 6.0.7 |
| API layer | djangorestframework | 3.17.1 |
| Auth | djangorestframework-simplejwt | 5.5.1 |
| Real-time | channels | 4.3.2 |
| Real-time transport | channels_redis | 4.3.0 |
| ASGI server | daphne | 4.2.2 |
| Postgres driver | psycopg (v3) | 3.3.4 |
| Redis client | redis | 8.0.1 |
| CORS | django-cors-headers | 4.9.0 |

Full pinned list is in `requirements.txt`. Virtualenv lives in `venv/` (not committed).

---

## 2. Project layout

```
logistica_tracking/
├── manage.py
├── requirements.txt
├── .env.example              — env vars for Postgres/Redis, all optional
├── .gitignore
├── logistica_tracking/        — Django project config package
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                — ProtocolTypeRouter: HTTP + WebSocket
│   ├── wsgi.py
│   └── env_check.py           — Postgres/Redis reachability probes
├── accounts/                  — custom User model, JWT auth, roles
├── deliveries/                 — Delivery model, accept/confirm lifecycle
├── tracking/                   — Location model, GPS endpoints, WS consumers, Redis cache
├── admin_panel/                 — PriorityList, broadcast/notify, conflict resolution
├── trips/                       — TripSummary model + generation
└── frontend/                    — Tailwind/HTML/JS test console (Django app serving templates+static)
```

---

## 3. Data model

- **User** (`accounts.User`, extends `AbstractUser`) — adds `role` (`client` / `driver` / `admin`) and `phone_number`. A custom manager makes `createsuperuser` automatically set `role=admin`.
- **Delivery** (`deliveries.Delivery`) — `client` FK, `driver` FK (nullable), `pickup_location`, `dropoff_location`, `status` (`pending → accepted → in_transit → delivered`), timestamps.
- **DeliveryAcceptAttempt** (`deliveries.DeliveryAcceptAttempt`) — internal only, not spec'd directly; records each driver's accept tap so simultaneous-accept conflicts can be detected server-side (see §5).
- **Location** (`tracking.Location`) — reduced-interval GPS history (~60s apart), used for trip summaries. The raw 5-10s pings never touch this table (see §6).
- **PriorityList** (`admin_panel.PriorityList`) — `driver` FK (one entry per driver), `added_by` (admin) FK.
- **TripSummary** (`trips.TripSummary`) — `delivery` FK, `total_duration`, `start_time`, `end_time`, `route_snapshot` (JSON list of `{latitude, longitude, timestamp}`).

---

## 4. Auth

- `POST /api/auth/register/driver/`, `POST /api/auth/register/client/` — public, create a user with the matching role, return JWT pair immediately.
- `POST /api/auth/login/` — body includes `role`; rejects if the account's actual role doesn't match what was selected.
- `POST /api/auth/admin/login/` — separate endpoint, only succeeds for `role=admin` accounts.
- JWT access tokens carry a custom `role` claim (`accounts/tokens.py`) so the frontend/RN app can branch UI without an extra lookup.
- Every endpoint requires JWT by default (`DEFAULT_PERMISSION_CLASSES = IsAuthenticated`); role-specific endpoints add `IsDriverRole` / `IsClientRole` / `IsAdminRole` (`accounts/permissions.py`).
- **There's no public admin registration route, by design** — matches the spec ("Admin has own login credentials"). To create the first admin: `python manage.py createsuperuser` — the custom `UserManager` in `accounts/models.py` automatically sets `role=admin` for superusers, so no extra steps are needed. Log in with the **username** you gave `createsuperuser`, not an email (Django's default `username` field, not email-based auth).

---

## 5. Delivery lifecycle

1. **Admin creates a job** — `POST /api/deliveries/` (admin only), status starts `pending`.
2. **Admin pushes it** — either `POST /api/admin/deliveries/{id}/notify/all/` (every priority driver) or `.../notify/{driver_id}/` (one driver). This sends a `job_request` WebSocket event to the driver's personal channel (`driver_{id}`).
3. **Driver accepts** — `POST /api/deliveries/{id}/accept/`. Implementation detail worth knowing: the **first** accept request for a delivery blocks server-side for `ACCEPT_CONFLICT_WINDOW_SECONDS` (default 1s) before resolving, giving a near-simultaneous second tap time to register. If exactly one attempt exists when the window closes, that driver is assigned (`job_accepted` to them, `job_taken` to anyone else who tapped). If more than one, **neither is assigned** — admin gets a `conflict_alert` WebSocket event and must resolve manually via `POST /api/admin/deliveries/{id}/resolve/`. This is server-side only; client-reported timestamps are never trusted for arbitration.
4. **Tracking begins** — driver's app posts GPS via `POST /api/location/update/`. The **first** ping after acceptance flips status to `in_transit` automatically (no separate "start tracking" endpoint). Every ping broadcasts `location_update` to the `delivery_{id}` WebSocket group (client + admin watching that delivery).
5. **Client confirms** — `POST /api/deliveries/{id}/confirm/`, only valid while `in_transit`. This flips status to `delivered`, generates the `TripSummary`, and broadcasts `delivery_confirmed` to both the delivery group and the driver's personal channel (that's the driver's cue to stop GPS — there's no server-side kill switch, the RN app is expected to stop posting on this event, matching the spec's "only client confirmation ends the session").

---

## 6. Performance rules (as specified)

- Every GPS ping updates **Redis only** (`tracking/redis_client.py`) — `delivery:{id}:latest_location`, always the newest coordinate.
- Postgres gets a `Location` row only once per `LOCATION_DB_WRITE_INTERVAL_SECONDS` (default 60s) per delivery — the 5-10s pings do not all hit the database.
- If Redis is unreachable, GPS caching falls back to an in-process Python dict (single-process only — documented limitation, see §7).
- `GET /api/location/{delivery_id}/latest/` reads Redis first, falls back to the most recent `Location` DB row if Redis has nothing cached yet.

---

## 7. Postgres/Redis fallback (per your request)

`logistica_tracking/env_check.py` probes `POSTGRES_HOST:POSTGRES_PORT` and `REDIS_HOST:REDIS_PORT` (0.3s timeout) at process startup:

- Reachable → uses Postgres / Redis normally.
- Unreachable (or `FORCE_SQLITE=1` / `FORCE_INMEMORY=1` set) → falls back to SQLite (`db.sqlite3`) / Channels' `InMemoryChannelLayer`.
- The chosen backend is printed once on startup: `[logistica_tracking] database=... channel_layer=...`.
- **Caveat**: the in-memory channel layer and in-process GPS cache only work correctly within a single server process — fine for local dev, not for multi-worker/production deployment. Real Redis is needed once you run more than one process.

All knobs are in `.env.example` (copy to `.env` or export directly — nothing is hardcoded).

---

## 8. WebSocket layer

- `logistica_tracking/asgi.py` — `ProtocolTypeRouter` splitting HTTP (normal Django) from WebSocket (Channels).
- `tracking/ws_auth.py` — custom JWT middleware for WebSocket connections. Since browsers/RN clients can't set an `Authorization` header on a WS handshake, the access token goes in the query string: `ws://host/ws/.../?token=<jwt>`.
- `tracking/consumers.py` — three consumers:
  - `DriverConsumer` (`/ws/driver/`) — joins `driver_{user.id}`, receives `job_request` / `job_taken` / `job_accepted` / `delivery_confirmed`.
  - `TrackingConsumer` (`/ws/tracking/{delivery_id}/`) — joins `delivery_{id}`, permission-checked (client must own the delivery, driver must be assigned to it, admin always allowed), receives `location_update` / `delivery_confirmed`.
  - `AdminConsumer` (`/ws/admin/`) — joins `admin_dashboard`, receives `conflict_alert` / `job_taken`.
- `tracking/notify.py` — the only place that calls `channel_layer.group_send`; every app (`deliveries`, `admin_panel`) imports from here rather than talking to Channels directly, so group names stay consistent in one place.

---

## 9. Full endpoint list

**Auth**
- `POST /api/auth/register/driver/`
- `POST /api/auth/register/client/`
- `POST /api/auth/login/`
- `POST /api/auth/admin/login/`

**Deliveries**
- `POST /api/deliveries/` (admin)
- `GET /api/deliveries/` (role-filtered: client sees own, driver sees assigned, admin sees all)
- `POST /api/deliveries/{id}/accept/` (driver)
- `POST /api/deliveries/{id}/confirm/` (client)

**Tracking**
- `POST /api/location/update/` (driver)
- `GET /api/location/{delivery_id}/latest/` (client/driver/admin, ownership-checked)

**Admin**
- `GET /api/admin/deliveries/`
- `GET /api/admin/priority/`, `POST /api/admin/priority/`, `DELETE /api/admin/priority/{driver_id}/`
- `POST /api/admin/deliveries/{id}/notify/all/`
- `POST /api/admin/deliveries/{id}/notify/{driver_id}/`
- `POST /api/admin/deliveries/{id}/resolve/`
- `GET /api/admin/trips/{delivery_id}/summary/`

**Trips**
- `GET /api/trips/{delivery_id}/summary/` (client, own delivery only)

---

## 10. Test frontend (`frontend/` app)

Each role has its **own dedicated dashboard page/URL** (not a shared single-page layout), so each can be opened in a separate tab and driven independently:

| URL | Page |
|---|---|
| `/` | Landing page — three cards linking to the dashboards below |
| `/admin/` | Admin Dashboard |
| `/driver/` | Driver Dashboard |
| `/client/` | Client Dashboard |

Each dashboard page is self-contained: it shows a login/register form if there's no token in `localStorage` for that role, or the full dashboard in place if there is. Tokens are stored per role (`la_admin_token`, `la_driver_token`, `la_client_token`), so logging into one dashboard in one tab has no effect on the others.

**Note**: Django's own built-in admin site (the model-admin UI at `/admin/` that ships with every Django project) was moved to `/django-admin/` to free up `/admin/` for the Admin Dashboard above — that's the far more relevant destination for this project. If you ever need the raw Django admin (e.g. to browse/edit rows directly), it's at `/django-admin/` (requires a superuser login there too).

Tailwind is loaded via the Play CDN (fine for local testing, not meant for production — it prints a console warning, which is expected).

Files:
- `frontend/static/frontend/js/api.js` — thin `fetch()` wrapper (one function per endpoint) plus shared UI helpers (`$`, `logLine`, `statusBadge`, `withBusyButton`) used by all three dashboards.
- `frontend/static/frontend/js/admin.js`, `driver.js`, `client.js` — one self-contained script per dashboard.
- `frontend/templates/frontend/{index,admin,driver,client}.html`.

---

## 11. Bug found and fixed after initial handoff

**Symptom**: registering (or double-clicking Register/Login) could occasionally produce `"... failed: null"` in the UI instead of a real error.

**Root cause**: Django's `UniqueValidator` checks for an existing username with a `SELECT`, not a lock. Two near-simultaneous POSTs (e.g. an impatient double-click) could both pass that check before either `INSERT` committed — the second one then hit a raw `IntegrityError` at the database level, which DRF doesn't auto-convert to JSON. Django returned an HTML 500 error page; the frontend's `fetch` wrapper couldn't parse it as JSON, producing the confusing `"null"` message.

**Fix** (both layers, in this commit):
- `accounts/views.py` — `RegisterDriverView`/`RegisterClientView` now catch `IntegrityError` and return a clean `400 {"username": ["A user with that username already exists."]}`.
- `frontend/static/frontend/js/app.js` — a `withBusyButton()` helper now disables register/login buttons for the duration of the request across all three columns, so the race is far less likely to happen at all.

Verified with 5 concurrent registration requests for the same username: 1×`201`, 4×clean `400` — no more raw server errors.

---

## 12. What was verified, and how

- Full REST lifecycle (register → login → priority list → create job → broadcast → accept → GPS ping → live tracking read → confirm → trip summary) — scripted end-to-end, passed.
- WebSocket auth + group routing — a driver WS client received a real-time `job_request` push, confirmed via a live socket in a test script.
- Full lifecycle **through the actual browser UI** (not just the API) — driven with a headless Chromium browser clicking through all three columns exactly as a person would; all steps passed, including live `location_update` reaching the client's WebSocket and the trip summary rendering.
- Concurrent-registration race condition — reproduced and fixed (§11).

---

## 13. Open items / things you may want to decide

- **Admin account creation**: no UI for it by design (matches spec) — must be done via `python manage.py createsuperuser` on the server. **This is the #1 cause of "Invalid username or password" on the Admin Dashboard** — if you haven't run that command yet, no admin account exists at all. Log in with the exact username you gave `createsuperuser` (a plain username like `admin`, not necessarily an email — Django authenticates by username here, not email).
- Postgres/Redis aren't running in this environment by default — everything currently runs on the SQLite/in-memory fallback. Point `.env` at real instances (or start them via Docker) whenever you're ready to test the production path.
- Each dev-server restart with `DEBUG=True` uses SQLite by default; data (users, deliveries) doesn't persist across a fresh `migrate` on a deleted `db.sqlite3`, so re-register test accounts after any full reset.

---

## 14. Visual redesign (Admin Dashboard priority)

A full redesign per a detailed design spec: dark "logistics operations center" look, Leaflet maps, toasts, per-role login pages, sidebar-driven admin dashboard. Backend was not touched for this pass. File-by-file:

**New files**
- `frontend/templates/frontend/_head.html` — shared `<head>` partial: Google Fonts (Inter), Leaflet CSS/JS, `theme.css`, Tailwind CDN + a custom color config (`base`, `surface`, `surface2`, `edge`, `ink`/`ink2`/`ink3`, and `green`/`amber`/`red`/`blue` overridden to the spec's exact hex values), and `api.js`. Included via `{% include %}` at the top of every page's `<head>` so the design system stays in one place.
- `frontend/templates/frontend/login.html` — single shared login/register template for all three roles; role comes from the URL via Django context (`{{ role }}`).
- `frontend/static/frontend/js/login.js` — login page logic: role-aware login vs. register mode toggle (register only offered for driver/client — no admin registration route exists), redirects to the matching dashboard on success.
- `frontend/static/frontend/css/theme.css` — keyframes (toast slide-in, conflict-banner slide-down, radar pulse for the driver empty state, accordion open/close), dark scrollbars, Leaflet dark-popup override.
- `frontend/static/frontend/favicon.svg` — small brand mark for the `<link rel="icon">` the design system references.
- `BUILD_REPORT.md` §14 (this section).

**Rewritten files**
- `frontend/views.py`, `frontend/urls.py` — added `LoginPageView` (role passed via URL kwarg) and three routes: `/admin-login/`, `/driver-login/`, `/client-login/`. Existing `/admin/`, `/driver/`, `/client/`, `/` routes unchanged.
- `frontend/templates/frontend/index.html` — landing page: wordmark top-left, centered tagline, three role cards (icon, name, one-liner, CTA button) linking to the new login pages instead of straight to the dashboards.
- `frontend/templates/frontend/admin.html` / `admin.js` — full rebuild: fixed sidebar (Deliveries / Drivers / Priority List nav, admin identity + logout pinned at bottom), top bar with live clock and WS connection indicator, stat cards, filter pills, accordion delivery list with inline actions (notify, cancel, resolve), New Delivery modal, conflict banner, per-delivery Leaflet mini-map for `in_transit` deliveries, Drivers table with priority/active toggle icons, Priority List with inline remove-confirmation.
- `frontend/templates/frontend/driver.html` / `driver.js` — full rebuild: top bar with cosmetic availability toggle, left job-feed panel (job cards with a 30s visual countdown bar, Active Delivery card with a 3-stage progress bar), full-height Leaflet map on the right with a glowing driver marker and pickup/dropoff pins.
- `frontend/templates/frontend/client.html` / `client.js` — full rebuild: left delivery list + active-delivery detail panel (status-aware messaging, Confirm Delivery button gated to `in_transit`), full-height Leaflet map showing live driver position while in transit and the full route polyline from the trip summary once delivered.
- `frontend/static/frontend/js/api.js` — rewritten as the shared runtime for every page: `Auth` (single shared identity via `logistica_access`/`logistica_refresh`/`logistica_user_id`/`logistica_username`/`logistica_role`, plus `Auth.guard(role)` for the redirect-if-wrong-role behavior the spec asked for), `Toast`, the `API` client (now list-endpoint-aware — DRF's pagination envelope `{count, next, previous, results}` — and covering the newer admin endpoints: users list, deactivate/activate, cancel delivery), `connectWS()` (auto-reconnect every 5s with toast feedback), and shared UI helpers (`statusBadge`/`timeAgo`/`emptyState`/icon set/`initMap`/marker + route helpers).

**Design decisions made that the spec didn't cover**
- **No admin registration UI.** The spec's login page doesn't mention register at all; I added a register toggle for driver/client only, matching the backend (there's no `/api/auth/register/admin/` endpoint — admins are created via `createsuperuser`, per §4).
- **Driver "Available/Off Duty" toggle is purely cosmetic.** There's no backend concept of driver availability — it doesn't call any endpoint or affect job delivery. Flagging this so it isn't mistaken for working filtering logic.
- **Pickup/dropoff map pins use deterministic placeholder coordinates, not real geocoding.** `Delivery.pickup_location` / `dropoff_location` are free-text addresses in the backend — there's no lat/lng stored for them (only the driver's live GPS has real coordinates, via `tracking.Location`/Redis). The spec's map requirements assume real pickup/dropoff points, so I generate a stable pseudo-random position near Uyo per delivery ID (same delivery always renders at the same spot, different deliveries land in different spots) purely so the map isn't empty. If real geocoding matters later, this needs an actual address→coordinate step server-side.
- **Single shared identity instead of per-role-tab identity.** The spec's `localStorage` keys (`logistica_access` etc.) are one flat set, not namespaced per role — meaning only one role can be logged in per browser context at a time (matches `Auth.guard`'s redirect-on-mismatch behavior as specified). Practical effect for testing: you now need separate browser profiles/incognito windows (or separate automated browser contexts) to have admin, driver, and client logged in simultaneously, unlike the previous single-page 3-column version. This was implied by the spec's exact key names and guard behavior, not stated outright.
- **Django's own built-in admin site** stays at `/django-admin/` (moved there in the prior revision, §10) so `/admin/` is free for this dashboard — unchanged by this pass, just flagging it's still true.
- **Drivers table pagination** uses DRF's `next`/`previous` links (Previous/Next buttons) rather than numbered pages, since the API doesn't expose total page count directly — simplest correct mapping to what the endpoint actually returns.

**Verified against the live backend**: registration/login through the new per-role login pages, priority-list management from the Drivers tab, delivery creation via the modal, live `job_request` WebSocket delivery to the driver's job feed, accept → `ACTIVE DELIVERY` panel + live map, GPS pings → client's live map + in-transit status, confirm → delivered state + driver's GPS auto-stop. All verified with a real (headless) browser driving all three dashboards simultaneously across separate browser contexts.

---

## 15. Closing the gaps — wiring the remaining mocked/unwired UI to real backend

Three things flagged in §14 as "not covered by spec" turned out to be places where the UI was faking or simply not displaying data the backend could actually provide. Built real backend support for all three rather than leaving them cosmetic.

### 15.1 Driver availability (was: pure CSS toggle, no backend)

- `accounts/models.py` — added `User.is_available` (`BooleanField`, default `False`). Migration: `accounts/migrations/0002_user_is_available.py`.
- `accounts/serializers.py` — `UserSerializer` now includes `is_available`, so it shows up everywhere a user is serialized (admin's Drivers table, login responses, etc.).
- `accounts/views.py` — new `DriverAvailabilityView` (`POST /api/auth/driver/availability/`, driver-only). Body: `{"is_available": true|false}`; rejects anything that isn't a real boolean with a 400.
- `frontend/static/frontend/js/driver.js` — the toggle now calls `API.setDriverAvailability()` and only updates the UI once the backend confirms the change; on failure it shows a toast and leaves the switch in its prior state instead of lying about it.
- `frontend/templates/frontend/admin.html` / `admin.js` — added an "On Duty" column to the Drivers table so admin can see real availability, not just active/inactive.
- **Still a deliberate scope boundary**: this is a status flag only — it does not filter who receives `job_request` broadcasts. Admin's "Notify All Priority Drivers" / "Notify Everyone" still reach every matching driver regardless of duty status. Filtering by availability would change existing dispatch behavior, which felt like a product decision, not a "wire it up" fix — flagging it here in case you want that as a follow-up.

### 15.2 Real pickup/dropoff coordinates (was: fake, deterministic placeholder positions)

- `deliveries/models.py` — added `pickup_lat`, `pickup_lng`, `dropoff_lat`, `dropoff_lng` (all nullable `FloatField`s) to `Delivery`. Migration: `deliveries/migrations/0003_delivery_dropoff_lat_delivery_dropoff_lng_and_more.py`.
- `deliveries/serializers.py` — `DeliverySerializer` exposes all four; `DeliveryCreateSerializer` accepts them as optional, range-validated (`-90..90` / `-180..180`), and rejects a half-supplied pair (latitude without longitude or vice versa) with a clear 400.
- `frontend/templates/frontend/admin.html` — New Delivery modal gained an optional "Coordinates" section (4 number inputs); left blank, delivery creation behaves exactly as before.
- `frontend/static/frontend/js/admin.js`, `driver.js`, `client.js` — every place that draws a pickup/dropoff pin now checks `delivery.pickup_lat != null` first and uses the real coordinate; the deterministic placeholder from §14 is now strictly a fallback for deliveries that were never given real coordinates, not the only option. Admin's `in_transit` mini-map also gained pickup/dropoff pins it didn't have before (previously showed only the driver marker).
- This does **not** add geocoding — admin still has to know/enter the actual lat/lng. A real "type an address, get coordinates" flow would need a geocoding API integration, which is a bigger, separate piece of work if you want it.

### 15.3 Trip summary display (was: backend endpoints existed, nothing in the UI called them)

- No backend changes needed — `AdminTripSummaryView`, `ClientTripSummaryView`, and `DriverTripSummaryView` already existed and worked; they just weren't wired to anything.
- `admin.js` — delivered deliveries now show a "View Trip Summary" button in the accordion detail (duration, start/end time, GPS point count via `API.adminTripSummary`).
- `client.js` — the active-delivery panel shows a "TRIP SUMMARY" box (duration, started/ended times) once a delivery reaches `delivered`, using the same `API.tripSummary` call that already fed the completed-route polyline.
- `driver.js` — on receiving `delivery_confirmed`, fetches its own trip summary (`API.driverTripSummary`) and surfaces the duration as a toast before clearing the active-delivery panel.
- `frontend/static/frontend/js/api.js` — added `parseDuration()` / `formatDuration()` helpers to turn DRF's `DurationField` string (`"HH:MM:SS.ffffff"`) into human-readable text; shared by all three dashboards rather than duplicated.

**Verified**: availability toggle updates the backend and is reflected in admin's Drivers table; delivery creation with coordinates round-trips correctly and rejects half-supplied pairs; delivery creation without coordinates is unaffected; all three trip-summary endpoints return correct data through a full accept→track→confirm lifecycle; the admin, client, and driver dashboards each display it. Tested via direct API calls and a real (headless) browser exercising the actual UI controls.
