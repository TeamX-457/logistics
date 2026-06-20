# LogisticsPro Backend

Django REST API for the LogisticsPro logistics marketplace, plus the working frontend — `templates/` (HTML/Tailwind pages) and `static/` (JS/CSS) — served by Django itself so the whole app runs on one origin/port. The UI was designed against the screens prototyped in `../frontend/design-prototypes`.

## Stack

- Django 5.1 + Django REST Framework
- JWT auth (`djangorestframework-simplejwt`)
- SQLite for local dev, Postgres in production (`DATABASE_URL`)
- Django Channels (WebSockets) for live tracking, negotiation chat, and live marketplace bidding — in-memory channel layer by default, Redis in production
- `drf-spectacular` for an auto-generated OpenAPI schema

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

App (frontend): `http://localhost:8000/`
API root: `http://localhost:8000/api/`
Interactive docs: `http://localhost:8000/api/docs/`
Hand-written API reference: `http://localhost:8000/static/docs/index.html` (served as a static file)
Admin: `http://localhost:8000/admin/`

Frontend pages are plain templates rendered by `config.views.page` (e.g. `/wallet.html` → `templates/wallet.html`) and call the API at `/api/...` on the same origin — no CORS hop needed for the bundled frontend. `CORS_ALLOWED_ORIGINS` in `.env` only matters if you point a separate client (e.g. a Next.js dev server) at this API.

## Apps

- **accounts** — custom `User` (email login, `role`: customer/driver/admin), `CustomerProfile`, `Address` book, `DriverProfile` + `DriverDocument` (KYC)
- **fleet** — admin-facing driver/fleet verification review workflow (operates on `accounts` data)
- **deliveries** — the core domain: `DeliveryRequest` (shipments), `Bid`, `StatusEvent` (milestone timeline), `TrackingPing`, `Message` (negotiation chat), `PriceProposal` (counter-offers)
- **disputes** — `Dispute`, `DisputeMessage`, `DisputeEvidence`, admin resolution workflow
- **wallet** — `Wallet`, `Transaction`, `PaymentMethod`, `Settlement` (enterprise/group payouts)
- **dashboard** — `Notification`, `Alert`, plus read-only aggregation endpoints for the admin/customer/driver dashboard screens

## Auth

All endpoints except registration/login/password-reset require `Authorization: Bearer <access_token>`. Roles (`customer`, `driver`, `admin`) gate access at the view level — e.g. only `customer` can create a `DeliveryRequest`, only `driver` can submit a `Bid`, only `admin` can approve fleet verifications or resolve disputes.

| Endpoint | Method | Notes |
|---|---|---|
| `/api/auth/register/customer/` | POST | `email, password, full_name, company_name?, phone_number?` → returns tokens + user |
| `/api/auth/register/driver/` | POST | `email, password, full_name, vehicle_type, license_number, nin_number, phone_number?` → returns tokens + user |
| `/api/auth/login/` | POST | `email, password` → `access`, `refresh`, `user` |
| `/api/auth/token/refresh/` | POST | `refresh` → new `access` |
| `/api/auth/password-reset/` | POST | `email` → reset token (emailed in production) |
| `/api/auth/password-reset/confirm/` | POST | `uid, token, new_password` |
| `/api/auth/me/` | GET/PATCH | current user profile |
| `/api/addresses/` | GET/POST | customer address book |
| `/api/addresses/{id}/` | GET/PATCH/DELETE | |

## Fleet verification (admin)

| Endpoint | Method | Notes |
|---|---|---|
| `/api/verifications/?verification_status=&vehicle_type=&entity_type=&search=` | GET | list drivers pending/approved/rejected |
| `/api/verifications/{id}/` | GET | detail incl. uploaded documents |
| `/api/verifications/{id}/approve/` | POST | |
| `/api/verifications/{id}/reject/` | POST | `reason?` |

## Deliveries (the core marketplace)

| Endpoint | Method | Notes |
|---|---|---|
| `/api/deliveries/` | GET/POST | customers see own; drivers see assigned + open marketplace loads; admin sees all |
| `/api/deliveries/{id}/` | GET/PATCH | |
| `/api/deliveries/estimate/` | POST | `pickup_lat/lng, dropoff_lat/lng, weight_kg, package_type` → `distance_miles`, `market_average_price` |
| `/api/deliveries/marketplace/` | GET | open loads (status=pending, unassigned) for drivers to browse |
| `/api/deliveries/{id}/cancel/` | POST | |
| `/api/deliveries/{id}/accept-load/` | POST | driver accepts an open load directly at the listed price |
| `/api/deliveries/{id}/advance-status/` | POST | `status`, optional `note`/`otp` (OTP required to transition to `delivered`) |
| `/api/deliveries/{id}/bids/` | GET/POST | list offers / driver submits an offer |
| `/api/deliveries/{id}/bids/{bid_id}/accept/` | POST | customer accepts an offer → assigns driver, generates delivery OTP |
| `/api/deliveries/{id}/bids/{bid_id}/reject/` | POST | |
| `/api/deliveries/{id}/tracking/` | GET/POST | GET: milestones + recent pings + ETA + OTP (customer only); POST: driver posts a location ping |
| `/api/deliveries/{id}/messages/` | GET/POST | negotiation chat thread |
| `/api/deliveries/{id}/proposals/` | GET/POST | price counter-offers |
| `/api/deliveries/{id}/proposals/{id}/accept/` | POST | |
| `/api/deliveries/{id}/proposals/{id}/decline/` | POST | |

### Live updates (WebSocket)

Connect with `?token=<JWT access token>`:

- `ws://localhost:8000/ws/deliveries/{id}/tracking/` — driver sends `{lat, lng, heading?}`; all connected clients receive `{event: "tracking_update", data}`
- `ws://localhost:8000/ws/deliveries/{id}/chat/` — send `{text}`; broadcasts `{event: "new_message", data}`
- `ws://localhost:8000/ws/deliveries/{id}/marketplace/` — receive-only; broadcasts `{event: "new_bid", data}` as drivers bid

REST POSTs to `bids/`, `tracking/`, and `messages/` also broadcast to these same groups, so polling and WebSocket clients stay in sync.

## Disputes

| Endpoint | Method | Notes |
|---|---|---|
| `/api/disputes/?status=&priority=` | GET/POST | customer/driver see disputes on their own deliveries; admin sees all |
| `/api/disputes/{id}/` | GET | |
| `/api/disputes/{id}/messages/` | GET/POST | |
| `/api/disputes/{id}/evidence/` | POST | image upload |
| `/api/disputes/{id}/resolve/` | POST (admin) | `resolution_type`: `refund_customer` / `release_driver` / `partial_settlement`, `resolved_amount?`, `admin_note?` |

## Wallet

| Endpoint | Method | Notes |
|---|---|---|
| `/api/wallet/` | GET | balance (auto-created on first access) |
| `/api/wallet/transactions/?category=&status=&search=` | GET | paginated history |
| `/api/wallet/withdraw/` | POST | `amount, payment_method` |
| `/api/wallet/transfer/` | POST | `amount, recipient_email` |
| `/api/wallet/payment-methods/` | GET/POST | |
| `/api/wallet/payment-methods/{id}/` | PATCH/DELETE | |
| `/api/wallet/payment-methods/{id}/set-default/` | POST | |
| `/api/wallet/spending-summary/?range=1M\|6M\|1Y` | GET | monthly spend chart |
| `/api/wallet/settlements/` | GET (admin) | enterprise/group settlement table |

## Dashboard / analytics

| Endpoint | Method | Role |
|---|---|---|
| `/api/dashboard/customer/` | GET | customer — active shipment count, recent orders, wallet balance |
| `/api/dashboard/driver/` | GET | driver — daily earnings, completed deliveries, rating, active delivery, weekly earnings chart |
| `/api/dashboard/admin-overview/` | GET | admin — KPI cards + 7-day delivery volume + recent alerts |
| `/api/dashboard/financial-analytics/` | GET | admin — commission/inflow/outflow/net revenue + 12-month trend |
| `/api/dashboard/operations-monitoring/` | GET | admin — active delivery / open dispute counts |
| `/api/dashboard/notifications/` | GET | any role — own notification feed |
| `/api/dashboard/notifications/clear/` | POST | mark all as read |
| `/api/dashboard/alerts/` | GET/POST/PATCH (admin) | critical alerts table |

## Pricing model

`deliveries/services.py` has placeholder distance (haversine) and market-rate pricing formulas — swap these for real routing/pricing providers when available. The 2.5% service fee shown in the "Create Delivery" wizard is `SERVICE_FEE_RATE` in `deliveries/serializers.py`.
