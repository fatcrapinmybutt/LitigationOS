# Runs backend + desktop dev mode
$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "services\backend"
$desktop = Join-Path $root "apps\desktop"

Write-Host "Starting backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$backend`"; .\.venv\Scripts\Activate.ps1; python -m app.server"

Write-Host "Starting desktop..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$desktop`"; npm run dev"
