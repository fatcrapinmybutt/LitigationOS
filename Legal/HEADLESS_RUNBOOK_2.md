# Headless mode (FIX10)
Build stamp (local): 2026-01-20 07:20:40

## Purpose
Run without UI for:
- Task Scheduler
- Batch automation
- Single EXE usage

## Flags
- `--headless`                      : enable headless mode
- `--search=auto|drive|folder`      : scope
- `--drive=X:\`                    : used when `--search=drive`
- `--folder=C:\path`               : used when `--search=folder`
- `--dest=F:\L3`                   : install destination
- `--install`                       : perform non-destructive install/sync before run
- `--no-run`                        : do not run pipeline
- `--open-docs`                     : open primary docs after completion
- `--no-logfile`                    : disable headless log file

## Examples
### 1) Install to F:\L3 then run pipeline (preferred)
`LitigationOSLauncherGUI.exe --headless --install --dest=F:\L3 --search=auto`

### 2) Run pipeline only (no install)
`LitigationOSLauncherGUI.exe --headless --search=auto`

### 3) Search a specific drive then run
`LitigationOSLauncherGUI.exe --headless --search=drive --drive=F:\`

### 4) Search a specific folder then run
`LitigationOSLauncherGUI.exe --headless --search=folder --folder=C:\L3pack`

## Logs
By default a logfile is written to:
- `<root>\sp\headless\headless_YYYYMMDD_HHMMSS.log`
