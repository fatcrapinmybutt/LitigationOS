@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

:: === CONFIG ===
set "ALFIS_SCRIPT=F:\ALFIS.ps1"
set "STAGING_ROOT=F:\_Git_Staging"
set "BATCH_LOG=%STAGING_ROOT%\00_SYSTEM_CORE\_batch_execution_log.txt"
set "INGEST_DIR=F:\"
set "INCOMING_DIR=%STAGING_ROOT%\Incoming"
set "EXCLUDE_DIR=%STAGING_ROOT%"

:: === LOG START ===
echo =================================================== >> "%BATCH_LOG%"
echo [START] Batch Run: %DATE% %TIME% >> "%BATCH_LOG%"

:: === ENSURE PATHS EXIST ===
if not exist "%INCOMING_DIR%" mkdir "%INCOMING_DIR%"
if not exist "%STAGING_ROOT%\00_SYSTEM_CORE" mkdir "%STAGING_ROOT%\00_SYSTEM_CORE"

:: === VALIDATE ALFIS ===
IF NOT EXIST "%ALFIS_SCRIPT%" (
    echo [ERROR] ALFIS.ps1 not found at %ALFIS_SCRIPT% >> "%BATCH_LOG%"
    exit /b
)

:: === RECURSIVE INGEST ===
for /R "%INGEST_DIR%" %%F in (*) do (
    echo "%%F" | find /I "%EXCLUDE_DIR%" >nul
    if errorlevel 1 (
        echo [COPY] %%F → %INCOMING_DIR% >> "%BATCH_LOG%"
        xcopy "%%F" "%INCOMING_DIR%\" /Y /I /Q >nul
    )
)

:: === RUN ALFIS ===
powershell -ExecutionPolicy Bypass -File "%ALFIS_SCRIPT%" >> "%BATCH_LOG%" 2>&1

:: === LOG END ===
echo [END] Batch Run: %DATE% %TIME% >> "%BATCH_LOG%"
echo =================================================== >> "%BATCH_LOG%"
