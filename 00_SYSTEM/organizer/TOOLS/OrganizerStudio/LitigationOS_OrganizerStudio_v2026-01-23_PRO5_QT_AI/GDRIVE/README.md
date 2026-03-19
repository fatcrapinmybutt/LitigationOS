# GDRIVE lane (scoped, safe-by-default)

This lane organizes Google Drive **inside a single folder subtree**.

## Hard safety guard
- You must provide a real folder id as --root-id or in config.yaml.
- The tool refuses to operate with root_id == "root".

## Modes
- PLAN (default): creates a plan + ledger; does not mutate Drive
- APPLY: executes the plan and writes undo artifacts
- UNDO: reverts using the most recent undo.csv

## Auth
Supports OAuth (credentials.json + token.json) or service account JSON.

Recommended:
- Use OAuth desktop app credentials when acting on "My Drive" personal files.
- Use service account only when you own the target folder (shared drive policies vary).
