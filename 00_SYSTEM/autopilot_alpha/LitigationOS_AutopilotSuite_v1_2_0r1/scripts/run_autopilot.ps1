\
#requires -Version 5.1
$ErrorActionPreference = "Stop"
function Info($m){Write-Host "[INFO] $m" -ForegroundColor Cyan}
function Fail($m){Write-Host "[FAIL] $m" -ForegroundColor Red; exit 2}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent $root
Set-Location $proj

if (-not (Test-Path ".\.venv")) { Fail "Missing .venv. Run scripts\setup_windows.ps1 first." }

$inDir = $proj
$outDir = Join-Path $proj "out"

Info "Running Autopilot..."
.\.venv\Scripts\python.exe .\src\litigationos_autopilot.py --in-dir $inDir --out-dir $outDir --emit-graphml
Info "Done. Outputs: $outDir"
