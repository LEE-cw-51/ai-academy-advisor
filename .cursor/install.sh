#!/usr/bin/env bash
# Repository bootstrap for AI Academy Advisor (학원콕).
# Idempotent: safe to run repeatedly and against cached/snapshot state.
# Prepares durable state only (toolchains, system packages, dependencies,
# local env files). Per-boot service startup lives in .cursor/start.sh.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- uv (Python package manager) -------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# --- PostgreSQL 16 + pgvector ----------------------------------------------
# The app stores review embeddings in a pgvector column and migration 0003
# runs `CREATE EXTENSION vector`, so the server needs the extension available.
if ! command -v psql >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    postgresql postgresql-contrib postgresql-16-pgvector
fi

# --- Backend dependencies ---------------------------------------------------
( cd backend && uv sync )

# --- Frontend dependencies --------------------------------------------------
# Prefer the reproducible `npm ci`; fall back to `npm install` if the lockfile
# has drifted (missing optional platform-native transitive deps).
( cd frontend && (npm ci || npm install) )

# --- Local env files (defaults already work; these make config explicit) ----
[ -f .env ] || cp .env.example .env
[ -f frontend/.env.local ] || cp frontend/.env.local.example frontend/.env.local

echo "install.sh: done"
