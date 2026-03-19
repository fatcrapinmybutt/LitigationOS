\
param(
  [string]$PythonExe = "",
  [switch]$WithOcrExtras
)

$ErrorActionPreference = "Stop"

function Write-Section($t) { Write-Host "`n=== $t ===`n" -ForegroundColor Cyan }
function Exists($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

Write-Section "LitigationOS Toolchain Bootstrap (venv + deps)"

# Resolve python
if ($PythonExe -and (Test-Path $PythonExe)) {
  $py = $PythonExe
} elseif (Exists "py") {
  $py = "py"
} elseif (Exists "python") {
  $py = "python"
} else {
  Write-Host "Python not found (py/python)."
  Write-Host "Install Python 3.11+ first. Options:"
  Write-Host "  - winget: winget install -e --id Python.Python.3.11"
  Write-Host "  - Microsoft Store: Python 3.11"
  throw "Python is required."
}

Write-Host "Using Python command: $py"

# Create venv
if (!(Test-Path ".\.venv")) {
  Write-Host "Creating venv at .\.venv ..."
  & $py -m venv ".\.venv"
} else {
  Write-Host "venv already exists: .\.venv"
}

# Activate
Write-Host "Activating venv..."
. ".\.venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
if (!(Test-Path ".\requirements.txt")) {
  Write-Host "requirements.txt not found in current folder."
  Write-Host "Place the compiler runtime here (litigationos_compiler_runtime.py + requirements.txt) then rerun."
  throw "Missing requirements.txt"
}

Write-Host "Installing requirements.txt..."
pip install -r ".\requirements.txt"

if ($WithOcrExtras) {
  if (Test-Path ".\requirements_extras_ocr.txt") {
    Write-Host "Installing OCR extras..."
    pip install -r ".\requirements_extras_ocr.txt"
  } else {
    Write-Host "requirements_extras_ocr.txt not found; skipping OCR extras."
  }
}

Write-Host "`nOK. venv ready."
Write-Host "Next: .\run_cycle0.ps1 -InDir <attachments_dir> -OutDir <out_dir>"
