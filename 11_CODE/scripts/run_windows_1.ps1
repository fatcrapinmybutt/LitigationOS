param(
  [Parameter(Mandatory=$true)][string]$InputPath,
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$TesseractExe = ""
)

$ErrorActionPreference = "Stop"

# Try to auto-detect tesseract.exe if not provided
if ([string]::IsNullOrWhiteSpace($TesseractExe)) {
  $candidates = @(
    "$env:ProgramFiles\Tesseract-OCR\tesseract.exe",
    "$env:ProgramFiles(x86)\Tesseract-OCR\tesseract.exe",
    "$env:USERPROFILE\Downloads\tesseract.exe",
    "$env:USERPROFILE\Downloads\tesseract-main\tesseract.exe",
    "$env:USERPROFILE\Downloads\tesseract-main\bin\tesseract.exe"
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { $TesseractExe = $c; break }
  }
}

Write-Host "Input:" $InputPath
Write-Host "Out:" $OutDir
if (-not [string]::IsNullOrWhiteSpace($TesseractExe)) { Write-Host "Tesseract:" $TesseractExe }

# Create venv (idempotent)
$venv = Join-Path $OutDir ".venv"
if (-not (Test-Path $venv)) {
  python -m venv $venv
}

$py = Join-Path $venv "Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install pymupdf pillow pytesseract

$script = Join-Path $PSScriptRoot "harvest_ocr_extract.py"

if ([string]::IsNullOrWhiteSpace($TesseractExe)) {
  & $py $script --inputs $InputPath --out $OutDir
} else {
  & $py $script --inputs $InputPath --out $OutDir --tesseract $TesseractExe
}
