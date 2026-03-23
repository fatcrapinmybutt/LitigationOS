@echo off
echo ========================================
echo EMERGENCY MOTIONS CREATION SCRIPT
echo Andrew Pigors - 14th Circuit Court
echo ========================================
echo.

REM Create directory structure
echo Creating directory structure...
mkdir "C:\Users\andre\FINAL_FILINGS\EMERGENCY_MOTIONS\PROPOSED_ORDERS" 2>nul
echo ✓ Directories created
echo.

REM Run Python scripts to create all documents
echo Creating motion documents...
python "C:\Users\andre\create_emergency_motions.py"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Error creating motions
    pause
    exit /b 1
)
echo.

echo Creating proposed orders...
python "C:\Users\andre\create_proposed_orders.py"
if %ERRORLEVEL% NEQ 0 (
    echo ✗ Error creating proposed orders
    pause
    exit /b 1
)
echo.

REM Copy filing guide to the emergency motions folder
echo Copying filing guide...
copy "C:\Users\andre\EMERGENCY_MOTIONS_FILING_GUIDE.md" "C:\Users\andre\FINAL_FILINGS\EMERGENCY_MOTIONS\" >nul 2>&1
echo ✓ Filing guide copied
echo.

REM List created files
echo ========================================
echo FILES CREATED:
echo ========================================
dir /B "C:\Users\andre\FINAL_FILINGS\EMERGENCY_MOTIONS"
echo.
echo PROPOSED ORDERS:
dir /B "C:\Users\andre\FINAL_FILINGS\EMERGENCY_MOTIONS\PROPOSED_ORDERS"
echo.
echo ========================================
echo CREATION COMPLETE
echo ========================================
echo.
echo Location: C:\Users\andre\FINAL_FILINGS\EMERGENCY_MOTIONS
echo.
echo Next steps:
echo 1. Review all motions and fill in placeholders
echo 2. Review EMERGENCY_MOTIONS_FILING_GUIDE.md
echo 3. Get motions notarized
echo 4. File with 14th Circuit Court
echo.
pause
