$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
cd $root
.\.venv\Scripts\uvicorn backend.app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
