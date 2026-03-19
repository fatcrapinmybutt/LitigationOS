@echo off
:: FRED-PRIME OS Launcher Script
:: Version: 2025.7.1
:: Purpose: Load FRED-PRIME OS high-level system structure into GUI interface

SET ROOT=F:\FRED-PRIME_OS_SYSTEMS_ONLY

:: Check that the core JSON and README exist
IF NOT EXIST "%ROOT%\FRED_PRIME_OS_STRUCTURE.json" (
    echo ❌ Error: OS structure file not found at %ROOT%\FRED_PRIME_OS_STRUCTURE.json
    pause
    exit /b
)

IF NOT EXIST "%ROOT%\README_OS_BOOT.md" (
    echo ❌ Error: README_OS_BOOT.md not found at %ROOT%
    pause
    exit /b
)

:: Launch the GUI or open fallback log
echo ✅ OS structure files validated.

:: Attempt to run GUI Python dashboard if present
IF EXIST "%ROOT%\central_dashboard.py" (
    echo 🚀 Launching Central Dashboard GUI...
    python "%ROOT%\central_dashboard.py"
) ELSE (
    echo ℹ️ No dashboard.py file found. Opening README instead...
    start notepad "%ROOT%\README_OS_BOOT.md"
)

exit /b
