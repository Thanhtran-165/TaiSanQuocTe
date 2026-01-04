#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONUNBUFFERED=1

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

PYTHON_BIN="${APP_PYTHON:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
  elif [[ -x "${ROOT_DIR}/.venv_wgc/bin/python" ]]; then
    PYTHON_BIN="${ROOT_DIR}/.venv_wgc/bin/python"
  else
    PYTHON_BIN="$(command -v python3 || command -v python)"
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "ERROR: Python not found. Install Python 3 and/or create venv at .venv/" >&2
  exit 1
fi

exec "${PYTHON_BIN}" -m uvicorn main:app \
  --app-dir "${ROOT_DIR}/price-tracker-backend" \
  --host "${BACKEND_HOST}" \
  --port "${BACKEND_PORT}"

