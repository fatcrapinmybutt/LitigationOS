
# One-click launcher for Litigation OS (Windows)
# Requires: Docker Desktop (WSL2 enabled)

$ErrorActionPreference = "Stop"

Write-Host "Starting Litigation OS..."

# Ensure Docker is running
docker info | Out-Null

# Build Neo4j image if not present
$img = docker images -q litigationos-neo4j
if (-not $img) {
  Write-Host "Building Neo4j image..."
  docker build -f Dockerfile.neo4j-import -t litigationos-neo4j .
}

# Launch stack
docker compose up -d

Start-Process "http://localhost:7474"
Start-Process "http://localhost:8080"

Write-Host "Litigation OS is running."
