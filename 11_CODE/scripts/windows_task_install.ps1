Param(
  [string]$TaskName = "MBPPortalDaily",
  [string]$PortalCmd = "$PSScriptRoot\..\bin\mbp-portal.cmd",
  [string]$StartTime = "09:00"
)

# schtasks expects a single command line; use cmd.exe /c so operators like && work.
$Cmd = "cmd.exe /c `"`"$PortalCmd`" tick --reason daily && `"`"$PortalCmd`" worker`""

schtasks /Create /F /SC DAILY /TN $TaskName /TR $Cmd /ST $StartTime | Out-Null
Write-Host "Created/updated scheduled task: $TaskName at $StartTime"
