$ErrorActionPreference = "Stop"
    python --version
    Write-Host "[+] Building Nucleus Wheel v3..." -ForegroundColor Cyan
    python ".\scripts\nucleus_wheel_builder.py" --config ".\config.yaml"
    Write-Host "[+] Done. See OUT/NUCLEUS_WHEEL_*" -ForegroundColor Green
