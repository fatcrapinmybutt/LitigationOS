@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-core.txt
python -m mbp_truemaster gui
