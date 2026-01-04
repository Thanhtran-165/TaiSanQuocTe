Param(
  [int]$Port = 3000
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (!(Test-Path (Join-Path $Root "price-tracker-frontend\\node_modules"))) {
  throw "Missing price-tracker-frontend\\node_modules. Run: npm -C price-tracker-frontend install"
}

if (!(Test-Path (Join-Path $Root "price-tracker-frontend\\.next\\BUILD_ID"))) {
  npm -C price-tracker-frontend run build
}

npm -C price-tracker-frontend run start -- -p $Port

