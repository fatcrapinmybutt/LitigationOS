# LitigationOS — MSC Risk Engine + JTC Milestone Engine + Unified RiskEvent Ontology (COA/MSC/JTC)
Version: v2026-02-08.1

This is a build-ready specification and ontology expansion that:

1) Implements **MSC Risk Engine** in parity with the COA dismissal-risk engine for:
   - **Presentation gate** (what prevents being “presented to the Court”)
   - **Defect cure** (what gets stricken/dismissed if not corrected)
   - **Return-without-docketing / reject-without-docketing** behaviors

2) Expands **JTC Milestone Engine** into a typed timeline that matches the public process narrative:
   - Intake → preliminary investigation → confidential disposition OR public disposition milestones
   - Public complaint track includes 28‑day letter, answer, master hearing, decision & recommendation, and Supreme Court review clocks.

3) Unifies **COA/MSC/JTC RiskEvents** into a single ontology so one dashboard can answer:
   - “What can kill this matter next?”
   - “What cures it fastest?”

---

## A. Unified ontology: `RiskEvent` (one dashboard, three systems)

### A1) Core nodes
- `Matter` — the litigation unit being tracked (lane + court posture + case identifiers).
- `RecordEvent` — a normalized record-spine event (filed/served/received/letter/transcript/etc.).
- `Clock` — a computed time window (start, due, basis).
- `Trigger` — the event or requirement that created the clock.
- `RiskEvent` — typed hazard state that can “kill” or derail a matter if uncured.
- `CureTask` — concrete action item(s) that can cure/mitigate the risk.
- `CommitSuite` — an atomic packaging commit (files + proofs + manifests) that closes one or more risks.

### A2) `RiskEvent` contract (functional, not restrictive)
Risk engines **never block outputs**. They always emit:
- `RiskEvent` (typed)
- `CurePlan` (typed tasks)
- optionally, `AltRoute` suggestions (vehicle selection fallback)

This allows results to be produced immediately while continuously minimizing dismissal/strike risk.

### A3) Key fields (dashboard-grade)
- `risk_kind` — court + hazard type (dismissal/strike/reject/presentation gate, etc.)
- `risk_state` — WATCH | AT_RISK | VIOLATED | CURED | MOOT
- `severity` — LOW | MED | HIGH | CRITICAL
- `clock.due_at` — “what date/time kills next”
- `cure_plan.tasks[]` — “what cures fastest” (sorted by due_at)

Schema included in the bundle: `schemas/risk_event_ontology.schema.json`.

---

## B. COA dismissal-risk engine: the reference behavior

### B1) COA risk anchors (what the engine watches)
**1) Docketing statement timing**
- COA Docketing Statement form warns that failure to timely file may lead to dismissal.  
- The form references MCR 7.204(H) and 7.205(E)(3) and states “within 28 days” in civil appeals.  
- MCR 7.204(H) includes a dismissal provision for failure to file a timely docketing statement.  

**2) Transcript certification timing**
- MC 501 indicates the certificate must be filed within 7 days after transcript is ordered on appeals to COA.  

**3) Briefing-clock triggers**
- MCR 7.211 contains “21 days after trial court decision or transcript filed, whichever is later” triggers in certain remand contexts (engine models this as a configurable clock basis).  

**4) IOP enforcement behaviors**
- COA IOPs describe deficiency letters and dismissal risk when docketing steps are not completed.

(Authority points cited in the narrative response.)

### B2) COA engine output format
COA emits `RiskEvents` such as:
- `COA_DOCKETING_STATEMENT_LATE_DISMISSAL_RISK`
- `COA_TRANSCRIPT_CERTIFICATE_MISSING`
- `COA_BRIEF_LATE_DISMISSAL_RISK`
- `COA_IOP_DEFICIENCY_NOTICE_UNCURED`

Each has CureTasks that are “doable” immediately (file, call clerk, order transcript, etc.).

---

## C. MSC Risk Engine — parity implementation

### C1) Presentation gate (MSC)
The MSC’s public case-processing guidance states that a filing is “not docketed” and “not presented to the Court” until proof of service is provided. It also notes that incomplete docketing delays processing.  
This becomes the MSC “presentation gate” risk type.

**RiskEvent:** `MSC_PRESENTATION_GATE_PROOF_OF_SERVICE_MISSING`  
**Trigger:** `filing_received_by_clerk` without `proof_of_service_filed`  
**Clock:** immediate (0‑day gate)  
**Cure:** serve + file proof of service.

### C2) Defect cure (MSC)
MSC case-processing guidance explains defect correction: certain defects may be curable, while time limits/grounds/required contents may not be curable, and noncompliance can lead to dismissal/strike.  
MSC Internal Operating Procedures also describe issuing defect letters (example: missing signature) and that failure to comply can result in the filing being stricken/dismissed.

**RiskEvent:** `MSC_DEFECT_LETTER_UNCURED_SIGNATURE_OR_FORMAT`  
**Trigger:** `clerk_defect_letter_received`  
**Clock:** cure window (defaults to configurable 14 days; override by letter’s terms)  
**Cure:** file corrected document exactly as specified; confirm cure receipt.

**RiskEvent:** `MSC_NONCONFORMING_PLEADING_STRICKEN_OR_DISMISSED`  
**Trigger:** `filing_nonconforming_flag` or defect-letter equivalent  
**Clock:** cure window  
**Cure:** replace with conforming pleading.

### C3) Return-without-docketing (MSC)
MSC IOPs describe filings that are rejected/returned without being docketed (including untimely motions for reconsideration), using phrases like “rejected without docketing” and “returned without being docketed.”  
This becomes an explicit risk type with CRITICAL severity.

**RiskEvent:** `MSC_REJECTED_WITHOUT_DOCKETING_UNTIMELY_OR_NONCONFORMING`  
**Trigger:** (a) known `filing_rejected_without_docketing`, or (b) inferred untimeliness (e.g., reconsideration filed after deadline)  
**Clock:** deadline clock (e.g., 21 days; configurable)  
**Cure:** obtain return reason; re-file corrected if allowed; otherwise route to alternate authorized vehicle.

### C4) MSC parity mapping table (COA ↔ MSC)
| Engine concept | COA implementation | MSC implementation |
|---|---|---|
| Presentation gate | Docketing statement + transcript certificate + fees (case “not ready”) | Proof-of-service gate: not docketed/presented until POS provided |
| Defect cure | Clerk deficiency letter cure window | Clerk defect letter; nonconforming pleadings; strike/dismiss if uncured |
| Return-without-docketing | Clerk refusal / dismissal risk via IOP enforcement | Reject/return without docketing for untimely/nonconforming filings |

---

## D. JTC Milestone Engine — typed timeline aligned to public process

### D1) Intake gate (RFI execution + submission method)
The JTC RFI form instructions require:
- original signature in front of a notary  
- submit by permitted method (and explicitly says not to submit by fax or e-mail)  
- keep copies because materials won’t be returned.  

**RiskEvent:** `JTC_RFI_NOT_PROPERLY_EXECUTED_OR_NOTARIZED`  
**RiskEvent:** `JTC_RFI_SUBMITTED_IMPROPERLY_FAX_EMAIL`

### D2) Preliminary investigation phase
Public JTC materials describe preliminary investigation by staff and Commission review, including judge comment in some cases (and required comment in some dispositions).

**Milestones (typed):**
- `JTC_INTAKE_RECEIVED`
- `JTC_PRELIM_INVESTIGATION_OPEN`
- `JTC_JUDGE_COMMENT_REQUESTED` (optional)
- `JTC_PRELIM_INVESTIGATION_COMPLETE`

### D3) Disposition split
**Confidential disposition** page describes closure possibilities (dismissal/no jurisdiction/unprovable) and confidential letters (letter of explanation) after investigation.  
**Public disposition** page describes “public proceedings” after preliminary investigation for serious allegations, including:
- 28‑day letter + response window
- public complaint
- answer due within 14 days
- discovery/witness exchange
- hearing before a master (like civil trial; MRE applies)
- master report → objections/briefing → Commission decision & recommendation
- record filed in Supreme Court within 21 days; petition to modify/reject within 28 days after service; Supreme Court de novo review.

These become typed milestones and clocks.

**Public track RiskEvents (examples):**
- `JTC_28_DAY_LETTER_RESPONSE_WINDOW`
- `JTC_PUBLIC_PROCEEDINGS_ANSWER_DUE`
- `JTC_MSC_RECORD_FILED_CLOCK`
- `JTC_MSC_PETITION_TO_MODIFY_OR_REJECT_DUE`

### D4) Confidentiality guardrail as a RiskEvent
The JTC confidentiality page cites constitutional and court-rule confidentiality (with limited exceptions) until a public complaint is issued.  
This becomes a “confidentiality breach risk” that can poison other filings if mishandled.

**RiskEvent:** `JTC_CONFIDENTIALITY_BREACH_RISK`  
**Cure:** quarantine non-public materials; package them separately under MEEK4 with access controls.

---

## E. Unification: one ontology, one dashboard

### E1) Unification rule
COA/MSC/JTC engines **must emit the same top-level RiskEvent schema**. The court-specific part is `risk_kind` (plus optional `source_ref` pointers). Everything else is stable.

### E2) Dashboard question 1: “What can kill this matter next?”
Compute:
- `risk_state ∈ {AT_RISK, VIOLATED}`
- rank by `severity` then `clock.due_at` (earliest first)
- show `risk_kind`, `due_at`, `cure_plan.summary`

### E3) Dashboard question 2: “What cures it fastest?”
Compute:
- open CureTasks across active risks
- rank by `due_at` + “effectiveness” heuristics (e.g., tasks that satisfy multiple risks rank higher)

### E4) Neo4j crosswire (core)
- `(Matter)-[:HAS_EVENT]->(RecordEvent)`
- `(Matter)-[:HAS_RISK]->(RiskEvent)`
- `(RiskEvent)-[:TRIGGERED_BY]->(Trigger)`
- `(RiskEvent)-[:HAS_CLOCK]->(Clock)`
- `(RiskEvent)-[:HAS_CURE_TASK]->(CureTask)`
- `(CommitSuite)-[:CURES]->(RiskEvent)`
- `(CommitSuite)-[:PACKS]->(Pack)` (evidence/record pack)

---

## F. Build-sequence integration (where this slots into your pipeline)

### F1) Where it runs
Risk engines run at **two** points in every cycle:
1) **Early** (immediately after Intake normalization) → catch deadline risks before drafting.
2) **Late** (right before packaging/compilation) → validate that defects are cured or explicitly logged with a cure plan.

### F2) Output contract for every cycle
- `RiskEventSet.json` (all risks)
- `CureTaskBoard.json` (open tasks)
- `KillNext.md` (top 10 kill risks + cure actions)
- `CureFast.md` (top 20 fastest cures)

(These are *system artifacts*, not exhibits.)

---

## G. Included implementation bundle
This bundle includes runnable stdlib-only engines and schemas:
- `engines/risk_engine_coa.py`
- `engines/risk_engine_msc.py`
- `engines/jtc_milestone_engine.py`
- `schemas/risk_event_ontology.schema.json`
- `dashboard/queries.cypher`

