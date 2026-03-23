@echo off
cls
echo ============================================================
echo    WATSON CASE - LITIGATIONOS DESKTOP LAUNCHER
echo    Pigors v. Watson (COA-366810)
echo ============================================================
echo.
echo Integration Status: COMPLETE (All 8 phases)
echo Case ID: watson-coa-366810
echo Evidence: 204,707 files (cataloged)
echo Documents: 4 analysis files (imported)
echo.
echo ============================================================
echo    LAUNCHING LITIGATIONOS...
echo ============================================================
echo.

cd /d "C:\Users\andre\Desktop\LitigationOS-Desktop"

echo [Step 1/2] Starting Backend Server...
echo          API will be available at http://localhost:3001
echo.
start "LitigationOS Backend" cmd /k "cd backend && npm start"

echo          Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul
echo          Backend startup initiated.
echo.

echo [Step 2/2] Starting Desktop Application...
echo          Electron window will open shortly...
echo.
cd electron-app
start "LitigationOS Desktop" cmd /k "npm start"

echo.
echo ============================================================
echo    LAUNCH COMPLETE!
echo ============================================================
echo.
echo Backend API: http://localhost:3001
echo Desktop App: Opening in Electron window...
echo.
echo Watson Case Data:
echo   - Case ID: watson-coa-366810
echo   - Database: backend\database\litigationos.db
echo   - Evidence: C:\Users\andre\Desktop\LITIGATION_OS\ALL_PC_EVIDENCE_EXTRACTED
echo   - AI Agents: C:\Users\andre\Desktop\LITIGATION_OS\AI_AGENTS
echo.
echo Neo4j Import (Optional):
echo   1. Open http://localhost:7474
echo   2. See WATSON_INTEGRATION_COMPLETE.md for Cypher script
echo.
echo Documentation:
echo   - WATSON_INTEGRATION_COMPLETE.md
echo   - WATSON_INTEGRATION_REPORT.json
echo.
echo ============================================================
echo.
echo You can close this window. Services will continue running.
echo To stop services, close the Backend and Desktop windows.
echo.
pause
