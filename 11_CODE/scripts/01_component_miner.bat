@echo off
setlocal
cd /d "%~dp0..\apps"
python component_miner.py --roots E:\ F:\ --out "%~dp0..\component_manifest.json"
pause
