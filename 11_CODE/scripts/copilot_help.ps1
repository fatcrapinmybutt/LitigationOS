param()

$cp = Get-Command "copilot" -ErrorAction SilentlyContinue
if ($null -eq $cp) {
  Write-Host "copilot not found on PATH."
  Write-Host "If you expected it, confirm the GitHub.copilot-chat extension injected its copilotCli path into PATH for this terminal."
  exit 2
}

Write-Host "copilot path:" $cp.Source
Write-Host "Attempting: copilot --help"
& copilot --help
exit $LASTEXITCODE
