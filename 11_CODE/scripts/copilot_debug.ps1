param(
  [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

# Wrapper that runs copilot-debug if present, otherwise prints a helpful message.
$cd = Get-Command "copilot-debug" -ErrorAction SilentlyContinue
if ($null -eq $cd) {
  Write-Host "copilot-debug not found on PATH."
  Write-Host "If you installed GitHub Copilot Chat for VS Code, ensure the extension injected its debugCommand path into PATH for this terminal session."
  exit 2
}

Write-Host "Running: copilot-debug $($Args -join ' ')"
& copilot-debug @Args
exit $LASTEXITCODE
