@echo off
SETLOCAL ENABLEEXTENSIONS

:: Step 1: Kill any existing Python processes
taskkill /IM python.exe /F >nul 2>&1

:: Step 2: Remove existing Python 3.12 installation
rd /s /q "%LocalAppData%\Programs\Python\Python312"
del /f /q "%LocalAppData%\Programs\Python\Launcher\py.exe"

:: Step 3: Download and install Python 3.13.5 with pip
set PYTHON_INSTALLER=python-3.13.5-amd64.exe
set DOWNLOAD_URL=https://www.python.org/ftp/python/3.13.5/%PYTHON_INSTALLER%
curl -L -o %PYTHON_INSTALLER% %DOWNLOAD_URL%

start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1

:: Step 4: Verify installation
python --version
python -m pip --version

:: Step 5: Clean up
if exist %PYTHON_INSTALLER% del %PYTHON_INSTALLER%

ENDLOCAL
pause
