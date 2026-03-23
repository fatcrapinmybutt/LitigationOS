@echo off
setlocal
cd /d %~dp0\..
if not exist .venv\Scripts\python.exe (
  echo ERROR: venv missing. Create it:
  echo   python -m venv .venv
  echo   .\.venv\Scripts\Activate.ps1
  echo   python -m pip install -r requirements.txt
  exit /b 2
)
.venv\Scripts\python.exe run_pipeline.py merge --base-nodes ..\inputs\uploaded\nodes.csv --base-edges ..\inputs\uploaded\edges.csv --rels ..\inputs\uploaded\rels.csv --authorities-edges ..\inputs\uploaded\authorities_edges.csv --nucleus-nodes ..\inputs\uploaded\NUCLEUS_APEX_SUPERGRAPH_20250908_030140_nodes.csv --nucleus-edges ..\inputs\uploaded\NUCLEUS_APEX_SUPERGRAPH_20250908_030140_edges.csv --out out
if errorlevel 1 exit /b %errorlevel%
echo.
echo PASS: merged graph payload written to CANONICAL_KERNEL_v2026_01_17\out\neo4j_admin
endlocal
