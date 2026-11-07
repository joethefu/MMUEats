FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# libpq-dev + build-essential: needed to build psycopg2 from source on slim images.
# curl: used by the Docker HEALTHCHECK below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Static files are code-only (no user uploads), so baking them into the image
# at build time is safe and keeps the running container immutable.
# DEBUG/SECRET_KEY here are build-time only; the real values come from the host at runtime.
RUN DEBUG=True SECRET_KEY=build-only python manage.py collectstatic --noinput

RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health/ || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]

# Daphne serves both plain HTTP and WebSocket (ws/notifications/) over the same
# ASGI application — no separate WS server/port needed, matching what
# config/asgi.py already wires up for local dev.
# Railway/other hosts inject PORT; fall back to 8000 locally.
CMD ["sh", "-c", "daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
