Param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendScript = Join-Path $Root "scripts\\run_backend_windows.ps1"
$FrontendScript = Join-Path $Root "scripts\\run_frontend_windows.ps1"

$BackendTask = "TaiSanQuocTe Backend"
$FrontendTask = "TaiSanQuocTe Frontend"

schtasks /Delete /TN $BackendTask /F 2>$null | Out-Null
schtasks /Delete /TN $FrontendTask /F 2>$null | Out-Null

$BackendCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$BackendScript`" -Port $BackendPort"
$FrontendCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$FrontendScript`" -Port $FrontendPort"

schtasks /Create /SC ONLOGON /RL LIMITED /TN $BackendTask /TR $BackendCmd /F | Out-Null
schtasks /Create /SC ONLOGON /RL LIMITED /TN $FrontendTask /TR $FrontendCmd /F | Out-Null

Write-Host "✅ Installed autostart (Task Scheduler)."
Write-Host "- Backend:  http://localhost:$BackendPort/docs"
Write-Host "- Frontend: http://localhost:$FrontendPort"

