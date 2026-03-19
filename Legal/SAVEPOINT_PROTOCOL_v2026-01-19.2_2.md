# LitigationOS SavePoint Protocol (C2) — v2026-01-19.2

## Purpose
This protocol makes the system **restartable** and **infinitely chainable**: every stage emits a SavePoint (checkpoint) that is sufficient to resume the pipeline without redoing earlier work, while preserving **append-only** discipline.

## Core invariants
- **No mutation of originals**: all inputs are referenced by path, or copied into `sources/original/` as immutable snapshots.
- **Every derived artifact is linked** to its parent via `derived_from_artifact_id` (or equivalent) and is tagged with stage metadata.
- **SavePoints are read-only**: a later stage may reference them but cannot alter them.
- **Resume is deterministic**: same SavePoint + same policy bundle + same snapshot inputs => same outputs.

## SavePoint anatomy (minimum)
Each SavePoint is a directory under `runs/<run_id>/checkpoints/<stage_id>/` containing:

1) `checkpoint.json`
- `run_id`
- `stage_id` (e.g., `S10_INGEST`, `S20_EXTRACT`, `S30_ATOMS`, ...)
- `created_ts`
- `inputs`: list of artifact IDs/paths the stage consumed
- `outputs`: list of artifact IDs/paths the stage produced
- `policy_hash`: fingerprint of the policy bundle/spec-cards used
- `authority_snapshot_id` (if relevant)
- `status`: `OK|WARN|BLOCKED`
- `blockers`: structured list of missing POs / missing files / failed validations

2) `event_log_slice.jsonl`
- the append-only events emitted during this stage (subset view)

3) `counts.json`
- per-entity counts and per-artifact counts (used to assert drift)

4) `resume_instructions.md`
- exact CLI invocations that reproduce the stage from the SavePoint inputs

## Stage ladder (recommended)
Use the following stable stage IDs so chained cycles remain compatible:

- `S10_INGEST` — inventory + container explode (ZIP/PDF bundles) + ARTIFACT spine
- `S20_EXTRACT` — text extraction, OCR, metadata extraction, page anchors
- `S30_ATOMS` — EvidenceAtoms/AuthorityAtoms/OrderAtoms/ServiceAtoms + Quote candidates
- `S40_NORMALIZE` — normalize names, docket schema, case keys, dedupe keys
- `S50_GRAPHIR` — emit GraphIR CSV packs (nodes + relationships) + constraints
- `S60_VALIDATE` — validate GraphIR against JSON Schemas; fail-soft unless PCG boundary
- `S70_IMPORT` — Neo4j import pack build + Bloom perspective pack
- `S80_COMPILE` — timelines, matrices, authority triples, contradiction maps
- `S90_PCW` — ProofObligation graph overlay + PO states + acquisition tasks
- `S100_DRAFT` — vehicle-first doc factories + paragraph trace maps
- `S110_PACKET` — release binder (exhibits, cover pages, index, manifest)
- `S120_PCG` — irreversible boundary gate (file/service) — PASS only if core POs satisfied

## Chainable cycles (C1 → C2 → C3 ...)
A “cycle” is an execution that **starts from the most recent SavePoint** and advances one or more stages. Recommended discipline:

- Keep each cycle’s run directory append-only: `runs/R###_<cycle_tag>/...`
- Never rewrite prior cycle outputs; if you refine a schema, create a new versioned schema file.
- Record **delta** between cycles in `compile/delta/`:
  - added entities/fields
  - changed validators
  - changed policies/spec-cards

## Minimal resume contract
A later cycle may assume the presence of:
- `runs/<run_id>/manifests/manifest.csv`
- `runs/<run_id>/checkpoints/<last_stage>/checkpoint.json`
- `runs/<run_id>/graph/graphir_nodes.csv` and `graphir_rels.csv` (once S50 exists)

If these are missing, the pipeline must fall back to the earlier stage (S10) and re-emit.

## “Hard” SavePoints
Mark a SavePoint as **HARD** when:
- it has passed GraphIR validation (S60) and
- its AuthoritySnapshot is complete and versioned and
- its QuoteLock verification set is complete for any quotes used in file-ready outputs.

Hard SavePoints are the only permitted bases for `S120_PCG`.
