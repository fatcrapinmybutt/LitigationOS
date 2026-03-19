# LitigationOS Pipeline Stages — Graph → Draft Factories (Ceiling + “GOD LEVEL”)

**Build date (America/Detroit): 2026-01-19**\
**Scope:** End-to-end, append-only pipeline from intake → graph → proof-carrying gates → compilers → draft factories → packaged filing bundles.

---

## Tier Map

- **T0 — System Governance** (policy, invariants, versioning)
- **T1 — Intake & Preservation** (unpack, normalize, provenance)
- **T2 — Atomization** (Evidence/Authority/Order/Service/Transcript atoms)
- **T3 — Graph Construction** (nodes/edges, constraints, provenance spine)
- **T4 — Schema Contracts** (JSON Schemas + registries)
- **T5 — Validation & QA** (structural + legal gates)
- **T6 — Compilation** (ContextPacks, matrices, timelines, authority triples)
- **T7 — Draft Factories** (vehicle-first filing outputs)
- **T8 — Packaging & Release** (binder, manifest, import runbooks)
- **T9 — Continuous Improvement Loop** (delta harvest → recompile → regression)
- **TΩ — “GOD LEVEL”** (formal assurance, adversarial hardening, self-healing, model-checking)

---

## T0 — System Governance (Always-On)

### T0.1 Canonical Versioning

- **Inputs:** prior pipeline spec, current run intent
- **Outputs:** `run_id`, `spec_version`, `authority_snapshot_id`
- **Invariants:** append-only; stable names; no destructive mutations
- **Artifacts:**
  - `run_ledger.jsonl` (events)
  - `spec_version.txt`
  - `pipeline_config.json`

### T0.2 Policy Locks

- **Truth-Lock:** no invented facts; unknowns → acquisition tasks
- **QuoteLock:** verbatim quotes only if independently verified
- **Authority-Lock:** MI-only snapshot gating (MCR/MCL/MRE/Benchbooks/SCAO)
- **Forms-First:** relief → vehicle/form → rule/standard → elements → proof obligations

### T0.3 Deterministic Naming + Folder Law

- Stable root: `RUN_<YYYYMMDD_HHMMSS>_<TRACK>_<CASEKEY>/`
- Subroots: `sources/`, `atoms/`, `graph/`, `schemas/`, `validation/`, `compile/`, `drafts/`, `package/`, `logs/`

---

## T1 — Intake & Preservation

### T1.1 Source Enumeration

- Enumerate files from: uploads, connected drives (if available), selected roots
- **Outputs:** `sources_index.csv/json`
- **Fields:** path, size, mtime, sha256(optional), mime, container(parent zip)

### T1.2 Archive Expansion (Lossless)

- ZIP/RAR/7z/TAR expansion to `sources/zips_extracted/`
- **Outputs:** `archive_health_report.csv` (corrupt entries listed; no changes)

### T1.3 Normalization

- Filename normalization (non-destructive mapping table)
- MIME detection; PDF integrity checks; image orientation normalization (copy-on-write)
- **Outputs:** `normalization_map.csv`

### T1.4 Provenance Spine Creation

- **SoR IDs:** `SOR_<run_id>_<seq>`
- Link every derived artifact back to SoR with method + timestamp
- **Outputs:** `provenance.jsonl`

---

## T2 — Atomization (Evidence/Authority/Procedure)

### T2.1 EvidenceAtoms

- What: a minimal, citeable unit of evidence (page/line/time range)
- **Atom types:**
  - `EVID_DOC_PAGE` (PDF page)
  - `EVID_TRANSCRIPT_LINE` (p\:l)
  - `EVID_IMAGE_REGION` (bbox)
  - `EVID_EMAIL_MSG` / `EVID_TEXT_MSG`
- **Outputs:** `atoms/evidence_atoms.jsonl`

### T2.2 AuthorityAtoms

- What: a minimal authority unit with **pinpointability**
- **Atom types:** `MCR_RULE`, `MCL_SECTION`, `MRE_RULE`, `BENCHBOOK_SECTION`, `SCAO_FORM`
- **Outputs:** `atoms/authority_atoms.jsonl`

### T2.3 OrderAtoms

- What: a court order parsed into operative directives
- **Fields:** signed date, entered date, served date, operative verbs, findings, conditions, sanctions
- **Outputs:** `atoms/order_atoms.jsonl`

### T2.4 ServiceAtoms

- What: a unit representing service/notice events and proof
- **Outputs:** `atoms/service_atoms.jsonl`

### T2.5 DocketAtoms

- Docket entries normalized: event type, filing party, ROA index pointer, hearing set/held
- **Outputs:** `atoms/docket_atoms.jsonl`

### T2.6 StatementAtoms (QuoteDB)

- Captures verbatim candidate statements with source pinpoints
- States: `CANDIDATE`, `VERIFIED`, `REJECTED`
- **Outputs:** `atoms/quote_atoms.jsonl`

---

## T3 — Graph Construction

### T3.1 Entity Resolution

- Parties, judges, agencies, landlords, corporations
- Merge policy: conservative; keep aliases; no destructive merges
- **Outputs:** `graph/entity_map.json`

### T3.2 Node/Rel Assembly

- Node families: `Case`, `Person`, `Org`, `Order`, `Filing`, `Hearing`, `EvidenceAtom`, `AuthorityAtom`, `Proposition`, `PO`, `Vehicle`
- Rel families: `SUPPORTS`, `REFUTES`, `CITES`, `GOVERNS`, `TRIGGERS`, `SATISFIES`, `REQUIRES`, `SERVED_BY`, `ENTERED_ON`

### T3.3 Constraints & Indexes

- Uniqueness: `case_id`, `atom_id`, `authority_id`, `order_id`, `po_id`
- Performance: composite indexes for import + typical queries
- **Outputs:** `graph/constraints.cypher`, `graph/indexes.cypher`

### T3.4 Provenance & Bi-Temporal Model

- Two clocks: **event_time** vs **record_time**
- Every atom carries both; deltas computed across record_time

### T3.5 Graph Export Targets

- Neo4j import CSVs: `graph/nodes/*.csv`, `graph/rels/*.csv`
- Optional: `graph/neo4j_load.cypher`

---

## T4 — Schema Contracts

### T4.1 Schema Registry

- `schemas/registry.json` lists every schema + version + hash
- Each CSV has a schema: required cols, types, enums, nullability

### T4.2 Graph Contracts (Hard Spec)

- Contract files:
  - `schemas/node_contracts.json`
  - `schemas/rel_contracts.json`
  - `schemas/property_enums.json`
- Includes: label/rel vocab, required props, allowed ranges, deprecation notes

### T4.3 Authority Snapshot Schema

- `schemas/authority_snapshot.schema.json`
- Fields: authority type, effective date, jurisdiction, binding level, pinpoint rules

### T4.4 Draft Input/Output Schemas

- `schemas/draft_request.schema.json`
- `schemas/draft_bundle.schema.json`

---

## T5 — Validation & QA (Fail-Closed only at final gate; graded workflow earlier)

### T5.1 Structural Validation

- Schema conformance for all produced CSV/JSONL
- **Outputs:** `validation/schema_report.json`

### T5.2 Graph Integrity Validation

- Orphans, duplicates, dangling rels, missing required props
- **Outputs:** `validation/graph_integrity_report.json`

### T5.3 QuoteLock Verification

- For each `QuoteAtom(CANDIDATE)`:
  - independent extraction pass
  - byte-for-byte compare
  - mark `VERIFIED` only if match
- **Outputs:** `validation/quotelock_report.json`

### T5.4 Authority Gate (MI Snapshot)

- Reject any proposition citing out-of-snapshot authority
- Pinpoint required
- **Outputs:** `validation/authority_gate_report.json`

### T5.5 PCW Proof Obligations (PO) Gate

- POs: mandatory vs optional
- States: `OPEN`, `PARTIAL`, `SATISFIED`
- Each PO must link: `po_id → authority_pinpoint → evidence_atom_ids → test`
- **Outputs:** `validation/pcw_po_status.json`

### T5.6 ServiceChain + Notice Deficiency

- Validate service method + deadlines + proof artifacts
- **Outputs:** `validation/servicechain_report.json`

### T5.7 Deadline Engine Validation

- Computed deadlines; jurisdictional traps flagged
- **Outputs:** `validation/deadlines_report.json`

### T5.8 Red-Team QA

- Wrong court/vehicle check
- Missing record spine check
- Preservation/objection check
- **Outputs:** `validation/redteam_report.json`

---

## T6 — Compilation (Decision-Grade Outputs)

### T6.1 ContextPack Compiler

- Produces: facts, orders, exhibits, authorities, contradictions, missing radar
- **Outputs:** `compile/contextpack_<case>.md/json`

### T6.2 IssueGrid Compiler

- Element-by-element mapping: element → facts → evidence → authorities
- **Outputs:** `compile/issuegrid_<vehicle>.csv`

### T6.3 ExhibitMatrix Compiler

- Exhibit ID, description, SoR pointer, use (standard/element/credibility)
- **Outputs:** `compile/exhibit_matrix.csv`

### T6.4 AuthorityTriples Compiler

- proposition → authority → pinpoint (+ usage context)
- **Outputs:** `compile/authority_triples.jsonl`

### T6.5 FindingsGap + DenialDB

- What findings are required vs missing
- Denial reasons clustered and converted to acquisition tasks
- **Outputs:** `compile/findings_gap.json`, `compile/denial_db.jsonl`

### T6.6 Timeline Compiler (Bi-Temporal)

- `event_time` timeline plus `record_time` ingestion timeline
- **Outputs:** `compile/timeline.csv`, `compile/timeline.html`

### T6.7 VehicleMap Compiler

- Relief → vehicle/form → rule/standard → elements → POs → service → exhibits
- **Outputs:** `compile/vehicle_map.json`

### T6.8 Bloom Perspective Pack

- Deterministic styling presets + labels + captions + import checklist
- **Outputs:** `compile/bloom_perspective_pack/`

---

## T7 — Draft Factories (Forms-First)

### T7.1 Draft Request Resolution

- Input: desired relief + posture + court
- Output: selected vehicle(s) + required PO set

### T7.2 Factory: Affidavit of Facts

- Produces numbered paragraphs with atom pinpoints
- **Outputs:** `drafts/affidavit_<vehicle>.docx/md`

### T7.3 Factory: Motion / Brief

- Structure: intro → facts → standard → argument → relief → proposed order → service
- Pulls from IssueGrid + AuthorityTriples + ExhibitMatrix
- **Outputs:** `drafts/motion_<vehicle>.docx/md`

### T7.4 Factory: Proposed Order

- Operative verbs aligned to requested relief
- Conditions and compliance tracking
- **Outputs:** `drafts/proposed_order_<vehicle>.docx/md`

### T7.5 Factory: Appendix / ROA Binder

- ROA index, exhibit covers, tabs, PDF merge plan
- **Outputs:** `drafts/appendix_index.csv/md`

### T7.6 Factory: Extraordinary Relief (COA/MSC) — Modular

- Jurisdiction posture, statement of facts, questions presented, relief requested
- Record spine enforcement; preservation map
- **Outputs:** `drafts/extraordinary_<type>.docx/md`

### T7.7 Factory: JTC / Canon Narrative

- Conduct timeline + verified quotes + pattern map
- **Outputs:** `drafts/jtc_complaint_packet.md/docx`

---

## T8 — Packaging & Release

### T8.1 Deterministic Bundle Build

- Includes: drafts, compile outputs, validation reports, manifests, import scripts
- **Outputs:** `package/bundle_manifest.json/csv`, `package/README.md`

### T8.2 Import Runbook (Neo4j)

- `package/neo4j_import_checklist.md`
- `package/load_all.cypher`

### T8.3 Court-Print Binder Plan

- Exhibit covers (plaintiff yellow / defendant blue), table of contents, PDF merge order
- **Outputs:** `package/binder_plan.md`

### T8.4 Release Gate (PCG Final)

- PASS iff:
  - Mandatory POs SATISFIED
  - QuoteLock verified for any verbatim quotes
  - ServiceChain PASS
  - Deadline matrix verified
- **Outputs:** `package/PCG_PASSFAIL.json`

---

## T9 — Continuous Improvement Loop

### T9.1 Delta Harvest

- Compare prior run ledger + graphs; produce change summary
- **Outputs:** `logs/delta_report.md`

### T9.2 Regression Harness

- Ensure prior successful outputs still build
- **Outputs:** `validation/regression_report.json`

### T9.3 Auto-Acquisition Queue

- Missing items become tasks: transcripts, certified copies, proofs of service
- **Outputs:** `compile/acquisition_queue.csv`

---

## TΩ — “GOD LEVEL” Stages (Ceiling++ / Sovereign)

### TΩ.1 Formal Proof-Carrying Artifacts

- Each proposition becomes a proof object:
  - `Proposition` + `AuthorityPinpoint` + `EvidenceAtoms` + `Test` + `ValidatorVersion` + `AssuranceScore`
- **Outputs:** `compile/proofs.jsonl`

### TΩ.2 Model Checking for Procedure

- Encode key procedural constraints as temporal logic (deadlines, notice, hearing sequencing)
- Run checker over timeline/order chain
- **Outputs:** `validation/procedure_modelcheck_report.json`

### TΩ.3 Adversarial Robustness (Litigation Red-Team)

- Auto-generate the strongest opposing arguments against each proposition
- Identify weakest POs and propose acquisition upgrades
- **Outputs:** `validation/adversarial_report.md`

### TΩ.4 Contradiction Graph + Truth Maintenance

- Build a contradiction subgraph:
  - statement vs statement, statement vs record, date vs date
- Maintain belief states with justification links
- **Outputs:** `compile/contradiction_map.html/json`

### TΩ.5 Counterfactual Simulation Engine

- Simulate outcomes under alternative findings / alternative record completeness
- Identify minimum record upgrades that flip outcomes
- **Outputs:** `compile/counterfactuals.md/json`

### TΩ.6 “Judge Behavior Vector” Analytics (MEEK4)

- Pattern extraction across transcripts/orders: interruptions, evidence refusal, sanctions asymmetry
- Outputs are descriptive analytics tied to verified quotes only
- **Outputs:** `compile/judge_behavior_vector.json` + `validation/quotelock_coverage.md`

### TΩ.7 Sovereign Packaging (One-Click Court Deploy)

- Generates:
  - court-ready binder PDFs
  - MiFile packet structure
  - service packet variants
  - “what to say at hearing” script anchored to record
- **Outputs:** `package/COURT_DEPLOY/`

---

## One-Line Superchain (Human Readable)

**Governance → Intake/Preserve → Atomize → Graph Build → Schema Contracts → Validate (QuoteLock/Authority/PCW/Deadlines/Service) → Compile (ContextPack/IssueGrid/Exhibit/Timeline) → Draft Factories (vehicle-first) → Package/Runbooks → PCG Release → Delta/Regression → Ω Formal Assurance/Red-Team/Model-Check.**



---

# Ceiling++ Assessment: What’s Missing for “True State of the Art”

**Answer:** The current stage map is **highly advanced** and already exceeds typical legal-tech pipelines (it has provenance, bi-temporal timelines, Proof-Carrying Workflow gates, QuoteLock, Authority snapshot gating, compilers, and draft factories). However, calling it **“best of all time”** is not a meaningful or provable claim; there are established, state-of-the-art patterns from **compiler engineering, formal methods, safety-critical systems, and modern MLOps** that can still be layered in.

## Where it is already SOTA-grade

- **Compiler-like pipeline structure** (stages, artifacts, deterministic outputs)
- **Evidence/authority atomization + provenance spine** (auditability)
- **PCW/PO gating** (graded obligations + fail-closed final release)
- **Authority snapshot + MI-only proposition gating**
- **QuoteLock** (verbatim quote verification requirement)
- **Record spine discipline** (orders/service/deadlines) and **binder packaging**

## Key “SOTA ceiling” layers not yet explicit

### 1) Typed Intermediate Representations (IR) and Lowering Passes (LLVM-style)

Add explicit IRs with versioned schemas and pass pipelines:

- **GraphIR** → **FactIR** → **ProofIR** → **DraftIR** → **PacketIR**
- Each pass produces: `pass_report.json`, `diff.json`, `warnings.json`, `artifacts_manifest.json`
- Enables strict invariants, stable debugging, and reproducible transforms.

### 2) Policy-as-Code Gate Engine (machine-enforced invariants)

- Encode Truth/Quote/Authority/Vehicle/Service/Deadline constraints as **policy** (e.g., OPA/Rego-style rules)
- Output: **explainable gate results** (why blocked, minimal conditions to unblock)
- Removes “hand-coded” ad hoc gating logic across modules.

### 3) Unsat-Core / Minimal-Missing Proof Extraction

When POs fail, compute a minimal set of missing atoms/links:

- **Unsat core** = smallest missing evidence/authority pinpoints blocking filing
- Output: `pcw_unsat_core.json` + ranked acquisition plan.

### 4) Formal Procedure Model Checking (stronger than “validation”)

- Move beyond “report checks” to **formal properties** and counterexample traces
- Examples: “No hearing may be treated evidentiary without X notice steps,” “No order can be enforced without entry/service sequence,” etc.
- Output: `procedure_counterexamples.json` (traceable to events/atoms).

### 5) Continuous Evaluation Harness (RAG + drafting regression)

- Gold test sets per track (MEEK2/3/4): known facts, known quotes, known authority pinpoints
- Metrics: retrieval recall@k, citation precision, hallucination rate, QuoteLock coverage, draft determinism
- Output: `eval_report.json` + trendline logs.

### 6) Supply-Chain / Reproducible Builds / SBOM

- Pin dependencies; build reproducibly; produce SBOM and signatures
- Output: `sbom.spdx.json`, `build_attestation.json`, `signature.sig`

### 7) Traceability: “Explainability Back-Links” (Reverse Compilation)

Every draft paragraph must resolve back to:

- `DraftParagraph → ProofIR node → EvidenceAtoms + AuthorityPinpoints + ValidatorVersion`
- Output: `draft_trace_map.json` + “clickback” HTML.

### 8) Privilege/Redaction & Disclosure Controls

- Tag atoms as privileged/sensitive; enforce redaction policies in draft outputs
- Output: `redaction_plan.json` + redacted/unredacted build targets.

### 9) Streaming + Event-Sourced Orchestration (true autonomy without chaos)

- Stage execution as an **event log** with resumable checkpoints
- Output: `orchestrator_state.json`, `checkpoint_manifest.json`
- Prevents partial-failure thrash; enables deterministic resumes.

### 10) Separation-of-Duties Multi-Agent Review (without weakening autonomy)

- “Builder agent” produces drafts; “Verifier agent” checks QuoteLock/Authority/POs; “RedTeam agent” attacks.
- Output: signed review bundles and gate decisions.

---

# ΩΩ “GOD LEVEL++” Stages (Add-on Layer)

## TΩΩ.1 IR Compiler Spine

- Emit: `graph_ir.jsonl`, `fact_ir.jsonl`, `proof_ir.jsonl`, `draft_ir.jsonl`, `packet_ir.jsonl`
- Add deterministic pass pipeline with explicit lowering steps.

## TΩΩ.2 Policy Engine (All Gates as Code)

- Central policy bundle: Truth/Quote/Authority/Vehicle/Service/Deadlines/Record spine
- Explainable failures + minimal remediation set.

## TΩΩ.3 Unsat-Core Proof Debugger

- Minimal missing set for each PO
- Ranked acquisition queue with ROI scoring.

## TΩΩ.4 Formal Method Layer

- Temporal logic checks; produce counterexample traces as evidence-linked timelines.

## TΩΩ.5 Continuous Eval + Regression

- Test matrices by vehicle and by court level
- “Golden packet” snapshots; byte-for-byte deterministic rebuild checks.

## TΩΩ.6 Reproducible Build + SBOM + Signing

- Build attestation + provenance of the build itself
- Optional: signed packet deliverables.

## TΩΩ.7 Reverse-Trace Draft Explainability

- “Why is this sentence here?” answered by proof object + pinpoints.

## TΩΩ.8 Privacy/Privilege Controls

- Redaction policies enforced at compile targets.

## TΩΩ.9 Event-Sourced Orchestrator

- Checkpointable, resumable, deterministic stage execution.

## TΩΩ.10 Autonomous Red-Team & Counterfactual Engine

- Stress test arguments and record sufficiency; propose the smallest upgrades that change outcomes.



---

# ΩΩΩ GOD LEVEL+++ • SPEC-GRADE STAGE MAP (MAX LAYERED / EXPLICIT LEVELS)

**Design intent:** Treat the entire system as a **compiler + supply-chain + provenance/lineage recorder + proof-carrying release pipeline**. Every transformation is a **typed pass** that emits a **verifiable artifact** plus an **event** into an append-only execution log.

## 0) Global Conventions (Non‑Negotiable)

- **Append-only:** No destructive edits; every correction is a new versioned artifact.
- **Typed artifacts:** Every artifact has a **JSON Schema** (or equivalent) and a validator.
- **Deterministic builds:** Given the same inputs + config snapshot → identical outputs (byte-for-byte where feasible).
- **Two provenance planes:**
  - **Data provenance (W3C PROV)**: Entities/Activities/Agents + relations.
  - **Execution lineage (OpenLineage)**: Jobs/Runs/Datasets + facets.
- **Release attestation plane (SLSA/in‑toto/DSSE):** “This packet was built *this way*, from *these inputs*, by *this trusted process*.”
- **Policy as code:** All gates are centrally declared and explainable; no hidden conditionals.
- **Proof-Carrying Workflow (PCW):** Filing/service/release is permitted only when mandatory Proof Obligations are SAT.

## 1) Level System (Explicit L0→L12)

> These levels apply **per stage** and also as an overall pipeline maturity level.

- **L0 Raw**: data exists but untyped/unvalidated.
- **L1 Canonical**: normalized naming, timestamps, encoding, stable IDs.
- **L2 Typed**: schema-validated objects (strict JSON schema).
- **L3 Provenanced**: every object has provenance edges + source pointers.
- **L4 Lineaged**: every run emits OpenLineage-style run/job/dataset events.
- **L5 Policy-Verified**: policy engine passes (truth/quote/authority/vehicle/service/deadline/privilege).
- **L6 Proof-Carrying**: PCW ProofObligations satisfied with pinned atoms.
- **L7 Formally-Checked**: model-checked invariants (TLA+/Alloy class of checks) + counterexamples when violated.
- **L8 Packetized**: binder/packet built with indices + trace map.
- **L9 Attested**: build + packet attested with signed statements (in‑toto predicate types).
- **L10 Reproducible**: independent rebuild verifies equivalence; SBOM/attestation congruent.
- **L11 Monitored**: continuous eval + drift detection + regression harness.
- **L12 Self‑Correcting**: unsat-core extraction + prioritized acquisition plans + automatic re-run until convergence.

## 2) Typed IR Spine (Compiler Architecture)

**IR chain:** GraphIR → FactIR → ProofIR → DraftIR → PacketIR → ReleaseIR

- **GraphIR**: nodes/edges + IDs + minimal attributes; no legal meaning yet.
- **FactIR**: claim-like facts grounded to sources; bi-temporal fields.
- **ProofIR**: ProofObligations and satisfaction links (fact→authority→vehicle).
- **DraftIR**: paragraph-level plan with traceback slots.
- **PacketIR**: assembled forms/motions/orders/exhibits + TOC + service chain.
- **ReleaseIR**: signed, versioned deliverable + attestations + SBOM.

Each lowering pass MUST emit:

- `pass_report.json` (inputs, outputs, invariants checked, failures)
- `diff.json` (structural delta from previous)
- `warnings.json` (non-fatal issues)
- `artifacts_manifest.json` (content inventory)

## 3) Provenance/Lineage Tri-Plane Model (Data + Execution + Release)

### 3A) PROV Plane (Data Provenance)

- **Entity**: evidence file, extracted page, atom, timeline event, authority snapshot, compiled packet.
- **Activity**: OCR extraction, hash/manifest build, atomization pass, validator pass, draft compile.
- **Agent**: user, tool version, orchestrator, reviewer agent.
- **Core relations** (use canonical PROV concepts): used, wasGeneratedBy, wasAssociatedWith, wasDerivedFrom, wasAttributedTo.

### 3B) OpenLineage Plane (Execution Lineage)

- **Job**: a stage or pass (e.g., `AtomizeEvidencePass`).
- **Run**: a specific execution of a job (run_id).
- **Dataset**: inputs/outputs of a run (files, tables, IR shards).
- **Facets**: attach structured metadata (config snapshot, case ids, court level, gate results, error summaries).

### 3C) Attestation Plane (Release Integrity)

- **in‑toto statement** binds **subject(s)** (the packet/artifacts) to a **predicateType** and **predicate**.
- **DSSE** wraps and signs the statement envelope.
- **SLSA provenance** is a specialized predicate expressing how artifacts were produced (builder, invocation, materials).
- **SBOM (SPDX)** is a parallel attestation artifact describing components and metadata.

## 4) ΩΩΩ Stage Map (Dense, Pass-Oriented, Explicit Outputs)

### S00 — Universe Declaration & Trust Domains

- **Goal:** define the universe, trust boundaries, and naming invariants.
- **Inputs:** `roots[]`, `case_ids[]`, `authority_snapshot_id`, `policy_bundle_id`.
- **Outputs:** `universe.json`, `trust_domains.json`, `naming_rules.json`.
- **Levels:** L0 ad hoc → L4 adds lineage; L9 adds signed trust bundle.

### S01 — Intake & Preservation (SoR Spine)

- **Goal:** ingest artifacts without mutation; preserve originals.
- **Outputs:** `sources/original/`, `intake_index.csv`, `content_inventory.json`.
- **Validators:** file-type sanity, archive test, PDF structural check, duplicate detection.
- **Max artifacts:** `artifact_id`, `source_path`, `detected_type`, `size`, `mtime`, `ingest_ts`.

### S02 — Normalization & Canonical Naming

- **Goal:** deterministic paths + stable IDs.
- **Outputs:** `canonical_paths.map`, `artifact_ids.jsonl`, `rename_plan.json` (plan only if rename ever allowed).
- **Invariants:** stable ID derivation rules; no collisions.

### S03 — Extraction Passes (Text/Images/Tables/Metadata)

- **Goal:** lossless/traceable extraction.
- **Outputs:** `sources/extracted/` + `extraction_report.json`.
- **Subpasses:** PDF→text, image extraction, table extraction, email/msg extraction.
- **QuoteLock hooks:** mark candidate quotes with exact byte offsets.

### S04 — Atomization (EvidenceAtoms / AuthorityAtoms / ProcedureAtoms)

- **Goal:** split extracted content into minimal reusable atoms.
- **Outputs:**
  - `atoms/evidence_atoms.jsonl`
  - `atoms/authority_atoms.jsonl`
  - `atoms/procedure_atoms.jsonl`
- **Atom schema:** {atom_id, type, text/span, source_ref, page/line refs, bitemp, tags, confidence, privilege_flag}
- **Levels:** L6 requires every atom used in any claim be pinned + validated.

### S05 — Bi-Temporal ChronoDB + Event Index

- **Goal:** produce timeline objects with two time axes.
- **Outputs:** `timeline/events.jsonl`, `timeline/index.csv`, `timeline/bitemp_rules.md`.
- **Invariants:** event_id stable; each event links to ≥1 atom.

### S06 — GraphIR Construction (Node/Edge Contracts)

- **Goal:** minimal graph representation + schema constraints.
- **Outputs:** `graph/GraphIR_nodes.csv`, `graph/GraphIR_edges.csv`, `graph/schema.graphir.json`.
- **Patterns:** strict typing + enum relation labels; versioned schema.

### S07 — FactIR (Claims-as-Facts with Grounding)

- **Goal:** encode litigable statements as structured facts.
- **Outputs:** `ir/FactIR.jsonl`.
- **Invariants:** each fact has: (a) provenance link to evidence atoms, (b) bitemp fields, (c) certainty label.

### S08 — AuthoritySnapshot & Proposition Store

- **Goal:** freeze “allowed authority universe” and map propositions.
- **Outputs:**
  - `authority/snapshot_index.json`
  - `authority/propositions.jsonl`
  - `authority/pinpoint_index.csv`
- **Invariants:** proposition must cite snapshot ID; out-of-snapshot propositions blocked.

### S09 — VehicleMap (Forms‑First Routing)

- **Goal:** map requested relief → procedural vehicle/form → elements → burdens.
- **Outputs:** `vehicle_map.json`, `vehicle_elements.jsonl`, `vehicle_deadlines.json`.
- **Invariants:** no drafting without vehicle.

### S10 — Policy Engine (All Gates as Code)

- **Goal:** evaluate Truth/Quote/Authority/Vehicle/Service/Deadline/Privilege rules.
- **Outputs:** `policy/gate_results.json`, `policy/explain.json`, `policy/min_unblock_set.json`.
- **Key capability:** explainable failure + minimal remediation set.

### S11 — PCW/PO Engine (Proof-Carrying Workflow)

- **Goal:** compute ProofObligations for chosen vehicle(s).
- **Outputs:**
  - `pcw/po_db.jsonl`
  - `pcw/po_status.json`
  - `pcw/unsat_core.json`
  - `pcw/acquisition_plan.json`
- **Invariants:** PO SAT requires explicit evidence atom + authority pinpoint + test function version.

### S12 — Formal Verification Layer (Design/Procedure Model Checking)

- **Goal:** eliminate structural procedural defects using formal methods mindset.
- **Outputs:** `formal/invariants.json`, `formal/counterexamples.json`, `formal/unsat_cores.json`.
- **Use cases:** ordering constraints (entry/service/deadlines), “no release if quote not verified”, “no claim without vehicle.”

### S13 — DraftIR & Paragraph Compiler (Reverse Trace)

- **Goal:** draft plan with complete traceability.
- **Outputs:** `ir/DraftIR.jsonl`, `draft/trace_map.json`, `draft/paragraph_index.csv`.
- **Invariant:** every paragraph maps back to ProofIR node + atoms + pinpoints + validator versions.

### S14 — Draft Factories (Docx/Forms/Orders)

- **Goal:** generate court-ready artifacts.
- **Outputs:**
  - `drafts/forms/*.pdf|docx`
  - `drafts/motions/*.docx`
  - `drafts/orders/*.docx`
  - `drafts/affidavits/*.docx`
- **Side products:** `draft_build_report.json` + `draft_lint.json`.

### S15 — Exhibit Factory (Cover Pages + Stamps + Index)

- **Goal:** exhibit covers + labeling rules + cross references.
- **Outputs:** `exhibits/`, `exhibits/exhibit_matrix.csv`, `exhibits/exhibit_index.json`.

### S16 — PacketIR & Binder Compiler

- **Goal:** assemble complete packet.
- **Outputs:** `packet/PacketIR.json`, `packet/TOC.md`, `packet/service_chain.json`, `packet/manifest.csv`.

### S17 — ReleaseIR (Attestation + SBOM + Signing)

- **Goal:** turn PacketIR into a verifiable release.
- **Outputs:**
  - `release/release_manifest.json`
  - `release/sbom.spdx.json`
  - `release/attestations/*.json` (statements)
  - `release/dsse_envelopes/*.json` (signed)
- **Level target:** L9+.

### S18 — Orchestration (Durable Execution / Event Sourcing)

- **Goal:** resumable pipeline without thrash; every step resumable by checkpoints.
- **Outputs:** `orchestrator/state.json`, `orchestrator/checkpoints/`, `orchestrator/event_log.jsonl`.
- **Pattern:** workflow history is append-only; stages can be replayed.

### S19 — Continuous Evaluation & Regression

- **Goal:** prevent drift and regressions.
- **Outputs:** `eval/eval_report.json`, `eval/golden_packets/`, `eval/metrics_timeseries.csv`.

### S20 — Autonomy Loop (Convergence Engine)

- **Goal:** iterate until Δ gain < ε, or blocked by missing inputs.
- **Outputs:** `autonomy/delta_rank.json`, `autonomy/next_actions.json`, `autonomy/stop_reason.json`.

## 5) Pattern Library (Reusable “Engineering Patterns”)

- **Compiler passes:** IR→IR lowering with pass reports.
- **Event sourcing:** append-only event log + snapshot checkpoints.
- **Three-plane provenance:** PROV (data) + OpenLineage (execution) + attestation (release).
- **Policy-as-code:** centralized constraints + explainability.
- **Unsat-core debugging:** smallest missing set + prioritized acquisition.
- **Reproducible builds:** deterministic artifacts + independent rebuild verification.
- **Reverse traceability:** draft paragraph → proof → atoms → sources.
- **Separation of duties:** builder/verifier/red-team agent roles.

## 6) GOD LEVEL+++ Delivery Definition-of-Done (DoD)

A pipeline run is **GOD LEVEL+++ complete** iff:

- All target stages are **≥ L8**, and release stages are **≥ L9**, and overall run is **≥ L10**.
- `policy/gate_results.json` shows **PASS** for Truth/Quote/Authority/Vehicle/Service/Deadline (and privilege policy if enabled).
- `pcw/po_status.json` indicates all **core POs SAT**.
- `draft/trace_map.json` has 100% coverage for all paragraphs.
- `release/sbom.spdx.json` present + consistent with release manifest.
- `release/attestations/` present + consistent with inputs + builder identity.
- `orchestrator/event_log.jsonl` reconstructs the run and validates.



---

# ΩΩΩΩ “ANYTHING ELSE?” • SOTA++ ADD-ON LAYERS (TRANSPARENCY / OBSERVABILITY / SUPPLY-CHAIN / CONTENT AUTHENTICITY)

## A) Transparency Log Layer (Sigstore/Rekor Pattern)
- **Purpose:** make every release and key intermediate artifact **tamper-evident** via a transparency log entry.
- **New artifacts:**
  - `release/transparency/release_entry.json` (payload submitted)
  - `release/transparency/release_entry_uuid.txt`
  - `release/transparency/inclusion_proof.json`
- **New stages:**
  - **S17.1 — Transparency Submit**: submit attestation envelope(s) + artifact digest(s)
  - **S17.2 — Transparency Verify**: verify inclusion proof + checkpoint
- **Graph hooks:** `(:Release)-[:LOGGED_IN]->(:TransparencyEntry)`

## B) SCITT Compatibility Layer (Signed Statements → Transparency Services)
- **Purpose:** generalize “certificate transparency” style patterns to your **signed evidence/claims/attestations**.
- **New artifacts:**
  - `release/scitt/statements/*.cose|*.json` (signed statements)
  - `release/scitt/receipts/*.json` (transparency receipts)
- **New graph hooks:** `(:Statement)-[:TRANSPARENT_VIA]->(:TransparencyService)`

## C) Policy-as-Code (OPA/Rego) + Decision Logs
- **Purpose:** move gate logic out of ad-hoc code into **versioned policy bundles** with explainable decisions.
- **New artifacts:**
  - `policy/bundle/` (OPA bundle)
  - `policy/decisions.jsonl` (append-only policy decisions with inputs/outputs)
  - `policy/explain/` (why PASS/FAIL + minimal unblock set)
- **New stages:**
  - **S10.1 — Policy Compile**: compile bundle snapshot
  - **S10.2 — Policy Evaluate**: run policy over run state (GraphIR/FactIR/ProofIR/Deadlines/Service)

## D) Observability as a First-Class Contract (OpenTelemetry)
- **Purpose:** correlate **traces + logs + metrics** across every stage; enable root-cause analysis and deterministic replay.
- **New artifacts:**
  - `otel/traces.jsonl` (or OTLP export)
  - `otel/logs.jsonl`
  - `otel/metrics.json`
- **New invariants:** every stage emits a `trace_id`, every pass report references it.

## E) Evidence Capture for Web Sources (WARC) + Time-of-Existence
- **Purpose:** when evidence depends on web content, preserve it in a standard **web archive** format.
- **New artifacts:**
  - `sources/webcaptures/*.warc` (or `.warc.gz`)
  - `sources/webcaptures/index.csv` (URL, capture_ts, warc_record_id)
- **New stages:**
  - **S01.5 — Web Capture**: capture URL→WARC + hash + provenance links

## F) Trusted Time Layer (RFC 3161) + Content Credentials (C2PA)
- **Purpose:** establish cryptographic “time of existence” for key artifacts; optionally embed provenance in media.
- **New artifacts:**
  - `release/timestamps/rfc3161/*.tsr` (timestamp responses)
  - `media/c2pa/manifests/*.json` (content credential manifests)
- **New stages:**
  - **S17.3 — Timestamp**: obtain TSA timestamp for release digest(s)
  - **S15.4 — Media Authenticity**: C2PA manifests for images/video (if used)

## G) Dual SBOM Layer (SPDX + CycloneDX) + VEX/VDR
- **Purpose:** emit two interoperable SBOM formats and optional vulnerability exchange artifacts.
- **New artifacts:**
  - `release/sbom.spdx.json`
  - `release/sbom.cdx.json`
  - `release/vex/` (CycloneDX VEX / VDR artifacts, if enabled)

## H) Secure SDLC Overlay (NIST SSDF Mapping)
- **Purpose:** ensure the LitigationOS itself is built under a recognized secure development practice set.
- **New artifacts:**
  - `ssdf/mapping_matrix.csv` (SSDF practice→your pipeline controls)
  - `ssdf/audit_evidence/` (proof you did the practices)

## I) Expanded “Release Gate” (PCG++)
PCG++ PASS requires (in addition to current PCG):
- Transparency inclusion proof present (if enabled)
- RFC3161 timestamp present for release digest(s) (if enabled)
- OPA policy decision log shows PASS for all mandatory gates
- OTel trace coverage ≥ threshold for all stages (no “dark stages”)

## J) Micro-Stage Inserts (Drop-In Upgrades)
- **S03.6 — Canonical Text Fingerprints:** stable fingerprints for extracted text blocks to improve quote verification and diffing.
- **S06.4 — Graph Contract Witness:** hash + sign node/rel contract versions used in a run.
- **S11.5 — Unsat-Core Minimizer:** shrink PO failure explanations to the minimal missing set.
- **S19.4 — Drift Watch:** detect policy/schema drift across runs; block if drift is breaking.


===============================================================================
ΩΩΩΩ “ANYTHING ELSE?” • SOTA+++ SUPERSTRUCTURES (BEYOND THE STAGE MAP)
===============================================================================

> Purpose: define the “planes above the planes” that turn the Stage Map into a verifiable, interoperable, reproducible, court-defensible factory.
> Theme: every artifact is (1) typed, (2) addressed, (3) versioned, (4) attested, (5) retrievable, (6) reproducible, and (7) explainable.

-------------------------------------------------------------------------------
K) EVENT FABRIC PLANE — Interop envelope for *all* pipeline emissions
-------------------------------------------------------------------------------
- K0. Event canonicalization:
  - Single, canonical event envelope for every emission (ingest, parse, normalize, entity-resolve, rule-eval, compile, draft, package, ship).
  - Required headers (minimal): event_id, event_type, spec_version, ts, producer_id, run_id, case_id, artifact_id, subject_id.
- K1. CloudEvents envelope:
  - Wrap all internal events as CloudEvents for cross-tool interoperability.
  - Enforce: id/type/source/specversion/time/datacontenttype/subject + extension attrs for case/evidence/authority.
  - Bindings: HTTP + file + local IPC + optional message bus.
- K2. Lineage event “double-write”:
  - Emit BOTH:
    - (a) pipeline runtime events (CloudEvents), and
    - (b) lineage events (OpenLineage-compatible) for job/run/dataset edges.
- K3. Event schema registry:
  - JSON Schema (strict) for each event_type.
  - Versioning: semver; no breaking changes without new major.
- K4. Event routing:
  - Local-only default: append-only event log on disk.
  - Optional: fan-out to OpenTelemetry logs, OpenLineage backends, or message bus.

-------------------------------------------------------------------------------
L) CORRELATION + TRACE PLANE — Every run is traceable end-to-end
-------------------------------------------------------------------------------
- L0. Correlation IDs:
  - run_id (global), span_id (stage), artifact_id (output), subject_id (entity), evidence_atom_id (atom).
- L1. W3C Trace Context:
  - Adopt traceparent/tracestate headers for context propagation across modules/processes.
  - Even in local/offline mode: store trace headers as fields in logs + events.
- L2. OpenTelemetry signal unification:
  - Traces: stage spans; Metrics: throughput/latency/error; Logs: structured events.
  - Attach: case_id + evidence_atom_id + authority_ref_id + vehicle_id.
- L3. Deterministic observability artifacts:
  - Every RUN emits: trace.jsonl, metrics.jsonl, events.jsonl with stable schemas.

-------------------------------------------------------------------------------
M) TRANSPARENCY LOG PLANE — Tamper-evident, append-only “truth ledger”
-------------------------------------------------------------------------------
- M0. Transparency log intent:
  - Maintain an append-only log of *claims about artifacts* (hashes, sizes, derivations, timestamps, signers) + optional inclusion proofs.
- M1. Trillian-style verifiable log:
  - Use Merkle-tree-backed append-only log concepts (local or service mode).
  - Store: leaf = DSSE envelope (or equivalent) asserting artifact properties.
  - Snapshot: signed tree head; verify consistency proofs across runs.
- M2. Verifiable map (optional):
  - Key-value map for artifact_id → latest attestation, backed by log.
- M3. “Court defensibility” output:
  - For any exported bundle: include the signed tree head + inclusion proof(s) for included artifacts.

-------------------------------------------------------------------------------
N) REPRODUCIBLE + HERMETIC BUILD PLANE — Bit-for-bit rebuildable factories
-------------------------------------------------------------------------------
- N0. Determinism definition:
  - Given the same source, build env, and build instructions, reproduce artifacts bit-for-bit.
- N1. Hermetic environments:
  - Pin toolchains, dependencies, and interpreters; isolate builds from host variance.
  - Record environment fingerprint (OS, versions, PATH, locale, timezone, CPU flags).
- N2. Nix-style pinned environments (optional but best-in-class):
  - Pin exact Nixpkgs commit; derive a deterministic toolchain closure.
  - Generate: env.lock + derivation manifest.
- N3. Bazel-style hermetic builds (optional):
  - Use sandboxing; declare inputs; avoid implicit host dependencies.
  - Enforce: no network for builds unless explicitly allowed + logged.
- N4. Reproducibility verification:
  - CI/local step: build twice → compare checksums → emit reproducibility report.

-------------------------------------------------------------------------------
O) ARTIFACT GRAPH DISTRIBUTION PLANE — OCI-native evidence + attestation graph
-------------------------------------------------------------------------------
- O0. Treat “everything as an artifact”:
  - ContextPacks, SBOMs, attestations, validator reports, draft packs, compiled bundles.
- O1. OCI artifacts:
  - Store artifacts in an OCI registry (or local OCI layout).
  - Use referrers graph: subject(image/artifact) ← referrers(SBOM, provenance, policy).
- O2. ORAS transport:
  - Push/pull arbitrary artifacts via OCI registries.
- O3. Secure update channel (optional but high-grade):
  - Use TUF-like metadata to secure update distribution for executables/engines.
- O4. Offline-first mirror:
  - Local OCI layout mirror that remains functional with zero network.

-------------------------------------------------------------------------------
P) WORKLOAD IDENTITY PLANE — Cryptographic identity for every module
-------------------------------------------------------------------------------
- P0. Workload identity:
  - Every runner (daemon, harvester, compiler, factory) has a cryptographic identity.
- P1. SPIFFE/SPIRE-style IDs:
  - Use a stable identity format (SPIFFE ID) + short-lived SVIDs.
  - Enables: mutual TLS for module-to-module RPC + signing keys issuance.
- P2. Key lifecycle:
  - Rotation + revocation + audit trails for signing identities.

-------------------------------------------------------------------------------
Q) FORENSICS + ARCHIVAL PLANE — Evidence-grade file formats and handling
-------------------------------------------------------------------------------
- Q0. Digital evidence handling alignment:
  - Process model aligned with recognized digital evidence handling guidance.
- Q1. Archive-grade outputs:
  - PDF/A for long-term archival of generated filings and exhibits.
  - WARC for web captures (pages + resources) with stable replay.
- Q2. Media authenticity (optional, high-grade):
  - C2PA manifests for images/video where you want provenance assertions.
- Q3. Evidence packaging posture:
  - Each evidence atom outputs: source pointer, transform chain, derived artifacts list, and retention class.

-------------------------------------------------------------------------------
R) EDISCOVERY + LEGAL HOLD PLANE — Custodian mapping, retention, and exportability
-------------------------------------------------------------------------------
- R0. EDRM-aligned exports:
  - Export packs that map cleanly to standard eDiscovery phases (collection → processing → review → production).
- R1. Custodian and location registry:
  - Who/where each source came from; drives/folders/devices; collection method.
- R2. Retention schedules:
  - WORM-like “do not overwrite” constraints for canonical evidence stores; separate scratch/work dirs.

-------------------------------------------------------------------------------
S) SOFTWARE ASSURANCE PLANE — Security+quality by default, auditable by design
-------------------------------------------------------------------------------
- S0. Secure SDLC alignment:
  - Build and ship with recognized secure development practices.
- S1. Policy-as-code:
  - Gate releases on: signed commits, reviewed changes, reproducible builds, attestations present.
- S2. Threat models:
  - Document: adversaries, tampering vectors, supply-chain threats, data exfiltration threats.
- S3. “Hardening as artifacts”:
  - Every mitigation emits evidence (configs, policies, reports) that gets ingested as nodes/edges.

-------------------------------------------------------------------------------
ΩΩΩΩΩ INTEGRATION RULE (NON-NEGOTIABLE)
-------------------------------------------------------------------------------
- All planes above must integrate into the existing core chain:
  - Graph → Steps → Schemas → Validators → Compilers → Draft factories
- For each stage, require:
  - (1) Schema (what it is), (2) Validator (prove it), (3) Compiler (produce it), (4) Provenance (how), (5) Addressability (where), (6) Attestation (who), (7) Retrieval (get it), (8) Rebuildability (redo it).

-------------------------------------------------------------------------------
ΩΩΩΩΩ “CEILING-GRADE” COMPLETION CHECKLIST
-------------------------------------------------------------------------------
- One command can:
  - run an end-to-end pipeline,
  - produce a complete artifact graph,
  - emit lineage + trace + proofs,
  - generate draft packs,
  - and export a court-binder bundle.
- Every claim about any artifact can be:
  - traced (trace context),
  - replayed (lineage),
  - verified (validators),
  - and audited (transparency proofs).

