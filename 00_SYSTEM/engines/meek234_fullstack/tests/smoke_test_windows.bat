@echo off
setlocal enabledelayedexpansion
python MEEK234_FULLSTACK_REBUILD_v20260208_2.py --intake ".\_smoke_intake" --out ".\_smoke_out" --max-passes 3 --make-cyclepack >NUL
if exist ".\_smoke_out\latest\index.html" (
  echo SMOKE OK
  exit /b 0
) else (
  echo SMOKE FAILED
  exit /b 1
)
