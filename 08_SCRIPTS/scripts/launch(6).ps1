$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python .\runtime\launch.py
