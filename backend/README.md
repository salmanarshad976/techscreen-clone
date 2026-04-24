# Tech Screen Backend

FastAPI + SQLite + JWT auth backend powering the Tech Screen replica's signup, login, and dashboard.

## Run locally

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8001
```

## Endpoints

- `GET  /api/health`
- `POST /api/auth/register` — `{ email, password, full_name }` → `{ access_token }`
- `POST /api/auth/login` — `{ email, password }` → `{ access_token }`
- `GET  /api/me` — current user (Bearer token)
- `GET  /api/dashboard` — user, usage, plan limits
- `POST /api/dashboard/consume-token` — decrement tokens by 1 (demo)

## Environment

- `DATABASE_URL` (default `sqlite:///./techscreen.db`)
- `JWT_SECRET` (default `dev-secret-change-me` — set in production)
- `JWT_TTL_HOURS` (default `24`)
- `CORS_ORIGINS` (comma-separated; defaults include the deployed frontend)
