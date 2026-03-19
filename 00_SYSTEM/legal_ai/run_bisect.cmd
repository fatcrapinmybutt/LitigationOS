@echo off
setlocal enabledelayedexpansion

REM Set environment variables
set PYTHONUTF8=1
set TRANSFORMERS_OFFLINE=1
set HF_HUB_OFFLINE=1

REM Change to legal_ai directory
cd /d "C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai"

REM Run the bisect script
python tests\_bisect.py

REM Check if output file was created
if exist "tests\_bisect_out.txt" (
    echo.
    echo ============ BISECT OUTPUT FILE FOUND ============
    echo.
    type "tests\_bisect_out.txt"
) else (
    echo.
    echo ============ BISECT OUTPUT FILE NOT FOUND ============
    echo.
    echo Checking files in tests directory:
    dir /b "tests\*.*"
)

endlocal
