<# 
Install a Windows Scheduled Task to refresh WGC data daily.

Usage (PowerShell as current user):
  powershell -ExecutionPolicy Bypass -File scripts\install_wgc_refresh_windows.ps1
  powershell -ExecutionPolicy Bypass -File scripts\install_wgc_refresh_windows.ps1 -Time "08:10"
  powershell -ExecutionPolicy Bypass -File scripts\install_wgc_refresh_windows.ps1 -Uninstall

Prereqs:
  - Create venv `.venv_wgc` and install deps:
      python -m venv .venv_wgc
      .\.venv_wgc\Scripts\python -m pip install -U pip requests pandas openpyxl playwright
      .\.venv_wgc\Scripts\python -m playwright install chromium
  - Bootstrap cookie:
      .\.venv_wgc\Scripts\python scripts\wgc_bootstrap_cookie.py
    -> creates `.secrets\wgc_auth_cookie.txt`
#>

param(
  [string]$Time = "08:10",
  [switch]$Uninstall
)

$TaskName = "WordAsset-WGC-Refresh"
$RepoDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPy = Join-Path $RepoDir ".venv_wgc\Scripts\python.exe"
$RefreshPy = Join-Path $RepoDir "scripts\wgc_refresh.py"
$CookieFile = Join-Path $RepoDir ".secrets\wgc_auth_cookie.txt"
$LogDir = Join-Path $RepoDir ".secrets"
$OutLog = Join-Path $LogDir "wgc_refresh_windows.out.log"
$ErrLog = Join-Path $LogDir "wgc_refresh_windows.err.log"

if ($Uninstall) {
  schtasks /Delete /TN $TaskName /F | Out-Null
  Write-Host "Uninstalled scheduled task: $TaskName"
  exit 0
}

if (!(Test-Path $CookieFile)) {
  Write-Error "Missing cookie file: $CookieFile`nRun: $VenvPy scripts\wgc_bootstrap_cookie.py"
  exit 2
}

if (!(Test-Path $VenvPy)) {
  Write-Error "Missing venv python: $VenvPy"
  exit 2
}

# Validate time HH:MM
if ($Time -notmatch "^\d{1,2}:\d{2}$") {
  Write-Error "Invalid -Time format. Expected HH:MM (e.g. 08:10). Got: $Time"
  exit 2
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Command: run refresh script and tee logs
$Cmd = "`"$VenvPy`" `"$RefreshPy`" --python `"$VenvPy`" --outdir data_wgc 1>> `"$OutLog`" 2>> `"$ErrLog`""

# Create task for current user (no admin required typically).
schtasks /Create `
  /TN $TaskName `
  /SC DAILY `
  /ST $Time `
  /TR "cmd.exe /c $Cmd" `
  /RL LIMITED `
  /F | Out-Null

Write-Host "Installed scheduled task: $TaskName"
Write-Host "Runs daily at: $Time"
Write-Host "Logs:"
Write-Host "  $OutLog"
Write-Host "  $ErrLog"

