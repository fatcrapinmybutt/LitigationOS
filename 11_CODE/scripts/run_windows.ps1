# Windows PowerShell runner
# Usage:
#   cd gateway
#   .\.venv\Scripts\Activate.ps1
#   $env:GATEWAY_TOKEN="your_token"
#   .\run_windows.ps1

$ErrorActionPreference = "Stop"

if (-not $env:GATEWAY_TOKEN) {
  Write-Host "ERROR: Set GATEWAY_TOKEN first." -ForegroundColor Red
  exit 1
}

$port = $env:GATEWAY_PORT
if (-not $port) { $port = "8787" }

python -m uvicorn ollama_gateway:APP --host 127.0.0.1 --port $port
