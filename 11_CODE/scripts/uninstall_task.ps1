param([string]$TaskName="WorldFirst_GDrive_Daily")
$ErrorActionPreference="Stop"
schtasks /Delete /TN $TaskName /F | Out-Null
Write-Host "Removed scheduled task: $TaskName"
