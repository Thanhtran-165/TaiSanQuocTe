#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BACKEND_LABEL="com.taisanquocte.backend"
FRONTEND_LABEL="com.taisanquocte.frontend"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

LOG_DIR="${HOME}/Library/Logs/TaiSanQuocTe"
mkdir -p "${LOG_DIR}"

PLIST_DIR="${HOME}/Library/LaunchAgents"
mkdir -p "${PLIST_DIR}"

BACKEND_PLIST="${PLIST_DIR}/${BACKEND_LABEL}.plist"
FRONTEND_PLIST="${PLIST_DIR}/${FRONTEND_LABEL}.plist"

write_plist() {
  local label="$1"
  local program="$2"
  local stdout_path="$3"
  local stderr_path="$4"
  local env_backend_port="$5"
  local env_frontend_port="$6"

  cat > "${program}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${label}</string>

    <key>WorkingDirectory</key>
    <string>${ROOT_DIR}</string>

    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>${ROOT_DIR}/scripts/$(basename "${program}" .plist | sed 's/^com\\.taisanquocte\\.//; s/$/.sh/')</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${stdout_path}</string>

    <key>StandardErrorPath</key>
    <string>${stderr_path}</string>

    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
      <key>BACKEND_PORT</key>
      <string>${env_backend_port}</string>
      <key>FRONTEND_PORT</key>
      <string>${env_frontend_port}</string>
    </dict>
  </dict>
</plist>
EOF
}

# Write plists
cat > "${BACKEND_PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${BACKEND_LABEL}</string>
    <key>WorkingDirectory</key>
    <string>${ROOT_DIR}</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>${ROOT_DIR}/scripts/run_backend.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/backend.out.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/backend.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
      <key>BACKEND_PORT</key>
      <string>${BACKEND_PORT}</string>
    </dict>
  </dict>
</plist>
EOF

cat > "${FRONTEND_PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>${FRONTEND_LABEL}</string>
    <key>WorkingDirectory</key>
    <string>${ROOT_DIR}</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>${ROOT_DIR}/scripts/run_frontend.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/frontend.out.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/frontend.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
      <key>PATH</key>
      <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
      <key>FRONTEND_PORT</key>
      <string>${FRONTEND_PORT}</string>
      <key>BACKEND_URL</key>
      <string>http://localhost:${BACKEND_PORT}</string>
      <key>NEXT_PUBLIC_API_URL</key>
      <string>http://localhost:${BACKEND_PORT}</string>
    </dict>
  </dict>
</plist>
EOF

load_service() {
  local label="$1"
  local plist="$2"
  launchctl bootout "gui/${UID}" "${plist}" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/${UID}" "${plist}"
  launchctl enable "gui/${UID}/${label}" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/${UID}/${label}"
}

load_service "${BACKEND_LABEL}" "${BACKEND_PLIST}"
load_service "${FRONTEND_LABEL}" "${FRONTEND_PLIST}"

echo "✅ Installed autostart (launchd)."
echo "- Backend:  http://localhost:${BACKEND_PORT}/docs"
echo "- Frontend: http://localhost:${FRONTEND_PORT}"
echo "Logs: ${LOG_DIR}"

