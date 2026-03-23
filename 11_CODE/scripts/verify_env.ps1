param()

Write-Host "=== VS Code / Copilot Terminal Environment Verification ==="
Write-Host "Time (UTC):" ([DateTime]::UtcNow.ToString("o"))
Write-Host ""

$vars = @(
  "GK_GL_ADDR","GK_GL_PATH",
  "GIT_ASKPASS","VSCODE_GIT_ASKPASS_NODE","VSCODE_GIT_ASKPASS_EXTRA_ARGS","VSCODE_GIT_ASKPASS_MAIN","VSCODE_GIT_IPC_HANDLE"
)

Write-Host "---- Key environment variables ----"
foreach ($v in $vars) {
  $val = [Environment]::GetEnvironmentVariable($v)
  if ($null -eq $val) { $val = "" }
  Write-Host ("{0}={1}" -f $v, $val)
}
Write-Host ""

Write-Host "---- Command availability ----"
$cmds = @("copilot","copilot-debug","code","git","python","py")
foreach ($c in $cmds) {
  $found = Get-Command $c -ErrorAction SilentlyContinue
  if ($null -eq $found) {
    Write-Host ("{0}: NOT FOUND" -f $c)
  } else {
    Write-Host ("{0}: {1}" -f $c, $found.Source)
  }
}
Write-Host ""

Write-Host "---- PATH includes Copilot Chat extension dirs? ----"
$path = $env:PATH
$needles = @("github.copilot-chat","debugCommand","copilotCli")
foreach ($n in $needles) {
  if ($path -match [regex]::Escape($n)) { Write-Host ("FOUND: {0}" -f $n) } else { Write-Host ("MISSING: {0}" -f $n) }
}
Write-Host ""

Write-Host "Done."
