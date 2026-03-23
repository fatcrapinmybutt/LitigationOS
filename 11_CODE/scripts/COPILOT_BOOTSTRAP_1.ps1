#requires -Version 7.0
<#
COPILOT_BOOTSTRAP.ps1

One-command local bootstrap for any repo:
- Applies Copilot+MCP pack (non-destructive)
- Optionally installs recommended extensions

Run from the repo root (or any subfolder):
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\COPILOT_BOOTSTRAP.ps1

Optional:
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\COPILOT_BOOTSTRAP.ps1 -InstallExtensions
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

[CmdletBinding()]
param([switch]$InstallExtensions)

Write-Output "Bootstrap: applying Copilot+MCP pack..."
& pwsh -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "tooling/ai/ApplyPack.ps1") -Mode all -InstallExtensions:$InstallExtensions

Write-Output ""
Write-Output "Bootstrap complete."
Write-Output "In VS Code: run Tasks → 'AI: Doctor (env + MCP + Copilot)' to verify."
