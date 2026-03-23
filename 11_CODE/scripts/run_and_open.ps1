$ErrorActionPreference = "Stop"
    python --version
    Write-Host "[+] Building Nucleus Wheel v3..." -ForegroundColor Cyan
    python ".\scripts\nucleus_wheel_builder.py" --config ".\config.yaml"
    Write-Host "[+] Opening latest viewer..." -ForegroundColor Cyan
    python ".\scripts\open_latest.py"
