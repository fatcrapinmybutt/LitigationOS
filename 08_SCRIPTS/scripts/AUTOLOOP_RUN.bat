@echo off
title Litigation OS AutoLoop
echo [✓] Starting Litigation OS Full Automation Loop...
cd /d F:\SYSTEM

REM -- Step 1: Auto-Ingest
echo [1/6] Ingesting new files...
python auto_ingest_daemon_v9999.py

REM -- Step 2: Motion + Affidavit Generator
echo [2/6] Generating motions and affidavits...
python motion_generator.py
python affidavit_generator.py

REM -- Step 3: Exhibit Embedding + Binder Compilation
echo [3/6] Embedding exhibits and compiling binder...
python exhibit_embedder.py
python binder_compiler.py

REM -- Step 4: ZIP Compliance Validation
echo [4/6] Validating ZIP bundle...
python zip_validator.py

REM -- Step 5: SCAO Overlay Autofill
echo [5/6] Filling SCAO forms...
python scao_overlay_autofill.py

REM -- Step 6: Export and log
echo [6/6] Centralizing outputs...
move *.docx F:\LITIGATION_DRIVE\OUTPUTS\
move *.pdf  F:\LITIGATION_DRIVE\OUTPUTS\
move *.zip  F:\LITIGATION_DRIVE\ZIPS\
move *.log  F:\LITIGATION_DRIVE\LEGAL_RESULTS\

echo [✓] Automation loop completed.
pause
