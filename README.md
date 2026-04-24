# Tech Screen — Replica

A full-stack replica of [techscreen.app](https://techscreen.app) — an "invisible AI interview assistant" marketing site, plus a working signup / login / dashboard backend.

> Educational replica only. Not affiliated with the original Tech Screen product.

## Stack

| Layer    | Tech                                                       |
| -------- | ---------------------------------------------------------- |
| Frontend | Static HTML + Tailwind CSS (CDN) + vanilla JS              |
| Backend  | FastAPI · SQLAlchemy 2 · SQLite · JWT (PyJWT) · bcrypt     |
| Hosting  | Frontend → static hosting / Backend → Fly.io (Dockerfile)  |

## Layout

```
techscreen-clone/
├── frontend/              # static landing + multi-page app
│   ├── index.html         # landing (hero, features, comparison, FAQ, CTA)
│   ├── pricing.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── assets/
│       ├── app.css        # shared styles
│       └── api.js         # tiny API client (localStorage JWT)
└── backend/               # FastAPI app
    ├── pyproject.toml
    └── app/
        ├── main.py        # routes
        ├── auth.py        # JWT + password hashing
        ├── db.py          # SQLAlchemy engine / session
        ├── models.py      # User
        └── schemas.py     # Pydantic schemas
```

## Frontend — local

Just open `frontend/index.html` in a browser. To exercise the auth flows, also run the backend (next section). The frontend will hit `http://127.0.0.1:8001` automatically when you load it from `localhost`.

For a local static server:

```bash
cd frontend
python -m http.server 8000
# then open http://localhost:8000
```

## Backend — local

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8001
```

Endpoints:

| Method | Path                              | Description                       |
| ------ | --------------------------------- | --------------------------------- |
| GET    | `/api/health`                     | health check                      |
| POST   | `/api/auth/register`              | create account, returns JWT       |
| POST   | `/api/auth/login`                 | exchange creds for JWT            |
| GET    | `/api/me`                         | current user (Bearer)             |
| GET    | `/api/dashboard`                  | usage + plan limits               |
| POST   | `/api/dashboard/consume-token`    | demo: decrement tokens by 1       |

## Environment variables (backend)

| Name           | Default                          |
| -------------- | -------------------------------- |
| `DATABASE_URL` | `sqlite:///./techscreen.db`      |
| `JWT_SECRET`   | `dev-secret-change-me`           |
| `JWT_TTL_HOURS`| `24`                             |
| `CORS_ORIGINS` | localhost + the deployed preview |

## Pointing the frontend at a deployed backend

The frontend chooses its API base via `window.__TECHSCREEN_API_BASE__`. To override:

```html
<script>window.__TECHSCREEN_API_BASE__ = "https://your-backend.fly.dev";</script>
```

…before `assets/api.js` loads. When the page is served from `localhost`, it falls back to `http://127.0.0.1:8001`.
