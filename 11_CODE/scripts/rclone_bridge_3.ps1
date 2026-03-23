Param(
  [Parameter(Position=0)][string]$Command = "doctor",
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$Python = $null

function Find-Python {
  if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
  if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
  return $null
}

$Python = Find-Python
if ($Python) {
  $cmdLine = "$Python `"$Root\tools\rclone_bridge.py`" --root `"$Root`" $Command"
  if ($Args) { $cmdLine = $cmdLine + " " + ($Args -join " ") }
  Write-Host "[rclone_bridge.ps1] -> $cmdLine"
  iex $cmdLine
  exit $LASTEXITCODE
}

# Fallback: call rclone directly (policy gate is NOT enforced here). Prefer using cmd/py.
$rclone = Join-Path $Root "APP\Tools\RcloneBridge\bin\rclone.exe"
if (-not (Test-Path $rclone)) {
  $rclone = (Get-Command rclone -ErrorAction SilentlyContinue).Source
}
if (-not $rclone) { throw "rclone not found. Place rclone.exe in APP\Tools\RcloneBridge\bin or in PATH." }

Write-Host "[fallback] Running rclone directly: $rclone" 
& $rclone @($Command) @($Args)
exit $LASTEXITCODE
