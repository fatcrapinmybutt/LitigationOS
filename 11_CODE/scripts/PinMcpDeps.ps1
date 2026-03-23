#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
Pins MCP Node dependencies locally so you can avoid `npx -y <latest>` supply-chain drift.

Creates:
  tooling/mcp/package.json
  tooling/mcp/package-lock.json

Usage:
  pwsh tooling/ai/PinMcpDeps.ps1

Note: uses --save-exact so versions are pinned in the lockfile.
#>

$root = Resolve-Path .
$dir = Join-Path $root "tooling/mcp"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$pkg = @{
  name = "litigationos-mcp-tooling"
  private = $true
  version = "0.0.0"
  description = "Local pinned MCP server deps for VS Code/Copilot"
} | ConvertTo-Json -Depth 10

Set-Content -Path (Join-Path $dir "package.json") -Value $pkg -Encoding utf8

Push-Location $dir
try {
  npm install --save-exact @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-memory @modelcontextprotocol/server-everything @modelcontextprotocol/server-sequential-thinking
  Write-Output "Pinned MCP node deps installed under tooling/mcp/"
} finally {
  Pop-Location
}
