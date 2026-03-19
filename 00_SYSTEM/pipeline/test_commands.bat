@echo off
cd /d "C:\Users\andre\scans\tooling\"

echo === COMMAND 1: python -c "print('hello')" ===
timeout /t 5 /nobreak
python -c "print('hello')"
echo Exit Code: %ERRORLEVEL%
echo.

echo === COMMAND 2: config import ===
timeout /t 5 /nobreak
python -c "import sys; sys.path.insert(0,'.'); import config; print('config OK')"
echo Exit Code: %ERRORLEVEL%
echo.

echo === COMMAND 3: safety import ===
timeout /t 5 /nobreak
python -c "import sys; sys.path.insert(0,'.'); import safety; print('safety OK')"
echo Exit Code: %ERRORLEVEL%
echo.

echo === COMMAND 4: run_omega_pipeline import ===
timeout /t 5 /nobreak
python -c "import sys; sys.path.insert(0,'.'); import run_omega_pipeline; print('orchestrator OK')"
echo Exit Code: %ERRORLEVEL%
echo.

echo === COMMAND 5: python run_omega_pipeline.py --list-phases ===
timeout /t 5 /nobreak
python run_omega_pipeline.py --list-phases
echo Exit Code: %ERRORLEVEL%
echo.

echo === COMMAND 6: python run_omega_pipeline.py --dry-run --create-snapshot (30s timeout) ===
timeout /t 5 /nobreak
timeout /t 30 /nobreak
python run_omega_pipeline.py --dry-run --create-snapshot
echo Exit Code: %ERRORLEVEL%
