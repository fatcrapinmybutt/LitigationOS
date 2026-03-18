---
name: litigation-foc-challenge-engine
description: >-
  Use when challenging Friend of Court recommendations, filing objections per
  MCR 3.218, requesting de novo hearings, documenting FOC investigation bias,
  preparing FOIA requests for FOC records, or seeking to opt-out of FOC
  involvement per MCL 552.505b in Michigan family law proceedings.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    FOC, Friend of Court, MCR 3.218, objection, de novo hearing,
    FOC bias, MCL 552.505, opt-out, FOC recommendation, referee,
    MCR 3.224, domestic relations referee, FOIA
---

# litigation-foc-challenge-engine

> **Tier:** 2 — Discipline Specialist
> **Category:** discipline
> **Version:** 1.0.0
> **Lane:** A (Custody — 2024-001507-DC), D (PPO — 2023-5907-PP)

## Description

Friend of Court Challenge and Objection Specialist for the Pigors v. Watson
litigation. Provides comprehensive support for challenging FOC recommendations,
filing timely objections per MCR 3.218, requesting de novo hearings, documenting
FOC investigation bias, and when appropriate, seeking removal of FOC involvement
per MCL 552.505b. Handles both custody-lane (A) and PPO-lane (D) FOC encounters.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case Nos. | 2024-001507-DC, 2023-5907-PP |
| FOC Office | Muskegon County Friend of the Court |
| Lanes | A (Custody), D (PPO) |

## Triggers

- User received an adverse FOC recommendation
- User needs to file MCR 3.218 objection within 21-day deadline
- User wants de novo hearing before the judge (not referee)
- User suspects FOC investigator bias or procedural errors
- User wants FOIA request for FOC internal records
- User considering MCL 552.505b opt-out of FOC services
- User challenging domestic relations referee per MCR 3.224

## FOC Objection Framework (MCR 3.218)

### Critical Deadlines

| Event | Deadline | Authority |
|-------|----------|-----------|
| FOC recommendation issued | Day 0 | MCL 552.507 |
| Written objection due | **21 days** from service | MCR 3.218(A) |
| De novo hearing request | With objection or within 21 days | MCR 3.218(B) |
| Referee hearing (if not de novo) | Set by court | MCR 3.224 |

> ⚠️ **CRITICAL**: Missing the 21-day objection deadline waives the right
> to contest the FOC recommendation. The recommendation becomes an order
> of the court. Calendar this immediately upon receipt.

### Objection Process — Step by Step

1. **Receive FOC Recommendation**
   - Record date of service (personal service, mail, or e-filing).
   - Calculate 21-day deadline. For mail service, add 3 days per MCR 2.107(C)(3).
   - Enter deadline in `deadlines` table with urgency score.

2. **Analyze the Recommendation**
   - Identify factual errors (wrong dates, incorrect income, misquoted statements).
   - Identify legal errors (wrong standard applied, factors not analyzed).
   - Identify procedural errors (ex parte contacts, failure to interview witnesses).
   - Document bias indicators (predetermined conclusions, selective evidence).

3. **Draft Written Objection**
   - File on SCAO form MC 292 (Objection to Friend of the Court Recommendation).
   - State specific grounds for each objection (not general disagreement).
   - Attach supporting evidence for each objection point.
   - Request de novo hearing before the judge (not just referee review).

4. **File and Serve**
   - File with Muskegon County Clerk.
   - Serve opposing party per MCR 2.107.
   - Serve FOC office with copy.
   - File proof of service.

5. **De Novo Hearing Preparation**
   - Subpoena FOC investigator if needed.
   - Prepare cross-examination on bias/errors.
   - Prepare direct evidence contradicting FOC findings.
   - Brief judge on legal errors in recommendation.

### Objection Categories

| Category | Description | Common Grounds |
|----------|-------------|----------------|
| **Factual Error** | FOC got facts wrong | Income miscalculation, wrong overnights count, misquoted statements |
| **Legal Error** | Wrong legal standard applied | Incorrect best-interest factor analysis, wrong burden of proof |
| **Procedural Error** | FOC violated procedures | No home visit, ex parte communications, failure to interview |
| **Bias** | FOC investigator showed partiality | Predetermined conclusions, selective evidence, credibility prejudgment |
| **Omission** | FOC ignored relevant evidence | Excluded documents, didn't interview witnesses, ignored patterns |

## FOC Bias Documentation Protocol

### Bias Indicators to Catalog

| Indicator | Description | Documentation Method |
|-----------|-------------|---------------------|
| Selective interviews | FOC only interviewed one party's witnesses | Compare witness lists submitted vs. interviewed |
| Leading questions | FOC asked suggestive questions during investigation | Recording transcripts (if permitted), contemporaneous notes |
| Predetermined conclusions | Report language suggests conclusion before investigation | Textual analysis of report drafts vs. final |
| Ex parte contacts | FOC communicated with one party without notice | FOIA records, email logs, phone records |
| Factual cherry-picking | FOC cited only evidence favoring one party | Side-by-side comparison of evidence submitted vs. cited |
| Time allocation | FOC spent disproportionate time with one party | Appointment records via FOIA |
| Ignoring contradictions | FOC did not address conflicting evidence | Systematic review of contradictions in report |

### Bias Score Calculation

```
Per indicator:
  Confirmed with documentation:     +3 points
  Probable (circumstantial evidence): +2 points
  Possible (pattern suggests):       +1 point

Total Bias Score:
  0-5:   Within normal range — challenge on substance
  6-12:  Moderate bias — include bias argument in objection
  13+:   Severe bias — move to disqualify investigator, request new investigation
```

## FOIA Request for FOC Records

### Requestable Records (MCL 15.231 — FOIA Act)

| Record Type | Basis | Notes |
|-------------|-------|-------|
| Investigation notes | MCL 15.231 | May be partially exempt under MCL 15.243 |
| Internal communications | MCL 15.231 | Emails, memos re: case |
| Time logs | MCL 15.231 | How long spent on each party |
| Prior recommendations | MCL 15.231 | Pattern of recommendations |
| Training records | MCL 15.231 | Qualifications of investigator |
| Complaint history | MCL 15.231 | Prior complaints against investigator |

### FOIA Request Template

```
[Date]
Friend of the Court
Muskegon County
990 Terrace Street
Muskegon, MI 49442

RE: Freedom of Information Act Request
    Case No. 2024-001507-DC / 2023-5907-PP
    Pigors v. Watson

Dear FOIA Coordinator:

Pursuant to MCL 15.231 et seq., I request copies of:

1. All investigation notes, memoranda, and internal communications
   related to Case Nos. 2024-001507-DC and 2023-5907-PP.
2. Time logs showing hours spent on investigation activities.
3. All communications with Emily A. Watson or her representatives.
4. Training and qualification records for the assigned investigator.
5. [Specific additional records].

I request a fee waiver per MCL 15.234(3) as this information is in
the public interest and contributes to understanding of government
operations.

Please respond within 5 business days per MCL 15.235(2).

Respectfully,
Andrew James Pigors
1977 Whitehall Road, Lot 17
North Muskegon, MI 49445
```

## MCL 552.505b — Opt-Out of FOC Services

### Eligibility Requirements

Both parties must agree to opt out (MCL 552.505b(1)), OR the court may order
opt-out when:

| Condition | Authority |
|-----------|-----------|
| Both parties consent in writing | MCL 552.505b(1) |
| Court finds FOC involvement unnecessary | MCL 552.505b(2) |
| Parties can manage without FOC | MCL 552.505b(2) |

### Opt-Out Motion Checklist

- [ ] Verify eligibility under MCL 552.505b
- [ ] Draft motion citing specific grounds
- [ ] Document FOC performance issues (if unilateral request)
- [ ] Propose alternative dispute resolution mechanism
- [ ] Address child support enforcement continuation (if applicable)
- [ ] File and serve per MCR 2.107

## Domestic Relations Referee Challenges (MCR 3.224)

### Referee vs. Judge — Key Differences

| Aspect | Referee | Judge |
|--------|---------|-------|
| Authority | MCR 3.224 — limited to recommendations | MCR 3.210 — full authority |
| Decision type | Recommendation to judge | Binding order |
| Challenge method | Objection within 21 days | Appeal to COA |
| De novo review | Available upon objection | Not applicable |
| Bias challenge | Object to assignment | MCR 2.003 disqualification |

### Right to De Novo Hearing

Under MCR 3.218(B), any party may request a **de novo hearing** before the
judge rather than accepting a referee's recommendation. This is a critical
right for pro se litigants:

1. File written request with objection.
2. Hearing is before the assigned judge (Hon. Jenny L. McNeill).
3. Judge considers the matter fresh — referee's recommendation carries no weight.
4. Present evidence directly to the decision-maker.

## Database Queries

```sql
-- Track FOC recommendations and objections
SELECT
    fr.recommendation_id,
    fr.received_date,
    fr.objection_deadline,
    fr.objection_filed,
    fr.de_novo_requested,
    fr.hearing_date,
    fr.outcome
FROM foc_recommendations fr
WHERE fr.case_number IN ('2024-001507-DC', '2023-5907-PP')
ORDER BY fr.received_date DESC;

-- FOC bias indicators
SELECT
    bi.indicator_type,
    bi.description,
    bi.severity,
    bi.evidence_ref,
    bi.documented_date
FROM foc_bias_indicators bi
WHERE bi.case_number = '2024-001507-DC'
ORDER BY bi.severity DESC;
```

## Integration

### Companion Skills

- [litigation-custody-specialist](skill://litigation-custody-specialist) — Custody law framework
- [litigation-ppo-specialist](skill://litigation-ppo-specialist) — PPO-related FOC issues
- [litigation-filing-architect](skill://litigation-filing-architect) — Filing the objection
- [litigation-service-engine](skill://litigation-service-engine) — Proof of service
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Gathering FOC evidence

### Companion Agents

- `court-order-tracker` — Track FOC recommendation deadlines
- `filing-countdown` — Countdown for 21-day objection deadline

## Fabrication Warnings

- **DO NOT** fabricate FOC recommendation content or dates.
- **DO NOT** invent bias indicators without evidence basis.
- **DO NOT** overstate legal rights — FOC opt-out requires specific conditions.
- **DO NOT** use "Emily Ann" or "Emily M." — defendant is Emily A. Watson.
- **ALWAYS** verify the 21-day deadline from actual date of service.
- **ALWAYS** use L.D.W. for the child per MCR 8.119(H).
- **ALWAYS** spell Judge McNeill with TWO L's.

## Output Format

```markdown
## FOC Challenge Analysis — [Case Number]

### Recommendation Summary
[Date received] | [Deadline: date] | [Status: pending/filed/heard]

### Objection Grounds
| # | Category | Ground | Evidence |
|---|----------|--------|----------|
| 1 | [Type] | [Specific ground] | [Evidence ref] |

### Bias Score: [X] — [Level]

### Recommended Actions
1. [Action with deadline]
2. [Action with legal basis]
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
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D,E,F | Verified |
| Emergency Custody | 55/100 | A,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,E,F | Verified |
| Contempt | 70/100 | A,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,D,E,F | Verified |
| Appeal Brief | 70/100 | A,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,D,E,F | Verified |

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
