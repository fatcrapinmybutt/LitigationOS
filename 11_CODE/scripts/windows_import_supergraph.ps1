\
# PowerShell
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$CsvDir = Join-Path $RootDir "csv"

$Nodes = "NUCLEUS_APEX_SUPERGRAPH_20250908_030140_nodes.csv"
$Edges = "NUCLEUS_APEX_SUPERGRAPH_20250908_030140_edges.csv"

Stop-Service neo4j -ErrorAction SilentlyContinue
$ImportDir = "C:\Neo4j\import\apex"
New-Item -ItemType Directory -Force $ImportDir | Out-Null
Copy-Item (Join-Path $CsvDir $Nodes) $ImportDir -Force
Copy-Item (Join-Path $CsvDir $Edges) $ImportDir -Force

& "C:\Program Files\Neo4j\bin\neo4j-admin.exe" database import full --overwrite-destination=true nucleus_apex_supergraph `
  --nodes="$ImportDir\$Nodes" `
  --relationships="$ImportDir\$Edges"

Start-Service neo4j
Write-Host "Imported nucleus_apex_supergraph. In Browser: :use nucleus_apex_supergraph"
