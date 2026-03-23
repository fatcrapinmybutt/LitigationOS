#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

.\.venv\Scripts\Activate.ps1

if (-not (Test-Path engine_config.json)) {
  python -m engine.cli init --config engine_config.json | Out-Null
}

python -m engine.cli --config engine_config.json harvest --with-rclone
