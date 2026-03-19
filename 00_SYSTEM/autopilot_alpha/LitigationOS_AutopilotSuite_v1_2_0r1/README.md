# LitigationOS AutopilotSuite v1.2.0r1

This package upgrades the runtime to:
- authority→vehicle edges (corpus-driven)
- vehicle→court routing
- operating-order pin gates
- lane-first Bloom perspectives
- directory-safe Tesseract discovery for OCR

## Run (Windows)
```powershell
scripts\setup_windows.ps1
scripts\run_autopilot.ps1
```

## Pass Tesseract directory (your case)
```powershell
$env:TESSERACT_CMD="C:\Users\andre\Downloads\tesseract-main"
.\.venv\Scripts\python.exe .\src\litigationos_autopilot.py --in-dir . --out-dir .\out --emit-graphml
```

## Build EXE
```powershell
scripts\build_exe_windows.ps1
```
