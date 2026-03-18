---
name: litigation-guardian-ad-litem-specialist
description: >-
  Use when interacting with or challenging a Guardian ad Litem (GAL),
  rebutting GAL reports, documenting GAL bias, filing motions to remove
  GAL, challenging GAL appointment under MCL 722.24, navigating
  MCR 3.204 and MCR 5.121 procedures, or addressing GAL fee disputes.
metadata:
  category: custody
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    guardian ad litem, GAL, MCL 722.24, MCR 3.204, MCR 5.121,
    GAL report, GAL bias, remove GAL, GAL challenge, GAL appointment,
    child advocate, best interest investigation, GAL fees,
    GAL recommendation, GAL interview, motion to remove GAL
---

# litigation-guardian-ad-litem-specialist

> **Tier:** 2 — Custody Specialist
> **Category:** custody
> **Version:** 1.0.0
> **Lane:** A (Custody)

## Description

Guardian ad Litem (GAL) interaction and challenge specialist for Michigan
family law. Addresses GAL appointment challenges, GAL report analysis
and rebuttal, GAL bias documentation, motions to remove GAL, GAL fee
disputes, and strategic interaction with GAL during the investigation
process. Critical for ensuring that GAL recommendations are properly
scrutinized and that L.D.W.'s best interests are genuinely served.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case No. | 2024-001507-DC |
| Lane | A (Custody) |

## Triggers

- Court appoints a Guardian ad Litem
- User receives GAL report and needs to analyze/rebut it
- User identifies GAL bias or procedural failures
- User preparing motion to remove or replace GAL
- User disputes GAL fees
- User needs to prepare for GAL interview
- User challenging GAL recommendation at hearing

## Michigan Rules — Guardian ad Litem

### MCL 722.24 — Appointment of GAL

**(1)** The court may appoint a guardian ad litem (GAL) for a child in a
custody dispute.

**(2)** The GAL's duty is to determine the child's best interests. The
GAL shall:
- Interview the child (if of suitable age)
- Interview each parent
- Investigate the child's home environment
- Make a written report and recommendation to the court

**(3)** The GAL shall consider all best-interest factors (MCL 722.23(a)-(l)).

**(4)** The GAL is not bound by the rules of evidence in conducting
the investigation, but the GAL report may be challenged at hearing.

### MCR 3.204 — Guardian ad Litem

**(A) Appointment:**
- Court may appoint GAL on its own initiative or on motion
- Court must specify duties and scope of investigation

**(B) Duties:**
- Investigate and report on child's best interests
- Attend all hearings
- File written report with the court
- Report must be provided to parties ≥7 days before hearing

**(C) Challenges to GAL Report:**
- Parties have the right to cross-examine the GAL at hearing
- Parties may present evidence rebutting GAL findings
- Court is not bound by GAL recommendation

### MCR 5.121 — Guardian ad Litem (Probate)

Applies in probate proceedings. Similar appointment and duty framework
as MCR 3.204.

## GAL Report Analysis Framework

### Step 1: Structural Review

| Element | Check | MCL Reference |
|---------|-------|---------------|
| Child interview | Was L.D.W. interviewed? Age-appropriate? | MCL 722.24(2) |
| Parent interviews | Were both parents interviewed equally? | MCL 722.24(2) |
| Home visits | Were both homes visited? | MCL 722.24(2) |
| Collateral contacts | Were teachers, doctors, etc. contacted? | MCL 722.23 |
| Best-interest factors | All 12 factors addressed? | MCL 722.23(a)-(l) |
| Written report | Provided ≥7 days before hearing? | MCR 3.204(B) |

### Step 2: Bias Indicators

| Indicator | Description | Severity |
|-----------|-------------|----------|
| Unequal time | Significantly more time with one parent | High |
| Leading questions | Questions designed to elicit specific answers | High |
| Ignored evidence | Failed to consider documented evidence | Critical |
| Ex parte with judge | Communication with judge outside proceedings | Critical |
| Predetermined conclusion | Conclusion formed before investigation complete | Critical |
| Credential gaps | Acting beyond professional qualification | Medium |
| Fee motivation | Extended investigation to increase fees | Medium |

### Step 3: Factor-by-Factor Rebuttal

For each MCL 722.23 factor where GAL recommendation differs from
Plaintiff's position:

1. State GAL's finding on the factor
2. Identify the evidence GAL relied upon
3. Present contradicting evidence
4. Explain why GAL's analysis is flawed
5. State the correct finding with supporting evidence

## Patterns

### Pattern 1: GAL Report Rebuttal

**Context:** GAL filed a report with unfavorable recommendations.

**Steps:**
1. Obtain GAL report (must be received ≥7 days before hearing)
2. Perform structural review (all required elements present?)
3. Analyze each best-interest factor finding
4. Identify bias indicators
5. Prepare written rebuttal addressing each flawed finding
6. Gather evidence supporting Plaintiff's position on each factor
7. Prepare cross-examination questions for GAL at hearing

**Michigan basis:** MCR 3.204(C), MCL 722.23, MCL 722.24

```python
from legal_ai.guardian_ad_litem_specialist import GALSpecialist

gal = GALSpecialist()
rebuttal = gal.analyze_report(
    report_text=gal_report,
    factors_disputed=["a", "c", "f", "j"],
    evidence_refs=evidence_list,
)
cross_exam = gal.prepare_cross_examination(rebuttal)
```

### Pattern 2: Motion to Remove GAL

**Context:** GAL is biased or has committed procedural violations.

**Steps:**
1. Document specific instances of bias or violation
2. Map each instance to the standard for removal
3. Draft motion to remove/replace GAL
4. Include affidavit with factual allegations
5. Cite *Brown v Brown*, 332 Mich App 1 (2020) or similar authority
6. Request appointment of replacement GAL
7. Request that removed GAL's report be stricken or given no weight

**Michigan basis:** MCR 3.204, MCL 722.24

### Pattern 3: GAL Interview Preparation

**Context:** GAL has scheduled an interview with Plaintiff.

**Steps:**
1. Review all best-interest factors (MCL 722.23(a)-(l))
2. Prepare concise talking points for each factor
3. Organize supporting documents to share with GAL
4. Document the home environment (photos, schedule, etc.)
5. Prepare character references (teachers, doctors, neighbors)
6. Be truthful, cooperative, and focused on L.D.W.'s needs
7. Take notes during the interview for the record

### Pattern 4: GAL Fee Challenge

**Context:** GAL fees are excessive or unreasonable.

**Steps:**
1. Review GAL fee petition and hourly rate
2. Compare to local market rates for GAL services
3. Review hours billed against actual investigation activities
4. Identify excessive or unnecessary charges
5. File objection to GAL fee petition
6. Request itemized billing and hearing on fees

**Michigan basis:** MCL 722.24, local rules on GAL compensation

## Anti-Patterns

### Anti-Pattern 1: Antagonizing the GAL

❌ Being hostile, uncooperative, or adversarial with the GAL.
**Why it fails:** GAL reports to the court. Hostility will be noted
and will hurt your case. The GAL is investigating — cooperate.
**Fix:** Be professional, responsive, and child-focused. Present
evidence calmly. Save adversarial advocacy for the hearing.

### Anti-Pattern 2: Ignoring the GAL Report

❌ Failing to respond to an unfavorable GAL report.
**Why it fails:** Unrebutted GAL reports carry significant weight with
the court. Silence implies agreement.
**Fix:** Always file a written response to the GAL report. Address
every unfavorable finding with evidence.

### Anti-Pattern 3: Attacking GAL Credentials Without Basis

❌ Challenging the GAL's qualifications without specific factual support.
**Why it fails:** Courts appoint GALs and generally trust their
qualifications. Unfounded attacks look desperate.
**Fix:** Focus challenges on specific methodology failures, not
general credential attacks. Use the bias indicator framework above.

## GAL Cross-Examination Template

### Foundation Questions
1. What is your professional background and training?
2. How were you appointed to this case?
3. What specific duties were you given?
4. How many hours did you spend on this investigation?

### Investigation Questions
5. Did you interview L.D.W.? When? For how long?
6. Did you interview both parents? Equal time?
7. Did you visit both homes? When?
8. What collateral contacts did you make?
9. What documents did you review?
10. Did you review all evidence provided by both parties?

### Bias-Probing Questions
11. Did you form a preliminary opinion before completing your investigation?
12. Did you communicate with the court about this case outside of hearings?
13. Did you give both parties equal opportunity to present information?
14. Were there any documents you chose not to review? Why?

### Factor-Specific Questions
15. For each disputed factor: "What evidence did you rely upon for your
    finding on Factor [X]?"
16. "Were you aware of [specific contradicting evidence]?"
17. "Would that evidence change your analysis?"

## Integration Points

### Upstream Skills
- `litigation-custody-specialist` — Best-interest factor analysis
- `litigation-evidence-harvester` — Evidence for GAL rebuttal
- `litigation-witness-preparation` — Preparing for GAL interview

### Downstream Skills
- `litigation-filing-architect` — Filing motion to remove GAL
- `litigation-brief-writer` — Brief supporting GAL challenge
- `litigation-appellate-strategist` — Appeal of GAL-related rulings


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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
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
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D,F | Verified |
| Emergency Custody | 55/100 | A,D,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,F | Verified |
| Contempt | 70/100 | A,D,F | Verified |
| Appeal Brief | 70/100 | A,D,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,F | Verified |

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
