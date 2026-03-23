#!/usr/bin/env pwsh
<#
terminal_env_doctor.ps1

Checks environment variables commonly injected by VS Code extensions and writes:
  Vault/90_REPORTS/terminal_env_doctor.json

Read-only. Never prints secrets; only checks existence and basic shapes.
#>

param(
  [string]$VaultRoot = "Vault"
)

$ErrorActionPreference = "Stop"

function Test-PathContains($pathValue, $needle) {
  if ([string]::IsNullOrWhiteSpace($pathValue)) { return $false }
  return $pathValue.ToLower().Contains($needle.ToLower())
}

$report = [ordered]@{
  generated_at = (Get-Date).ToString("o")
  os = $env:OS
  shell = "pwsh"
  copilot_chat = [ordered]@{
    path_has_debugCommand = Test-PathContains $env:PATH "github.copilot-chat\debugCommand"
    path_has_copilotCli  = Test-PathContains $env:PATH "github.copilot-chat\copilotCli"
    commands = [ordered]@{
      copilot_found = $null
      copilot_debug_found = $null
    }
  }
  gitlens_gk = [ordered]@{
    GK_GL_ADDR_present = -not [string]::IsNullOrWhiteSpace($env:GK_GL_ADDR)
    GK_GL_PATH_present = -not [string]::IsNullOrWhiteSpace($env:GK_GL_PATH)
    GK_GL_ADDR = $env:GK_GL_ADDR
    GK_GL_PATH = $env:GK_GL_PATH
  }
  vscode_git_askpass = [ordered]@{
    GIT_ASKPASS_present = -not [string]::IsNullOrWhiteSpace($env:GIT_ASKPASS)
    VSCODE_GIT_ASKPASS_NODE_present = -not [string]::IsNullOrWhiteSpace($env:VSCODE_GIT_ASKPASS_NODE)
    VSCODE_GIT_ASKPASS_MAIN_present = -not [string]::IsNullOrWhiteSpace($env:VSCODE_GIT_ASKPASS_MAIN)
    VSCODE_GIT_IPC_HANDLE_present = -not [string]::IsNullOrWhiteSpace($env:VSCODE_GIT_IPC_HANDLE)
  }
  warnings = @()
}

try { $report.copilot_chat.commands.copilot_found = (Get-Command copilot -ErrorAction Stop).Source } catch { }
try { $report.copilot_chat.commands.copilot_debug_found = (Get-Command copilot-debug -ErrorAction Stop).Source } catch { }

if (-not $report.copilot_chat.path_has_debugCommand -or -not $report.copilot_chat.path_has_copilotCli) {
  $report.warnings += "Copilot Chat PATH injectors not detected. Ensure github.copilot-chat is enabled and you're using the integrated terminal."
}

if (-not $report.vscode_git_askpass.GIT_ASKPASS_present) {
  $report.warnings += "GIT_ASKPASS not present (OK in CI). In VS Code, it should exist when vscode.git auth provider is active."
}

$outDir = Join-Path $VaultRoot "90_REPORTS"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir "terminal_env_doctor.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $outFile
Write-Host ("OK: wrote " + $outFile)
