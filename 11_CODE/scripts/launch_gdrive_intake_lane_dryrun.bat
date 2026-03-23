\
@echo off
REM launch_gdrive_intake_lane_dryrun.bat - GDrive Intake (rclone) DRY RUN

setlocal ENABLEDELAYEDEXPANSION

set PYTHON_EXE=python
set BASE_DIR=F:\LitigationOS
set SCRIPT_DIR=%BASE_DIR%\code

echo GDrive Intake lane launcher (rclone) [DRY RUN]
echo ----------------------------------------------
echo Config file:
echo   %BASE_DIR%\config\gdrive_intake.json
echo.

if not exist "%BASE_DIR%\config\gdrive_intake.json" (
  echo [FAIL] Missing config: %BASE_DIR%\config\gdrive_intake.json
  echo Fix: unzip the bundle into %BASE_DIR% or copy the config into place.
  echo.
  pause
  exit /b 1
)

cd /d "%SCRIPT_DIR%"
echo Running DRY RUN (no sync/copy; no state update)...
"%PYTHON_EXE%" "%SCRIPT_DIR%\run_gdrive_intake_lane.py" --base-dir "%BASE_DIR%" --dry-run
echo.
echo Done. Check snapshots + delta under:
echo   %BASE_DIR%\intake\gdrive_snapshots
echo   %BASE_DIR%\intake\gdrive_deltas
echo   %BASE_DIR%\logs
echo.
pause
endlocal
