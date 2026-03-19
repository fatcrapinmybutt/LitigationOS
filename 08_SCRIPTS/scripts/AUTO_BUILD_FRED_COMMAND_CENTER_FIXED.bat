
@echo off
cd /d F:\

echo === AUTO-BUILDING FRED_COMMAND_CENTER ===

:: Step 1: Compile GUI Dashboard to .exe
pyinstaller --noconfirm --onefile --windowed --icon=F:\fred.ico F:\FRED_COMMAND_CENTER.py

:: Step 2: Ensure installer folder exists
if not exist F:\dist_installer mkdir F:\dist_installer

:: Step 3: Move compiled EXE to installer folder
copy /y F:\dist\FRED_COMMAND_CENTER.exe F:\dist_installer\

:: Step 4: Build NSIS installer (Update path if NSIS isn't in PATH)
"C:\Program Files (x86)\NSIS\makensis.exe" F:\setup_the_program_main_launcher.nsi

echo === FRED_COMMAND_CENTER integrated, compiled, and packed ===
pause
