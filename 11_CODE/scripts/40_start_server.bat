@echo off
setlocal
cd /d "%~dp0.."
echo === START SUPERGRAPH SERVER ===
echo Open: http://127.0.0.1:8899/
python APP\server.py --port 8899
