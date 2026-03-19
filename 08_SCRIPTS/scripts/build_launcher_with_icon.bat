
@echo off
echo === BUILDING THE_PROGRAM_LAUNCHER.EXE WITH ICON ===
pyinstaller --noconfirm --onefile --windowed --icon=fred.ico main_launcher.py
echo.
echo === COPY OUTPUT TO INSTALLER DIRECTORY ===
mkdir dist_installer
copy dist\THE_PROGRAM_LAUNCHER.exe dist_installer\
echo === BUILD COMPLETE ===
pause
