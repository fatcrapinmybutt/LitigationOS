\
param(
  [Parameter(Mandatory=$true)][string]$InDir,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [switch]$DryRun,
  [switch]$FailHard
)

$ErrorActionPreference = "Stop"

function Write-Section($t) { Write-Host "`n=== $t ===`n" -ForegroundColor Cyan }

Write-Section "LitigationOS Cycle 0 Runner"

if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Host "venv not found. Run bootstrap first:"
  Write-Host "  .\bootstrap_windows.ps1"
  throw "Missing venv"
}

. ".\.venv\Scripts\Activate.ps1"

if (!(Test-Path ".\litigationos_compiler_runtime.py")) {
  Write-Host "litigationos_compiler_runtime.py not found in current folder."
  Write-Host "Extract the runtime ZIP into this folder."
  throw "Missing runtime script"
}

$cmd = @("python", ".\litigationos_compiler_runtime.py", "--in", $InDir, "--out", $OutDir)

if ($DryRun) { $cmd += "--dry-run" }
if ($FailHard) { $cmd += "--fail-hard" }

Write-Host "Running:"
Write-Host ("  " + ($cmd -join " "))

& $cmd[0] $cmd[1..($cmd.Length-1)]

Write-Host "`nDone. Outputs in: $OutDir"
Write-Host "Key files:"
Write-Host "  - neo4j_nodes.csv"
Write-Host "  - neo4j_edges.csv"
Write-Host "  - graph.graphml"
Write-Host "  - action_report.md"
