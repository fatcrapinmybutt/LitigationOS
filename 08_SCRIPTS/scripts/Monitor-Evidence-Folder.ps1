$watchPath = "F:\FRED_EVIDENCE"
$tailGlobalLog = $true

Write-Host "`n📡 Monitoring $watchPath for activity..."

# Create and configure FileSystemWatcher
$watcher = New-Object IO.FileSystemWatcher $watchPath -Property @{
    IncludeSubdirectories = $true
    EnableRaisingEvents   = $true
}

# Register live file creation event
Register-ObjectEvent -InputObject $watcher -EventName Created -Action {
    $path = $Event.SourceEventArgs.FullPath
    Write-Host "[CREATED] $path"
} | Out-Null

# Tail latest GLOBAL_EVIDENCE_LOG if it exists
if ($tailGlobalLog) {
    $logFile = Get-ChildItem "$watchPath\GLOBAL_EVIDENCE_LOG_*.txt" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1

    if ($logFile) {
        Write-Host "`n📖 Tailing: $($logFile.Name)`n"
        Get-Content $logFile.FullName -Wait -Tail 20
    } else {
        Write-Warning "No GLOBAL_EVIDENCE_LOG found yet."
        # Keep script running even if no log exists
        while ($true) {
            Start-Sleep -Seconds 5
        }
    }
} else {
    # If tailing disabled, still keep console alive to show CREATED events
    while ($true) {
        Start-Sleep -Seconds 5
    }
}
