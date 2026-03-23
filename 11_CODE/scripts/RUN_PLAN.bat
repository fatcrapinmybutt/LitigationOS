@echo off
setlocal
cd /d %~dp0
echo.
echo TRUE_MASTER_BUCKET_ORGANIZER_v4 - PLAN
echo.
python "%~dp0scripts\TRUE_MASTER_BUCKET_ORGANIZER_v4.py" --mode plan --drives auto --include-hidden
echo.
echo Done. Review per-drive outputs in BUCKET_15_NAME_COLLISIONS on each drive.
pause
