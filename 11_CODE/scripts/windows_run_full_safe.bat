@echo off
setlocal
set BUNDLE=%~dp0..
python "%BUNDLE%\cli\LITIGATIONOS_PIPELINE.py" full
pause
