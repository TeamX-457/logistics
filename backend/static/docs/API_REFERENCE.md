# LogisticsPro API Reference

The LogisticsPro API is organized around REST. It uses standard HTTP response codes, standard HTTP verbs, and JSON request/response bodies for everything except file uploads (`multipart/form-data`).

All requests must be made over HTTP to your local backend during development:

```
http://localhost:8000/api
```

Interactive, auto-generated schema browsing is also available once the server is running:

- OpenAPI schema: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`

This document is the hand-written, narrative companion to that schema — it explains *why* each endpoint exists, what triggers it on the frontend, and what the full request/response shapes look like.

---

## Table of contents

1. [Authentication](#authentication)
2. [Errors](#errors)
3. [Pagination](#pagination)
4. [Conventions](#conventions)
5. [Accounts](#accounts)
6. [Fleet Verification](#fleet-verification)
7. [Deliveries](#deliveries)
8. [Disputes](#disputes)
9. [Wallet](#wallet)
10. [Dashboard](#dashboard)
11. [Real-time (WebSockets)](#real-time-websockets)
12. [Object & enum reference](#object--enum-reference)

---

## Authentication

LogisticsPro uses **JSON Web Tokens** (JWT) via `djangorestframework-simplejwt`. There is no session/cookie auth — every authenticated request carries a bearer token.

```
Authorization: Bearer <access_token>
```

### Token lifecycle

| Token | Lifetime | Notes |
|---|---|---|
| `access` | 60 minutes | sent on every request |
| `refresh` | 7 days | rotates on use (`ROTATE_REFRESH_TOKENS=True`) — exchange it for a new `access`/`refresh` pair |

Registration and login both return an `access`/`refresh` pair immediately — there's no separate "verify email then log in" step required to start calling the API.

### Typical frontend flow

```js
// 1. Register or log in, store both tokens
const { access, refresh, user } = await api.login(email, password);
localStorage.setItem("access_token", access);
localStorage.setItem("refresh_token", refresh);
localStorage.setItem("user", JSON.stringify(user));

// 2. Attach the access token to every subsequent request
fetch(`${BASE_URL}/deliveries/`, {
  headers: { Authorization: `Bearer ${access}` },
});

// 3. When a request 401s, refresh once and retry
const res = await fetch(`${BASE_URL}/auth/token/refresh/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refresh: localStorage.getItem("refresh_token") }),
});
```

This exact pattern is implemented in [`backend/static/js/api.js`](../js/api.js) if you want working reference code.

### Roles

Every user has exactly one `role`: `customer`, `driver`, or `admin`. Roles are assigned at registration (customer/driver) or via `createsuperuser` / Django admin (admin). Most endpoints are gated by role at the view level — see each endpoint's **Auth** line below.

---

## Errors

LogisticsPro uses standard HTTP status codes:

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `204` | No Content (successful delete) |
| `400` | Bad Request — validation error, see body |
| `401` | Unauthorized — missing/invalid/expired access token |
| `403` | Forbidden — authenticated, but role doesn't permit this action |
| `404` | Not Found |
| `429` | Too Many Requests (rate-limited endpoints, if enabled) |
| `500` | Server error |

**Validation errors** (`400`) come back as a field → message(s) map, matching DRF's default serializer error format:

```json
{
  "email": ["An account with this email already exists."],
  "password": ["This field must be at least 8 characters."]
}
```

**Permission errors** (`403`):

```json
{ "detail": "Only customers can create delivery requests." }
```

**Not found** (`404`):

```json
{ "detail": "Not found." }
```

---

## Pagination

List endpoints that can grow unbounded (deliveries, transactions, disputes, fleet verifications) are paginated with DRF's `PageNumberPagination`:

```json
{
  "count": 248,
  "next": "http://localhost:8000/api/wallet/transactions/?page=3",
  "previous": "http://localhost:8000/api/wallet/transactions/?page=1",
  "results": [ /* ... */ ]
}
```

Query params: `?page=2&page_size=50` (max `page_size` is 100, default 20).

Sub-resources nested under a single delivery (bids, messages, proposals, tracking pings) are **not** paginated — they return a plain array, since they're scoped to one delivery and bounded in practice.

---

## Conventions

- **IDs** are integers (`id`), except for human-facing reference codes which are short strings: `DeliveryRequest.reference` (`LP-XXXXXXXX`), `Dispute.case_id` (`DP-XXXXXXXX`), `Transaction.transaction_id` (`TXN-XXXXXXXXXX`).
- **Money** fields are decimal strings (e.g. `"1240.00"`), not floats — avoid parsing them as JS `Number` for arithmetic; display as-is or use a decimal library.
- **Timestamps** are ISO-8601 UTC (e.g. `"2026-06-18T10:29:27.821185Z"`).
- **Enums** are lowercase snake_case strings (e.g. `"in_transit"`, `"standard_freight"`). Full enum tables are in the [reference appendix](#object--enum-reference).
- **Booleans** sent in form data over `multipart/form-data` (file upload endpoints) must be the strings `"true"`/`"false"`.

---

## Accounts

### Register a customer (shipper)

Maps to the **Customer Registration** screen.

```
POST /api/auth/register/customer/
Auth: none
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | yes | must be unique |
| `password` | string | yes | min 8 characters |
| `full_name` | string | yes | split into `first_name`/`last_name` on the first space |
| `company_name` | string | no | shown on the dashboard header |
| `phone_number` | string | no | |

```bash
curl -X POST http://localhost:8000/api/auth/register/customer/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@acme.com",
    "password": "SuperSecret1!",
    "full_name": "Jane Shipper",
    "company_name": "Acme Corp",
    "phone_number": "+15551234567"
  }'
```

**Response `201`**

```json
{
  "access": "<jwt>",
  "refresh": "<jwt>",
  "user": {
    "id": 1,
    "email": "jane@acme.com",
    "first_name": "Jane",
    "last_name": "Shipper",
    "role": "customer",
    "phone_number": "+15551234567",
    "is_phone_verified": false,
    "avatar": null,
    "customer_profile": { "company_name": "Acme Corp", "account_type": "enterprise" },
    "driver_profile": null,
    "created_at": "2026-06-18T10:23:26.336012Z"
  }
}
```

### Register a driver (carrier)

Maps to the **Join as a Driver** screen.

```
POST /api/auth/register/driver/
Auth: none
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | yes | |
| `password` | string | yes | min 8 characters |
| `full_name` | string | yes | |
| `vehicle_type` | enum | yes | `bike`, `motorcycle`, `van`, `cargo_van`, `truck`, `heavy_truck` |
| `license_number` | string | yes | |
| `nin_number` | string | yes | 11-digit national ID |
| `phone_number` | string | no | |

Response shape is identical to customer registration, with `role: "driver"` and a populated `driver_profile` (`verification_status: "pending"` until an admin approves it — see [Fleet Verification](#fleet-verification)).

### Login

```
POST /api/auth/login/
Auth: none
```

| Field | Type |
|---|---|
| `email` | string |
| `password` | string |

Response is the same `{ access, refresh, user }` shape as registration. Invalid credentials return `401` with `{"detail": "No active account found with the given credentials"}`.

### Refresh token

```
POST /api/auth/token/refresh/
Auth: none
Body: { "refresh": "<jwt>" }
```

```json
{ "access": "<new-jwt>", "refresh": "<new-jwt>" }
```

### Password reset

```
POST /api/auth/password-reset/          Body: { "email": "jane@acme.com" }
POST /api/auth/password-reset/confirm/  Body: { "uid": "...", "token": "...", "new_password": "..." }
```

In development, the request endpoint returns the `uid`/`token` directly in the response body so you can test the flow without an email backend configured. In production, wire `PasswordResetRequestView` to send these via email instead of returning them.

### Current user

```
GET   /api/auth/me/   Auth: any authenticated user
PATCH /api/auth/me/   Auth: any authenticated user
```

`PATCH` accepts any subset of `first_name`, `last_name`, `phone_number`, `avatar` (`role` is read-only — it cannot be changed after registration).

### Driver online status

Maps to the **Driver Dashboard** "Online / Go Offline" toggle.

```
PATCH /api/drivers/me/status/
Auth: driver
Body: { "is_online": true, "current_lat"?: 33.12, "current_lng"?: -83.45 }
```

Returns the updated `DriverProfile`.

### Address book

Maps to the customer's saved addresses (used to prefill the **Create Delivery** wizard).

```
GET    /api/addresses/        Auth: customer
POST   /api/addresses/        Auth: customer
GET    /api/addresses/{id}/   Auth: customer (own only)
PATCH  /api/addresses/{id}/   Auth: customer (own only)
DELETE /api/addresses/{id}/   Auth: customer (own only)
```

**Address object**

```json
{
  "id": 4,
  "label": "Warehouse - Savannah",
  "line1": "100 Port Rd",
  "line2": "",
  "city": "Savannah",
  "state": "GA",
  "country": "US",
  "postal_code": "31401",
  "lat": "32.080900",
  "lng": "-81.091200",
  "is_default": true,
  "created_at": "2026-06-18T10:23:26.336012Z"
}
```

---

## Fleet Verification

Admin-only review queue for driver/fleet KYC. Maps to the **Fleet Verification** screen (tabs: Individual / Group / Enterprise map to `entity_type`).

```
GET  /api/verifications/                Auth: admin
GET  /api/verifications/{id}/           Auth: admin
POST /api/verifications/{id}/approve/   Auth: admin
POST /api/verifications/{id}/reject/    Auth: admin   Body: { "reason"?: string }
```

**Filters** (query params on the list endpoint): `verification_status` (`pending`/`approved`/`rejected`), `vehicle_type`, `entity_type`, `search` (matches email/name/license number).

**List item**

```json
{
  "id": 1,
  "full_name": "Dan Driver",
  "email": "driver@fleet.com",
  "avatar": null,
  "entity_type": "individual",
  "vehicle_type": "truck",
  "registration_date": "2026-06-18T10:23:30.702571Z",
  "verification_status": "pending"
}
```

**Detail** adds: `phone_number`, `license_number`, `nin_number`, `date_of_birth`, `company_name`, `rejection_reason`, `verified_at`, and `documents` (array of `{ id, doc_type, file, uploaded_at }`, where `doc_type` is one of `license_front`, `license_back`, `nin_card`, `tax_id`, `other`).

Approving or rejecting returns the full detail object with `verification_status` updated and `verified_at`/`verified_by` stamped server-side.

---

## Deliveries

This is the core of the platform — a `DeliveryRequest` is a shipment that moves through this lifecycle:

```
draft → pending → negotiating → accepted → driver_arrived → in_transit → delivered
                                                        ↘ delayed ↗
              (any non-terminal state) → cancelled
              (any state) → disputed
```

### The DeliveryRequest object

```json
{
  "id": 2,
  "reference": "LP-AFD8F9C8",
  "customer": { "...": "UserSerializer" },
  "driver": { "...": "UserSerializer | null" },
  "pickup_address": "Port of Savannah",
  "pickup_lat": "32.080900",
  "pickup_lng": "-81.091200",
  "dropoff_address": "Atlanta Distribution Hub",
  "dropoff_lat": "33.749000",
  "dropoff_lng": "-84.388000",
  "distance_miles": "223.25",
  "package_type": "standard_freight",
  "weight_kg": "4200.00",
  "is_fragile": false,
  "is_perishable": false,
  "is_hazardous": false,
  "is_stackable": false,
  "target_price": "1240.00",
  "allow_counter_offers": true,
  "market_average_price": "1043.01",
  "service_fee": "31.00",
  "final_price": null,
  "service_type": "standard",
  "status": "pending",
  "payment_method": "wallet",
  "delivery_otp": "",
  "bidding_expires_at": null,
  "status_events": [{ "status": "pending", "note": "", "created_at": "..." }],
  "bids": [ "...BidObject" ],
  "proposals": [ "...PriceProposalObject" ],
  "latest_ping": null,
  "created_at": "2026-06-18T10:23:30.000000Z",
  "updated_at": "2026-06-18T10:23:30.000000Z"
}
```

> The **list** serializer omits `status_events`, `bids`, `proposals`, `latest_ping`, and the lat/lng/flag fields — fetch the detail endpoint for the full object.

### Estimate price & distance

Maps to steps 2–4 of the **Create Delivery** wizard ("Estimated Distance" and "Market Average").

```
POST /api/deliveries/estimate/
Auth: any authenticated user
```

```json
{
  "pickup_lat": 32.0809, "pickup_lng": -81.0912,
  "dropoff_lat": 33.7490, "dropoff_lng": -84.3880,
  "weight_kg": 4200,
  "package_type": "standard_freight"
}
```

```json
{ "distance_miles": "223.25", "market_average_price": "1043.01" }
```

> This uses a haversine-distance + per-mile/per-kg placeholder formula (`deliveries/services.py`) — swap in a real routing/pricing provider before production use.

### Create a delivery

Maps to the final "Confirm Order" step of the **Create Delivery** wizard.

```
POST /api/deliveries/
Auth: customer
```

| Field | Type | Required |
|---|---|---|
| `pickup_address` | string | yes |
| `pickup_lat`, `pickup_lng` | decimal | no (omit to skip auto distance/price calc) |
| `dropoff_address` | string | yes |
| `dropoff_lat`, `dropoff_lng` | decimal | no |
| `package_type` | enum | yes — `standard_freight`, `oversized_equipment`, `small_parcel`, `liquid_bulk` |
| `weight_kg` | decimal | yes |
| `is_fragile`, `is_perishable`, `is_hazardous`, `is_stackable` | bool | no, default `false` |
| `target_price` | decimal | yes |
| `allow_counter_offers` | bool | no, default `true` |
| `service_type` | enum | no, default `standard` — or `priority` |
| `payment_method` | enum | no, default `wallet` — or `card` |

Returns the full `DeliveryRequest` detail object (`201`), with `service_fee` computed as 2.5% of `target_price`, and `distance_miles`/`market_average_price` auto-filled if all four lat/lng values were provided.

### List / retrieve deliveries

```
GET /api/deliveries/                Auth: any role — see scoping below
GET /api/deliveries/{id}/           Auth: any role — see scoping below
```

Query params: `status`, `package_type`, `service_type`, `ordering` (`created_at`, `target_price`, `eta`, prefix `-` for descending).

**Visibility scoping** (enforced server-side, not just a UI filter):

- **customer** → only their own delivery requests
- **driver** → deliveries assigned to them, **plus** any unassigned `pending` delivery (the open marketplace)
- **admin** → everything

### Browse the marketplace

Maps to the **Driver Dashboard "Available Loads"** panel and the **Live Marketplace** screen (from the customer's side, "Searching for Drivers" — that view is really just *this delivery's* `bids` array growing in real time, see [WebSockets](#real-time-websockets)).

```
GET /api/deliveries/marketplace/
Auth: any authenticated user (intended for drivers)
```

Returns a paginated list of `pending`, unassigned deliveries — i.e. the same object shape as the list endpoint, scoped to open loads regardless of who's asking.

### Cancel

```
POST /api/deliveries/{id}/cancel/
Auth: the delivery's customer, or admin
```

Fails with `400` if the delivery is already `delivered` or `cancelled`.

### Accept a load directly

The driver-dashboard "Accept Load" button — skips bidding/negotiation and locks in the customer's `target_price`.

```
POST /api/deliveries/{id}/accept-load/
Auth: driver
```

Fails with `400` if the load already has a driver or isn't `pending`. On success: assigns `driver`, sets `final_price = target_price`, `status = accepted`, generates a 4-digit `delivery_otp`, and logs a `status_events` entry.

### Advance status / mark delivered

Drives the **Live Tracking** milestone timeline and the **Driver Dashboard** "mark complete" action.

```
POST /api/deliveries/{id}/advance-status/
Auth: the assigned driver, the customer, or admin
Body: { "status": "in_transit", "note"?: "string", "otp"?: "1234" }
```

`status` must be one of the [DeliveryRequest.Status](#deliveryrequeststatus) values. If `status` is `delivered` and the delivery has a non-empty `delivery_otp`, the request must also include a matching `otp` — this is the 4-digit code shown on the customer's tracking screen and read aloud/handed to the driver on physical handoff. Mismatched OTP returns `400`.

### Bids (the negotiation/bidding marketplace)

Maps to the **Live Marketplace** "Incoming Driver Offers" panel.

```
GET  /api/deliveries/{id}/bids/                  Auth: any party to the delivery
POST /api/deliveries/{id}/bids/                  Auth: driver   Body: { "amount": "1190.00", "message"?: "string" }
POST /api/deliveries/{id}/bids/{bid_id}/accept/   Auth: the delivery's customer
POST /api/deliveries/{id}/bids/{bid_id}/reject/   Auth: the delivery's customer
```

Submitting a bid flips the parent delivery to `negotiating`. Accepting a bid: marks it `accepted`, auto-rejects every other bid on that delivery, assigns the driver, sets `final_price` to the bid amount, generates the delivery OTP, and moves the delivery to `accepted`.

**Bid object**

```json
{
  "id": 1,
  "delivery": 2,
  "driver": { "...": "UserSerializer, includes driver_profile.rating/tier" },
  "amount": "1190.00",
  "message": "Can deliver by tomorrow",
  "status": "pending",
  "created_at": "2026-06-18T10:29:28.623778Z"
}
```

### Tracking

Maps to the **Live Tracking** screen.

```
GET  /api/deliveries/{id}/tracking/
Auth: any party to the delivery

POST /api/deliveries/{id}/tracking/
Auth: the assigned driver only
Body: { "lat": 33.12, "lng": -83.45, "heading"?: 90.0 }
```

**GET response**

```json
{
  "milestones": [
    { "status": "pending", "note": "", "created_at": "..." },
    { "status": "accepted", "note": "Bid #1 accepted", "created_at": "..." }
  ],
  "pings": [{ "id": 9, "lat": "33.120000", "lng": "-83.450000", "heading": "90.00", "recorded_at": "..." }],
  "eta": null,
  "delivery_otp": "3401"
}
```

> `delivery_otp` is only populated in the response when the requester **is** the customer — drivers and admins get `null` here (the OTP is meant to be relayed to the driver verbally/in person at drop-off, not read from their own app).

### Negotiation chat

Maps to the **Negotiation Chat** screen.

```
GET  /api/deliveries/{id}/messages/   Auth: any party to the delivery
POST /api/deliveries/{id}/messages/   Auth: any party to the delivery   Body: { "text": "string", "attachment"?: file }
```

### Price proposals (counter-offers)

The "PRICE PROPOSAL" card in the negotiation chat.

```
GET  /api/deliveries/{id}/proposals/                       Auth: any party to the delivery
POST /api/deliveries/{id}/proposals/                       Auth: any party    Body: { "amount": "1450.00", "justification"?: "string" }
POST /api/deliveries/{id}/proposals/{proposal_id}/accept/   Auth: any party — sets delivery.final_price
POST /api/deliveries/{id}/proposals/{proposal_id}/decline/  Auth: any party
```

---

## Disputes

Maps to **Dispute Resolution Detail** and **Operations Monitoring**'s dispute queue.

```
GET  /api/disputes/                  Auth: any role — see scoping below
POST /api/disputes/                  Auth: any role   Body: { "delivery": 2, "title": "string", "description"?: "string", "priority"?: "low"|"medium"|"high"|"critical" }
GET  /api/disputes/{id}/             Auth: any role — see scoping below
GET  /api/disputes/{id}/messages/    Auth: any role — see scoping below
POST /api/disputes/{id}/messages/    Auth: any role — see scoping below   Body: { "text": "string" }
POST /api/disputes/{id}/evidence/    Auth: any role — see scoping below   multipart/form-data: { "image": file, "caption"?: "string" }
POST /api/disputes/{id}/resolve/     Auth: admin only
```

**Visibility scoping**: customer/driver see disputes where they raised it, or where they're the customer/driver on the underlying delivery. Admin sees all.

**Resolve** body:

```json
{
  "resolution_type": "partial_settlement",
  "resolved_amount": "2425.00",
  "admin_note": "50/50 split per force-majeure policy for 4+ hour delays."
}
```

`resolution_type` is one of `refund_customer`, `release_driver`, `partial_settlement` (maps directly to the three buttons on the **Dispute Resolution Detail** adjudication panel). Resolving sets `status: "resolved"`, stamps `resolved_by`/`resolved_at`.

**Dispute object** (detail)

```json
{
  "id": 2,
  "case_id": "DP-7A4E097C",
  "delivery": { "...": "DeliveryRequestListSerializer" },
  "delivery_reference": "LP-AFD8F9C8",
  "raised_by": { "...": "UserSerializer" },
  "title": "Cargo Damage Claim",
  "status": "under_investigation",
  "priority": "high",
  "assigned_agent": null,
  "description": "Box arrived crushed",
  "resolution_type": "",
  "resolved_amount": null,
  "admin_note": "",
  "resolved_by": null,
  "resolved_at": null,
  "messages": [],
  "evidence": [],
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Wallet

Maps to **Financial Wallet** (customer) and contributes data to **Financial Analytics** (admin).

```
GET  /api/wallet/                              Auth: any authenticated user — auto-created on first access
GET  /api/wallet/transactions/                 Auth: own transactions, or all if admin
GET  /api/wallet/spending-summary/?range=1M    Auth: any authenticated user   range: 1M | 6M | 1Y
POST /api/wallet/withdraw/                     Auth: any authenticated user   Body: { "amount": "100.00", "payment_method": 1 }
POST /api/wallet/transfer/                     Auth: any authenticated user   Body: { "amount": "50.00", "recipient_email": "other@user.com" }
GET  /api/wallet/payment-methods/              Auth: own payment methods
POST /api/wallet/payment-methods/              Auth: any authenticated user   Body: { "method_type": "card", "label": "Chase Business", "last4": "4291", "expiry_month": 9, "expiry_year": 2027 }
PATCH/DELETE /api/wallet/payment-methods/{id}/  Auth: own payment methods
POST /api/wallet/payment-methods/{id}/set-default/  Auth: own payment methods
GET  /api/wallet/settlements/                  Auth: admin — enterprise/group payout table
```

**Transaction object**

```json
{
  "id": 5,
  "transaction_id": "TXN-9F2C1A4B7D",
  "delivery": 2,
  "category": "delivery_payment",
  "amount": "-1190.00",
  "counterparty": "driver@fleet.com",
  "status": "completed",
  "created_at": "..."
}
```

`category` is one of `delivery_payment`, `deposit`, `refund`, `withdrawal`, `payout`, `commission`. `amount` is signed — negative for money leaving the wallet, positive for money arriving.

**Spending summary response**

```json
{ "range": "1M", "total": "412.50", "series": [{ "month": "2026-06", "total": "412.50" }] }
```

---

## Dashboard

Read-only aggregation endpoints that back each role's home screen — exactly the numbers shown on the summary cards, with no business logic the frontend needs to replicate.

```
GET /api/dashboard/customer/              Auth: customer
GET /api/dashboard/driver/                Auth: driver
GET /api/dashboard/admin-overview/        Auth: admin
GET /api/dashboard/financial-analytics/   Auth: admin
GET /api/dashboard/operations-monitoring/ Auth: admin
GET /api/dashboard/notifications/         Auth: any role — own notifications
POST /api/dashboard/notifications/clear/  Auth: any role — marks all own notifications read
GET/POST/PATCH /api/dashboard/alerts/     Auth: admin — critical alerts table
```

**`/api/dashboard/customer/`**

```json
{
  "active_shipments_count": 2,
  "recent_orders_count": 2,
  "wallet_balance": "0.00",
  "current_shipments": [ "...DeliveryRequestListSerializer" ],
  "recent_orders": [ "...DeliveryRequestListSerializer" ]
}
```

**`/api/dashboard/driver/`**

```json
{
  "daily_earnings": "0.00",
  "completed_deliveries_today": 0,
  "rating": "5.00",
  "total_trips": 0,
  "is_online": false,
  "active_delivery": null,
  "weekly_earnings": [{ "day": "2026-06-18", "total": "0.00" }]
}
```

**`/api/dashboard/admin-overview/`**

```json
{
  "active_deliveries": 2,
  "pending_kyc_approvals": 1,
  "daily_revenue": 0,
  "active_disputes": 0,
  "delivery_volume": [{ "day": "2026-06-18", "count": 2 }],
  "alerts": [ "...AlertSerializer" ]
}
```

**`/api/dashboard/financial-analytics/`**

```json
{
  "total_platform_commission": 0,
  "inflow_escrow": 0,
  "outflow_payouts": 0,
  "net_revenue": 0,
  "revenue_trends": [{ "month": "2026-06-01", "total": 0 }]
}
```

---

## Real-time (WebSockets)

Three screens are explicitly "live" in the design — live tracking, negotiation chat, and the live marketplace bid feed — so they're backed by WebSocket consumers (Django Channels) in addition to the plain REST endpoints above. **REST is always sufficient on its own** (poll if you don't need push); WebSockets are an enhancement, not a requirement.

Connect with the access token as a query param (there's no cookie session to rely on):

```js
const ws = new WebSocket(
  `ws://localhost:8000/ws/deliveries/${deliveryId}/tracking/?token=${accessToken}`
);
ws.onmessage = (e) => {
  const { event, data } = JSON.parse(e.data);
  // event === "tracking_update"
};
```

| Path | Direction | Client sends | Server broadcasts |
|---|---|---|---|
| `/ws/deliveries/{id}/tracking/` | bidirectional (driver sends, all receive) | `{ "lat": 33.1, "lng": -83.4, "heading"?: 90 }` | `{ "event": "tracking_update", "data": TrackingPing }` |
| `/ws/deliveries/{id}/chat/` | bidirectional | `{ "text": "string" }` | `{ "event": "new_message", "data": Message }` |
| `/ws/deliveries/{id}/marketplace/` | receive-only (server → client) | — | `{ "event": "new_bid", "data": Bid }` |

A REST `POST` to `bids/`, `tracking/`, or `messages/` on the same delivery also triggers the matching broadcast — so a client that mixes REST writes with WebSocket reads still sees consistent live updates.

In local dev the channel layer is in-memory (single process, fine for `runserver`). Set `USE_REDIS_CHANNEL_LAYER=True` and `REDIS_URL` in `.env` for a multi-process/production deployment.

---

## Object & enum reference

### DeliveryRequest.status

`draft` `pending` `negotiating` `accepted` `driver_arrived` `in_transit` `delayed` `delivered` `disputed` `cancelled`

### DeliveryRequest.package_type

`standard_freight` `oversized_equipment` `small_parcel` `liquid_bulk`

### DeliveryRequest.service_type

`standard` `priority`

### DeliveryRequest.payment_method

`wallet` `card`

### Bid.status / PriceProposal.status

`pending` `accepted` `rejected` (`withdrawn` also valid for Bid) / `pending` `accepted` `declined`

### DriverProfile.vehicle_type

`bike` `motorcycle` `van` `cargo_van` `truck` `heavy_truck`

### DriverProfile.verification_status

`pending` `approved` `rejected`

### DriverProfile.entity_type

`individual` `group` `enterprise`

### DriverProfile.tier

`standard` `repeat` `elite` `carrier`

### Dispute.status

`under_investigation` `active` `resolved`

### Dispute.priority

`low` `medium` `high` `critical`

### Dispute.resolution_type

`refund_customer` `release_driver` `partial_settlement`

### Transaction.category

`delivery_payment` `deposit` `refund` `withdrawal` `payout` `commission`

### Transaction.status

`completed` `processing` `pending` `failed`

### PaymentMethod.method_type

`card` `bank` `wallet`

### Settlement.entity_type / Settlement.status

`enterprise` `group` / `processing` `scheduled` `completed` `flagged`

### Alert.severity / Alert.status

`low` `medium` `high` `critical` / `investigating` `active` `pending` `resolved`
