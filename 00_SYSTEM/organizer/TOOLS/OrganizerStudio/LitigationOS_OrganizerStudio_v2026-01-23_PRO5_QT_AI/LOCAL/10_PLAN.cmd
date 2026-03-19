@echo off
setlocal
cd /d %~dp0
call .venv\Scripts\activate
python ai_organizer_stack.py --config config.yaml --mode plan
pause
