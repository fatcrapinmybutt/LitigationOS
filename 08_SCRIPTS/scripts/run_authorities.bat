@echo off
setlocal
cd /d %~dp0
if not exist .venv (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_authorities.py
echo.
echo Authorities harvested to .\out\authorities_nodes.jsonl
pause
