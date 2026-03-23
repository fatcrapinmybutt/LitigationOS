@echo off
setlocal
cd /d %~dp0
echo.
echo TRUE_MASTER_BUCKET_ORGANIZER_v4 - APPLY (MUTATES FILES)
echo.
echo Close all apps that may be using files on target drives.
echo.
pause
python "%~dp0scripts\TRUE_MASTER_BUCKET_ORGANIZER_v4.py" --mode apply --drives auto --include-hidden --remove-empty-dirs
echo.
echo Done. Review per-drive outputs in BUCKET_15_NAME_COLLISIONS on each drive.
pause
