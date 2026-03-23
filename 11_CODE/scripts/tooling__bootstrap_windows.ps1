# LitigationOS Executive Suite - Windows bootstrap
# - Creates Python venv for backend
# - Installs backend requirements
# - Installs desktop npm deps
# NOTE: assumes Node.js + Python are already installed.

$ErrorActionPreference = "Stop"

Write-Host "== Backend venv + deps ==" -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "..\services\backend")
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Pop-Location

Write-Host "== Desktop npm install ==" -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "..\apps\desktop")
npm install
Pop-Location

Write-Host "Bootstrap complete." -ForegroundColor Green
