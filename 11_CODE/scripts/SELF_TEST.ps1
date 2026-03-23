$ErrorActionPreference="Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "Python:" -ForegroundColor Cyan
python --version

Write-Host "Pip packages:" -ForegroundColor Cyan
python -c "import pypdf, pdfminer, pypdfium2, pytesseract, sentence_transformers, qdrant_client; print('OK')"

Write-Host "FTS smoke test:" -ForegroundColor Cyan
$testDir = Join-Path $root "tests\data"
New-Item -ItemType Directory -Force -Path $testDir | Out-Null
Set-Content -Path (Join-Path $testDir "hello.txt") -Value "Hello Lincoln. This is a test document." -Encoding UTF8

python -m litos_harvest.main --config (Join-Path $root "config\harvest_config.json") --root $testDir --run-id "TEST" --out (Join-Path $root ".out\TEST")

python -m litos_harvest.query --run-dir (Join-Path $root ".out\TEST") --query "Lincoln"

Write-Host "Self-test complete." -ForegroundColor Green
