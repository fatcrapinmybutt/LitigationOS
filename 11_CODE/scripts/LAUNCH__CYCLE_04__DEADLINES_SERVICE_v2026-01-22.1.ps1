param(
  [string]$Neo4jImportDir = "",
  [switch]$OpenNeo4jBrowser = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host ""
Write-Host "=== SuperBloom STACK — CYCLE_04 (Deadlines + Service) Launcher ==="
Write-Host "Root: $root"
Write-Host ""

# 1) Open offline ERD viewer + delta doc
$viewer = Join-Path $root "SuperBloom_ERD_Superset_v2026-01-22.1.html"
$delta  = Join-Path $root "DELTA__CYCLE_04__DEADLINES_SERVICE_v2026-01-22.1.md"

if (Test-Path $viewer) { Start-Process $viewer } else { Write-Host "Missing viewer: $viewer" }
if (Test-Path $delta)  { Start-Process $delta }  else { Write-Host "Missing delta:  $delta" }

# 2) Optional: copy CSVs into Neo4j import directory (user-supplied)
if ($Neo4jImportDir -ne "") {
  Write-Host ""
  Write-Host "Copying ERD CSVs into Neo4j import dir: $Neo4jImportDir"
  $srcDir = Join-Path $root "Neo4jImport_ERD_v2026-01-22.1"
  $csvs = @("erd_tables.csv","erd_fields.csv","erd_relationships.csv")
  foreach ($c in $csvs) {
    $src = Join-Path $srcDir $c
    $dst = Join-Path $Neo4jImportDir $c
    if (!(Test-Path $src)) { throw "Missing source CSV: $src" }
    Copy-Item -Force $src $dst
  }
  Write-Host "CSV copy complete."
  Write-Host "Next: run cypher scripts from Neo4jImport_ERD_v2026-01-22.1 in Neo4j Browser."
}

# 3) Optional: open Neo4j Browser URL (best-effort)
if ($OpenNeo4jBrowser) {
  try {
    Start-Process "http://localhost:7474/browser/"
  } catch {
    Write-Host "Could not open Neo4j Browser URL. Ensure Neo4j is running."
  }
}

Write-Host ""
Write-Host "Done."
Write-Host ""
