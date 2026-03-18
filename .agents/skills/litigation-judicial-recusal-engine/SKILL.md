---
name: litigation-judicial-recusal-engine
description: >-
  Use when preparing judicial disqualification motions under MCR 2.003,
  cataloging bias indicators (ex parte contacts, prejudgment, financial interest),
  exercising peremptory disqualification rights, filing for-cause disqualification
  with supporting affidavit, preparing JTC complaints per MCR 9.104, or
  documenting judicial code of conduct violations.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    recusal, disqualification, MCR 2.003, judicial bias, ex parte,
    prejudgment, peremptory disqualification, for-cause, JTC,
    Judicial Tenure Commission, MCR 9.104, judicial conduct,
    Canon 2, Canon 3, McNeill
---

# litigation-judicial-recusal-engine

> **Tier:** 2 — Discipline Specialist
> **Category:** discipline
> **Version:** 1.0.0
> **Lane:** E (Judicial Misconduct / JTC)

## Description

Judicial Disqualification and Recusal Motion Specialist for the Pigors v.
Watson litigation. Provides comprehensive support for all MCR 2.003
disqualification grounds, bias indicator cataloging, peremptory
disqualification exercise, for-cause disqualification with affidavit
preparation, JTC complaint preparation per MCR 9.104, and systematic
documentation of judicial code of conduct violations. Primary focus on
Judge Hon. Jenny L. McNeill, 14th Circuit Court.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case Nos. | 2024-001507-DC (primary) |
| Lane | E (Judicial Misconduct / JTC) |
| JTC | Judicial Tenure Commission |

## Triggers

- User identifies judicial bias or prejudgment
- User needs to file MCR 2.003 disqualification motion
- User wants to exercise peremptory disqualification right
- User documenting ex parte contacts
- User preparing JTC complaint
- User analyzing judicial code of conduct violations
- User needs appellate review of disqualification denial

## MCR 2.003 — Disqualification Framework

### MCR 2.003(C)(1) — Grounds for Disqualification

| Ground | MCR Section | Description | Evidence Type |
|--------|-------------|-------------|--------------|
| (a) Personal bias or prejudice | 2.003(C)(1)(a) | Judge has personal bias concerning a party | Statements, rulings pattern, ex parte contacts |
| (b) Personal knowledge of disputed facts | 2.003(C)(1)(b) | Judge has personal knowledge of disputed evidentiary facts | Prior involvement, personal observations |
| (c) Prior involvement as attorney | 2.003(C)(1)(c) | Judge served as attorney in the matter | Bar records, case docket review |
| (d) Financial interest | 2.003(C)(1)(d) | Judge has financial interest in controversy | Financial disclosures, property records |
| (e) Related to party or attorney | 2.003(C)(1)(e) | Within third degree of relationship | Family records |
| (f) Former associate of attorney | 2.003(C)(1)(f) | Judge and attorney were associated in practice | Bar association records |
| (g) Other grounds | 2.003(C)(1)(g) | Judge's conduct would create appearance of impropriety | Pattern of conduct |

### MCR 2.003(B) — Peremptory Disqualification

> Each party is entitled to ONE peremptory disqualification of the
> assigned judge as of right, without showing cause.

| Requirement | Detail |
|-------------|--------|
| **Timing** | Must be filed within 14 days of case assignment OR discovery of grounds |
| **Limit** | One per party per case |
| **No grounds required** | Simply file notice; no affidavit needed |
| **Effect** | Case reassigned to new judge |
| **Restriction** | Cannot be used after judge has ruled on contested matter |

> ⚠️ **CRITICAL**: The peremptory right is **lost** once the judge has made
> any ruling on a contested issue. Exercise early or lose it forever.

### MCR 2.003(D) — For-Cause Procedure

1. **File motion and affidavit** — Must include:
   - Specific facts demonstrating bias or disqualification ground
   - Sworn affidavit attesting to truth of facts
   - Legal argument connecting facts to MCR 2.003(C)(1) grounds

2. **Service** — Serve motion on all parties AND the judge.

3. **Referral to chief judge** — If challenged judge does not recuse:
   - Motion is referred to chief judge of the circuit (or designee)
   - Chief judge decides without evidentiary hearing (usually)
   - May order evidentiary hearing in rare cases

4. **Decision** — Chief judge grants or denies.

5. **Appellate review** — Denial is reviewable by COA under MCR 7.203(A).

## Bias Indicator Catalog

### Categories of Judicial Bias

| Category | Description | Examples |
|----------|-------------|---------|
| **Verbal bias** | Statements revealing prejudgment | Comments about credibility before testimony, sarcasm toward party |
| **Procedural bias** | Differential treatment in courtroom | Allowing objections from one side, cutting off arguments from other |
| **Evidentiary bias** | Unfair evidence rulings | Excluding relevant evidence from one party, admitting hearsay from other |
| **Ex parte bias** | Unauthorized communications | Private meetings with one party, off-record discussions |
| **Temporal bias** | Disproportionate time allocation | Rushing one party's presentation, extending other's |
| **Outcome bias** | Pattern of one-sided rulings | Statistical analysis of ruling patterns |
| **Demeanor bias** | Non-verbal indicators | Eye-rolling, sighing, hostile body language toward one party |

### Bias Indicator Scoring

```
Per incident:
  Documented (transcript/recording):  +3 points
  Corroborated by witness:            +2 points
  Self-reported (notes):              +1 point

Severity multipliers:
  Isolated incident:                  ×1
  Recurring pattern (3+ incidents):   ×2
  Systematic (affects case outcome):  ×3

Total Bias Score:
  0-10:   Within judicial discretion — document but no motion
  11-25:  Moderate bias — file for-cause disqualification
  26-50:  Severe bias — file disqualification + JTC complaint
  51+:    Extreme bias — emergency motion + JTC + appellate review
```

### Bias Documentation Template

```markdown
## Bias Indicator Record

| Field | Value |
|-------|-------|
| Date | [Date of incident] |
| Setting | [Hearing/Conference/Order/Ex parte] |
| Category | [Verbal/Procedural/Evidentiary/Ex parte/etc.] |
| Description | [Detailed factual description] |
| Witnesses | [Names of persons present] |
| Transcript ref | [Page:Line if available] |
| MCR 2.003 ground | [Specific subsection] |
| Evidence | [Documents, recordings, etc.] |
| Severity | [1-3] |
```

## JTC Complaint Preparation (MCR 9.104)

### Judicial Tenure Commission Overview

| Aspect | Detail |
|--------|--------|
| Authority | Michigan Constitution Art. 6 § 30; MCR 9.104 |
| Address | Judicial Tenure Commission, 3034 W. Grand Blvd., Ste. 8-450, Detroit, MI 48202 |
| Filing | Written complaint, notarized |
| Investigation | JTC investigates independently |
| Outcomes | Confidential admonishment, public censure, suspension, removal |

### Complaint Requirements

| Element | Description |
|---------|-------------|
| **Complainant identification** | Full name, address, phone |
| **Judge identification** | Full name, court, circuit |
| **Factual allegations** | Specific dates, events, witnesses |
| **Misconduct category** | See categories below |
| **Supporting documents** | Transcripts, orders, correspondence |
| **Verification** | Sworn/notarized statement of truth |

### JTC Misconduct Categories

| Category | Description | Canon Reference |
|----------|-------------|----------------|
| Misconduct in office | Acts in judicial capacity that violate law or rules | Canon 3A |
| Conduct prejudicial to administration of justice | Acts undermining public confidence | Canon 2A |
| Failure to perform duties | Neglect of judicial responsibilities | Canon 3A(1) |
| Habitual intemperance | Substance abuse affecting duties | Canon 2A |
| Conduct in violation of code | Specific code of judicial conduct violations | Various |
| Persistent failure to perform | Ongoing neglect pattern | Canon 3A(1) |

### Michigan Code of Judicial Conduct — Key Canons

| Canon | Subject | Key Provision |
|-------|---------|---------------|
| **Canon 1** | Integrity and independence | Judge shall uphold integrity of judiciary |
| **Canon 2** | Avoid impropriety | Judge shall avoid impropriety and appearance thereof |
| **Canon 2A** | Public confidence | Conduct that promotes public confidence |
| **Canon 2B** | No prestige lending | Cannot lend prestige of office |
| **Canon 3** | Duties of office | Adjudicative and administrative duties |
| **Canon 3A(1)** | Faithful duties | Faithfully perform duties |
| **Canon 3A(4)** | Patience and courtesy | Patient, dignified, courteous to all |
| **Canon 3A(7)** | No ex parte | Shall not initiate or consider ex parte communications |
| **Canon 3C** | Disqualification | When disqualification is required |
| **Canon 4** | Extra-judicial activities | Limits on outside activities |

### Ex Parte Contact Documentation

> **Canon 3A(7):** A judge shall not initiate, permit, or consider
> ex parte communications, or consider other communications made to
> the judge outside the presence of the parties concerning a pending
> or impending proceeding.

| Ex Parte Type | Description | Documentation Method |
|---------------|-------------|---------------------|
| Private chambers meeting | One party meets judge privately | Court calendar, security logs, witness accounts |
| Off-record communication | Judge communicates outside hearings | Email records, phone logs, FOIA |
| FOC back-channel | Judge discusses case with FOC ex parte | FOC communication logs, FOIA |
| Bench conference exclusion | Pro se party excluded from bench conference | Transcript showing sidebar without party |
| Email/letter | Written communication not shared with all parties | Court file review, FOIA |

## Appellate Review of Disqualification Denial

### MCR 7.203(A) — Appeal of Right

| Element | Detail |
|---------|--------|
| Basis | Denial of motion for disqualification |
| Filing deadline | 21 days from order denying disqualification |
| Court | Michigan Court of Appeals |
| Standard of review | Abuse of discretion |
| Interim relief | May seek stay of trial court proceedings |

### Mandamus as Alternative (MCR 7.206)

If ordinary appeal is inadequate, extraordinary writ of mandamus:

| Requirement | Standard |
|-------------|----------|
| No other adequate remedy | Appeal inadequate to protect rights |
| Clear legal right | Right to fair and impartial judge |
| Clear legal duty | Judge's duty to recuse when grounds exist |
| Irreparable harm | Prejudice from continued service cannot be undone |

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS judicial_bias_indicators (
    indicator_id    TEXT PRIMARY KEY,
    judge_name      TEXT DEFAULT 'Hon. Jenny L. McNeill',
    court           TEXT DEFAULT '14th Circuit Court',
    incident_date   TEXT NOT NULL,
    category        TEXT NOT NULL,
    description     TEXT NOT NULL,
    mcr_ground      TEXT,
    canon_violated  TEXT,
    severity        INTEGER CHECK(severity BETWEEN 1 AND 3),
    evidence_refs   TEXT,  -- JSON array
    witnesses       TEXT,  -- JSON array
    transcript_ref  TEXT,
    lane            TEXT DEFAULT 'E',
    case_number     TEXT DEFAULT '2024-001507-DC',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recusal_motions (
    motion_id       TEXT PRIMARY KEY,
    judge_name      TEXT DEFAULT 'Hon. Jenny L. McNeill',
    motion_type     TEXT CHECK(motion_type IN ('peremptory','for_cause')),
    mcr_grounds     TEXT,  -- JSON array of MCR 2.003 subsections
    filed_date      TEXT,
    hearing_date    TEXT,
    decided_date    TEXT,
    outcome         TEXT CHECK(outcome IN ('granted','denied','pending','withdrawn')),
    appealed        INTEGER DEFAULT 0,
    appeal_case     TEXT,
    indicator_refs  TEXT,  -- JSON array of indicator_ids
    lane            TEXT DEFAULT 'E',
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bias_judge
    ON judicial_bias_indicators(judge_name, incident_date);
CREATE INDEX IF NOT EXISTS idx_bias_category
    ON judicial_bias_indicators(category, severity);
CREATE INDEX IF NOT EXISTS idx_recusal_outcome
    ON recusal_motions(outcome, motion_type);
```

## Integration

### Companion Skills

- [litigation-judicial-analyst](skill://litigation-judicial-analyst) — Judicial pattern analysis
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Evidence gathering
- [litigation-appellate-strategist](skill://litigation-appellate-strategist) — Appeal of denial
- [litigation-sanctions-engine](skill://litigation-sanctions-engine) — Judicial misconduct sanctions
- [litigation-filing-architect](skill://litigation-filing-architect) — Motion filing

### Companion Agents

- `judicial-recusal-engine` — Automated bias cataloging and motion preparation
- `transcript-analyzer` — Extract bias indicators from transcripts
- `order-compliance-monitor` — Track judicial conduct across orders

### Python Module

- `00_SYSTEM/legal_ai/judicial_recusal_engine.py` — Computational engine

## Fabrication Warnings

- **DO NOT** fabricate bias incidents, dates, or transcript references.
- **DO NOT** invent Canon violations or JTC outcomes.
- **DO NOT** make personal attacks on the judge — focus on documented conduct.
- **DO NOT** use "Emily Ann" or "Emily M." — defendant is Emily A. Watson.
- **ALWAYS** spell Judge McNeill with TWO L's: Hon. Jenny L. McNeill.
- **ALWAYS** use L.D.W. for the child per MCR 8.119(H).
- **ALWAYS** verify MCR and Canon citations against current rules.
- **ALWAYS** note that JTC proceedings are confidential until public action.

## Output Format

```markdown
## Judicial Disqualification Analysis — [Case Number]

### Judge: Hon. Jenny L. McNeill — 14th Circuit Court
### Bias Score: [X] — [Level]

| # | Date | Category | Description | MCR Ground | Severity |
|---|------|----------|-------------|------------|----------|
| 1 | [Date] | [Type] | [Description] | 2.003(C)(1)([x]) | [1-3] |

### Recommended Action
- [ ] Peremptory disqualification (if available)
- [ ] For-cause disqualification motion
- [ ] JTC complaint
- [ ] Appellate review

### Motion Draft Elements
1. [Factual basis with evidence refs]
2. [Legal argument with MCR citation]
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

### Governing Authority (Verified)
**MCR:** MCR 2.003(C)(1), MCR 2.003(C)(2), MCR 2.003(D)(1), MCR 2.003(D)(3)
**MCL:** MCL 600.225, Const 1963 art 6 § 30
**Binding Cases:**
- *Armstrong v Ypsilanti Twp, 248 Mich App 573*
- *Kern v Kern-Koskela, 320 Mich App 212*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 3.210 | 761 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
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
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
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
| PPO Modification/Termination | 60/100 | D,E,F | Verified |
| Judicial Disqualification | 75/100 | D,E,F | Verified |
| Appeal Brief | 70/100 | D,E,F | Verified |
| Leave Application (MSC) | 80/100 | D,E,F | Verified |
| JTC Formal Complaint | 75/100 | D,E,F | Verified |

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
