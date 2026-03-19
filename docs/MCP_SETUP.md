# MCP Setup (VS Code) — LitigationOS Event Horizon Δ∞
Date: 2026-02-28

VS Code can load MCP server configs from **`.vscode/mcp.json`** and expose MCP tools to Copilot Agent mode. citeturn1search0turn1search1

## This repo ships a workspace MCP config
- `.vscode/mcp.json` (workspace-scoped)
- servers included:
  - `github` (remote) — for GitHub MCP endpoints (if enabled)
  - `fetch` — `mcp-server-fetch` (uvx)
  - `filesystem` — filesystem server (npx)
  - `litigationos` — local MCP server provided by this repo

## Security
MCP servers can run arbitrary code; only trust servers you understand. VS Code requires trust confirmation for new servers. citeturn1search0

## Start
1) Open Copilot Chat → switch to **Agent mode**
2) Tools icon → start servers / select tools
3) Governor agent uses MCP tools when available.

## Notes
- Avoid hardcoding secrets; use `inputs` or environment variables. citeturn1search1
