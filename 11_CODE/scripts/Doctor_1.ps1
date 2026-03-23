#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Section([string]$t) {
  Write-Output ""
  Write-Output ("=" * 84)
  Write-Output $t
  Write-Output ("=" * 84)
}

function TryCmd([string]$name, [string]$cmd) {
  Write-Output ("`n[$name] $cmd")
  try {
    $out = Invoke-Expression $cmd 2>&1
    if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
      Write-Output $out
      Write-Warning "$name exit code: $LASTEXITCODE"
    } else {
      Write-Output $out
    }
  } catch {
    Write-Warning "$name error: $($_.Exception.Message)"
  }
}

Section "AI Doctor — Environment"
TryCmd "pwsh" '$PSVersionTable | ConvertTo-Json -Depth 3'
TryCmd "os" '[System.Environment]::OSVersion.VersionString'
TryCmd "git"  'git --version'
TryCmd "node" 'node --version'
TryCmd "npm"  'npm --version'
TryCmd "python" 'python --version'
TryCmd "uv" 'uv --version'
TryCmd "uvx" 'uvx --version'
TryCmd "code" 'code --version'

Section "AI Doctor — VS Code Extensions (installed)"
TryCmd "extensions" 'code --list-extensions'

Section "AI Doctor — MCP Config"
TryCmd "mcp.json" 'if (Test-Path .vscode/mcp.json) { Get-Content -Raw .vscode/mcp.json } else { "MISSING .vscode/mcp.json" }'

Section "AI Doctor — MCP Smoke (help output)"
TryCmd "filesystem" 'npx -y @modelcontextprotocol/server-filesystem --help'
TryCmd "memory" 'npx -y @modelcontextprotocol/server-memory --help'
TryCmd "github" 'npx -y @modelcontextprotocol/server-github --help'
TryCmd "git (uvx)" 'uvx mcp-server-git --help'

Section "AI Doctor — Token presence (env only)"
if ($env:GITHUB_PERSONAL_ACCESS_TOKEN) {
  Write-Output "GITHUB_PERSONAL_ACCESS_TOKEN: PRESENT (length=$($env:GITHUB_PERSONAL_ACCESS_TOKEN.Length))"
} else {
  Write-Output "GITHUB_PERSONAL_ACCESS_TOKEN: MISSING"
}

Section "Done"


Write-Output "\nAgent Skills:"
Write-Output "- .github/skills present: $((Test-Path '.github/skills'))"
Write-Output "- chat.useAgentSkills should be true (see .vscode/settings.json)"
Write-Output "\nOptional MCP config: .vscode/mcp.optional.json (merge manually if needed)"
