# Task Scheduler (FIX11)
Build stamp (local): 2026-01-20 07:31:40

## Create 4x daily runs
Run:
- `L3\ops\MAKE_TASKS_4X_DAILY.bat`

Default times:
- 06:00
- 12:00
- 18:00
- 23:30

## Remove tasks
Run:
- `L3\ops\REMOVE_TASKS.bat`

## Command used
Prefers EXE if present:
- `F:\L3\gui\dist\LitigationOSLauncherGUI.exe --headless --search=auto --install --dest=F:\L3`

Fallback if EXE not present:
- `cmd.exe /c "F:\L3\LAUNCH_GUI.bat --headless --search=auto --install --dest=F:\L3"`

## Notes
- Tasks are created with interactive token behavior (runs only when you are logged in).
- This avoids storing any passwords in Task Scheduler.
