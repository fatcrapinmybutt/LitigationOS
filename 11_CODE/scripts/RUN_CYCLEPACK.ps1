<#
RUN_CYCLEPACK.ps1
- Double-click to run (or right-click → Run with PowerShell).
- Creates an isolated venv under .venv/
- Installs requirements
- Runs tools/cycle_runner.py against INPUT/ and writes OUTPUT/

Safe by default: append-only, idempotent, deterministic zip.
#>

$ErrorActionPreference = "Stop"

function Write-Section($t) {
  Write-Host ""
  Write-Host "=== $t ==="
}

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

Write-Section "LitigationOS CyclePack Runner"
Write-Host "Root: $ROOT"

# Choose python
$PY = $null
foreach ($c in @("py", "python", "python3")) {
  try {
    & $c -c "import sys; print(sys.executable)" | Out-Null
    $PY = $c
    break
  } catch {}
}
if (-not $PY) {
  throw "Python not found. Install Python 3.10+ and ensure it's on PATH."
}
Write-Host "Python command: $PY"

# Venv
$VENV = Join-Path $ROOT ".venv"
if (-not (Test-Path $VENV)) {
  Write-Section "Creating venv"
  & $PY -m venv $VENV
}

$PYV = Join-Path $VENV "Scripts\python.exe"
if (-not (Test-Path $PYV)) {
  throw "Venv python not found at: $PYV"
}

Write-Section "Upgrading pip"
& $PYV -m pip install --upgrade pip

Write-Section "Installing requirements"
& $PYV -m pip install -r (Join-Path $ROOT "requirements.txt")

Write-Section "Running cycle"
& $PYV (Join-Path $ROOT "tools\cycle_runner.py") --root $ROOT

Write-Section "Done"
Write-Host "Outputs: $(Join-Path $ROOT 'OUTPUT')"
