Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

docker compose -f docker\docker-compose.yml up -d
Write-Host "Waiting for Neo4j..."
for ($i=0; $i -lt 60; $i++) {
  try {
    docker exec litigationos-neo4j cypher-shell -u neo4j -p litigationos "RETURN 1;" | Out-Null
    break
  } catch {
    Start-Sleep -Seconds 2
  }
}
Get-Content neo4j\constraints.cypher | docker exec -i litigationos-neo4j cypher-shell -u neo4j -p litigationos
Get-Content neo4j\load_all.cypher | docker exec -i litigationos-neo4j cypher-shell -u neo4j -p litigationos
Write-Host "Loaded. Open http://localhost:7474 (neo4j / litigationos)"
