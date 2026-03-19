# VS Code Profile Integration (LitigationOS)
Date: 2026-02-28

This repo provides:
- `.vscode/settings.jsonc` (safe, shareable)
- `.vscode/settings.local.example.jsonc` (template for secrets/personal preferences)
- `.vscode/extensions.json` (recommended extensions)

## Recommended workflow
1) Keep repo settings in `.vscode/settings.jsonc` (no secrets).
2) Copy `.vscode/settings.local.example.jsonc` → `.vscode/settings.local.jsonc` and put keys there.
3) Run sanitizer for legacy settings:
   `python scripts/sanitize_vscode_settings.py --in <your settings.jsonc> --out-dir .vscode`
