\
$ErrorActionPreference = "Stop"
function Write-Section($t) { Write-Host "`n=== $t ===`n" -ForegroundColor Cyan }

Write-Section "Toolchain Check"

Write-Host "PowerShell:" $PSVersionTable.PSVersion

if (Get-Command py -ErrorAction SilentlyContinue) {
  Write-Host "py:" (& py -V)
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  Write-Host "python:" (& python -V)
} else {
  Write-Host "python: NOT FOUND"
}

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
  Write-Host "venv: present"
  . ".\.venv\Scripts\Activate.ps1"
  Write-Host "pip:" (pip --version)
  Write-Host "python:" (python -V)
  python -c "import pandas, networkx, PyPDF2; print('pandas', pandas.__version__); print('networkx', networkx.__version__); print('PyPDF2', PyPDF2.__version__)"
} else {
  Write-Host "venv: NOT FOUND (run bootstrap_windows.ps1)"
}

Write-Host "`nOptional (install separately):"
Write-Host "  - Neo4j Desktop"
Write-Host "  - Gephi"
Write-Host "  - Tesseract OCR + Poppler (for OCR pipeline)"
