Param(
  [string]$HostAddr = "127.0.0.1",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPy = Join-Path $Root ".venv\\Scripts\\python.exe"

if (Test-Path $VenvPy) {
  $Py = $VenvPy
} else {
  $Py = "py"
}

Set-Location $Root
& $Py -m uvicorn main:app --app-dir (Join-Path $Root "price-tracker-backend") --host $HostAddr --port $Port

