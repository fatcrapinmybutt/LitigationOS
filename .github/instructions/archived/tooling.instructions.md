---
applyTo: "00_SYSTEM/engines/**/*.py,00_SYSTEM/brains/**/*.py,00_SYSTEM/shared/**/*.py"
excludeAgent: "code-review"
---

# Engine & Brain Instructions (LitigationOS Event Horizon Δ∞)

- Every engine/brain must import from `00_SYSTEM/shared/` (get_db, sanitize_fts5, config).
- Every CLI tool must support `--help` and return non-zero on failure.
- Every tool output must be machine-readable when possible (JSON to file).
- Never delete source evidence; append-only new versions.
- Always write reports into `04_ANALYSIS/` or `12_WORKSPACE/` with sha256 receipts.
- Prefer deterministic IDs and stable file names.
- DB paths must come from shared.config, never hardcoded.
