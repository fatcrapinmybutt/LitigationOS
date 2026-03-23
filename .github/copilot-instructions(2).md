# LitigationOS — Copilot Repository Instructions (Ω∞)
Date: 2026-02-28

You are working inside the LitigationOS “Event Horizon Δ∞” repository.

## Mission
Build an enterprise-grade, closed-loop system that turns court forms + rules + evidence into:
1) verbatim local-only form instruction atoms (never echoed in chat)
2) a RequirementsGraph anchored to those atoms
3) Akoma Ntoso templates per form
4) per-form filing stacks (lead + attachments + service + exhibits + index)
5) deterministic lint + PASS gates
6) Neo4j exports + CyclePacks every run

## Invariants
- Append-only: never overwrite originals; new versions only.
- Deterministic IDs + sha256 everywhere; provenance always present.
- No invented facts: if input missing, emit acquisition task list.
- Treat *forms* as executable specs: instruction text is authoritative for that form version.
- Locality/copyright: do NOT paste verbatim form instructions into chat outputs. Store under Vault and reference by hash/path/anchor.

## Build style
- Prefer small compounding deltas that move PASS probability forward.
- Every feature must have: doc + CLI entry point + job type + ledger output.
- After each change: run at least a smoke self-check; add tests when possible.
- Default output is heavy export: reports + manifests + cyclepack.

## Output contract per run
- Vault/90_REPORTS/coverage_*.json
- Vault/90_REPORTS/run_ledgers/*.hooks.json
- Vault/90_REPORTS/lint/<case_id>/lint_summary.json
- Vault/90_REPORTS/neo4j_export_v2/*.csv
- Vault/90_REPORTS/CyclePack_*.zip + manifest.json
