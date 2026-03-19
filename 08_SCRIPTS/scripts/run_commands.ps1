$env:PYTHONUTF8=1
Set-Location C:\Users\andre\LitigationOS\00_SYSTEM\tools

Write-Host "=== STEP 1: Current Directory ===" -ForegroundColor Green
Get-Location

Write-Host "`n=== STEP 2: Running env-check ===" -ForegroundColor Green
python safe_shell.py env-check

Write-Host "`n=== STEP 3: Running shadow-audit ===" -ForegroundColor Green
python safe_shell.py shadow-audit

Write-Host "`n=== STEP 4: Running check command ===" -ForegroundColor Green
python safe_shell.py check C:\Users\andre\LitigationOS\00_SYSTEM\org_agents\__init__.py
