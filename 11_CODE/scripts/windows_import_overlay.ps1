# PowerShell
$ErrorActionPreference = "Stop"
$ImportDir = "C:\Neo4j\import\apex"
Stop-Service neo4j -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $ImportDir | Out-Null
Copy-Item "/mnt/data/APEX_NEO4_ORG_20250908_024944/csv/APEX_OVERLAY_nodes.csv" $ImportDir -Force
Copy-Item "/mnt/data/APEX_NEO4_ORG_20250908_024944/csv/APEX_OVERLAY_edges.csv" $ImportDir -Force
& "C:\Program Files\Neo4j\bin\neo4j-admin.exe" database import full --overwrite-destination=true nucleus_blooming_overlay `
  --nodes="$ImportDir\APEX_OVERLAY_nodes.csv" `
  --relationships="$ImportDir\APEX_OVERLAY_edges.csv"
Start-Service neo4j
Write-Host "Imported nucleus_blooming_overlay. In Browser: :use nucleus_blooming_overlay"
