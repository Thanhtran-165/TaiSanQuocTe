#!/usr/bin/env bash
set -euo pipefail

# Install a user LaunchAgent to refresh WGC data daily on macOS.
# It runs `scripts/wgc_refresh.py` using the repo-local venv `.venv_wgc`.
#
# Usage:
#   bash scripts/install_wgc_refresh_macos.sh
#   bash scripts/install_wgc_refresh_macos.sh --time 08:10
#   bash scripts/install_wgc_refresh_macos.sh --uninstall
#
# Notes:
# - Requires `.secrets/wgc_auth_cookie.txt` to exist (run `scripts/wgc_bootstrap_cookie.py` first).
# - LaunchAgent logs go to `~/Library/Logs/wordasset-wgc-refresh.{out,err}.log`.

PLIST_ID="com.wordasset.wgc-refresh"
AGENTS_DIR="${HOME}/Library/LaunchAgents"
LOG_DIR="${HOME}/Library/Logs"
OUT_LOG="${LOG_DIR}/wordasset-wgc-refresh.out.log"
ERR_LOG="${LOG_DIR}/wordasset-wgc-refresh.err.log"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${REPO_DIR}/.venv_wgc/bin/python"
REFRESH_PY="${REPO_DIR}/scripts/wgc_refresh.py"

TIME_HHMM="08:10"
UNINSTALL="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --time)
      TIME_HHMM="${2:-}"
      shift 2
      ;;
    --uninstall)
      UNINSTALL="1"
      shift 1
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

PLIST_PATH="${AGENTS_DIR}/${PLIST_ID}.plist"

if [[ "${UNINSTALL}" == "1" ]]; then
  mkdir -p "${AGENTS_DIR}"
  launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" 2>/dev/null || true
  rm -f "${PLIST_PATH}"
  echo "Uninstalled LaunchAgent: ${PLIST_ID}"
  exit 0
fi

if [[ ! -f "${REPO_DIR}/.secrets/wgc_auth_cookie.txt" ]]; then
  echo "Missing cookie file: ${REPO_DIR}/.secrets/wgc_auth_cookie.txt" >&2
  echo "Run: ./.venv_wgc/bin/python scripts/wgc_bootstrap_cookie.py" >&2
  exit 2
fi

if [[ ! -x "${VENV_PY}" ]]; then
  echo "Missing venv python: ${VENV_PY}" >&2
  echo "Create it with:" >&2
  echo "  python3 -m venv .venv_wgc" >&2
  echo "  ./.venv_wgc/bin/python -m pip install -U pip requests pandas openpyxl playwright" >&2
  echo "  ./.venv_wgc/bin/python -m playwright install chromium" >&2
  exit 2
fi

mkdir -p "${AGENTS_DIR}" "${LOG_DIR}"

HOUR="${TIME_HHMM%:*}"
MIN="${TIME_HHMM#*:}"
if [[ ! "${HOUR}" =~ ^[0-9]{1,2}$ ]] || [[ ! "${MIN}" =~ ^[0-9]{2}$ ]]; then
  echo "Invalid --time format, expected HH:MM, got: ${TIME_HHMM}" >&2
  exit 2
fi

cat > "${PLIST_PATH}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${PLIST_ID}</string>

    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>

    <key>ProgramArguments</key>
    <array>
      <string>${VENV_PY}</string>
      <string>${REFRESH_PY}</string>
      <string>--python</string>
      <string>${VENV_PY}</string>
      <string>--outdir</string>
      <string>data_wgc</string>
    </array>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PYTHONUNBUFFERED</key>
      <string>1</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>${HOUR}</integer>
      <key>Minute</key>
      <integer>${MIN}</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>${OUT_LOG}</string>
    <key>StandardErrorPath</key>
    <string>${ERR_LOG}</string>
  </dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_PATH}"
launchctl enable "gui/$(id -u)/${PLIST_ID}" || true
launchctl kickstart -k "gui/$(id -u)/${PLIST_ID}" || true

echo "Installed LaunchAgent: ${PLIST_ID}"
echo "Runs daily at: ${TIME_HHMM}"
echo "Logs:"
echo "  ${OUT_LOG}"
echo "  ${ERR_LOG}"

