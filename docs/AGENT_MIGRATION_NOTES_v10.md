# Agent migration notes (v10)
Date: 2026-02-28

This version aligns agent frontmatter to **VS Code custom agents** schema:
- Valid: name, description, argument-hint, tools, model, handoffs, agents citeturn0search0turn0search2
- Repo instructions: `.github/copilot-instructions.md` citeturn0search4turn0search6
- Path-scoped instructions: `.github/instructions/*.instructions.md` citeturn0search5turn0search6

If you used extra YAML keys previously (e.g., user-invokable), VS Code will ignore them; we removed them for maximum compatibility.
