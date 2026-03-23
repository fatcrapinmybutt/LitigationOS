\
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Output "MCP Validate — best-effort smoke tests"
Write-Output "Workspace: $(Resolve-Path .)"

$tests = @(
  @{ name = "filesystem"; cmd = "npx -y @modelcontextprotocol/server-filesystem --help" },
  @{ name = "memory"; cmd = "npx -y @modelcontextprotocol/server-memory --help" },
  @{ name = "github"; cmd = "npx -y @modelcontextprotocol/server-github --help" },
  @{ name = "git"; cmd = "uvx mcp-server-git --help" }
)

foreach ($t in $tests) {
  Write-Output "`n== $($t.name) =="
  try {
    $out = Invoke-Expression $t.cmd 2>&1
    Write-Output $out
  } catch {
    Write-Warning "$($t.name) failed: $($_.Exception.Message)"
  }
}
Write-Output "`nDone."
