$ErrorActionPreference="Stop"
# Tries to install the popular Windows build. Requires winget.
$wg = Get-Command winget -ErrorAction SilentlyContinue
if (!$wg) { throw "winget not found. Install App Installer from Microsoft Store or install Tesseract manually." }

# UB Mannheim distribution is commonly used on Windows.
winget install --id UB-Mannheim.TesseractOCR -e --source winget
Write-Host "Installed. Re-open your terminal so PATH updates." -ForegroundColor Green
