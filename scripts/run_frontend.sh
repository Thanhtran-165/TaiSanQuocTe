#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# launchd often has a minimal PATH; add common Homebrew locations.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"

FRONTEND_PORT="${FRONTEND_PORT:-3000}"

NPM_BIN="${NPM_BIN:-}"
if [[ -z "${NPM_BIN}" ]]; then
  NPM_BIN="$(command -v npm || true)"
fi
if [[ -z "${NPM_BIN}" ]]; then
  echo "ERROR: npm not found. Install Node.js (npm) and ensure it is in PATH." >&2
  exit 1
fi

if [[ ! -d "${ROOT_DIR}/price-tracker-frontend/node_modules" ]]; then
  echo "ERROR: Missing price-tracker-frontend/node_modules. Run: npm -C price-tracker-frontend install" >&2
  exit 1
fi

# Build once if needed.
if [[ ! -f "${ROOT_DIR}/price-tracker-frontend/.next/BUILD_ID" ]]; then
  "${NPM_BIN}" -C "${ROOT_DIR}/price-tracker-frontend" run build
fi

exec "${NPM_BIN}" -C "${ROOT_DIR}/price-tracker-frontend" run start -- -p "${FRONTEND_PORT}"

