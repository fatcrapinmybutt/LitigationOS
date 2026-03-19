# LitigationOS Pipeline Stages — Graph → Draft Factories (Ceiling + “GOD LEVEL”)
**Build date (America/Detroit): 2026-01-19**  
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
  - `EVID_TRANSCRIPT_LINE` (p:l)
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
- Encode Truth/Quote/Authority/Vehicle/Service/Deadline constraints as **policy** (OPA/Rego-style rules)
- Output: **explainable gate results** (why blocked, minimal conditions to unblock)
- Removes “hand-coded” ad hoc gating logic across modules.

### 3) Unsat-Core / Minimal-Missing Proof Extraction
When POs fail, compute a minimal set of missing atoms/links:
- **Unsat core** = smallest missing evidence/authority pinpoints blocking filing
- Output: `pcw_unsat_core.json` + ranked acquisition plan.

### 4) Formal Procedure Model Checking (stronger than “validation”)
- Move beyond “report checks” to **formal properties** and counterexample traces
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
- Explainable failures + minimal unblock set.

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
