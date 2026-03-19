
@echo off
echo Creating THE_PROGRAM_LAUNCHER.exe with pyinstaller...
pyinstaller --noconfirm --onefile --windowed --icon=fred.ico main_launcher.py
echo.
echo Build complete. Copying to installer directory...
mkdir dist_installer
copy dist\THE_PROGRAM_LAUNCHER.exe dist_installer\
echo Done.
pause
