
@echo off
echo === AUTO-BUILDING FRED_COMMAND_CENTER ===

:: Step 1: Compile GUI Dashboard to .exe
pyinstaller --noconfirm --onefile --windowed --icon=fred.ico FRED_COMMAND_CENTER.py

:: Step 2: Ensure installer folder exists
if not exist dist_installer mkdir dist_installer

:: Step 3: Move compiled EXE to installer folder
copy dist\FRED_COMMAND_CENTER.exe dist_installer\

:: Step 4: Add to Registry (this will be merged manually or by script logic)

:: Step 5: Build NSIS installer
makensis setup_the_program_main_launcher.nsi

echo === FRED_COMMAND_CENTER integrated and compiled ===
pause
