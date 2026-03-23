# Windows PowerShell launcher (safe defaults)
# Usage: Right-click -> Run with PowerShell (or execute in PS)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundle = Split-Path -Parent $here
python (Join-Path $bundle "cli\LITIGATIONOS_PIPELINE.py") full
pause
