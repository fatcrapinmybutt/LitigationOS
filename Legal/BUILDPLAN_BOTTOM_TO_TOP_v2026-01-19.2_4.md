# LitigationOS Build Plan (Bottom → Top) — v2026-01-19.2

This is the granular build plan that matches the *spine* shown in your ERD-style diagram: **storage → artifact spine → extraction → atoms → graph → policy/PCW → compile → draft → packet → PCG**.

## 0) Preflight (environment + invariants)
### 0.1 Environments to support
- Windows 10/11 (primary)
- Termux/Android (secondary)
- Optional: Linux/WSL2 for batch rendering

### 0.2 Non-negotiable invariants
- Append-only truth discipline (originals immutable)
- Determinism and replay
- QuoteLock for any verbatim quotes that enter file-ready outputs
- AuthoritySnapshot lock for propositions at PCG boundary
- Proof-Carrying Workflow (PCW) with graded obligations; Proof-Carrying Gate (PCG) as final barrier

### 0.3 Deliverables
- `policies/` (spec-cards, thresholds)
- `schemas/` (GraphIR JSON Schemas)
- `runs/<run_id>/` scaffold with `run_ledger.json`

## 1) Storage plane (inputs + canonical run layout)
### 1.1 Goals
- Provide a deterministic run root with stable subfolders.
- Support *references* to originals (fast) or *snapshots* into `sources/original/` (portable).

### 1.2 Minimum run tree
- `inputs/` — pointers or snapshots
- `sources/original/` — immutable copies (optional)
- `sources/zips_extracted/` — container decompositions
- `manifests/` — manifest.csv + manifest.json
- `checkpoints/` — SavePoints by stage
- `logs/` — structured logs + event stream

### 1.3 Implementation tasks
- Inventory walker (drives + Drive mirror)
- Container handler for ZIP/PDF bundles
- Manifest writer

## 2) Artifact plane (universal spine)
### 2.1 Goals
Treat *every* file as an **ARTIFACT** with:
- stable ID
- type/kind
- path, bytes, timestamps
- derived-from lineage

### 2.2 Tables / entities
Primary: `Artifact`.
Recommended satellites:
- `ArtifactKind`
- `ArtifactTag`
- `Bundle` (logical packaging)
- `IntegrityKey` / `HashRecord`

### 2.3 Outputs
- `manifests/manifest.csv`
- `atoms/artifact_atoms.jsonl` (optional, if you want to graph it)

## 3) Extraction plane (format → text/anchors/metadata)
### 3.1 Goals
- PDF → extracted text (and optionally OCR)
- Images → OCR text
- DOCX/TXT → normalized text
- Preserve page/line anchors for later citations

### 3.2 Entities to populate
- `ExtractionRun`, `ExtractionJob`, `TextShard`, `Page`, `Anchor`, `OcrRun`, `OcrToken` (optional)

### 3.3 Outputs
- `sources/extracted/<artifact_id>/...`
- `atoms/quote_candidates.jsonl`

## 4) Atom plane (Evidence/Authority/Procedure atoms)
### 4.1 Goals
Convert extracted material into citeable, minimal units (“atoms”).

### 4.2 Atom families
Evidence:
- EvidenceAtom (fact-carrying snippet)
- QuoteAtom (verbatim text snippet with QuoteLock lifecycle)
Authority:
- AuthorityAtom (rule/statute/case holding)
- Pinpoint (page/line/section)
Procedure:
- OrderAtom, DocketAtom, ServiceAtom, HearingAtom, TranscriptAtom

### 4.3 Outputs
- `atoms/*.jsonl` per family
- `compile/anchors/anchor_index.csv`

## 5) Normalization plane (keys, identity, dedupe)
### 5.1 Goals
- Case keys, party/person keys, organization keys
- Dedupe duplicates across multiple sources
- Standardize court, case type, filing type

### 5.2 Entities
- `CanonicalIdentity`, `Alias`, `EntityResolutionEvent`
- `NormalizationRule`, `NormalizationRun`

### 5.3 Outputs
- `compile/normalize/*.csv`
- `validation_reports/identity_resolution.md`

## 6) Graph plane (GraphIR + Neo4j import packs)
### 6.1 Goals
- Emit CSVs that implement the schema contracts
- Import to Neo4j deterministically
- Export Bloom perspective

### 6.2 Inputs
- Atoms + normalization outputs
- Field/relationship catalogs (this cycle pack)

### 6.3 Outputs
- `graph/graphir_nodes.csv`
- `graph/graphir_rels.csv`
- `graph/constraints.cypher`
- `graph/indexes.cypher`
- `graph/import_runbook.md`

## 7) Policy plane (spec-cards, deltas, signals, scores, gates)
### 7.1 Goals
Compute system decisions from atoms:
`Atoms → Deltas → Signals → Scores → Gates → Actions`.

### 7.2 Entities
- `Delta`, `Signal`, `Score`, `Gate`, `Action`
- `SpecCard`, `SpecCardVersion`, `PolicyBundle`

### 7.3 Outputs
- `compile/deltas/*.jsonl`
- `compile/signals/*.jsonl`
- `compile/scores/*.json`
- `compile/gates/*.json`

## 8) PCW plane (Proof Obligations as first-class nodes)
### 8.1 Goals
- Define ProofObligations (POs) per vehicle and per claim
- Bind evidence and authority pins
- Maintain PO state machine

### 8.2 Entities
- `Vehicle`, `FormBinding`, `Claim`, `Defense`, `Remedy`
- `ProofObligation`, `ProofSatisfaction`, `AcquisitionTask`

### 8.3 Outputs
- `compile/pcw/po_matrix.csv`
- `compile/pcw/acquisition_tasks.jsonl`

## 9) Compilation plane (matrices + timelines + contradiction maps)
### 9.1 Goals
Produce court-ready intermediate artifacts:
- Exhibit matrix
- Authority triples
- Bitemporal timeline
- Findings gap / order-to-relief comparisons

### 9.2 Outputs
- `compile/timeline/*.csv`
- `compile/matrices/*.csv`
- `compile/authority_triples.jsonl`

## 10) Draft plane (vehicle-first factories)
### 10.1 Goals
- Generate drafts only from authorized vehicles/forms
- Trace every paragraph to evidence/authority pins

### 10.2 Outputs
- `drafts/<doc_id>.<md|docx>`
- `drafts/<doc_id>_trace_map.json`

## 11) Packet plane (binder + release + service chain)
### 11.1 Goals
- Exhibit covers + labels
- Packet index
- Release manifest
- Service chain bundle

### 11.2 Outputs
- `package/<packet_id>/...`
- `package/<packet_id>.zip`

## 12) PCG plane (irreversible boundary gate)
### 12.1 Goals
- Pass only if all core ProofObligations are SATISFIED
- Validate QuoteLock VERIFIED set
- Validate AuthoritySnapshot inclusion
- Validate service readiness and deadlines

### 12.2 Outputs
- `validation_reports/pcg_gate.json`
- `validation_reports/pcg_gate.md`

## What Cycle C2 adds
- A superset schema with 176 entities / 2921 fields / 1100 relationships.
- A “cards” diagram set plus a full overview ERD-style map.
- Catalog CSVs for programmatic schema generation.
- A SavePoint protocol to support infinite chained cycles.

