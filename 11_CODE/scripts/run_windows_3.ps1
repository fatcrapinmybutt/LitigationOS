# Requires Docker Desktop
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Pop-Location
# project root is one folder up
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location (Join-Path $root "docker")
docker compose up -d
Write-Host "Neo4j starting..."
Start-Sleep -Seconds 8
# apply constraints and load
$cypher = @(
  "$(Get-Content (Join-Path $root 'neo4j\constraints.cypher') -Raw)",
  "$(Get-Content (Join-Path $root 'neo4j\load_all.cypher') -Raw)"
) -join "`n"
$cypher | docker exec -i litigationos-neo4j cypher-shell -u neo4j -p litigationos
Write-Host "Loaded authority + propositions."
if (Test-Path (Join-Path $root 'import\vehicles.csv')) {
  Get-Content (Join-Path $root 'neo4j\load_vehicles_po.cypher') -Raw | docker exec -i litigationos-neo4j cypher-shell -u neo4j -p litigationos
  Write-Host "Loaded vehicles + proof obligations."
}
Write-Host "Open http://localhost:7474 (neo4j / litigationos)"
