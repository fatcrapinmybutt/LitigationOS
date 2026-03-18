---
name: litigation-supreme-court-architect
description: >
  Use when preparing, analyzing, or filing any action before the Michigan Supreme Court.
  Covers applications for leave to appeal, bypass applications, original jurisdiction
  proceedings, extraordinary writs, certified questions, rehearings, and miscellaneous
  motions under MCR 7.300–7.311. Provides state-machine filing workflows, grounds
  analysis under MCR 7.305(B), brief architecture per MCR 7.212(C), form catalogs,
  service requirements, and pro se compliance checks.
version: 1.1.0
category: discipline
changelog:
  v1.1.0: |
    - MSC audit complete: 6 filing packages verified (Superintending 93.7/100, Mandamus, Super, Habeas, Declaratory, Emergency)
    - VehicleMap output: 6 MSC vehicles mapped with risk/deadline/prerequisites
    - AuthorityTriple output: MCR 7.300-7.311 fully mapped to Pigors applications
    - RedTeam: Adversarial stress-test framework operational
    - COA 366810 tracked — if denied, MSC application within 28 days per MCR 7.305(D)
    - IFP application package (5 documents) verified
    - 56-day jurisdictional wall enforced in all filing workflows
triggers:
  - supreme court
  - MSC
  - michigan supreme court
  - MCR 7.300
  - MCR 7.301
  - MCR 7.302
  - MCR 7.303
  - MCR 7.305
  - MCR 7.306
  - MCR 7.308
  - MCR 7.311
  - leave to appeal
  - bypass application
  - extraordinary writ
  - mandamus
  - superintending control
  - habeas corpus
  - original jurisdiction
  - certified question
  - judicial review
  - MSC filing
  - peremptory reversal
context:
  case: Pigors v Watson
  circuit: 14th Judicial Circuit, Muskegon County, MI
  posture: Pro se plaintiff
  lanes:
    A: "Watson/Custody — 2024-001507-DC, 2023-5907-PP, Judge McNeill"
    B: "Shady Oaks/Housing — 2025-002760-CZ, Judge Hoopes"
    C: "Convergence/County — Muskegon County, 14th Circuit"
output_contracts:
  - "[VM] VehicleMap — MSC filing vehicle selection matrix"
  - "[AT] AuthorityTriples — (Rule, Proposition, Application) for every cited authority"
  - "[VR] RedTeam — Adversarial stress-test of every filing before submission"
modes:
  DRAFT: "Working analysis — not for filing. May contain open questions."
  FILE_READY: "All sections complete. Compliant with MCR formatting. Ready for signature and filing."
  PCG: "Post-Completion Guard — verify service, fees, deadlines, copy counts after filing."
---

# LITIGATION-SUPREME-COURT-ARCHITECT

## PURPOSE

This skill is the definitive state machine for Michigan Supreme Court practice.
It maps EVERY viable MSC action to its governing law, required forms, deadlines,
service rules, and strategic considerations. It produces court-ready filings for
a pro se litigant in the 14th Judicial Circuit.

---

## IRON LAWS — MSC PRACTICE

```
1. JURISDICTION FIRST — Confirm MSC has jurisdiction before drafting anything.
2. GROUNDS OR DEATH — Every application MUST articulate MCR 7.305(B) grounds.
3. 56-DAY WALL — Application for leave must be filed within 56 days of COA
   decision or order. MCR 7.305(C)(2). NO automatic extensions.
4. RECORD IS KING — MSC decides on the record below. If it is not in the
   record, it does not exist.
5. COPY COUNTS MATTER — File original + 1 signed copy + sufficient copies
   for all parties. MCR 7.302(B).
6. SERVICE IS JURISDICTIONAL — Failure to serve = failure to file.
   MCR 7.302(E), MCR 2.107.
7. FEE OR WAIVER — $375 filing fee OR MC 20 fee waiver MUST accompany filing.
8. FORMAT COMPLIANCE — MCR 7.212(C) formatting applies. Violations = rejection.
9. QUESTION PRESENTED CONTROLS — MSC grants leave on QUESTIONS, not cases.
   Frame questions precisely.
10. LESS IS MORE — Fewer, stronger issues > many weak ones at MSC level.
```

---

## DECISION TREE — WHAT FILING PATH?

```
START: What is the current procedural posture?
│
├─ COA has issued a final decision/order?
│  ├─ YES → APPLICATION FOR LEAVE TO APPEAL
│  │         MCR 7.302, MCR 7.305
│  │         Deadline: 56 days from COA decision
│  │         See: references/jurisdiction/filing-paths.md#leave-to-appeal
│  │
│  └─ NO → Has any claim been filed in COA?
│     ├─ YES (pending in COA) → BYPASS APPLICATION
│     │   MCR 7.305(B)(3) — Extraordinary circumstances
│     │   Must show: delay in COA would cause irreparable harm
│     │   See: references/jurisdiction/filing-paths.md#bypass
│     │
│     └─ NO → Is this a direct MSC matter?
│        ├─ Constitutional officer / Original jurisdiction?
│        │   → ORIGINAL PROCEEDING — MCR 7.303
│        │   Const 1963 Art 6 §4
│        │   See: references/jurisdiction/filing-paths.md#original
│        │
│        ├─ Need emergency coercive relief against lower court?
│        │   → EXTRAORDINARY WRIT — MCR 7.306
│        │   Mandamus / Superintending control / Habeas corpus
│        │   See: references/jurisdiction/filing-paths.md#writs
│        │
│        ├─ Federal court requesting state-law determination?
│        │   → CERTIFIED QUESTION — MCR 7.308
│        │   See: references/jurisdiction/filing-paths.md#certified
│        │
│        └─ Procedural / scheduling / administrative?
│            → MOTION — MCR 7.311
│            See: references/jurisdiction/filing-paths.md#motions
│
├─ MSC has already decided and you seek reconsideration?
│  → MOTION FOR REHEARING — MCR 7.309
│    Deadline: 21 days from MSC decision
│
└─ STOP. Re-evaluate procedural posture before filing anything.
```

---

## FILING PATH SUMMARIES

### PATH 1 — APPLICATION FOR LEAVE TO APPEAL (MCR 7.302 / 7.305)

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.302, MCR 7.305                                 |
| **Prerequisite**   | Final COA decision or order                           |
| **Deadline**       | 56 days from COA decision — MCR 7.305(C)(2)          |
| **Form**           | CC 298 + Cover page + TOC/TOA                         |
| **Brief**          | Per MCR 7.212(C) — see references/forms/brief-architecture.md |
| **Copies**         | Original + copies for each party + 1 for court        |
| **Fee**            | $375 OR MC 20 fee waiver                              |
| **Service**        | All parties — MCR 7.302(E), proof via MC 12           |
| **Grounds**        | Must satisfy MCR 7.305(B)(1)–(5) — see references/strategy/grounds-matrix.md |

### PATH 2 — BYPASS APPLICATION (MCR 7.305(B)(3))

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.305(B)(3)                                      |
| **Prerequisite**   | Case pending in COA OR no COA filing yet              |
| **Deadline**       | No fixed deadline — but must show urgency             |
| **Extra Requirement** | Demonstrate extraordinary circumstances; that delay in COA proceedings would cause irreparable harm |
| **Grounds**        | Issue of major significance to state jurisprudence     |
| **Strategic Note** | MSC grants bypass RARELY — < 5% acceptance rate       |

### PATH 3 — ORIGINAL JURISDICTION (MCR 7.303)

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.303, Const 1963 Art 6 §4                       |
| **Prerequisite**   | Matter within MSC original jurisdiction               |
| **Scope**          | Superintending control, mandamus, quo warranto vs constitutional officers |
| **Deadline**       | No fixed deadline — but laches may apply              |
| **Brief**          | Complaint + brief in support                          |

### PATH 4 — EXTRAORDINARY WRITS (MCR 7.306)

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.306                                             |
| **Types**          | Mandamus, superintending control, habeas corpus       |
| **Prerequisite**   | No adequate remedy at law; clear legal right          |
| **Standard**       | Extraordinary relief — must show clear entitlement    |
| **Service**        | Named respondent + all interested parties             |

### PATH 5 — CERTIFIED QUESTIONS (MCR 7.308)

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.308                                             |
| **Initiator**      | Federal court (6th Circuit, EDMI, WDMI)               |
| **Scope**          | Unsettled questions of Michigan law                   |
| **Party Role**     | Submit briefs as directed by MSC order                |

### PATH 6 — MOTIONS (MCR 7.311)

| Element         | Requirement                                              |
|-----------------|----------------------------------------------------------|
| **Governing Rule** | MCR 7.311                                             |
| **Types**          | Stay, extension, amicus, intervention, consolidation  |
| **Format**         | Motion + brief in support + proposed order            |
| **Response Time**  | 14 days unless otherwise ordered                      |

---

## MODE SWITCHES

### DRAFT MODE
```
Status: WORKING DRAFT — NOT FOR FILING
- Open questions flagged with [?]
- Missing authorities flagged with [CITE NEEDED]
- Incomplete sections flagged with [TODO]
```

### FILE_READY MODE
```
Status: FILE-READY — COMPLIANT WITH MCR 7.212(C)
Checklist:
  [ ] All required sections present
  [ ] TOC and TOA generated
  [ ] Page limits verified
  [ ] Citation format verified (Michigan citation rules)
  [ ] Copy count confirmed
  [ ] Fee / waiver prepared
  [ ] Proof of service prepared (MC 12)
  [ ] Signature block present
  [ ] Certificate of service included
```

### PCG MODE — POST-COMPLETION GUARD
```
Status: FILED — VERIFYING COMPLIANCE
  [ ] Filing receipt obtained
  [ ] Proof of service filed with court
  [ ] Calendar deadline set for response period
  [ ] Copy of filed documents retained
  [ ] Docket confirmation received
```

---

## OUTPUT CONTRACTS

### [VM] VEHICLEMAP — MSC Filing Vehicle Selection

```
Format:
  Vehicle: [Filing type]
  Rule: [MCR citation]
  Grounds: [MCR 7.305(B) subsection if applicable]
  Deadline: [Calendar date]
  Prerequisites: [What must exist before filing]
  Risk: [HIGH/MEDIUM/LOW] — [Brief risk assessment]
  Recommended: [YES/NO] — [Rationale]
```

### [AT] AUTHORITYTRIPLES

```
Format:
  Rule: [Full MCR or constitutional citation]
  Proposition: [What the rule establishes]
  Application: [How it applies to Pigors v Watson]
```

### [VR] REDTEAM — Adversarial Review

```
Format:
  Attack Vector: [What opposing counsel or court would challenge]
  Vulnerability: [Weakness in our filing]
  Mitigation: [How to address or preempt]
  Severity: [CRITICAL/HIGH/MEDIUM/LOW]
```

---

## CASE LANES — PIGORS v WATSON

### Lane A: Watson/Custody
- **Cases**: 2024-001507-DC, 2023-5907-PP
- **Judge**: McNeill, 14th Circuit
- **MSC Vehicles**: Leave to appeal (post-COA), bypass (if COA delay), extraordinary writ (if custody emergency)
- **Key Issues**: Parental alienation, due process, equal protection, judicial bias

### Lane B: Shady Oaks/Housing
- **Case**: 2025-002760-CZ
- **Judge**: Hoopes, 14th Circuit
- **MSC Vehicles**: Leave to appeal (post-COA), bypass (if systemic housing issue), certified question (if federal housing law intersection)
- **Key Issues**: Habitability, constructive eviction, landlord-tenant code violations

### Lane C: Convergence/County
- **Scope**: Muskegon County, 14th Circuit — systemic issues
- **MSC Vehicles**: Original jurisdiction (superintending control), extraordinary writ (mandamus against county officers)
- **Key Issues**: Pattern of judicial misconduct, county administrative failures, systemic due process violations

---

## CROSS-REFERENCES

- **Gotchas**: See `gotchas.md` — anti-rationalization tables
- **Filing Command**: See `commands/file-msc.md` — step-by-step workflow
- **Jurisdiction Detail**: See `references/jurisdiction/` — full MCR 7.300 map
- **Forms**: See `references/forms/` — form catalog + brief architecture
- **Strategy**: See `references/strategy/` — grounds matrix + immunity piercing

---

## USAGE

```
# Analyze which MSC filing path applies
@litigation-supreme-court-architect What filing path for Lane A post-COA?

# Generate vehicle map
@litigation-supreme-court-architect [VM] for Lane B bypass application

# Draft application for leave
@litigation-supreme-court-architect DRAFT application for leave — Lane A

# Red-team a filing
@litigation-supreme-court-architect [VR] stress-test my Lane C mandamus petition

# Check filing readiness
@litigation-supreme-court-architect FILE_READY checklist for Lane A application
```


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
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

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
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

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
  Ω-12 Filing Readiness → Ω-13 Document Generation → Ω-14 Red Team
  Ω-15 Validation → Ω-16 Deployment
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
