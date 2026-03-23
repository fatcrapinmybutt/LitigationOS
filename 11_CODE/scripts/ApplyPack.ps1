\
#requires -Version 7.0
<#
Applies the Copilot+MCP pack to the current repository with backups and merges.

Usage:
  pwsh tooling/ai/ApplyPack.ps1 -Mode workspace
  pwsh tooling/ai/ApplyPack.ps1 -Mode all -Force

Modes:
  workspace  -> writes/merges repo workspace files (.vscode, .github, tooling, docs)
  user       -> emits guidance for VS Code Profile / Settings Sync (no system modifications)
  all        -> workspace + optional extension install (if -InstallExtensions)

Safety:
- Non-destructive by default: merges JSON, preserves existing markdown, writes backups.
- Use -Force to overwrite specific files if needed.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

[CmdletBinding()]
param(
  [ValidateSet("workspace","user","all")]
  [string]$Mode = "workspace",
  [switch]$Force,
  [switch]$InstallExtensions
)

function RepoRoot {
  $p = Resolve-Path .
  while ($p -and -not (Test-Path (Join-Path $p ".git"))) {
    $parent = Split-Path $p -Parent
    if ($parent -eq $p) { break }
    $p = $parent
  }
  if (-not (Test-Path (Join-Path $p ".git"))) {
    # allow non-git workspaces but warn
    return (Resolve-Path .)
  }
  return $p
}

$root = RepoRoot
Set-Location $root

$backupRoot = Join-Path $root ".litigationos_backups"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $backupRoot $stamp
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

function Backup-File([string]$Path) {
  if (Test-Path $Path) {
    $rel = $Path.TrimStart('\','/')
    $dest = Join-Path $backupDir $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent) | Out-Null
    Copy-Item -Force $Path $dest
  }
}

function DeepMerge($baseObj, $patchObj) {
  foreach ($prop in $patchObj.PSObject.Properties) {
    $name = $prop.Name
    $pval = $prop.Value
    if ($null -eq $baseObj.$name) {
      $baseObj | Add-Member -NotePropertyName $name -NotePropertyValue $pval -Force
      continue
    }
    $bval = $baseObj.$name
    # hashtables/PSCustomObject
    if (($bval -is [hashtable] -or $bval -is [pscustomobject]) -and ($pval -is [hashtable] -or $pval -is [pscustomobject])) {
      DeepMerge $bval $pval
    } elseif (($bval -is [System.Collections.IList]) -and ($pval -is [System.Collections.IList])) {
      # union lists (stable)
      $set = New-Object 'System.Collections.Generic.HashSet[string]'
      $out = New-Object 'System.Collections.Generic.List[object]'
      foreach ($x in $bval) { $k = "$x"; if ($set.Add($k)) { $out.Add($x) } }
      foreach ($x in $pval) { $k = "$x"; if ($set.Add($k)) { $out.Add($x) } }
      $baseObj.$name = $out
    } else {
      # preserve existing unless Force explicitly requested
      if ($Force) { $baseObj.$name = $pval }
    }
  }
  return $baseObj
}

function Write-Text([string]$Path, [string]$Content) {
  New-Item -ItemType Directory -Force -Path (Split-Path $Path -Parent) | Out-Null
  Set-Content -Path $Path -Value $Content -Encoding UTF8
}

function Merge-JsonFile([string]$Path, [string]$JsonContent) {
  $patch = $JsonContent | ConvertFrom-Json -Depth 100
  $targetObj = $null
  if (Test-Path $Path) {
    $raw = Get-Content -Raw -Path $Path -Encoding UTF8
    try { $targetObj = $raw | ConvertFrom-Json -Depth 100 } catch { $targetObj = [pscustomobject]@{} }
  } else {
    $targetObj = [pscustomobject]@{}
  }
  $merged = DeepMerge $targetObj $patch
  $out = $merged | ConvertTo-Json -Depth 100
  Write-Text $Path $out
}

function Merge-Markdown([string]$Path, [string]$NewContent) {
  if (-not (Test-Path $Path) -or $Force) {
    Write-Text $Path $NewContent
    return
  }
  $old = Get-Content -Raw -Path $Path -Encoding UTF8
  if ($old -match [regex]::Escape($NewContent.Trim())) {
    return
  }
  $merged = @()
  $merged += $NewContent.TrimEnd()
  $merged += ""
  $merged += "## Legacy (preserved)"
  $merged += ""
  $merged += "> This section was preserved from the pre-existing file when applying the pack."
  $merged += ""
  $merged += $old.TrimEnd()
  Write-Text $Path ($merged -join "`n")
}

# Embedded pack files (text + json) — kept deliberately minimal & reproducible.
# If you want to add more files, add them here and rerun ApplyPack.
$filesText = @{
  ".github/copilot-instructions.md" = @"
# Copilot Instructions — LitigationOS (Repo-level)

## Prime directive
- **Discover, don’t guess.** Only document patterns you can prove from the repo.
- **Append-only bias.** Prefer new files + wiring over renames/moves. If you must refactor, ship a migration.
- **Traceability first.** Derived outputs must be reproducible and referenced by a manifest/run log.
- **Truth discipline.** Never invent facts (especially legal facts). If missing: label unknown + add a discovery plan.

## 10-minute onboarding (agent workflow)
1) Read: `AGENTS.md` and `docs/REPO_MAP.md` (generate via `tooling/ai/RepoMap.ps1` if missing).
2) Locate entrypoints by inspection:
   - `package.json` scripts, PowerShell CLIs, Python CLIs, `.vscode/tasks.json`.
3) Identify the “golden path” workflow and its artifacts:
   - ingest → extract → structure → validate → graph → draft → package.

## Repo conventions (LitigationOS style)
- **Evidence ≠ argument ≠ conclusion**
  - Evidence atoms are immutable (stable IDs + provenance).
  - Arguments cite authority as proposition → authority → pinpoint.
  - Conclusions are only as strong as evidence + authority support.
- Prefer structured artifacts over free-form prose:
  - schemas (`schemas/`), registries, JSONL logs, deterministic manifests.
- Separate “analysis voice” (internal) from “filing voice” (court-facing).

## Safety & security
- Never commit secrets. Use env vars; redact tokens in logs.
- MCP servers are local code. Treat them as part of your supply chain: least privilege + allowlists.

## If you’re stuck
- Run **AI: Doctor (env + MCP + Copilot)** and use its output to diagnose.
- Regenerate `docs/REPO_MAP.md`, then propose the smallest high-leverage change that improves correctness → reproducibility → traceability.
"@
  "AGENTS.md" = @"
# AGENTS — LitigationOS Operating Rules

## Mission
Turn documents → structured facts/evidence → graph → drafting/packaging outputs, with reproducibility and traceability.

## Non-negotiables
1) No hallucinations: unknowns must remain unknown until supported.
2) Append-only bias: add new files; avoid renames unless a migration exists.
3) Deterministic outputs: stable ordering, stable IDs, explicit seeds when needed.
4) Traceability: every run writes a log and a manifest (inputs, outputs, counts, timestamps).

## Golden path (how to operate here)
- Prefer VS Code tasks as the canonical “run” interface (`.vscode/tasks.json`).
- When adding capability:
  1) Schema (`schemas/`)
  2) Tool (PowerShell/Python) in `tooling/`
  3) Task wiring
  4) Docs update (`docs/REPO_MAP.md`, `docs/tools/*.md`)

## Diagnostics
- Run `tooling/ai/Doctor.ps1` to emit environment + MCP health.
- Run `tooling/ai/ValidateMcp.ps1` to smoke-test MCP server commands.

## MCP
- MCP config lives at `.vscode/mcp.json`.
- Use least-privileged allowlists and do not widen filesystem scope beyond the repo unless explicitly required.
"@
  ".github/instructions/general.instructions.md" = @"
---
applyTo: ""**""
---
Operate in LitigationOS mode:

- Discover patterns from files; do not assume project commands.
- Prefer append-only changes and deterministic outputs.
- Log and manifest all derived artifacts.
- Never invent facts or legal assertions; label unknowns + add a discovery plan.
"@
  ".github/instructions/powershell.instructions.md" = @"
---
applyTo: ""**/*.ps1""
---
PowerShell 7 conventions:

- Begin automation scripts with:
  - `Set-StrictMode -Version Latest`
  - `$ErrorActionPreference = 'Stop'`
- Prefer advanced functions (`[CmdletBinding()]`) with validated parameters.
- Log structured output (JSON/JSONL or key=value). Avoid `Write-Host` except UX.
- Add `-WhatIf`/`-Confirm` semantics for destructive actions when feasible.
- Exit non-zero on failure; never silently ignore errors.
"@
  ".github/instructions/python.instructions.md" = @"
---
applyTo: ""**/*.py""
---
Python conventions:

- Deterministic ordering for outputs; stable IDs for derived artifacts.
- Separate pure logic from I/O; prefer explicit types.
- For parsing/OCR: preserve raw extracts, and derive normalized artifacts with provenance.
- Return sensible exit codes for CLIs.
"@
  ".github/instructions/json.instructions.md" = @"
---
applyTo: ""**/*.{json,jsonc,jsonl}""
---
JSON/JSONL conventions:

- Keep configs machine-readable; avoid comments unless JSONC is explicitly used.
- Prefer stable key ordering in generated JSON to minimize diffs.
- For JSONL logs: one object per line, include timestamp, tool, workspace, and summary counts.
"@
  ".github/instructions/legal-drafting.instructions.md" = @"
---
applyTo: ""**/*.md""
---
Legal/drafting markdown conventions:

- Separate **FACTS** (assertions) from **EVIDENCE** (exhibits/atoms) from **AUTHORITY** (rule/statute/case) from **ARGUMENT**.
- Do not write conclusions unsupported by the repo record.
- Use stable IDs for evidence atoms and cross-reference consistently.
"@
  ".github/prompts/01-repomap.prompt.md" = @"
# Prompt: Generate/Update docs/REPO_MAP.md

Goal: create a 1-page repo map so an AI agent can become productive immediately.

Rules:
- Only document commands you can prove from repo files (`package.json`, `pyproject.toml`, `.vscode/tasks.json`, scripts).
- Provide a component table: component, path, purpose, inputs, outputs.
- Identify the “golden path” workflow: ingest → extract → structure → validate → graph → draft → package.
"@
  ".github/prompts/02-autopatch.prompt.md" = @"
# Prompt: Apply Copilot+MCP Pack (Agent Mode)

You are in VS Code Copilot **Agent mode**.

Do this:
1) Run the VS Code task: **AI: Apply Copilot+MCP Pack (non-destructive)**.
2) Then run: **AI: Doctor (env + MCP + Copilot)**.
3) Open `docs/REPO_MAP.md` and fill in meanings by inspecting the discovered entrypoints (do not guess).

If tasks are missing, create `.vscode/tasks.json` by reading `tooling/ai/ApplyPack.ps1` (it prints the expected tasks list).
"@
  ".github/prompts/03-mcp-debug.prompt.md" = @"
# Prompt: MCP Debugging

Produce a diagnosis report with:
- `.vscode/mcp.json` parse validity
- server start commands and stderr/stdout
- filesystem allowlist sanity check
- token presence check (env vars only)
- minimal reproduction steps
Then propose the smallest fix.
"@
  ".github/prompts/04-new-tool-wizard.prompt.md" = @"
# Prompt: New Tool Wizard

Create a new deterministic tool with:
- Schema in `schemas/`
- Implementation in `tooling/`
- Task in `.vscode/tasks.json`
- Logs + manifest outputs
- Minimal docs in `docs/tools/<tool>.md`
"@
}

$filesJson = @{
  ".vscode/extensions.json" = @"
{
  ""recommendations"": [
    ""GitHub.copilot"",
    ""GitHub.copilot-chat"",
    ""ms-vscode.powershell"",
    ""eamodio.gitlens"",
    ""GitHub.vscode-pull-request-github"",
    ""GitHub.vscode-github-actions"",
    ""redhat.vscode-yaml"",
    ""yzhang.markdown-all-in-one"",
    ""davidanson.vscode-markdownlint"",
    ""streetsidesoftware.code-spell-checker"",
    ""gruntfuggly.todo-tree"",
    ""alefragnani.project-manager"",
    ""ms-vscode.remote-repositories"",
    ""ms-vscode-remote.remote-ssh"",
    ""ms-azuretools.vscode-docker"",
    ""ms-python.python"",
    ""ms-python.vscode-pylance""
  ]
}
"@
  ".vscode/tasks.json" = @"
{
  ""version"": ""2.0.0"",
  ""tasks"": [
    {
      ""label"": ""AI: Apply Copilot+MCP Pack (non-destructive)"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/ApplyPack.ps1"",
        ""-Mode"",
        ""workspace""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Install Recommended Extensions"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/InstallExtensions.ps1""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Doctor (env + MCP + Copilot)"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/Doctor.ps1""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Validate MCP Servers (smoke tests)"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/ValidateMcp.ps1""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Generate Repo Map"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/RepoMap.ps1""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Index Mode = PERF (faster)"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/ToggleIndexMode.ps1"",
        ""-Mode"",
        ""perf""
      ],
      ""problemMatcher"": []
    },
    {
      ""label"": ""AI: Index Mode = MAX (more context)"",
      ""type"": ""shell"",
      ""command"": ""pwsh"",
      ""args"": [
        ""-NoProfile"",
        ""-ExecutionPolicy"",
        ""Bypass"",
        ""-File"",
        ""${workspaceFolder}/tooling/ai/ToggleIndexMode.ps1"",
        ""-Mode"",
        ""max""
      ],
      ""problemMatcher"": []
    }
  ]
}
"@
  ".vscode/launch.json" = @"
{
  ""version"": ""0.2.0"",
  ""configurations"": [
    {
      ""name"": ""Debug PowerShell Script (current file)"",
      ""type"": ""PowerShell"",
      ""request"": ""launch"",
      ""script"": ""${file}"",
      ""cwd"": ""${workspaceFolder}"",
      ""args"": [],
      ""internalConsoleOptions"": ""neverOpen""
    }
  ]
}
"@
  ".vscode/settings.json" = @"
{
  ""github.copilot.nextEditSuggestions.enabled"": true,
  ""editor.codeActions.triggerOnFocusChange"": true,
  ""editor.inlineSuggest.enabled"": true,
  ""files.trimTrailingWhitespace"": true,
  ""files.insertFinalNewline"": true,
  ""files.autoSave"": ""onFocusChange"",
  ""chat.includeApplyingInstructions"": true,
  ""chat.includeReferencedInstructions"": true,
  ""chat.useAgentsMdFile"": true,
  ""chat.useNestedAgentsMdFiles"": true
}
"@
  ".vscode/mcp.json" = @"
{
  ""servers"": {
    ""filesystem"": {
      ""command"": ""npx"",
      ""args"": [
        ""-y"",
        ""@modelcontextprotocol/server-filesystem"",
        "".""
      ]
    },
    ""memory"": {
      ""command"": ""npx"",
      ""args"": [
        ""-y"",
        ""@modelcontextprotocol/server-memory""
      ]
    },
    ""github"": {
      ""command"": ""npx"",
      ""args"": [
        ""-y"",
        ""@modelcontextprotocol/server-github""
      ],
      ""env"": {
        ""GITHUB_PERSONAL_ACCESS_TOKEN"": ""${env:GITHUB_PERSONAL_ACCESS_TOKEN}""
      }
    },
    ""git"": {
      ""command"": ""uvx"",
      ""args"": [
        ""mcp-server-git"",
        ""--repository"",
        "".""
      ]
    }
  }
}
"@
}

# Apply
Write-Output "Applying pack to: $root"
Write-Output "Backups stored at: $backupDir"
foreach ($kv in $filesText.GetEnumerator()) {
  $path = Join-Path $root $kv.Key
  Backup-File $path
  Merge-Markdown $path $kv.Value.TrimStart("`r","`n")
}

foreach ($kv in $filesJson.GetEnumerator()) {
  $path = Join-Path $root $kv.Key
  Backup-File $path
  Merge-JsonFile $path $kv.Value
}

Write-Output "Pack files applied."

if ($Mode -eq "all" -and $InstallExtensions) {
  & pwsh -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "tooling/ai/InstallExtensions.ps1")
}

Write-Output "Done."
