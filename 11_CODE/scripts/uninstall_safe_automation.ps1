<# 
Uninstalls the scheduled task DriveIntegrityToolkit-SafeScan
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) { throw "Run as Administrator." }

$taskName = "DriveIntegrityToolkit-SafeScan"
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop | Out-Null
Write-Output "Uninstalled scheduled task: $taskName"
