@echo off
setlocal
cd /d "%~dp0.."
echo === PRELOAD ALL (ingest->cache->lenses->server) ===
python APP\preload_all.py --port 8899
