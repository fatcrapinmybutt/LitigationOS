@echo off
setlocal
cd /d %~dp0
python compile_seed.py --in FormRegistry_seed.json --outdir compiled_out
echo.
echo Done. Outputs in compiled_out\
pause
