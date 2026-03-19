# Next Upgrade Playbook (v11)
Date: 2026-02-28

This upgrade focuses on **operational closure**:
- Standard agent schema alignment (VS Code custom agents) citeturn0search0
- MCP server configuration uses `.vscode/mcp.json` with top-level `servers` per VS Code docs citeturn3view0turn3view1
- Repository agent instructions via `AGENTS.md` (Copilot coding agent) citeturn0search1turn0search3
- Agent-specific scoping via `.instructions.md` + `excludeAgent` for code review separation citeturn0search6
- PASS aggregation via tooling/pass_gate_check.py (single source of PASS truth)
- Doctor health check via tooling/doctor_all.py
- VS Code tasks for one-click runs

Next deltas to pursue:
1) InstructionSectionParser v3 AST compiler
2) StackFactory PDF fill/flatten + DOCX->PDF renderer interface
3) EvidenceCitationWeaver v2 (affidavit paragraph generation with atom citations)
4) MiFILE lint v3 (image margin + font-size heuristics)
