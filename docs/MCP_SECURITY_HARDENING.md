# MCP Security Hardening (Ω∞)
Date: 2026-02-28

VS Code MCP servers can run arbitrary code. Only add servers you trust and restrict directory access. citeturn3view0turn1search0

## Filesystem MCP server risk
The filesystem MCP server has had path validation vulnerabilities in older versions; keep it updated and scope it to the minimum directory. citeturn1search5

Recommended constraints:
- Limit allowed directories to **workspaceFolder only**.
- Prefer read-only mounts where possible (Docker-based server) if you only need read operations.
- Review server logs and reset trust if configuration changes. citeturn3view0

## VS Code trust behavior
VS Code prompts for trust when starting new MCP servers from the UI, but starting directly from `mcp.json` may bypass prompts. citeturn3view0
