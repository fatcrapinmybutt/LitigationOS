@echo off
set SCRIPT=F:\AI_SUPRA_ORGANIZER.ps1

echo Running AI_SUPRA_ORGANIZER.ps1...

powershell -NoExit -ExecutionPolicy Bypass -NoProfile -Command "& '%SCRIPT%'"

echo.
echo If you see this message, the script completed or encountered an error.
echo Check F:\LITIGATION_SCAFFOLD_AI\_MANIFESTS\ for output logs.
pause
