$drive = Get-Volume -FileSystemLabel "LITIGATION_DRIVE"
$hostname = $env:COMPUTERNAME
$hardwareID = $drive.UniqueId.Guid
$lockfile = "F:\LITIGATION_DRIVE\SYSTEM\hardware_lock.json"

$lock = @{
    hostname = $hostname
    drive_signature = $hardwareID
    enforced = $true
}

$lock | ConvertTo-Json | Out-File -Encoding UTF8 $lockfile
Write-Host "Hardware Lock Applied to $hostname with Volume GUID: $hardwareID"
