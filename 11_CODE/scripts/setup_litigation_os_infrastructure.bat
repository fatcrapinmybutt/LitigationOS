@echo off
REM LitigationOS Infrastructure Setup - Batch Script
REM This script creates the folder structure for LitigationOS Ultimate

echo ====================================
echo LitigationOS Infrastructure Setup
echo ====================================
echo.

REM Check if I: drive exists
if exist I:\ (
    echo I: drive FOUND - using as primary target
    set BASE_PATH=I:\LitigationOS-Ultimate
    echo Creating folder structure at %BASE_PATH%
) else (
    echo I: drive NOT FOUND - using C: drive fallback
    set BASE_PATH=C:\Users\andre\Desktop\LITIGATION_OS\LitigationOS-Ultimate
    echo Creating folder structure at %BASE_PATH%
)

echo.
echo Creating folders...

mkdir "%BASE_PATH%\01-Desktop-Copy\" 2>nul
echo Created: 01-Desktop-Copy
mkdir "%BASE_PATH%\02-F-Drive-Archives\" 2>nul
echo Created: 02-F-Drive-Archives
mkdir "%BASE_PATH%\03-G-Drive-CAPSTONE\" 2>nul
echo Created: 03-G-Drive-CAPSTONE
mkdir "%BASE_PATH%\04-Unified-Evidence\" 2>nul
echo Created: 04-Unified-Evidence
mkdir "%BASE_PATH%\05-Unified-Databases\" 2>nul
echo Created: 05-Unified-Databases
mkdir "%BASE_PATH%\06-Unified-AI-Agents\" 2>nul
echo Created: 06-Unified-AI-Agents
mkdir "%BASE_PATH%\07-Master-Index\" 2>nul
echo Created: 07-Master-Index
mkdir "%BASE_PATH%\08-Backup-History\" 2>nul
echo Created: 08-Backup-History
mkdir "%BASE_PATH%\09-Visualizations\" 2>nul
echo Created: 09-Visualizations
mkdir "%BASE_PATH%\10-Documentation\" 2>nul
echo Created: 10-Documentation
mkdir "%BASE_PATH%\11-Scripts\" 2>nul
echo Created: 11-Scripts
mkdir "%BASE_PATH%\12-Logs\" 2>nul
echo Created: 12-Logs

echo.
echo Verifying source paths...

if exist "C:\Users\andre\Desktop\LITIGATION_OS\" (
    echo OK: C:\Users\andre\Desktop\LITIGATION_OS
) else (
    echo MISSING: C:\Users\andre\Desktop\LITIGATION_OS
)

if exist "C:\Users\andre\Desktop\LITIGATION_OS\ALL_PC_EVIDENCE_EXTRACTED\" (
    echo OK: ALL_PC_EVIDENCE_EXTRACTED
) else (
    echo MISSING: ALL_PC_EVIDENCE_EXTRACTED
)

if exist "G:\CAPSTONE\" (
    echo OK: G:\CAPSTONE
) else (
    echo MISSING or NOT ACCESSIBLE: G:\CAPSTONE
)

if exist "F:\" (
    echo OK: F:\ drive exists
) else (
    echo MISSING or NOT ACCESSIBLE: F:\
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
pause
