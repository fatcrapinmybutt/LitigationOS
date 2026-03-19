@echo off
REM Autonomous Litigation OS Runner - Authorities harvest
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
python run_authorities.py
echo Done.
pause
