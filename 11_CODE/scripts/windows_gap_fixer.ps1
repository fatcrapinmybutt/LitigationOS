\
# PowerShell
param(
  [string]$Host = "localhost",
  [string]$User = "neo4j",
  [string]$Pass = "neo4j"
)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cy = Join-Path $ScriptDir "cypher\gap_fixer_apply.cypher"
type $Cy | & "C:\Program Files\Neo4j\bin\cypher-shell.bat" -a ("neo4j://{0}:7687" -f $Host) -u $User -p $Pass
Write-Host "Gap-fixer applied."
