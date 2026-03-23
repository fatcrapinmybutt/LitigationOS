$ErrorActionPreference="Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Resolve-Path (Join-Path $root "..\..")
$code = Join-Path $proj "04_CODE"
$out = Join-Path $proj "05_OUTPUTS"
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $code
python -m mi_scao_forms.cli crawl --mode safe --out $out
python -m mi_scao_forms.cli fetch --out $out
python -m mi_scao_forms.cli parse --out $out
python -m mi_scao_forms.cli compile --out $out
python -m mi_scao_forms.cli graph --out $out
python -m mi_scao_forms.cli packets --out $out
python -m mi_scao_forms.cli validate --out $out
Pop-Location
Write-Host "DONE. See 05_OUTPUTS\coverage_report.json"
