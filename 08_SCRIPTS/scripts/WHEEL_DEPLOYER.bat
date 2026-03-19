@echo off
setlocal ENABLEEXTENSIONS

:: === CONFIG ===
set "WHEEL_DIR=Z:\site-packages\wheels"
set "TARGET_DIR=Z:\site-packages\Python311\site-packages"
set "PYTHON=python"

echo.
echo [🚀] Beginning portable wheel installation...

:: === CREATE FOLDERS IF MISSING ===
if not exist "%WHEEL_DIR%" (
    echo [📁] Creating wheel directory...
    mkdir "%WHEEL_DIR%"
)

if not exist "%TARGET_DIR%" (
    echo [📁] Creating target site-packages...
    mkdir "%TARGET_DIR%"
)

:: === MOVE TO WHEEL FOLDER ===
cd /d "%WHEEL_DIR%"
if errorlevel 1 (
    echo [❌] Failed to change directory to %WHEEL_DIR%
    pause
    exit /b 1
)

:: === INSTALL ALL WHEELS ===
echo [📦] Installing all wheels into portable site-packages...
%PYTHON% -m pip install *.whl --no-cache-dir --force-reinstall --target="%TARGET_DIR%" > install_log.txt 2>&1
if errorlevel 1 (
    echo [❌] pip install failed. Check install_log.txt
    pause
    exit /b 1
)

echo.
echo [✅] All dependencies installed successfully to %TARGET_DIR%
pause
