@echo off
echo ============================================
echo   Building LitigationOS Windows Installer
echo ============================================
echo.

echo [1/3] Installing build dependencies...
pip install pyinstaller --quiet

echo [2/3] Running PyInstaller build...
python build.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo BUILD FAILED — see errors above.
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo Output: dist\LitigationOS\LitigationOS.exe
echo.
pause
