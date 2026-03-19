\
#requires -Version 5.1
$ErrorActionPreference = "Stop"
function Info($m){Write-Host "[INFO] $m" -ForegroundColor Cyan}
function Fail($m){Write-Host "[FAIL] $m" -ForegroundColor Red; exit 2}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent $root
Set-Location $proj

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { Fail "Python not found on PATH. Install Python 3.10+." }

if (-not (Test-Path ".\.venv")) {
  Info "Creating .venv..."
  python -m venv .venv
}
Info "Upgrading pip..."
.\.venv\Scripts\python.exe -m pip install --upgrade pip
Info "Installing requirements..."
.\.venv\Scripts\pip.exe install -r .\requirements.txt
Info "Done."
