$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
if (Test-Path "$Root\.venv\Scripts\python.exe") { $Python = "$Root\.venv\Scripts\python.exe" }
if (!(Test-Path "$Root\config\config.json")) { throw "config.json not found" }
& $Python "$Root\litigationos_cli.py" ingest --config "$Root\config\config.json"
& $Python "$Root\litigationos_cli.py" ingest-corpus --config "$Root\config\config.json"
& $Python "$Root\litigationos_cli.py" run-contradictions --config "$Root\config\config.json"
& $Python "$Root\litigationos_cli.py" export-neo4j --config "$Root\config\config.json"
& $Python "$Root\litigationos_cli.py" export-html-offline --config "$Root\config\config.json"
Read-Host "Done. Press Enter"