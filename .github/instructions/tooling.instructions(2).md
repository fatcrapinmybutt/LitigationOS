---
applyTo: "tooling/**/*.py,tooling/**/*.sql"
excludeAgent: "code-review"
---

# Tooling instructions (LitigationOS Event Horizon Δ∞)

- Every CLI tool must support `--help` and return non-zero on failure.
- Every tool output must be machine-readable when possible (JSON to file).
- Never delete source evidence; append-only new versions.
- Always write reports into Vault/90_REPORTS with sha256 receipts.
- Prefer deterministic IDs and stable file names.
