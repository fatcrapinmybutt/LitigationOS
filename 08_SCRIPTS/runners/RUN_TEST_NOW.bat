@echo off
REM Wrapper for running tests - minimal dependencies
setlocal enabledelayedexpansion
cd /d C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai
set PYTHONUTF8=1
set TRANSFORMERS_OFFLINE=1
set HF_HUB_OFFLINE=1
set HF_DATASETS_OFFLINE=1
python tests\_run_fileonly.py
echo Test script exited with code %ERRORLEVEL%
