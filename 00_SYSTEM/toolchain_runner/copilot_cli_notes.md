# Copilot CLI notes (optional)

You can run the same commands inside Copilot CLI. Two helpful patterns:

1) Run local shell commands by prefixing with `!`:
   ! powershell -NoProfile -ExecutionPolicy Bypass -File .\bootstrap_windows.ps1
   ! powershell -NoProfile -ExecutionPolicy Bypass -File .\run_cycle0.ps1 -InDir "..." -OutDir ".\out_cycle0"

2) Allow Copilot file access in your repo/workdir:
   /add-dir C:\Users\andre\Desktop\THE_LITIGATION_OPERATING_SYSTEM
