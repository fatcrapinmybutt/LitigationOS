param(
  [Parameter(Mandatory=$true)][string]$LocalPath,
  [Parameter(Mandatory=$true)][string]$RemotePath,
  [switch]$Resync
)

$ErrorActionPreference = "Stop"

# rclone bisync: recommended for bidirectional sync. Read docs before use.
# First run requires --resync (dangerous if you point at the wrong places).

$cmd = @("rclone","bisync",$LocalPath,$RemotePath,"--verbose","--check-access","--fast-list")
if ($Resync) { $cmd += "--resync" }

Write-Host ($cmd -join " ")
& $cmd[0] $cmd[1..($cmd.Count-1)]
