#!/usr/bin/env bash
# Per-boot startup for AI Academy Advisor (학원콕).
# Brings up PostgreSQL, ensures the database exists, applies migrations, and
# seeds academy facts. Idempotent and safe across restarts; returns when the
# database is ready. Long-running dev servers run in `terminals`, not here.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
export PATH="$HOME/.local/bin:$PATH"

# --- Start PostgreSQL (idempotent) -----------------------------------------
sudo pg_ctlcluster 16 main start 2>/dev/null || true

# --- Wait for readiness -----------------------------------------------------
for _ in $(seq 1 30); do
  if sudo -u postgres pg_isready -q; then
    break
  fi
  sleep 1
done

# --- Ensure role password + application database ----------------------------
sudo -u postgres psql -tc "ALTER USER postgres WITH PASSWORD 'postgres';" >/dev/null
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='ai_academy_advisor'" \
  | grep -q 1 || sudo -u postgres createdb ai_academy_advisor

# --- Apply migrations and seed academy facts (both idempotent) --------------
# import_academies upserts from data/academies/*.json, the git source of truth.
( cd backend \
  && uv run alembic upgrade head \
  && uv run python -m app.cli.import_academies ../data/academies )

echo "start.sh: database ready and seeded"
