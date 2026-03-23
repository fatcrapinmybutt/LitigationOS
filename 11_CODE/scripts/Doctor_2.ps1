\
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section([string]$Title) {
  Write-Output ""
  Write-Output ("=" * 80)
  Write-Output $Title
  Write-Output ("=" * 80)
}

function Try-Cmd([string]$Name, [string]$Cmd) {
  Write-Output ("`n[$Name] $Cmd")
  try {
    $out = Invoke-Expression $Cmd 2>&1
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
      Write-Output $out
      Write-Error "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Output $out
  } catch {
    Write-Output $_.Exception.Message
  }
}

Write-Section "LitigationOS AI Doctor — Environment"
Try-Cmd "pwsh" '$PSVersionTable | ConvertTo-Json -Depth 3'
Try-Cmd "git"  'git --version'
Try-Cmd "node" 'node --version'
Try-Cmd "npm"  'npm --version'
Try-Cmd "python" 'python --version'
Try-Cmd "uv" 'uv --version'
Try-Cmd "uvx" 'uvx --version'

Write-Section "VS Code CLI"
Try-Cmd "code" 'code --version'
Try-Cmd "extensions" 'code --list-extensions'

Write-Section "MCP Smoke Tests (best-effort)"
Try-Cmd "npx-filesystem-help" 'npx -y @modelcontextprotocol/server-filesystem --help'
Try-Cmd "npx-memory-help" 'npx -y @modelcontextprotocol/server-memory --help'
Try-Cmd "npx-github-help" 'npx -y @modelcontextprotocol/server-github --help'
Try-Cmd "npx-postgres-help" 'npx -y @modelcontextprotocol/server-postgres --help'
Try-Cmd "uvx-git-help" 'uvx mcp-server-git --help'

Write-Section "Done"
