@echo off
setlocal
cd /d "%~dp0..\apps"
REM Edit the paths below to point to your real scripts on F:\ or E:\ once located
REM Example:
REM set ORG=F:\LitigationOS\OMNI_UNIFIED_DRIVE_ORGANIZER_UPGRADED.py
REM set HV=F:\LitigationOS\HARVEST_ENGINE_FULL.py
set ORG=
set HV=
python mbp_unified_launcher.py --roots E:\ F:\ --organizer-script "%ORG%" --harvest-script "%HV%" --harvest-unpack-archives --harvest-extract-text --harvest-sqlite --harvest-integrity hash --harvest-resume
pause
