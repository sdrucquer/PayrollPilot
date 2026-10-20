#!/usr/bin/env bash
# Start the PayrollPilot dev processes. Backend now; bridge (:3001) and web (:5173)
# are started when their lanes land (each guarded by a directory check).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -x backend/.venv/bin/python ]; then
  echo "[dev] creating backend venv"
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -e 'backend[dev]'
fi
if [ -f core/pyproject.toml ]; then
  backend/.venv/bin/pip install -q -e core 2>/dev/null || echo "[dev] core install failed; backend will report audit: stub"
fi

pids=()
cleanup() { for p in "${pids[@]:-}"; do kill "$p" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

echo "[dev] backend http://127.0.0.1:8000/api/health"
( cd backend && .venv/bin/uvicorn payrollpilot.app:app --port 8000 --reload ) &
pids+=($!)

if [ -f bridge/package.json ] && command -v bun >/dev/null 2>&1; then
  echo "[dev] bridge http://127.0.0.1:3001"
  ( cd bridge && bun run dev ) &
  pids+=($!)
fi

if [ -f web/package.json ]; then
  echo "[dev] web http://127.0.0.1:5173"
  ( cd web && npm run dev ) &
  pids+=($!)
fi

wait
