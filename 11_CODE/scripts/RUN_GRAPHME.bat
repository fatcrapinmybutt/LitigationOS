@echo off
setlocal enabledelayedexpansion
title GraphME — Folder→Graph CSV
chcp 65001 >nul
where python >nul 2>nul || (echo Python not found & pause & exit /b 1)
set ROOT=%1
if "%ROOT%"=="" set ROOT=F:\GRAPHME
echo Root: %ROOT%
python "tools\graphme_build.py" --root "%ROOT%" --unpack --out "GRAPHME" --hash
if errorlevel 1 (echo GraphME failed.& pause & exit /b 1)
echo Done. Outputs: GRAPHME_NODES.csv and GRAPHME_EDGES.csv
pause
