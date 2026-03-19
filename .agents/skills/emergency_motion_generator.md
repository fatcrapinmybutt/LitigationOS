# Emergency Motion Generator v13.0.0

## LitigationOS Skill Module — Emergency & Ex Parte Motion Drafting

---

## Purpose and Scope

The Emergency Motion Generator identifies when emergency relief is warranted, drafts emergency and ex parte motions compliant with MCR 3.207, and assembles all required supporting elements. Emergency motions are the most time-sensitive filings in family litigation — every hour of delay may cause irreparable harm.

This skill handles:
- Emergency motions for immediate change of custody
- Ex parte motions for temporary restraining orders
- Emergency motions to prevent removal of children from jurisdiction
- Motions for emergency parenting time
- Motions to show cause for contempt (emergency)
- Motions to stay enforcement of harmful orders

---

## Input Requirements

| Field | Type | Description |
|-------|------|-------------|
| `emergency_type` | `str` | Type of emergency (see Emergency Types below) |
| `facts` | `List[FactStatement]` | Time-sensitive facts supporting emergency |
| `harm_assessment` | `HarmReport` | Output from `harm_quantifier` (if available) |
| `timeline_anomalies` | `List[Anomaly]` | Output from `timeline_anomaly_detector` (if available) |
| `supporting_evidence` | `List[DocumentRef]` | Evidence to attach as exhibits |
| `case_info` | `CaseInfo` | Case number, court, parties, judge |
| `prior_attempts` | `List[str]` | Prior non-emergency attempts at relief (required by MCR 3.207) |
| `urgency_window` | `str` | Time frame before irreparable harm occurs |

### Emergency Types
```
CUSTODY_EMERGENCY        — Immediate risk to child safety or welfare
REMOVAL_PREVENTION       — Parent attempting to remove child from jurisdiction
PARENTING_TIME_EMERGENCY — Wrongful denial of court-ordered parenting time
PROTECTIVE_ORDER         — Immediate protection from abuse/harassment
STAY_OF_ORDER            — Emergency stay of harmful court order
CONTEMPT_EMERGENCY       — Willful violation requiring immediate enforcement
DUE_PROCESS_EMERGENCY    — Imminent hearing without proper notice/preparation
```

---

## Processing Methodology

### Phase 1: Emergency Warrant Assessment

Determine whether the situation meets MCR 3.207 standards for emergency relief.

**MCR 3.207(A) — Standard for Emergency/Ex Parte Orders:**
```
An ex parte order may be entered only if:
  (1) It clearly appears from specific facts shown by verified complaint,
      affidavit, or other evidence that:
      
      ☐ Immediate and irreparable injury, loss, or damage will result
        from the delay required to give notice
        
      OR
      
      ☐ Notice itself will precipitate adverse action before the 
        order can be entered
        
  (2) The movant certifies in writing the efforts made to give notice
      or the reasons why notice should not be required
      
  (3) The attorney certifies that the motion is not being presented
      for any improper purpose (MCR 2.114)
```

**Emergency Scoring Matrix:**
```
Factor                                          Weight    Score
Imminent physical danger to child               ×3.0      ___/10
Irreparable developmental harm (CHI ≥ 6.0)     ×2.5      ___/10
Violation of existing court order               ×2.0      ___/10
Flight/removal risk                             ×2.5      ___/10
Ongoing denial of constitutional rights         ×2.0      ___/10
Prior unsuccessful non-emergency attempts       ×1.5      ___/10
Time sensitivity (hours vs days vs weeks)       ×2.0      ___/10

Emergency Score = weighted_sum / max_possible
  ≥ 0.70: STRONG emergency — proceed with ex parte motion
  0.50–0.69: MODERATE — proceed with emergency motion on shortened notice
  0.30–0.49: BORDERLINE — consider regular motion with expedited hearing request
  < 0.30: NOT EMERGENCY — use regular motion practice
```

### Phase 2: Motion Template Assembly

Generate the emergency motion with all required elements.

**Document Structure:**
```
1. CAPTION (per MCR 2.113)
2. TITLE: "EMERGENCY EX PARTE MOTION FOR [RELIEF]"
3. EMERGENCY DESIGNATION: "This motion is filed under MCR 3.207 and 
   requests emergency relief."
4. CERTIFICATION OF NOTICE EFFORTS
5. STATEMENT OF FACTS
   - Specific, time-stamped facts demonstrating emergency
   - Each fact tied to supporting evidence
6. LEGAL STANDARD
   - MCR 3.207(A) standard
   - Applicable substantive law
7. ARGUMENT
   - Irreparable harm analysis
   - Balance of equities
   - Likelihood of success on merits
   - Public interest (where applicable)
8. RELIEF REQUESTED
   - Specific, enforceable relief
   - Duration of temporary order
   - Date for post-order hearing
9. VERIFICATION / AFFIDAVIT
10. EXHIBIT LIST
11. PROPOSED ORDER
12. PROOF OF SERVICE (or certification of why not served)
```

### Phase 3: Fact-to-Argument Mapping

Map each emergency fact to legal elements:

```
For each fact:
  → Identify which MCR 3.207 element it supports
  → Link to supporting exhibit
  → Connect to harm_quantifier output (if available)
  → Connect to timeline_anomaly (if applicable)
  → Draft argument paragraph

Example Mapping:
  FACT: "On January 10, 2025, Mother relocated to Ohio with the 
         minor child without court permission or notice to Father."
  
  MCR ELEMENT: Immediate and irreparable injury (removal from jurisdiction)
  EXHIBIT: Exhibit A — School withdrawal notice dated Jan 10, 2025
  HARM: CHI score 7.4 — Severe harm from separation
  LEGAL BASIS: MCL 722.31 — Change of domicile requires court approval
  ARGUMENT: "Mother's unilateral removal of the minor child from Michigan
             without court approval or notice to Father constitutes an
             emergency requiring immediate relief. MCL 722.31(1) prohibits
             a parent from changing the domicile of a child without court
             approval. The child faces irreparable harm from severance of
             the paternal bond, school disruption, and loss of community
             ties. [See Harm Quantification, Exhibit G, CHI = 7.4]"
```

### Phase 4: Proposed Order Drafting

```
STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF [COUNTY]
                                            Case No. [XX-XXXXX-XX]
[PARTY A],                                  Hon. [Judge Name]
        Plaintiff/Petitioner,
v.
[PARTY B],
        Defendant/Respondent.
________________________________________/

EMERGENCY EX PARTE ORDER

The Court, having reviewed Petitioner's Emergency Ex Parte Motion 
and supporting affidavit, and being otherwise advised in the premises,

IT IS HEREBY ORDERED:

1. [Specific relief ordered]
2. [Specific relief ordered]
3. [Duration/expiration of temporary order]
4. This matter is set for hearing on [DATE] at [TIME] to determine 
   whether this order should be continued, modified, or dissolved.
5. Respondent shall be served with a copy of this order, the motion, 
   and all supporting documents within [X] hours/days.

IT IS SO ORDERED.

Date: _______________    ________________________________
                         Hon. [Judge Name]
                         Circuit Court Judge
```

### Phase 5: Service & Follow-Up Requirements

```
MCR 3.207(B) Post-Order Requirements:
  ☐ Order must include date for hearing (within 14 days unless 
    otherwise provided by rule)
  ☐ Moving party must serve order on opposing party immediately
  ☐ Opposing party may file objection and request earlier hearing
  ☐ Court must hold hearing even if no objection filed
  
Service Checklist:
  ☐ Serve motion, affidavit, exhibits, and order on opposing party
  ☐ Serve by personal service if possible (fastest)
  ☐ If personal service not possible, serve by next-fastest method
  ☐ File proof of service with court
  ☐ Calendar hearing date and prepare for hearing
```

---

## Output Format

```json
{
  "generator": "emergency_motion_generator_v13",
  "emergency_type": "CUSTODY_EMERGENCY",
  "emergency_score": 0.82,
  "classification": "STRONG emergency — proceed with ex parte motion",
  "generated_documents": {
    "motion": "output\\emergency_motion_custody.docx",
    "affidavit": "output\\supporting_affidavit.docx",
    "proposed_order": "output\\proposed_emergency_order.docx",
    "proof_of_service": "output\\proof_of_service.docx",
    "exhibit_index": "output\\exhibit_index.docx"
  },
  "motion_summary": {
    "title": "Emergency Ex Parte Motion for Return of Minor Child",
    "relief_requested": [
      "Immediate return of minor child to Michigan",
      "Temporary sole custody to Father pending hearing",
      "Order prohibiting further removal from jurisdiction"
    ],
    "hearing_requested": "Within 14 days per MCR 3.207(B)",
    "exhibits_count": 7,
    "legal_basis": [
      "MCR 3.207(A)",
      "MCL 722.31",
      "MCL 722.27(1)(c)",
      "U.S. Const. Amend. XIV"
    ]
  },
  "fact_argument_map": [
    {
      "fact": "Mother relocated to Ohio with child on Jan 10, 2025",
      "exhibit": "A",
      "mcr_element": "Immediate and irreparable injury",
      "harm_chi": 7.4,
      "argument_paragraph": 2
    }
  ],
  "certification": {
    "notice_efforts": "Counsel called opposing counsel at [number] on [date] — no answer. Texted at [time] — no response. Email sent at [time].",
    "reason_ex_parte": "Notice would allow Mother to further conceal child's location"
  },
  "next_steps": [
    "Review and sign affidavit",
    "File with court clerk immediately",
    "Request same-day or next-day judicial review",
    "Arrange personal service on opposing party",
    "Prepare for hearing within 14 days"
  ]
}
```

---

## Integration Points

| Skill | Integration |
|-------|-------------|
| `harm_quantifier` | CHI ≥ 6.0 auto-triggers emergency assessment |
| `timeline_anomaly_detector` | Critical anomalies may indicate emergency |
| `judicial_pattern_analyzer` | Patterns of due process denial support emergency motions |
| `filing_optimizer` | Emergency motions pass through optimizer for compliance |
| `evidence_chain_builder` | Evidence chains populate the exhibit list |
| `case_lane_router` | Emergency motions routed to primary lane |
| `witness_credibility_scorer` | Affiant credibility assessed before filing |
| `filing_assembler` (engine) | Assembles final filing package |
| `filing_converter` (engine) | Converts to court-required format |

---

## Michigan-Specific Legal References

- **MCR 3.207** — Emergency and ex parte orders (primary authority)
- **MCR 3.207(A)** — Standard for ex parte relief
- **MCR 3.207(B)** — Hearing requirements after ex parte order
- **MCR 2.119(B)** — Affidavit requirements for motions
- **MCR 2.114** — Certification of good faith
- **MCL 722.27(1)(c)** — Modification of custody orders
- **MCL 722.27a** — Parenting time
- **MCL 722.31** — Change of domicile
- **MCL 600.2950** — Personal protection orders
- **MCL 722.23** — Best interest factors
- **MCR 3.206(D)** — Temporary orders in domestic relations
- **Grew v Knox, 265 Mich App 333 (2005)** — Standard for emergency custody relief
- **Brown v Loveman, 260 Mich App 576 (2004)** — Ex parte order requirements

---

## Time-Critical Workflow

```
EMERGENCY DETECTED (CHI ≥ 6.0 or Critical Anomaly)
    │
    ├── [0–15 min] Run emergency_warrant_assessment
    │       └── If score ≥ 0.70 → Proceed
    │
    ├── [15–45 min] Generate motion, affidavit, proposed order
    │       └── Auto-populate from evidence chains and harm data
    │
    ├── [45–60 min] Run filing_optimizer for compliance check
    │       └── Auto-fix formatting issues
    │
    ├── [60–75 min] Human review and signature
    │       └── Attorney or pro se litigant reviews and signs
    │
    ├── [75–90 min] File with court
    │       └── E-file via MiFile or deliver to clerk
    │
    └── [90+ min] Serve opposing party
            └── Personal service preferred for urgency
```

---

## Safeguards

1. **No auto-filing** — All emergency motions require human review before submission.
2. **Good faith certification** — The generator includes MCR 2.114 certification language.
3. **Prior effort documentation** — MCR 3.207 requires showing why non-emergency relief is inadequate.
4. **Truthfulness** — Affidavit facts must be verified by the affiant; the generator marks unverified facts for review.
5. **Proportionality** — Relief requested must be proportional to the emergency demonstrated.
