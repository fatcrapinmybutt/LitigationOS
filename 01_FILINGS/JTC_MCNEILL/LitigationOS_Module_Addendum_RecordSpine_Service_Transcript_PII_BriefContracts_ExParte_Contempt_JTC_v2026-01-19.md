# LitigationOS Higher-Court Harvest — Module Addendum (Record Spine → Service → Transcript → PII → Brief Contracts → Ex Parte → Contempt → JTC)
**Version:** v2026-01-19  
**Scope:** Michigan custody/parenting time + PPO/contempt + judicial-conduct (JTC) + higher-court routing (COA/MSC/original actions)  
**Outputs:** machine-checkable artifacts (JSON/CSV) + filing-ready draft factories gated by Proof Obligations (PCW/PCG)

---

## 0) Why these modules exist (fit in the LitigationOS operational loop)

These eight modules harden the **Record Spine** and **procedural proof layer** so higher-court work (COA/MSC/original actions) is built on a verifiable record:

- **Record Spine**: what was filed / when / what controls / what is missing.
- **ServiceChain**: who was served / how / when / proof / timing consequences.
- **Transcript**: what hearings matter / transcript ordered / received / gaps / escalation.
- **PII/Redaction**: MCR 1.109 compliance + correct nonpublic routing (MC 97/97a).
- **Brief/Pleading Contracts**: format/structure validators tied to rules & clerk IOPs.
- **Ex Parte Lane**: FOC 61 objection/rescind pipeline + procedure-following service tracking.
- **Contempt Lane**: due-process defect detection using MJI contempt checklist logic.
- **JTC Lane**: allegation units → evidence pointers → MCR 9.200 awareness + confidentiality gate.

---

## 1) Module specs (engineering + legal gates)

Each module defines:
- Inputs
- Extraction rules
- Artifacts (outputs)
- Proof Obligations (POs) with PCW states
- Validators (hard checks; fail-closed at PCG)

### 1.1 Record Spine module (ROA/case history + file-stamp classifier)

**Objective:** Build a canonical Register of Actions (ROA) + OrderChain + Filing chronology with file-stamp verification.

**Inputs**
- ZIP bundle; optional ROA export/PDF; MiFILE receipts; notices; orders.
- PDFs/images likely containing file stamps.

**Extraction rules**
- File-stamp classifier: detect stamp tokens (e.g., FILED/RECEIVED, court name, date/time, clerk).
- Extract file-stamp date/time and compare to signature date and service date (when present).
- ROA normalizer: parse ROA into rows `{entry_no, filed_date, title, party, disposition, pointer}`.
- Controlling-order resolver: for each lane (custody/PT/PPO/contempt/recusal), identify latest controlling order and supersession history.

**Artifacts**
- `record_spine.json` / `record_spine.csv`
- `order_chain.json` (supersession edges)
- `missing_radar.json` (missing orders/entries/stamps/notices)

**Core POs**
- PO_RS_001 ROA baseline captured (or acquisition task generated).
- PO_RS_002 Controlling orders identified per lane.
- PO_RS_003 File-stamp classification attempted for every candidate order/filing.

**Validators**
- No “control” assertion without a pointer to the file + stamp/ROA evidence.

---

### 1.2 ServiceChain module (proof-of-service capture + timing computations)

**Objective:** Convert service into computable events: proof-of-service evidence + deadline math.

**Inputs**
- Proofs of service, certificates of mailing, eService logs, USPS tracking, acknowledgments.

**Extraction rules**
- Extract served party, method, date/time, server identity, document list, and proof pointer.
- Compute derived deadlines (response windows, objection periods) anchored to service date.
- Tag method-specific defects (mail date unknown, certificate missing, wrong address, etc.).

**Artifacts**
- `service_chain.json` / `service_chain.csv`
- `service_deadlines.json` (deadlines + assumption log)
- `service_proof_index.json` (doc→service event links)

**Core POs**
- PO_SC_001 Every relied-on filing has a service event or explicit exception.
- PO_SC_002 Method+date sufficient to compute deadlines OR acquisition plan recorded.

**Validators**
- Every service event references a proof file or records a documented exception.

---

### 1.3 Transcript module (request packets + status ledger + “issue-critical hearing” tagging)

**Objective:** Ensure transcripts exist where required for COA/MSC and for due-process proof.

**Inputs**
- Hearing notices, orders referencing hearings, audio receipts, reporter contact/invoices.

**Extraction rules**
- Hearing enumerator: detect hearings from notices/orders/transcripts; build hearing list.
- Issue-critical tagging: custody/PT change, ex parte suspension, contempt/jail, evidentiary hearings, recusal, disputed evaluation reliance.
- Transcript request packet builder: request letter, payment/invoice, follow-up cadence, status ledger.

**Artifacts**
- `hearings_index.json`
- `transcript_ledger.json`
- `transcript_packet_checklist.csv`

**Core POs**
- PO_TR_001 All issue-critical hearings identified.
- PO_TR_002 Each issue-critical hearing has transcript status (requested/received/unavailable) with evidence.

**Validators**
- No “record defect” claim without linking the hearing + missing transcript evidence.

---

### 1.4 PII/Redaction module (MCR 1.109 scan + MC 97/97a routing)

**Objective:** Prevent rejection/sanctions and protect privacy by ensuring protected PII is handled under MCR 1.109.

**Inputs**
- All text-bearing files (PDF/DOCX/TXT/EML/MSG), including drafts.

**Scan**
- Detect PII patterns: DOB, SSN fragments, financial account numbers, DL/state ID patterns, minor identifiers, etc.
- Route protected PII to nonpublic packets using MC 97 / MC 97a where filing is necessary.

**Artifacts**
- `pii_scan_findings.json`
- `pii_routing_plan.json` (MC 97 vs MC 97a decisions)
- `redaction_worklist.csv`

**Core POs**
- PO_PII_001 PII scan completed for all intended-to-file documents.
- PO_PII_002 Protected PII redacted from public docs or routed to MC 97/97a.

**Validators**
- Fail if public-facing doc contains protected PII without routing record.

---

### 1.5 Brief/pleading structure contracts (COA/MSC/original actions) — hard validators

**Objective:** Convert clerk-facing rules/guides/IOPs into format contracts validated before filing.

**Contracts**
- COA principal brief (MCR 7.212)
- COA original action complaint (superintending control/original)
- MSC application for leave to appeal
- JTC Request for Investigation packet

**Artifacts**
- `structure_contracts.yaml`
- `structure_validation_report.json`

**Core POs**
- PO_FMT_001 Contract validation PASS for target court/vehicle.
- PO_FMT_002 Required sections and limits satisfied OR blocked with defect report.

---

### 1.6 Ex parte lane (FOC 61 auto-packet + procedure-following service tracker)

**Objective:** Turn ex parte suspensions into a clocked response lane with packet generation and service tracking.

**Artifacts**
- `exparte_lane.json` (order→objection timeline)
- `foc61_packet/` (compiled forms + exhibit list)
- `exparte_service_tracker.json`

**Core POs**
- PO_EP_001 Ex parte order anchored to service date (or gap recorded).
- PO_EP_002 FOC 61 packet built OR reasoned not-applicable record.

---

### 1.7 Contempt lane (MJI checklist-driven due-process defect detector)

**Objective:** Evaluate contempt proceedings for due-process and procedural defects and generate a defect report.

**Artifacts**
- `contempt_due_process_defects.json`
- `preservation_map_contempt.json`

**Core POs**
- PO_CT_001 Each contempt event has: initiating document + notice + hearing record pointer.
- PO_CT_002 Defect claims tied to transcript/record pointers.

---

### 1.8 JTC lane (allegation units + MCR 9.200 awareness + confidentiality gate)

**Objective:** Convert misconduct concerns into allegation units suitable for JTC RFI while enforcing confidentiality and nonpublic handling.

**Artifacts**
- `jtc_allegations.jsonl` (JSON lines; one allegation per line)
- `jtc_rfi_packet.md`
- `jtc_confidentiality_audit.json`

**Core POs**
- PO_JTC_001 Each allegation has at least one primary record pointer.
- PO_JTC_002 Confidentiality audit PASS.

---

## 2) Machine-checkable checklist + execution schema (YAML)

```yaml
version: "2026-01-19"
modes: [DISCOVERY, DRAFT, FILE_READY]
inputs:
  - id: zip_bundle
    type: path
    required: true

proof_obligations:
  - id: PO_RS_001
    required_in: [FILE_READY]
  - id: PO_SC_001
    required_in: [FILE_READY]
  - id: PO_TR_002
    required_in: [FILE_READY]
  - id: PO_PII_002
    required_in: [FILE_READY]
  - id: PO_FMT_001
    required_in: [FILE_READY]
  - id: PO_JTC_002
    required_in: [FILE_READY]

steps:
  - id: S01_inventory_manifest
    mode: DISCOVERY
    outputs: [outputs/manifest.json, outputs/manifest.csv]

  - id: S02_record_spine_build
    mode: DISCOVERY
    outputs: [outputs/record_spine.json]

  - id: S03_service_chain_build
    mode: DISCOVERY
    outputs: [outputs/service_chain.json]

  - id: S04_transcript_ledger_build
    mode: DISCOVERY
    outputs: [outputs/transcript_ledger.json]

  - id: S05_pii_scan
    mode: DISCOVERY
    outputs: [outputs/pii_scan_findings.json]

  - id: S06_structure_contract_validate
    mode: DRAFT
    outputs: [outputs/structure_validation_report.json]

  - id: S07_exparte_lane
    mode: DISCOVERY
    outputs: [outputs/exparte_lane.json]

  - id: S08_contempt_lane
    mode: DISCOVERY
    outputs: [outputs/contempt_due_process_defects.json]

  - id: S09_jtc_lane
    mode: DISCOVERY
    outputs: [outputs/jtc_allegations.jsonl]

pcg_gate:
  allow_if:
    - all_required_pos_satisfied: true
    - all_validations_passed: true
  block_if:
    - any_required_po_open_or_partial: true
    - any_validator_failed: true
```

---

## 3) Notes on the uploaded `COURT RULES.zip`

A deterministic ZIP manifest (CRC32 + bytes + mtime “IntegrityKey”) was generated:
- `court_rules_zip_manifest.csv`
- `court_rules_zip_manifest.json`
- `court_rules_zip_validity_findings.csv`

These files are included in the pack ZIP next to this specification.


## 4) Included unified JSON schema

- `schemas/litigationos_artifacts.schema.json`
