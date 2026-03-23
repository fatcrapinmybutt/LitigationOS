# PowerShell
$ErrorActionPreference = "Stop"
$ImportDir = "C:\Neo4j\import\apex"
Stop-Service neo4j -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $ImportDir | Out-Null
Copy-Item "/mnt/data/APEX_NEO4_ORG_20250908_024944/csv/APEX_OVERLAY_v2_nodes_20250908_023044.csv" $ImportDir -Force
Copy-Item "/mnt/data/APEX_NEO4_ORG_20250908_024944/csv/APEX_OVERLAY_v2_edges_20250908_023044.csv" $ImportDir -Force
& "C:\Program Files\Neo4j\bin\neo4j-admin.exe" database import full --overwrite-destination=true nucleus_blooming_v2 `
  --nodes="$ImportDir\APEX_OVERLAY_v2_nodes_20250908_023044.csv" `
  --relationships="$ImportDir\APEX_OVERLAY_v2_edges_20250908_023044.csv"
Start-Service neo4j
Write-Host "Imported nucleus_blooming_v2. In Browser: :use nucleus_blooming_v2"
