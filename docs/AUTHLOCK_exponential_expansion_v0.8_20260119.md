# AUTHLOCK — Exponential Expansion Layer (v0.8) — GraphContracts + AuthorityTriples + VehicleMap Wiring (Append-Only)

This file accelerates the AUTHLOCK ecosystem by hardening the **graph contract layer** and the **forms-first vehicle layer**
so the authority stack becomes executable: authorities → propositions → proof obligations → vehicles → filings.

---

## 1) GraphContracts (node/edge schema) — authority-grade minimums

### 1.1 Authority nodes
#### AuthorityRef
Required fields:
- authority_id (stable)
- jurisdiction = "MI"
- authority_type (enum)
- issuer (MSC/COA/SCAO/Legislature/Court/etc.)
- title
- citation_string
- publication_status (PUB/UNPUB/NA)
- bindingness (BINDING/PERSUASIVE/OVL_FED/NONCONTROLLING)
- effective_start_date, effective_end_date (nullable)
- capture_date
- snapshot_id
- source_locator (URL or vault path)
- checksum / integrity_key

#### AuthoritySection
- section_id (stable)
- authority_id (FK)
- pinpoint (rule/subrule; article/section; statute subsection; paragraph range)
- anchors[] (structured anchors for re-extraction)
- text (verbatim; QUOTELOCK gated)
- token_count (for retrieval planning)
- extraction_provenance (tool + version)

#### AuthorityChangeEvent
- event_id
- authority_id
- event_type (PROPOSED/ADOPTED/EFFECTIVE/AMENDED/REPEALED)
- event_date
- ADM_file_no (if applicable)
- summary
- links[]

### 1.2 Caselaw nodes
#### CaseLawDecision
- case_id
- court_level (MSC/COA)
- publication_status
- decision_date
- official_citation
- docket/app_id (if known)
- topics[] (lane tags)
- negative_treatment (list) + treatment_sources[]

### 1.3 Proposition nodes
#### Proposition
- proposition_id
- proposition_text (short, atomic)
- lane
- vehicle_id (nullable in discovery)
- authority_pinpoints[] (AuthoritySection refs)
- bindingness_required (bool)
- status (DRAFT/VERIFIED/DEPRECATED)
- validator_notes

### 1.4 PCW nodes
#### ProofObligation
- po_id
- po_type (AUTH_BINDING, AUTH_PINPOINT, AUTH_IN_SNAPSHOT, QUOTELOCK_PASS, LOCAL_RULE_VALID, etc.)
- lane
- vehicle_id
- proposition_id (FK)
- required (bool)
- status (OPEN/PARTIAL/SATISFIED)
- evidence_refs[] (EvidenceAtom ids)
- authority_refs[] (AuthoritySection ids)
- test_spec (how to validate)
- validator_result (PASS/FAIL/WARN) + audit trail

---

## 2) VehicleMap (forms-first execution layer)

### 2.1 VehicleMap node types
- `Vehicle` (e.g., “Motion”, “Objection”, “Claim of Appeal”, “Superintending Control Complaint”, “JTC Complaint”)
- `Form` (SCAO/MC/FOC mandated use forms)
- `AttachmentRequirement` (what must be included)
- `ServiceChain` (who/how/when)
- `DeadlineRule` (authority-bound deadline logic)
- `CourtPreference` (e.g., “oral argument preferred” as operational guidance; tagged non-authoritative unless sourced)

### 2.2 Mapping edges
- Vehicle REQUIRES Form (mandatory forms-first)
- Vehicle CONTROLLED_BY AuthoritySection (procedural standards)
- Vehicle SATISFIES/CREATES ProofObligation
- Vehicle REQUIRES ServiceChain + DeadlineRule
- Vehicle SUPPORTS Lane

### 2.3 Validator rules (minimum)
- A Vehicle cannot be FILE_READY unless:
  - all required POs are SATISFIED
  - all citations are in-snapshot
  - all verbatim quotes are QUOTELOCK_PASS
  - all local rules/LAOs used are VALIDATED_LOCAL
  - service chain is complete with address/fee/mileage rules as applicable

---

## 3) AuthorityTriples (Proposition ↔ Authority ↔ Pinpoint) — enforceable pattern

### 3.1 Triple schema
- triple_id
- proposition_id
- authority_section_id
- claim_strength (BINDING/PERSUASIVE)
- lane
- usage_role (elements, standard, procedure, deadline, remedy, evidence rule)
- notes

### 3.2 “No-claim” rule enforcement
Every filing-facing claim MUST map to ≥1 triple with:
- binding authority for the lane/court, OR
- explicit persuasive justification.

---

## 4) Bloom perspective pack (deterministic visualization)

### 4.1 Labels and colors (deterministic)
- AuthorityRef: label by authority_type (MCR/MCL/MRE/CONST/AO/etc.)
- Proposition: label by lane + status
- ProofObligation: label by status (OPEN/PARTIAL/SATISFIED)
- Vehicle/Form: label by vehicle type

### 4.2 Bloom import checklist
- Constraints (unique ids)
- Indexes (authority_id, section_id, proposition_id, po_id)
- Relationship types imported before styling
- Styles applied from a single JSON preset file
- Verification query pack (counts + orphan checks + “no-claim” checks)

---
Append-only note: v0.8 is designed to be directly compatible with “Graph contracts + Bloom perspective pack + AuthoritySnapshot ingestion + PO/PCW overlay” requirements.
