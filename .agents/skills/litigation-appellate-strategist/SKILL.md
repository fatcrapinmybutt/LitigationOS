---
name: litigation-appellate-strategist
description: >-
  Use when preparing Michigan appellate filings, selecting standards of review, preserving issues for appeal, or architecting briefs for COA or MSC.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: appeal, COA, MSC, appellate, brief, standard of review
---

# litigation-appellate-strategist

## Metadata

```yaml
name: litigation-appellate-strategist
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when preparing Michigan appellate filings, designating the record on
  appeal, preserving issues for review, selecting standards of review,
  architecting appellate briefs, or preparing for oral argument before the
  Michigan Court of Appeals or Michigan Supreme Court.
metadata:
  triggers:
    - appellate brief
    - Court of Appeals
    - COA filing
    - MSC application
    - standard of review
    - record on appeal
    - issue preservation
    - appellate strategy
    - MCR 7.201
    - oral argument
  lanes:
    - A: Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)
    - B: Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)
    - C: Convergence/County (Muskegon County, 14th Circuit)
  court: 14th Judicial Circuit, Muskegon County
  appellate_courts:
    - Michigan Court of Appeals (COA)
    - Michigan Supreme Court (MSC)
  case: Pigors v Watson
  dependencies:
    - litigation-authority-validator
    - litigation-filing-packager
    - litigation-brain-spec
```

---

## Purpose

Appeals are won or lost before the brief is written. Issue preservation at the
trial level, proper record designation, correct standard of review selection,
and strategic brief architecture determine outcomes far more than eloquent
writing. This skill enforces appellate discipline from trial-level preservation
through COA filing, MSC application, and oral argument preparation.

---

## Decision Tree

```
ENTRY: Appellate action needed
│
├─ Q1: What stage are we at?
│   ├─ PRE-TRIAL ─────── → BRANCH A: Issue Preservation Protocol
│   ├─ TRIAL ─────────── → BRANCH B: Real-Time Preservation
│   ├─ POST-JUDGMENT ──── → BRANCH C: Appeal Initiation
│   ├─ COA BRIEFING ───── → BRANCH D: Brief Architecture
│   ├─ COA DECIDED ────── → BRANCH E: MSC Application
│   └─ ORAL ARGUMENT ──── → BRANCH F: Argument Preparation
│
├─ BRANCH A: Issue Preservation Protocol
│   ├─ Step 1: Identify all potential appellate issues
│   ├─ Step 2: Ensure each issue raised in trial court (MCR 2.517)
│   ├─ Step 3: Make specific objections on the record
│   ├─ Step 4: Request findings of fact on each issue
│   ├─ Step 5: File post-judgment motions preserving issues
│   └─ OUTPUT: preservation_checklist
│
├─ BRANCH B: Real-Time Preservation
│   ├─ Step 1: Object with specificity at each critical moment
│   ├─ Step 2: Request court reporter note key exchanges
│   ├─ Step 3: Make offer of proof for excluded evidence
│   ├─ Step 4: Move for directed verdict / JNOV as appropriate
│   └─ OUTPUT: trial_preservation_log
│
├─ BRANCH C: Appeal Initiation
│   ├─ Step 1: Calculate appeal deadline (MCR 7.204)
│   │   ├─ Claim of appeal: 21 days from judgment (civil)
│   │   ├─ Custody: 21 days from order (MCR 7.202(6))
│   │   └─ Late application: within 6 months (MCR 7.205(F))
│   ├─ Step 2: File claim of appeal (MCR 7.204)
│   ├─ Step 3: Order transcript (MCR 7.210(B))
│   ├─ Step 4: Designate record (MCR 7.210(A))
│   ├─ Step 5: File docketing statement
│   └─ OUTPUT: appeal_initiation_package
│
├─ BRANCH D: Brief Architecture
│   ├─ Step 1: Select issues (max 3-4 strongest)
│   ├─ Step 2: Assign standard of review per issue
│   ├─ Step 3: Build argument structure (IRAC+)
│   ├─ Step 4: Draft with record citations throughout
│   ├─ Step 5: Authority validation via litigation-authority-validator
│   └─ OUTPUT: appellate_brief_draft
│
├─ BRANCH E: MSC Application
│   ├─ Step 1: Evaluate MSC-worthy grounds (MCR 7.305(B))
│   ├─ Step 2: Draft application for leave to appeal
│   ├─ Step 3: Identify conflict with other COA panels
│   ├─ Step 4: Frame issue of significant public interest
│   └─ OUTPUT: msc_application_draft
│
└─ BRANCH F: Argument Preparation
    ├─ Step 1: Distill to 2-3 core points
    ├─ Step 2: Prepare for hot bench (anticipate questions)
    ├─ Step 3: Build rebuttal matrix
    ├─ Step 4: Rehearse time management (typically 15-20 min)
    └─ OUTPUT: oral_argument_prep_package
```

---

## Standards of Review

| Standard | Applies To | Burden | Key Language |
|----------|-----------|--------|--------------|
| **De novo** | Questions of law, statutory interpretation, constitutional issues | No deference to trial court | "We review de novo..." |
| **Clear error** | Findings of fact (MCR 2.613(C)) | Definite and firm conviction of mistake | "A finding is clearly erroneous when..." |
| **Abuse of discretion** | Discretionary rulings (custody, evidentiary, discovery) | Outcome outside range of principled outcomes | "An abuse of discretion occurs when..." |
| **Great weight** | Custody best-interest findings (MCL 722.28) | Even greater deference than clear error | "Affirm unless the evidence clearly preponderates..." |
| **Plain error** | Unpreserved issues | Affects substantial rights, manifest injustice | "Plain error affecting substantial rights..." |

### Lane-Specific Standard of Review Map

**Lane A: Watson/Custody**
| Issue | Standard |
|-------|----------|
| Best interest factor findings | Great weight (MCL 722.28) |
| Change of established custodial environment | Clear error |
| Proper cause / change of circumstances | Clear error |
| PPO issuance/modification | Abuse of discretion |
| Evidentiary rulings | Abuse of discretion |
| Statutory interpretation | De novo |

**Lane B: Shady Oaks/Housing**
| Issue | Standard |
|-------|----------|
| Summary disposition ruling | De novo |
| Contract interpretation | De novo |
| Damage calculation | Clear error |
| Discovery rulings | Abuse of discretion |
| Warranty of habitability | De novo |

---

## Record Designation Protocol (MCR 7.210)

### Required Record Components
```
1. Register of actions
2. All original papers filed in the trial court
3. Transcripts of all proceedings (or settled statement)
4. All exhibits admitted or offered and refused
5. Jury instructions (if applicable)
6. Verdict form (if applicable)
```

### Record Designation Checklist

```yaml
record_designation:
  lower_court_file:
    - register_of_actions: boolean
    - complaint_and_amendments: boolean
    - answer_and_amendments: boolean
    - all_motions_and_responses: boolean
    - all_court_orders: boolean
    - final_judgment_or_order: boolean
  transcripts:
    - all_hearings: boolean
    - specific_hearings: list[date_and_description]
    - transcript_ordered_date: ISO-8601
    - transcript_due_date: ISO-8601
    - court_reporter_name: string
  exhibits:
    - plaintiff_exhibits: list[exhibit_id]
    - defendant_exhibits: list[exhibit_id]
    - admitted_exhibits: list[exhibit_id]
    - refused_exhibits: list[exhibit_id]
  supplemental:
    - deposition_transcripts: list[deponent_name]
    - discovery_responses: list[description]
```

---

## Brief Architecture Template

### Appellant's Brief Structure (MCR 7.212(C))

```
I.    TABLE OF CONTENTS
II.   INDEX OF AUTHORITIES
III.  JURISDICTIONAL STATEMENT
      - Basis for jurisdiction (MCR 7.203)
      - Timeliness of appeal
IV.   STATEMENT OF QUESTIONS PRESENTED
      - Frame favorably but accurately
      - One question per appellate issue
V.    STATEMENT OF FACTS
      - Record citations for every factual assertion
      - Chronological narrative
      - Neutral tone (save argument for later)
VI.   STANDARD OF REVIEW
      - Cite applicable standard per issue
      - Brief explanation of standard's requirements
VII.  ARGUMENT
      - Issue I: [strongest issue first]
        - Standard of review
        - Legal framework
        - Application to facts (with record cites)
        - Conclusion on issue
      - Issue II: [second strongest]
        (same structure)
      - Issue III: [if warranted]
        (same structure)
VIII. RELIEF REQUESTED
      - Specific relief sought
      - Remand instructions if applicable
IX.   SIGNATURE AND VERIFICATION
```

### Brief Quality Standards
- Every factual assertion MUST cite the record (Tr at X; Ex Y)
- Every legal proposition MUST cite authority
- Maximum 50 pages (MCR 7.212(B)) unless leave granted
- Font: 12-point, proportionally spaced (MCR 7.212(B))

---

## Issue Preservation Audit

```
FOR EACH potential appellate issue:
  1. Was the issue raised in the trial court? [Y/N]
  2. Was a specific objection made on the record? [Y/N]
  3. Was the trial court given opportunity to rule? [Y/N]
  4. Was the ruling adverse? [Y/N]
  5. Was a motion for reconsideration filed? [Y/N]
  6. Is the issue jurisdictional (preserved automatically)? [Y/N]

  IF all YES → FULLY PRESERVED → include in appeal
  IF any NO  → PARTIALLY PRESERVED → evaluate plain error
  IF multiple NO → LIKELY WAIVED → do not include unless plain error
```

---

## Output Contract

```yaml
appellate_strategy_report:
  case_lane: enum [A, B, C]
  appeal_from:
    court: string          # "14th Judicial Circuit"
    judge: string          # "McNeill" or "Hoopes"
    case_number: string
    judgment_date: ISO-8601
  deadlines:
    claim_of_appeal_due: ISO-8601
    transcript_order_due: ISO-8601
    brief_due: ISO-8601
    oral_argument_date: ISO-8601  # if scheduled
  issues:
    - issue_number: integer
      description: string
      preservation_status: enum [full, partial, waived]
      standard_of_review: string
      strength_assessment: enum [strong, moderate, weak]
      record_citations: list[string]
  brief_architecture:
    total_issues: integer
    page_estimate: integer
    authority_count: integer
  record_designation:
    transcripts_ordered: boolean
    exhibits_listed: boolean
    complete: boolean
```

---

## Appellate Timeline Management

```
DAY 0:  Adverse judgment entered
DAY 1:  Begin issue preservation audit
DAY 7:  File post-judgment motions (if needed)
DAY 14: Order transcripts from court reporter
DAY 21: FILE CLAIM OF APPEAL (HARD DEADLINE)
DAY 28: File docketing statement
DAY 56: Transcript due from court reporter
DAY 84: Appellant's brief due (or per scheduling order)
DAY 112: Appellee's brief due (28 days after appellant's)
DAY 133: Reply brief due (21 days after appellee's)
DAY 180+: Oral argument (if granted)
```

---

## MSC Application Criteria (MCR 7.305(B))

An application for leave to appeal to the Michigan Supreme Court should be
pursued ONLY when:

1. **COA panel conflict**: Different COA panels reached conflicting results
2. **Significant public interest**: Issue affects many beyond this case
3. **Constitutional question**: Substantial constitutional issue involved
4. **Clear legal error**: COA misapplied settled law
5. **Developing area**: Law is unsettled and MSC guidance needed

Do NOT pursue MSC application merely because the COA ruling was unfavorable.

## Related Skills

- [litigation-supreme-court-architect](skill://litigation-supreme-court-architect) — Prepares MSC application strategy
- [litigation-brief-writer](skill://litigation-brief-writer) — Drafts court-ready legal briefs


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Governing Authority (Verified)
**MCR:** MCR 7.203, MCR 7.204, MCR 7.205, MCR 7.212, MCR 7.215, MCR 7.302, MCR 7.305
**MCL:** MCL 600.308, MCL 600.862, MCL 722.28
**Binding Cases:**
- *Maldonado v Ford Motor Co, 476 Mich 372*
- *In re Hatcher, 443 Mich 426*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-appeal-brief-engine` | Integration | Bidirectional data exchange |
| `litigation-appellate-record-specialist` | Integration | Complementary analysis |
| `litigation-supreme-court-architect` | Integration | Complementary analysis |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-8 Authority Matching → Ω-9 Gap Analysis → Ω-13 Document Generation
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
