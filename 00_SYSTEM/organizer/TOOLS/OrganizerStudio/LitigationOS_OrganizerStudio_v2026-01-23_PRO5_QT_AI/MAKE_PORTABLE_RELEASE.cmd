@echo off
setlocal
cd /d %~dp0

echo Make portable release folder

if not exist dist (
  echo ERROR: dist folder not found. Build exe first using BUILD_EXE_QT.cmd
  pause
  exit /b 1
)

set OUT=portable_release
if exist %OUT% rmdir /s /q %OUT%

mkdir %OUT%
xcopy /e /i /y dist\OrganizerStudio %OUT%\OrganizerStudio >nul
copy README.md %OUT%\README.md >nul
copy LICENSE.txt %OUT%\LICENSE.txt >nul

echo Portable release created at %OUT%\OrganizerStudio
pause
