@echo off
echo ======================================
echo  AUTONOMOS Subsystem Setup
echo ======================================

echo Creating directories...
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos" 2>nul
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel" 2>nul
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor" 2>nul
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared" 2>nul
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db" 2>nul
mkdir "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests" 2>nul

echo Creating __init__.py files...
echo """AUTONOMOS — autonomos package."""> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\__init__.py"
echo """AUTONOMOS — sentinel package."""> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel\__init__.py"
echo """AUTONOMOS — inquisitor package."""> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor\__init__.py"
echo """AUTONOMOS — shared package."""> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared\__init__.py"
echo.> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db\.gitkeep"
echo.> "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests\__init__.py"

echo Creating result file...
(
echo AUTONOMOS Subsystem - Directory Creation Results
echo =================================================
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel\
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\inquisitor\
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\shared\
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\db\
echo Created: C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\tests\
echo Created: autonomos\__init__.py
echo Created: autonomos\sentinel\__init__.py
echo Created: autonomos\inquisitor\__init__.py
echo Created: autonomos\shared\__init__.py
echo Created: autonomos\db\.gitkeep
echo Created: autonomos\tests\__init__.py
echo.
echo --- Verification ---
) > "C:\Users\andre\LitigationOS\00_SYSTEM\_mkdirs_result.txt"

if exist "C:\Users\andre\LitigationOS\00_SYSTEM\autonomos\sentinel" (
    echo OK: All directories created >> "C:\Users\andre\LitigationOS\00_SYSTEM\_mkdirs_result.txt"
) else (
    echo FAILED: Directory creation failed >> "C:\Users\andre\LitigationOS\00_SYSTEM\_mkdirs_result.txt"
)
echo DONE >> "C:\Users\andre\LitigationOS\00_SYSTEM\_mkdirs_result.txt"

echo.
echo ======================================
echo  Setup complete! Check _mkdirs_result.txt
echo ======================================
pause
