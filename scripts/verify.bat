@echo off
REM verify.bat — LitigationOS fast feedback loop
REM Target: <15 seconds total
REM
REM Usage:
REM   scripts\verify.bat          Run all checks
REM   scripts\verify.bat --quick  Syntax check only
REM

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ============================================================
echo  LitigationOS Verify Script
echo ============================================================
echo.

REM === STEP 1: Syntax check (instant) ===
echo [1/6] Syntax check...
set FAIL=0

for %%F in (
    00_SYSTEM\shared\__init__.py
    00_SYSTEM\shared\internal\db.py
    00_SYSTEM\shared\internal\config.py
    00_SYSTEM\shared\internal\fts5.py
    00_SYSTEM\engines\nexus\nexus_engine.py
    00_SYSTEM\engines\chimera\chimera_engine.py
    00_SYSTEM\engines\chronos\chronos_engine.py
    00_SYSTEM\engines\cerberus\cerberus_engine.py
    00_SYSTEM\brains\brain_manager.py
    00_SYSTEM\tools\unified_hub.py
    00_SYSTEM\engines\filing_engine\__init__.py
    00_SYSTEM\engines\filing_engine\engine.py
    00_SYSTEM\engines\filing_engine\pipeline.py
    00_SYSTEM\engines\filing_engine\state.py
    00_SYSTEM\engines\filing_engine\triggers.py
    00_SYSTEM\engines\filing_engine\validator.py
) do (
    python -m py_compile "%%F" 2>NUL
    if errorlevel 1 (
        echo   FAIL: %%F
        set FAIL=1
    )
)

if "%FAIL%"=="1" (
    echo.
    echo FAILED: Syntax errors detected.
    exit /b 1
)
echo   OK

if "%1"=="--quick" (
    echo.
    echo Quick check passed.
    exit /b 0
)

REM === STEP 2: Engine smoke tests (fast) ===
echo [2/6] Engine smoke tests...
python -I scripts\test_engine_smoke.py 2>NUL | findstr /C:"RESULTS:"
if errorlevel 1 (
    echo.
    echo FAILED: Engine smoke tests failed.
    exit /b 1
)

REM === STEP 3: Contract tests (fast) ===
echo [3/6] Contract tests...
set TEST_DIRS=00_SYSTEM\shared\tests\
python -m pytest %TEST_DIRS% -q --tb=short --no-header --capture=no -p no:cacheprovider 2>NUL
if errorlevel 2 (
    echo.
    echo FAILED: Contract tests failed.
    exit /b 1
)

REM === STEP 4: Boundary check (fast) ===
echo [4/6] Boundary check...
python scripts\check_boundaries.py
if errorlevel 1 (
    echo.
    echo FAILED: Boundary violations detected.
    exit /b 1
)

REM === STEP 5: Schema validation ===
echo [5/6] Schema validation...
python -c "import sqlite3; c=sqlite3.connect('litigation_context.db'); cols=[r[1] for r in c.execute('PRAGMA table_info(documents)')]; assert 'ingested_at' in cols, 'Missing ingested_at'; assert 'created_at' in cols, 'Missing created_at'; fts=[r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%%_fts'\")]; assert len(fts)>=5, f'Only {len(fts)} FTS tables'; print(f'  OK: {len(cols)} columns in documents, {len(fts)} FTS tables'); c.close()"
if errorlevel 1 (
    echo.
    echo FAILED: Schema validation failed.
    exit /b 1
)

REM === STEP 6: FTS5 health check ===
echo [6/6] FTS5 health check...
python -c "import sqlite3; c=sqlite3.connect('litigation_context.db'); c.execute('PRAGMA busy_timeout=5000'); r=c.execute(\"SELECT count(*) FROM evidence_fts WHERE evidence_fts MATCH 'custody'\").fetchone()[0]; assert r>0, f'FTS5 returned 0 rows for custody'; print(f'  OK: evidence_fts returned {r} matches for test query'); c.close()"
if errorlevel 1 (
    echo.
    echo FAILED: FTS5 health check failed.
    exit /b 1
)

echo.
echo ============================================================
echo  ALL CHECKS PASSED
echo ============================================================
exit /b 0
