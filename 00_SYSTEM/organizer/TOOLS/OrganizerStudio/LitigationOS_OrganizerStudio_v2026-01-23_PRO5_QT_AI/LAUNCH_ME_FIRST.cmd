@echo off
setlocal
cd /d %~dp0

echo LitigationOS Drive Rename Test Fix Suite
echo Choose lane:
echo   [L] LOCAL drive organizer (Windows paths)
echo   [G] GDRIVE organizer (scoped Google Drive folder ID)
choice /c LG /n /m "Select L or G: "
if errorlevel 2 goto GDRIVE
if errorlevel 1 goto LOCAL

:LOCAL
echo Launching LOCAL lane
cd LOCAL
call 00_SETUP.cmd
call 30_SELF_TEST.cmd
echo Next: run 10_PLAN.cmd to generate a plan, then 15_VALIDATE.cmd, then 20_APPLY.cmd
pause
exit /b 0

:GDRIVE
echo Launching GDRIVE lane
cd GDRIVE
call 00_SETUP.cmd
call 30_SELF_TEST.cmd
echo Next: run 10_PLAN.cmd to generate a plan, then 15_VALIDATE.cmd, then 20_APPLY.cmd
pause
exit /b 0
