#!/bin/sh
set -eu

# Phase 0 has no feature tables or migrations. Run migrations here once added in Phase 1.
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --no-access-log
