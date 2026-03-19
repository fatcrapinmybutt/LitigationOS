
@echo off
echo === BUILDING THE_PROGRAM (.exe + Setup) ===

:: Step 1: Compile Python GUI to EXE
pyinstaller --noconfirm --onefile --windowed --icon=fred.ico main_launcher.py

:: Step 2: Create installer folder if missing
if not exist dist_installer mkdir dist_installer

:: Step 3: Move output .exe to installer folder
copy dist\main_launcher.exe dist_installer\THE_PROGRAM_LAUNCHER.exe

:: Step 4: Compile NSIS Installer
makensis setup_the_program_main_launcher.nsi

echo === BUILD COMPLETE: THE_PROGRAM_LAUNCHER.exe + Setup_THE_PROGRAM.exe ===
pause
