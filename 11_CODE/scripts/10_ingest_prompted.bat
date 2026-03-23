@echo off
setlocal
cd /d "%~dp0.."
echo === INGEST FILESYSTEM TO GRAPH ===
echo You will be prompted for a root folder if --root is not provided.
python TOOLS\ingest_filesystem_to_graph.py
pause
