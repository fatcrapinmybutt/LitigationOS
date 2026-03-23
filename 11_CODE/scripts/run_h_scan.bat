@echo off
echo === Starting H:\ Drive Scan ===
echo.
python C:\Users\andre\Scans\extracts_full\h_drive_scanner.py > C:\Users\andre\Scans\extracts_full\scan_log.txt 2>&1
echo.
echo === Scan Complete ===
echo Output logged to: C:\Users\andre\Scans\extracts_full\scan_log.txt
echo.
type C:\Users\andre\Scans\extracts_full\scan_log.txt
pause
