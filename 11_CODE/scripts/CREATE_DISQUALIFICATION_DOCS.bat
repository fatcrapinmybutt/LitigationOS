@echo off
echo Creating Disqualification Motion Documents...
echo.

cd /d C:\Users\andre

python create_all_disqualification_docs_complete.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! All documents created in C:\Users\andre\FINAL_FILINGS
    echo.
    dir C:\Users\andre\FINAL_FILINGS
) else (
    echo.
    echo ERROR: Failed to create documents
)

pause
