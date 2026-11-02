# MMUEats

Campus food delivery platform for Multimedia University of Kenya — customers,
vendors, delivery partners, and administrators, built as a Django REST API
backend with a React web frontend (Flutter mobile app planned).

See [`PROGRESS.md`](./PROGRESS.md) for a full phase-by-phase build log,
what's implemented, what's tested, and what's still open.

---

## Project structure

```
MMUEats/
├── backend/       Django REST API (12 apps — see backend/config/settings.py)
├── web/           React + Vite web app
├── mobile/        Flutter app (not yet started — see PROGRESS.md)
├── docker-compose.yml
├── .env.docker.example
└── PROGRESS.md
```

---

## Local development (no Docker)

### Backend

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env        # fill in real values as you get them; safe defaults otherwise
./venv/bin/python manage.py migrate
./venv/bin/python manage.py createsuperuser
./venv/bin/python manage.py runserver
```

Runs on SQLite by default — no Postgres/Redis install required to develop.
Emails print to the console; M-Pesa and Firebase run in a safe mock mode
until you add real credentials to `.env` (see the comments in
`backend/.env.example`). Visit `http://localhost:8000/api/docs/` for the
interactive Swagger API docs.

Run tests: `./venv/bin/python manage.py test`

### Web

```bash
cd web
npm install
cp .env.example .env
npm run dev
```

Runs on `http://localhost:5173`, talking to the backend at
`http://localhost:8000/api` by default (see `web/.env`).

---

## Docker deployment (production-style)

Requires Docker and Docker Compose. This runs Postgres, Redis, the
Django/Daphne backend (serving both the REST API and WebSocket traffic),
a Celery worker, and an Nginx container serving the built React app while
reverse-proxying `/api/`, `/admin/`, `/ws/`, `/static/`, and `/media/` to
the backend — so the frontend and API share one origin and CORS is a
non-issue in production.

```bash
# 1. Compose-level config (Postgres password, allowed hosts, web port)
cp .env.docker.example .env

# 2. Application-level config (email, M-Pesa, Firebase, Maps, secret keys)
cp backend/.env.example backend/.env
# then edit backend/.env — at minimum set real SECRET_KEY / JWT_SECRET values
# for production; everything else can stay in its safe mock/default mode

# 3. Build and start everything
docker compose up --build -d

# 4. Create an admin account
docker compose exec backend python manage.py createsuperuser
```

The site is then reachable at `http://localhost` (or whatever `WEB_PORT`
you set). The backend and Celery worker both wait for Postgres to become
reachable and run migrations automatically on startup
(`backend/docker-entrypoint.sh`) — no manual migration step needed after
the first `createsuperuser`.

**Note on this repository's own build process:** the Docker files
(`backend/Dockerfile`, `web/Dockerfile`, `docker-compose.yml`,
`backend/docker-entrypoint.sh`) were written and manually reviewed for
correctness (Dockerfile syntax, the entrypoint's embedded Python, and the
Compose YAML were all syntax-validated), but — since this development
sandbox has no Docker daemon available — `docker compose up` itself could
not be executed here. Django's own `manage.py check --deploy` was run
locally with `DEBUG=False` and reports zero security warnings against the
production hardening in `backend/config/settings.py`. Please run a real
`docker compose up --build` in an environment with Docker before relying
on this for production, and open an issue if anything doesn't come up
cleanly.

### What's configurable via environment variables

| File | Controls |
|---|---|
| `.env` (repo root, from `.env.docker.example`) | Postgres password, `ALLOWED_HOSTS`, the host port Nginx binds to |
| `backend/.env` (from `backend/.env.example`) | Django secret keys, email/SMTP, M-Pesa Daraja credentials, Firebase, Google Maps key, JWT lifetimes |

Every credential-dependent feature (email sending, M-Pesa payments, Firebase
push) runs in a clearly-logged mock mode until real credentials are supplied
— nothing blocks development or a first deployment on waiting for
third-party accounts to be set up.

### Scaling notes for a real production rollout

- Swap `MEDIA_ROOT` local disk storage for S3/GCS-compatible object storage
  (`django-storages`) once traffic grows — the codebase already isolates
  this behind Django's standard file storage API, so no application code
  needs to change.
- The `celery_worker` service can be scaled independently
  (`docker compose up --scale celery_worker=3`) for heavier notification/
  email volume.
- `SECURE_HSTS_SECONDS` and friends in `backend/config/settings.py` assume
  TLS is terminated in front of this stack (e.g. by a managed load balancer
  or by adding a TLS-terminating reverse proxy in front of the `web`
  container) — plain `docker compose up` here serves HTTP only.
