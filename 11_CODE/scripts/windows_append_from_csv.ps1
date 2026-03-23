\
# PowerShell
param(
  [string]$Nodes = "csv\NUCLEUS_APEX_SUPERGRAPH_20250908_030140_nodes.csv",
  [string]$Edges = "csv\NUCLEUS_APEX_SUPERGRAPH_20250908_030140_edges.csv",
  [string]$Host = "localhost",
  [string]$User = "neo4j",
  [string]$Pass = "neo4j"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cypher = Join-Path $ScriptDir "cypher\append_generic.cypher"
$ImportDir = "C:\Neo4j\import"

New-Item -ItemType Directory -Force $ImportDir | Out-Null
Copy-Item $Nodes $ImportDir -Force
Copy-Item $Edges $ImportDir -Force

type $Cypher | & "C:\Program Files\Neo4j\bin\cypher-shell.bat" -a "neo4j://$Host:7687" -u $User -p $Pass --param NODES_FILE (Split-Path -Leaf $Nodes) --param EDGES_FILE (Split-Path -Leaf $Edges)
Write-Host "Append complete."
