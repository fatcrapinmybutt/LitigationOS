# Agent HQ — How to Use (VS Code Copilot, Ω∞)
Date: 2026-02-28

This repo uses **VS Code custom agents** detected from `.github/agents/*.agent.md`. citeturn0search0turn0search2

## 1) Install/enable
- Ensure files exist:
  - `.github/copilot-instructions.md` (repo-wide instructions) citeturn0search4turn0search6
  - `.github/agents/*.agent.md` (custom agents) citeturn0search0turn0search2
  - `.github/instructions/*.instructions.md` (path-scoped instructions for Copilot coding agent) citeturn0search5turn0search6

## 2) Agent file schema
Agent files can use YAML frontmatter fields:
- name
- description
- argument-hint
- tools
- model
- handoffs
- agents (subagents list) citeturn0search0turn0search2

## 3) MCP tools
Configure MCP servers via `.vscode/mcp.json` so the Governor can call tools (filesystem, fetch, github, LitigationOS MCP). citeturn1search0turn1search1
See `docs/MCP_SETUP.md`.

## 4) Run pattern
Start with **Governor (Ω∞)**. Use handoffs to switch agents for each stage (harvest → specs → AKN → stacks → lint/PASS → export → release). citeturn0search2


## VS Code Profile (repo-safe)
This repo includes `.vscode/settings.jsonc` + `.vscode/extensions.json` and a local-only `.vscode/settings.local.jsonc` pattern for secrets.
