Write-Output "=== STEP 1: Kill stale Python process 11016 ==="
Stop-Process -Id 11016 -Force -ErrorAction SilentlyContinue
Write-Output "Process termination attempted (if it existed)"
Write-Output ""

Write-Output "=== STEP 2: Check for previous result file ==="
if (Test-Path "C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt") {
    Write-Output "PREVIOUS RESULT FILE EXISTS:"
    Get-Content "C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt"
} else {
    Write-Output "NO PREVIOUS RESULT FILE"
}
Write-Output ""

Write-Output "=== STEP 3: Running organize engine in LIVE mode ==="
$env:PYTHONUTF8 = "1"
cd C:\Users\andre\LitigationOS\00_SYSTEM\tools
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\_run_live.py

Write-Output ""
Write-Output "=== STEP 4: Read result file after completion ==="
Write-Output "LIVE RESULT:"
if (Test-Path "C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt") {
    Get-Content "C:\Users\andre\LitigationOS\00_SYSTEM\tools\_live_result.txt"
} else {
    Write-Output "Result file not found"
}
Write-Output ""

Write-Output "=== STEP 5: Show last 30 lines of organize log ==="
Write-Output "ORGANIZE LOG (last 30 lines):"
if (Test-Path "C:\Users\andre\LitigationOS\00_SYSTEM\organize_log.csv") {
    Get-Content "C:\Users\andre\LitigationOS\00_SYSTEM\organize_log.csv" -Tail 30
} else {
    Write-Output "Organize log file not found"
}
Write-Output ""

Write-Output "=== STEP 6: Count remaining root-level files ==="
$count = (Get-ChildItem "C:\Users\andre\LitigationOS" -File -ErrorAction SilentlyContinue).Count
Write-Output "Remaining root-level files: $count"
