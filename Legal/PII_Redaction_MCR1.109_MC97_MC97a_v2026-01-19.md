# PII / Redaction Authority Pack Seed

## Court Rule Anchor
- **MCR 1.109** — Protected Personal Identifying Information; filing/handling rules.

## SCAO Forms
- **MC 97** — Protected Personal Identifying Information (PII form)
- **MC 97a** — Addendum / additional PII submissions (as applicable)

## Use in Workflow
- PII Scan gate must run before any public-court bundle export.
- Outputs:
  - `pii_scan_report.json`
  - `mc97_candidate_fields.json`
  - `redaction_plan.md`

