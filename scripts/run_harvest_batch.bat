@echo off
REM Run harvest batch as a standalone process with logging
REM Usage: run_harvest_batch.bat [batch_size]
REM Default batch_size: 100

set BATCH_SIZE=%1
if "%BATCH_SIZE%"=="" set BATCH_SIZE=100

set DB=C:\Users\andre\LitigationOS\litigation_context.db
set ENGINE=C:\Users\andre\LitigationOS\00_SYSTEM\engines\harvest_go\harvest.exe
set LOG=C:\Users\andre\LitigationOS\logs\harvest_batch_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%.log

echo [%date% %time%] Starting batch of %BATCH_SIZE% files >> "%LOG%" 2>&1
"%ENGINE%" -db "%DB%" batch %BATCH_SIZE% >> "%LOG%" 2>&1
echo [%date% %time%] Batch complete. Exit code: %ERRORLEVEL% >> "%LOG%" 2>&1

REM Show final status
"%ENGINE%" -db "%DB%" status >> "%LOG%" 2>&1
