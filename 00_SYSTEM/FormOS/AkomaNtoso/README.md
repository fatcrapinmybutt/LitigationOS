# MI_AkomaNtoso_FormFactory_DeepResearch_Pack_20260228

This bundle is a **LitigationOS “Form Factory” research+spec pack** focused on **Akoma Ntoso (LegalDocML)** templates for Michigan court filings.

## What’s inside (high-level)

- **SUPERPIN prompt** for VS Code Copilot CLI to build a Form Factory that:
  - achieves **100% coverage** of Michigan SCAO-approved forms (hundreds) + appellate/trial doc-types,
  - generates **Akoma Ntoso XML templates** + JSON field maps,
  - attaches **composition requirements** (Michigan Court Rules + MiFILE standards),
  - stores everything into your LitigationOS database with hashes and provenance.
- **Michigan composition requirements RuleBank** (machine-readable YAML + narrative MD).
- **Seed Form Profiles** for several high-signal forms (FOC 65/87, DC 100a/100c/104, MC 01, MC 97m, CC 375M, etc.) showing the end-state schema.
- **Example AKN templates** (seed) to validate your pipeline and naming conventions.
- **JSON Schemas** for validation and CI.

## Why this looks “spec heavy” (and not a complete filled catalog here)

This chat environment cannot mass-fetch and parse the entire SCAO forms catalog in bulk.
So this bundle gives you the **research-backed rules**, the **complete database+generator spec**, and **seed profiles**
so your local Form Factory run can produce the **full hundreds-form dataset deterministically**.

## Entry points

- `SUPERPIN_AKN_MI_ALL_FORMS.md` — paste into Copilot CLI
- `MI_COMPOSITION_REQUIREMENTS_RULEBANK.md` — human-readable requirements
- `MI_COMPOSITION_REQUIREMENTS_RULEBANK.yaml` — machine rules
- `seeds/form_profiles_seed.jsonl` — example per-form records
- `seeds/akn_templates/*` — example Akoma Ntoso templates
- `schemas/*` — JSON schemas for CI validation

## Integrity

A `manifest.json` includes SHA-256 hashes for all files in this pack.

Generated: 2026-02-28
