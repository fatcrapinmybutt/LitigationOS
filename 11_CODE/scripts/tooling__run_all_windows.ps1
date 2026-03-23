# Runs backend + desktop dev mode (Windows)
# Optional: start Neo4j via Docker Desktop + docker compose.
param(
  [switch]$StartNeo4j
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$backend = Join-Path $root "services\backend"
$desktop = Join-Path $root "apps\desktop"
$compose = Join-Path $root "tooling\docker-compose.neo4j.yml"

if ($StartNeo4j) {
  Write-Host "Starting Neo4j (docker compose)..." -ForegroundColor Cyan
  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Install Docker Desktop, then re-run with -StartNeo4j." -ForegroundColor Yellow
  } else {
    docker compose -f $compose up -d
  }
}

Write-Host "Starting backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$backend`"; .\.venv\Scripts\Activate.ps1; python -m app.server"

Write-Host "Starting desktop..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$desktop`"; npm run dev"

Write-Host "Done." -ForegroundColor Green
