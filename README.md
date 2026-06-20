# Logistica

A logistics marketplace platform connecting shippers (customers), carriers (drivers), and platform admins/ops.

## Structure

- [`backend/`](backend/README.md) — Django REST API **and** the working frontend (`backend/templates/`, `backend/static/`). Both are served by Django on a single port — see its README for setup, endpoint reference, and architecture.
- `frontend/design-prototypes/` — original HTML/Tailwind design prototypes the API and UI were specced against. Reference only, not part of the deployed app, not pushed to this repo.

## Running it

```
cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Then open `http://localhost:8000/` — the full app (frontend + API) runs on that one port. Or use `docker compose up` from the repo root.
