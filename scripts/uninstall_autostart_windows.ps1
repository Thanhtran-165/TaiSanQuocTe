$ErrorActionPreference = "Continue"

$BackendTask = "TaiSanQuocTe Backend"
$FrontendTask = "TaiSanQuocTe Frontend"

schtasks /Delete /TN $BackendTask /F 2>$null | Out-Null
schtasks /Delete /TN $FrontendTask /F 2>$null | Out-Null

Write-Host "✅ Uninstalled autostart (Task Scheduler)."

