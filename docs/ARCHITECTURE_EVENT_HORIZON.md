# LitigationOS — Event Horizon Δ∞ Infrastructure Architecture

Date: 2026-02-28

This document turns FormOS into a **full LitigationOS enterprise infrastructure**: vault+DB truth spine, pipelines, services, CI, observability,
and “packet factory” outputs.

## 1) Systems (what exists, what we’re building)

### Core stores
- **Vault (CAS)**: content-addressed objects keyed by sha256. Immutable, append-only.
- **K-DB (Relational)**: SQLite baseline; upgrade path to Postgres for multi-user / concurrency.
- **G-DB (Graph)**: Neo4j for cross-case graph (forms, evidence atoms, requirements, filings).
- **V-DB (Vector)**: optional Qdrant for retrieval over shards/atoms (later).
- **Object Storage (optional)**: MinIO/S3-compatible for remote vault replication.

### Pipelines
- **Ingest**: scan → explode zips → CAS store → DB register.
- **Extract**: native text → OCR queue fallback → page anchors.
- **FormOS**: detect forms → instruction atoms → requirements → AKN templates.
- **EvidenceOS**: evidence atomization → exhibit covers → cite-weaving.
- **StackFactory**: per-form filing stacks (lead + attachments + service + exhibits + manifest).
- **Lint/QA**: MiFILE/MCR lint + stack completeness + satisfaction map.
- **CyclePack**: always emit heavy export ZIP + manifest(s).

### Services (optional but recommended)
- `neo4j` (graph)
- `postgres` (relational multi-user)
- `qdrant` (vector)
- `minio` (object store)
- `api` (FastAPI) (control plane / query / exports)

## 2) Invariants (the non-negotiables)
1. **Append-only**: no overwrites, only new versions.
2. **Deterministic IDs**: stable derivation from semantic keys + hashes.
3. **Proof-carrying artifacts**: every generated output links back to source doc hashes + anchors.
4. **Fail-closed optionality**: production mode fails closed on lint; development mode may warn.
5. **No “free text” truth**: narratives are stored as authored statements; evidence citations must resolve to EvidenceAtoms.

## 3) Delivery artifacts (per cycle)
- `coverage.json`
- `lint_reports/`
- `requirement_satisfaction/`
- `neo4j_export/*.csv`
- `cyclepack.zip` + `cyclepack.manifest.json`
- `run_ledger.json` (what ran, inputs, versions, outputs)

## 4) Event Horizon Δ∞: what “done” means
DONE when:
- form coverage == 100% (discovered + catalog-expected, if catalogs enabled)
- every form has instruction atoms + requirements graph + AKN template
- every stack requirement satisfied and linked to a concrete artifact
- every evidence citation resolves (doc_id + sha + anchor)
- all linters PASS in production mode
- cyclepack export produced and verified

## 5) Security & privacy notes
- Vault is sensitive: treat as confidential storage.
- Implement redaction pipeline for protected PII as a first-class step in generation.
- Prefer local-only operation; remote replication should be encrypted and user-controlled.
