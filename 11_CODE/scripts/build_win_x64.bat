\
@echo off
setlocal

cd /d %~dp0\..

if not exist .venv (
  echo [ERROR] .venv missing. Create venv and install requirements first.
  exit /b 2
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconfirm --clean --name LitigationOS --onedir --windowed app\main.py

echo Done: dist\LitigationOS\
endlocal
