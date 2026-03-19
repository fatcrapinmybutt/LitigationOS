param(
  [string]$ConfigPath = "$(Join-Path $PSScriptRoot '..\config\harvest_config.json')"
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$s){ Write-Host "`n=== $s ===`n" -ForegroundColor Cyan }

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Section "0) Workspace + config"
if (!(Test-Path $ConfigPath)) { throw "Config not found: $ConfigPath" }
$cfg = Get-Content $ConfigPath -Raw | ConvertFrom-Json

$workDir = Join-Path $root ".work"
$outDir  = Join-Path $root ".out"
New-Item -ItemType Directory -Force -Path $workDir,$outDir | Out-Null

Write-Section "1) Build HARVEST_ROOT hub (junctions only)"
$hub = Join-Path $root $cfg.hub.relative_path
if (Test-Path $hub) { Remove-Item $hub -Recurse -Force }
New-Item -ItemType Directory -Force -Path $hub | Out-Null

function New-Junction([string]$dst, [string]$src){
  if (!(Test-Path $src)) { return }
  if (Test-Path $dst) { return }
  cmd /c "mklink /J `"$dst`" `"$src`"" | Out-Null
}

foreach ($t in $cfg.targets) {
  $label = if ($cfg.hub.junction_labels) { $t.label } else { (Split-Path $t.path -Leaf) }
  $dst = Join-Path $hub $label
  New-Junction $dst $t.path
}

Write-Section "2) Python environment"
# Prefer py launcher if available
$py = $null
try { $py = (Get-Command py -ErrorAction Stop).Source } catch { }
if ($py) {
  $pythonCmd = "py -3"
} else {
  $pythonCmd = "python"
}

# Create venv
$venv = Join-Path $root ".venv"
if (!(Test-Path $venv)) {
  & $pythonCmd -m venv $venv
}

# Activate
$activate = Join-Path $venv "Scripts\Activate.ps1"
. $activate

python -m pip install --upgrade pip wheel setuptools

Write-Section "3) Install Python dependencies (free)"
pip install -r (Join-Path $root "requirements.txt")

# Install this package (editable)
pip install -e $root

Write-Section "4) Optional: start Qdrant (Docker) if available"
$wantQdrant = $cfg.index.qdrant
if ($wantQdrant) {
  try {
    $docker = (Get-Command docker -ErrorAction Stop).Source
    & (Join-Path $PSScriptRoot "START_QDRANT.ps1") -Root $root | Out-Null
  } catch {
    Write-Host "Docker not found; continuing with SQLite FTS only." -ForegroundColor Yellow
  }
}

Write-Section "5) Optional: OCR engine presence"
if ($cfg.ocr.enabled) {
  try {
    $tess = (Get-Command tesseract -ErrorAction Stop).Source
  } catch {
    Write-Host "Tesseract not found; OCR will be skipped. (You can run scripts\INSTALL_TESSERACT.ps1)" -ForegroundColor Yellow
  }
}

Write-Section "6) Run harvest"
$runId = (Get-Date).ToString("yyyyMMdd_HHmmss")
$runOut = Join-Path $outDir $runId
New-Item -ItemType Directory -Force -Path $runOut | Out-Null

python -m litos_harvest.main --config "$ConfigPath" --root "$hub" --run-id "$runId" --out "$runOut"

Write-Section "7) Done"
Write-Host ("Outputs: " + $runOut) -ForegroundColor Green
Write-Host ("Open: " + (Join-Path $runOut "DASHBOARD.md")) -ForegroundColor Green
Write-Host ("Next LLM prompt: " + (Join-Path $runOut "NEXT_PROMPT.md")) -ForegroundColor Green
