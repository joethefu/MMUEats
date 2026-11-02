#!/bin/sh
set -e

echo "Waiting for the database to be ready..."
python << 'PYEOF'
import os
import sys
import time
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
if not url:
    print("No DATABASE_URL set (using SQLite) — skipping wait.")
    sys.exit(0)

import psycopg2

parsed = urlparse(url)
for attempt in range(30):
    try:
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
            connect_timeout=3,
        )
        conn.close()
        print("Database is ready.")
        break
    except Exception as exc:
        print(f"Database not ready yet ({exc}); retrying in 2s... [{attempt + 1}/30]")
        time.sleep(2)
else:
    sys.exit("Database never became available after 60 seconds.")
PYEOF

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting: $@"
exec "$@"
