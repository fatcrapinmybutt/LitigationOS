# Security: Keys in VS Code settings (Action Required)
Date: 2026-02-28

If any VS Code settings file contains API keys or tokens, treat it as compromised if shared/committed.

## Do immediately
1) Rotate the key in the provider dashboard (generate a new key; revoke the old one).
2) Search repos/gists for the key and remove it from history if committed.
3) Move all keys into `.vscode/settings.local.jsonc` (gitignored) or environment variables.

## Repo policy
- `.vscode/settings.jsonc` is safe and contains **no secrets**.
- `.vscode/settings.local.jsonc` is **gitignored** and may contain machine-local keys.
