# LitigationOS Glossary + Judicial Crosswire Build Sequence (COA / MSC / JTC)

This document is a **results-producing glossary + build sequence**. Every term is defined as an object with:
- a role in the build pipeline,
- a concrete data shape,
- and **court-enforcement semantics** (how the court actually treats the thing).

---

## 0) Operating stance: “always produce,” while modeling enforcement

LitigationOS runs two loops at the same time:

1. **Production Loop (always-on):** Every intake produces at least one usable output pack (*DraftPack*).
2. **Compliance/Risk Loop (always-on):** In parallel, the system converts missing items into typed *RiskEvents* and *AcquisitionTasks* and incrementally upgrades the pack toward file-ready.

This prevents “paralysis by complexity” while still respecting real dismissal/strike/return behaviors.

---

## 1) Build sequence (what comes before SCHEMA, SCHEMA, what comes after)

### 1.1 BEFORE SCHEMA (pre-model prerequisites)

**Goal:** make sure the model can *produce court outputs* the day the schema exists.

**Pre-SCHEMA artifacts:**
- **CourtMap**: what courts exist in-scope (trial, COA, MSC; plus JTC as conduct/discipline channel).
- **LaneMap**: MEEK1–MEEK4 (housing / custody / PPO-contempt / judicial conduct).
- **VocabularySeed**: first-pass glossary of core terms and synonyms (this doc).
- **OutputContracts**: definition of “result” (DraftPack vs FileReadyPack vs CommitSuite).
- **EventTaxonomy**: canonical TriggerEvent / Clock / RiskEvent types.
- **IDPolicy**: deterministic identifiers for (Case, Filing, Service, EvidenceAtom, RiskEvent).
- **RecordSpinePrimitive**: what counts as “record” objects for each court channel.
- **AuthorityPlan**: how authority is stored (snapshots/registries) and how pinpoints attach.

### 1.2 SCHEMA (typed graph model)

**SCHEMA must support:**
- **Core legal objects:** cases, parties, orders, filings, service, exhibits, transcripts.
- **Procedural semantics:** “filed vs received vs served vs docketed vs presented.”
- **Appellate enforcement:** deficiency letters, cure windows, involuntary dismissal tracking.
- **JTC semantics:** RFI intake, investigation milestones, disposition stages.

**Schema design rule:** If you cannot map a term to:
- a TriggerEvent, OR
- a Clock, OR
- a RiskEvent, OR
- a Pack output,
then it’s not “real” enough to keep.

### 1.3 AFTER SCHEMA (engines + registries + packagers)

Once schema is stable, build:
- **Registries**: AuthorityRegistry / FormRegistry / IOPRegistry / DeadlineRegistry.
- **Engines**: IntentRouter, VehicleSelector, ClockEngine, RiskEngines, Packager.
- **Audit**: ProvenanceIndex, RunLedger, CommitSuite receipts.
- **GraphOps**: Upsert contracts, constraints, indexes, bloom perspectives.

---

## 2) Glossary (core terms)

Each term includes:
- **Definition**
- **Data shape**
- **Pipeline position**
- **Judicial enforcement semantics**
- **Failure mode**

---

# A) Design + modeling terms

## Term: SCHEMA
- **Definition:** Canonical typed model of LitigationOS objects + relationships.
- **Data shape:** `{schema_version, node_types[], edge_types[], constraints[], indexes[], validators[]}`
- **Pipeline position:** SCHEMA
- **Judicial semantics:** Must represent “missing item → clerk notice → cure window → dismissal/strike/return.”
- **Failure mode:** Nice graph; cannot produce packs or compute deadlines.

## Term: Ontology
- **Definition:** Meaning layer (what a type is and how it behaves).
- **Data shape:** `{term_id, label, definition, synonyms[], governed_by[]}`
- **Pipeline position:** pre-SCHEMA → SCHEMA
- **Judicial semantics:** Distinguish “filed” (submitted) from “received” (clerk receipt), and “docketed” from “presented.”

## Term: Registry
- **Definition:** Curated list of canonical items (forms, rules, IOPs, authority).
- **Data shape:** `{registry_id, item_type, items[], last_refresh_ts}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** IOPs function like an enforcement “surface.” They must be treated as first-class constraints.

## Term: AuthoritySnapshot
- **Definition:** Frozen authority corpus version used for drafting and checks.
- **Data shape:** `{snapshot_id, sources[], effective_date, hash_receipts[]}`
- **Pipeline position:** pre-SCHEMA policy + post-SCHEMA implementation
- **Judicial semantics:** Deadlines and defect processes are strict; drift matters.

## Term: AuthorityTriple
- **Definition:** Atomic mapping: (rule/standard) + (pinpoint) + (what it controls).
- **Data shape:** `{triple_id, authority_ref, pinpoint, controls:{term_id|vehicle_id|risk_type|clock_type}}`
- **Pipeline position:** post-SCHEMA enrichment
- **Judicial semantics:** Enables “why is this required?” explanations in court-ready form.

## Term: CourtSemantics
- **Definition:** Court-specific meaning rules for states/actions.
- **Data shape:** `{court, semantics_version, state_machine_defs[]}`
- **Pipeline position:** SCHEMA + post-SCHEMA engine config
- **Judicial semantics:** Example: MSC “presented to Court” is gated by proof of service; COA dismissal tracking is keyed to specific missing filings.

## Term: EnforcementBehavior
- **Definition:** Court practice that triggers consequences when requirements aren’t met.
- **Data shape:** `{behavior_id, court, trigger, consequence, cure_rules[]}`
- **Pipeline position:** post-SCHEMA (IOPRegistry + RiskEngines)
- **Judicial semantics:** Defect letters + cure windows, strike, administrative dismissal, return without docketing.

---

# B) Workflow / runtime terms

## Term: HarvestCycle
- **Definition:** One complete intake→extract→model→pack run.
- **Data shape:** `{cycle_id, inputs[], outputs[], run_logs[]}`
- **Pipeline position:** runtime
- **Judicial semantics:** Every cycle must produce a usable DraftPack, plus a risk/clock report.

## Term: IntakeSlice
- **Definition:** A bounded subset of the corpus being processed (folder, date range, case).
- **Data shape:** `{slice_id, scope_query, source_paths[]}`
- **Pipeline position:** ingest
- **Judicial semantics:** Must be able to slice by court case number, order date, or “clerk letter” to support quick responses.

## Term: IntentRouter
- **Definition:** Chooses target lane/court/posture/goals from the intake.
- **Data shape:** `{intent_id, lane, court, posture, goal, confidence}`
- **Pipeline position:** early post-SCHEMA
- **Judicial semantics:** Prevents wrong-vehicle filings; when uncertain, generate multi-vehicle DraftPacks and attach RiskEvents.

## Term: VehicleSelector
- **Definition:** Maps intent to the procedural vehicle(s).
- **Data shape:** `{selection_id, candidates[], chosen[], rationale}`
- **Pipeline position:** post-SCHEMA engine
- **Judicial semantics:** COA vs MSC “first-instance” constraints, and JTC’s RFI-only intake.

## Term: Posture
- **Definition:** Current procedural state (order entered, hearing set, appeal pending, etc.).
- **Data shape:** `{posture_id, court, state, basis_event_id}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** Posture determines which clocks and risks exist.

---

# C) Record + evidence terms (truth layer)

## Term: EvidenceAtom
- **Definition:** Smallest citeable evidence unit (page, image, email, transcript excerpt).
- **Data shape:** `{atom_id, source_path, kind, captured_ts, excerpt, integrity_key, provenance}`
- **Pipeline position:** extraction + model
- **Judicial semantics:** Drives appendix/record citations; also drives JTC attachments (copies, not originals).

## Term: RecordSpine
- **Definition:** Ordered chain of file-stamped entries + service proofs anchoring “what happened.”
- **Data shape:** `{case_id, entries[{date, doc_type, stamp, served?, service_proof?}]}`
- **Pipeline position:** pre-SCHEMA concept → post-SCHEMA operational
- **Judicial semantics:** Appellate enforcement is spine-driven: missing key filings triggers dismissal risk.

## Term: TranscriptUnit
- **Definition:** Transcript ordering, certification, filing, and notice events as a single tracked object.
- **Data shape:** `{transcript_id, ordered_date, certificate_filed_date, filed_date, notice_filed_date}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** COA practice materials warn that missing “Stenographer’s Certificate” can lead to dismissal risk.

## Term: QuoteDB
- **Definition:** Verbatim quote store with provenance.
- **Data shape:** `{quote_id, text, pinpoint, method, evidence_atom_id}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** Powers rebuttal packs and contradiction maps.

---

# D) Time + enforcement terms (TriggerEvent / Clock / RiskEvent)

## Term: TriggerEvent
- **Definition:** Procedural event that starts/changes obligations.
- **Data shape:** `{event_id, event_type, occurred_at, court, related_ids[]}`
- **Pipeline position:** taxonomy pre-SCHEMA; ingestion post-SCHEMA
- **Judicial semantics:** COA clerk letters, transcript ordering, MSC defect notices, JTC milestone actions.

## Term: Clock
- **Definition:** Computed deadline derived from rule + TriggerEvent.
- **Data shape:** `{clock_id, trigger_event_id, rule_ref, start_date, due_date, status}`
- **Pipeline position:** post-SCHEMA (ClockEngine)
- **Judicial semantics:** Cure windows and filing deadlines; strictness differs by court.

## Term: ClockEngine
- **Definition:** Computes and maintains clocks; emits “late/at-risk” signals.
- **Data shape:** `{engine_version, calendars[], computation_rules[]}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** Must model cure windows from clerk notices and “receipt by clerk” filing logic for MSC.

## Term: RiskEvent
- **Definition:** Typed risk that can cause dismissal/strike/return or loss of consideration.
- **Data shape:** `{risk_id, risk_type, court, severity, triggered_by, cure_by, status}`
- **Pipeline position:** post-SCHEMA (RiskEngines)
- **Judicial semantics:** COA dismissal risk pathways; MSC administrative dismissal/strike; JTC process-related risks (confidentiality, submission rules, missing attachments).

## Term: DefectLetter
- **Definition:** Clerk notice of missing/nonconforming items plus cure period.
- **Data shape:** `{letter_id, court, sent_date, deficiencies[], cure_window_days}`
- **Pipeline position:** post-SCHEMA
- **Judicial semantics:** COA civil appeal guide explains 21-day cure before dismissal for missing items; MSC IOPs describe defect letters and cure windows.

---

# E) Packaging + commit terms (output production)

## Term: Pack
- **Definition:** A structured bundle of documents + metadata produced by LitigationOS.
- **Data shape:** `{pack_id, pack_type, contents[], manifests[], run_logs[]}`
- **Pipeline position:** post-SCHEMA output
- **Judicial semantics:** Must align to court vehicle requirements.

## Term: DraftPack
- **Definition:** Usable output even with gaps; includes explicit RiskEvents and acquisition tasks.
- **Data shape:** `{pack_id, gaps[], risk_events[], next_actions[]}`

## Term: FileReadyPack
- **Definition:** Pack that satisfies core filing requirements for the vehicle.
- **Data shape:** `{pack_id, validation_pass=true, service_proofs[], fee_status}`

## Term: CommitSuite
- **Definition:** Audit-ready receipts: manifests + provenance + risk/clock reports.
- **Data shape:** `{commit_id, pack_id, manifest, provenance_index, risk_report, clock_report}`

---

# F) Court overlays (COA / MSC / JTC)

## Term: DocketingStatement (COA)
- **Definition:** Post-claim-of-appeal filing required by COA practice.
- **Judicial semantics:** COA clerk IOPs: docketing statement within 28 days; failure triggers letter; omission not cured within 21 days risks dismissal path.

## Term: InvoluntaryDismissalDocket (COA)
- **Definition:** COA tracking workflow where overdue required items are escalated.
- **Judicial semantics:** COA IOPs describe overdue tracking for docketing statement, stenographer’s certificate, notice of filing transcript, and appellant’s brief, with warning + 21-day cure before submission.

## Term: StenographerCertificate (COA)
- **Definition:** Court reporter certificate after transcript ordered.
- **Judicial semantics:** COA civil appeal guide explains appellant responsibility to ensure certificate is filed; missing certificate can lead to dismissal risk.

## Term: ProofOfService (MSC)
- **Definition:** Proof service on parties (MSC form exists).
- **Judicial semantics:** MSC materials: docketing not complete / matter not presented until proof of service is provided; MSC IOPs describe proof-of-service letter and potential administrative dismissal if not provided.

## Term: NonconformingPleading (MSC)
- **Definition:** Filing not in substantial compliance.
- **Judicial semantics:** MSC IOPs: cure within specified period (often 14 or 21 days); nonconforming pleading may be stricken if not corrected.

## Term: ReturnWithoutDocketing (MSC)
- **Definition:** Late jurisdictional filings returned without docketing.
- **Judicial semantics:** MSC IOPs emphasize strict time enforcement and “filing” meaning actual receipt by clerk.

## Term: RequestForInvestigation (RFI) (JTC)
- **Definition:** JTC intake vehicle (complaint submission form).
- **Judicial semantics:** Instructions: attach copies not originals; keep your own copy; do not submit by fax/email; signature notarization required.

## Term: PreliminaryInvestigation (JTC)
- **Definition:** Investigation phase at Commission direction.
- **Judicial semantics:** JTC process description includes contacting witnesses, reviewing records, observing proceedings.

## Term: 28DayLetter (JTC)
- **Definition:** Notice of charges to judge before public complaint.
- **Judicial semantics:** Public disposition description: judge has 28 days to respond (extendable for good cause).

---

## 3) COA dismissal-risk engine (typed RiskEvents)

**Purpose:** Convert every COA enforcement checkpoint into:
- TriggerEvent → Clock → RiskEvent → CurePlan → Pack delta.

**Key checkpoints (from COA clerk IOPs and COA civil appeal guide):**
- Docketing statement timing + cure window
- Stenographer’s certificate
- Notice of filing transcript
- Appellant’s brief
- Deficiency cure window (21 days after letter) before dismissal escalation

**Output artifacts:**
- `RiskReport_COA.md`
- `CureChecklist_COA.csv`
- `DeficiencyLetterTracker.jsonl`

---

## 4) MSC enforcement crosswire

**Key gates:**
- **Presentation gate:** MSC materials: matter not presented until proof of service provided.
- **Defect correction:** most defects curable within clerk-specified time; IOPs describe common cure windows and strike consequences.
- **Strict timeliness:** IOPs emphasize late filings returned without docketing; filing is receipt by clerk.

---

## 5) JTC (MEEK4) packaging alignment

**Hard constraints from intake materials:**
- RFI form required; attach copies; do not fax/email; keep your copy; notarized signature.
**Process crosswire from public descriptions:**
- preliminary investigation may include witness contact, record review, courtroom observation;
- serious cases may proceed through 28-day letter before public complaint.

---

## 6) Next delta expansions (append targets)
- Add a **MSC Risk Engine** parallel to COA dismissal-risk engine.
- Expand a **JTC Milestone Engine** (screening → prelim investigation → disposition) with evidence bundle templates keyed to likely investigative actions.
- Add a **Unified RiskEvent Ontology** so COA/MSC/JTC risks roll up in one dashboard.
