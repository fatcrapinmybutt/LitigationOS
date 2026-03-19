\
#requires -Version 5.1
$ErrorActionPreference = "Stop"
function Info($m){Write-Host "[INFO] $m" -ForegroundColor Cyan}
function Fail($m){Write-Host "[FAIL] $m" -ForegroundColor Red; exit 2}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent $root
Set-Location $proj

if (-not (Test-Path ".\.venv")) { Fail "Missing .venv. Run scripts\setup_windows.ps1 first." }

Info "Installing PyInstaller..."
.\.venv\Scripts\pip.exe install pyinstaller

Info "Building one-file EXE (bundles src\litigationos_config.json)..."
$cfg = Join-Path $proj "src\litigationos_config.json"
.\.venv\Scripts\pyinstaller.exe --noconfirm --onefile --name LitigationOS_Autopilot `
  --add-data "$cfg;src" `
  .\src\litigationos_autopilot.py

Info "EXE: dist\LitigationOS_Autopilot.exe"
Info "OCR: set TESSERACT_CMD or pass --tesseract <dir|exe>."
