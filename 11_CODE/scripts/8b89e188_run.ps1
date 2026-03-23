# Run FastAPI server (dev)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
cd $root\backend
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
