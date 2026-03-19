@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate

echo Enter scoped folder ID to organize (required). This must not be root
set /p RID=ROOT_ID:
python gdrive_scoped_organizer.py --mode plan --root-id "%RID%"
pause
