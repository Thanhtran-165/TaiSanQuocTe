#!/usr/bin/env bash
set -euo pipefail

BACKEND_LABEL="com.taisanquocte.backend"
FRONTEND_LABEL="com.taisanquocte.frontend"

PLIST_DIR="${HOME}/Library/LaunchAgents"
BACKEND_PLIST="${PLIST_DIR}/${BACKEND_LABEL}.plist"
FRONTEND_PLIST="${PLIST_DIR}/${FRONTEND_LABEL}.plist"

unload_service() {
  local label="$1"
  local plist="$2"
  launchctl bootout "gui/${UID}" "${plist}" >/dev/null 2>&1 || true
  launchctl disable "gui/${UID}/${label}" >/dev/null 2>&1 || true
  rm -f "${plist}"
}

unload_service "${BACKEND_LABEL}" "${BACKEND_PLIST}"
unload_service "${FRONTEND_LABEL}" "${FRONTEND_PLIST}"

echo "✅ Uninstalled autostart (launchd)."

