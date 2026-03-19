# LitigationOS — AGENTS.md (Ω∞)
Date: 2026-02-28

This file provides **agent-specific repository instructions** for Copilot coding agent and related background agents. citeturn0search1turn0search5

## Mission
Build and maintain LitigationOS Event Horizon Δ∞ as a closed-loop factory:
forms + rules + evidence → instruction atoms → requirements graph → AKN templates → filing stacks → lint → satisfaction → graph export → CyclePack.

## Absolute rules
1) **Append-only evidence**: never overwrite originals. New versions only.
2) **Deterministic provenance**: sha256 everywhere; stable IDs; every output points back to inputs.
3) **No hallucinations**: if missing inputs, create acquisition tasks.
4) **Copyright boundary**: do not paste verbatim court-form instruction text into PR descriptions/comments; store locally and reference by hash/path/anchors.
5) **PASS gates define done**: stop only when PASS or blocked.
6) **EAGAIN Prevention**: max 2 shells + 2 agents concurrent. Output ≤100 lines/shell. Stop shells immediately after use. See `.github/instructions/eagain-prevention.instructions.md`.

## Default workflow
- Run `EH:DOCTOR_ALL` (health + coverage + pass status).
- Run `EH:RUN_ALL` (batch enqueue) for target case_id.
- Fix failures in this order: OCR → instructions → requirements → stacks → lint → satisfaction → export.

## Outputs required per run
- Vault/90_REPORTS/coverage_*.json
- Vault/90_REPORTS/lint/<case_id>/lint_summary.json
- Vault/90_REPORTS/PASS_STATUS.json
- Vault/90_REPORTS/neo4j_export_v2/<timestamp>/
- Vault/90_REPORTS/CyclePack_*.zip + manifest verify

