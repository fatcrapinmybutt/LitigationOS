#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Output "MCP Validate — best-effort smoke tests"
Write-Output "Workspace: $(Resolve-Path .)"

$tests = @(
  @{ name = "filesystem"; cmd = "npx -y @modelcontextprotocol/server-filesystem --help" },
  @{ name = "memory"; cmd = "npx -y @modelcontextprotocol/server-memory --help" },
  @{ name = "everything"; cmd = "npx -y @modelcontextprotocol/server-everything --help" },
  @{ name = "sequential_thinking"; cmd = "npx -y @modelcontextprotocol/server-sequential-thinking --help" },
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

Write-Output "`nNote: GitHub MCP is configured as a remote HTTP server in .vscode/mcp.json."
Write-Output "Connectivity/auth is validated by VS Code when you start the server in the Copilot UI."
Write-Output "`nDone."
