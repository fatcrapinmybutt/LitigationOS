Param(
  [string]$Mode = "plan"  # plan | apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Stage($msg) {
  Write-Host ""
  Write-Host "=== $msg ==="
}

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Here

Write-Stage "1) Ensuring Python is available"
try {
  $py = (Get-Command python -ErrorAction Stop).Source
} catch {
  Write-Host "Python not found on PATH."
  Write-Host "Install Python 3.x (Microsoft Store or python.org), then re-run."
  exit 2
}

Write-Stage "2) Creating/using venv"
$VenvDir = Join-Path $Here ".venv"
if (!(Test-Path $VenvDir)) {
  & python -m venv $VenvDir
}
$PyExe = Join-Path $VenvDir "Scripts\python.exe"

Write-Stage "3) Installing deps"
& $PyExe -m pip install --upgrade pip
& $PyExe -m pip install -r (Join-Path $Here "requirements.txt")

Write-Stage "4) Optional: ensure Ollama (two automated attempts)"
$HasOllama = $false
try { if (Get-Command ollama -ErrorAction Stop) { $HasOllama = $true } } catch { $HasOllama = $false }

if (-not $HasOllama) {
  Write-Host "Ollama not found. Attempt 1: winget install Ollama.Ollama"
  try {
    if (Get-Command winget -ErrorAction Stop) {
      & winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    }
  } catch { }

  try { if (Get-Command ollama -ErrorAction Stop) { $HasOllama = $true } } catch { $HasOllama = $false }
}

if (-not $HasOllama) {
  Write-Host "Attempt 2: choco install ollama"
  try {
    if (Get-Command choco -ErrorAction Stop) {
      & choco install ollama -y
    }
  } catch { }

  try { if (Get-Command ollama -ErrorAction Stop) { $HasOllama = $true } } catch { $HasOllama = $false }
}

if ($HasOllama) {
  Write-Host "Ollama detected."
  try {
    Write-Host "Attempting to pull the default open model: qwen2.5:3b"
    & ollama pull qwen2.5:3b
  } catch { }
} else {
  Write-Host "Ollama not installed. The organizer will run in heuristic mode unless you set --llm none explicitly."
}


Write-Stage "4b) Optional: ensure rclone (two automated attempts) — useful for Google Drive mounts/sync"
$HasRclone = $false
try { if (Get-Command rclone -ErrorAction Stop) { $HasRclone = $true } } catch { $HasRclone = $false }

if (-not $HasRclone) {
  Write-Host "rclone not found. Attempt 1: winget install Rclone.Rclone"
  try {
    if (Get-Command winget -ErrorAction Stop) {
      & winget install -e --id Rclone.Rclone --accept-package-agreements --accept-source-agreements
    }
  } catch { }

  try { if (Get-Command rclone -ErrorAction Stop) { $HasRclone = $true } } catch { $HasRclone = $false }
}

if (-not $HasRclone) {
  Write-Host "Attempt 2: choco install rclone"
  try {
    if (Get-Command choco -ErrorAction Stop) {
      & choco install rclone -y
    }
  } catch { }

  try { if (Get-Command rclone -ErrorAction Stop) { $HasRclone = $true } } catch { $HasRclone = $false }
}

if ($HasRclone) {
  Write-Host "rclone detected."
} else {
  Write-Host "rclone not installed. That's OK unless you want automated Drive mount/sync."
}

Write-Stage "5) Running organizer"
$Config = Join-Path $Here "config.yaml"

if ($Mode -eq "plan") {
  & $PyExe (Join-Path $Here "ai_file_organizer.py") --config $Config --llm auto
} elseif ($Mode -eq "apply") {
  # Apply uses the newest RUN folder automatically.
  & $PyExe (Join-Path $Here "ai_file_organizer.py") --config $Config --llm auto --apply --use-latest-plan
} else {
  Write-Host "Unknown mode: $Mode (use plan|apply)"
  exit 3
}

Write-Stage "DONE"
