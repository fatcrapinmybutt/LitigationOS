#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "LitigationOS Intake Stack - Windows Setup"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python not found on PATH."
}

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Done. Activate venv with: .\.venv\Scripts\Activate.ps1"
