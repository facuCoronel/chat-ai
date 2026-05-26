#!/bin/sh
set -eu

python - <<'PY'
from sqlalchemy.engine import make_url

from app.infrastructure.config import get_database_settings

url = make_url(get_database_settings().sqlalchemy_database_url)
print(f"DATABASE_TARGET={url.set(password='***')}", flush=True)
PY
alembic upgrade head
alembic current
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
