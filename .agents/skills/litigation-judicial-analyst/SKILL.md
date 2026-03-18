---
name: litigation-judicial-analyst
description: >-
  Use when analyzing judicial behavior, detecting bias patterns, evaluating Canon compliance, or preparing recusal and disqualification motions.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: judicial, judge, bias, misconduct, disqualification, Canon
---

# litigation-judicial-analyst

## Metadata

```yaml
name: litigation-judicial-analyst
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when analyzing judicial behavior, detecting bias patterns, evaluating
  Canon compliance, or preparing recusal and disqualification motions for
  judges in the 14th Judicial Circuit, Muskegon County (McNeill, Hoopes).
triggers:
  - judge analysis
  - judicial bias
  - recusal
  - disqualification
  - canon violation
  - judge behavior
  - judicial misconduct
  - bench patterns
```

## Purpose

This skill provides systematic analysis of judicial conduct, decision patterns,
and potential bias indicators for judges presiding over Pigors v Watson litigation
in the Michigan 14th Judicial Circuit. It supports Canon violation documentation,
recusal motion preparation, and JTC complaint development.

## Judge Assignment Map

| Judge | Lane(s) | Case Type | Case Number(s) |
|-------|---------|-----------|-----------------|
| McNeill | A | Custody / PPO | 2024-001507-DC, 2023-5907-PP |
| Hoopes | B | Housing / Civil | 2025-002760-CZ |
| Multiple | C | Convergence | Cross-lane |

## Decision Tree

```
INPUT: Judge name + analysis type + source materials
  │
  ├─ Phase 1: PROFILE LOAD
  │   ├─ Load judge profile (background, appointment, tenure)
  │   ├─ Load prior ruling database (if available)
  │   ├─ Load known affiliations and recusal history
  │   └─ Load Canon compliance baseline
  │
  ├─ Phase 2: BEHAVIOR PATTERN ANALYSIS
  │   ├─ Ruling consistency analysis
  │   │   ├─ Compare similar motions → different outcomes?
  │   │   ├─ Compare treatment of parties (pro se vs. represented)
  │   │   └─ Compare procedural accommodation (extensions, hearings)
  │   │
  │   ├─ Courtroom conduct analysis
  │   │   ├─ Tone / demeanor differential between parties
  │   │   ├─ Speaking time allocation
  │   │   ├─ Interruption patterns
  │   │   └─ Ex parte communication indicators
  │   │
  │   └─ Record integrity analysis
  │       ├─ Delays in producing transcripts / orders
  │       ├─ Off-record conversations
  │       ├─ Sealed proceedings justification
  │       └─ Docket manipulation indicators
  │
  ├─ Phase 3: CANON VIOLATION ASSESSMENT
  │   ├─ Canon 1: Integrity and independence of judiciary
  │   ├─ Canon 2: Avoiding impropriety / appearance thereof
  │   ├─ Canon 3: Impartial and diligent performance
  │   │   ├─ 3(A)(3): Patience, dignity, courtesy
  │   │   ├─ 3(A)(4): No ex parte communications
  │   │   ├─ 3(B)(5): No bias based on protected characteristics
  │   │   └─ 3(B)(7): Recusal when impartiality questionable
  │   ├─ Canon 4: Extra-judicial activities
  │   └─ Canon 5: Political activity restrictions
  │
  ├─ Phase 4: RECOMMENDATION ENGINE
  │   ├─ If pattern score ≥ MODERATE → Prepare recusal brief
  │   ├─ If pattern score ≥ SEVERE → Prepare disqualification motion
  │   ├─ If pattern score ≥ EGREGIOUS → Prepare JTC complaint
  │   └─ Generate strategic advisory for courtroom adaptation
  │
  └─ OUTPUT: Judge analysis report + recommendations
```

## Mode Switches

### Mode 1: FULL PROFILE ANALYSIS
Complete analysis of a judge across all categories. Use for initial
strategic assessment before major filings.

### Mode 2: INCIDENT ANALYSIS
Analyze a specific judicial event (ruling, hearing, order) for
Canon compliance and bias indicators.

### Mode 3: RECUSAL PREPARATION
Generate recusal motion materials including legal authority,
factual basis, and supporting affidavit framework.

### Mode 4: JTC COMPLAINT DEVELOPMENT
Assemble materials for Michigan Judicial Tenure Commission complaint
under MCR 9.200 series, including pattern evidence compilation.

### Mode 5: COURTROOM STRATEGY
Generate tactical recommendations for appearing before a specific
judge — argument framing, demeanor, procedural preferences.

## Output Contract

```yaml
output:
  judge_analysis:
    type: report
    sections:
      - profile_summary: background, tenure, appointment source
      - pattern_analysis:
          ruling_patterns: list[{category, finding, severity}]
          conduct_patterns: list[{behavior, frequency, severity}]
          record_patterns: list[{issue, evidence, severity}]
      - canon_violations:
          type: checklist
          items: list[{canon, sub_section, status, evidence, severity}]
      - bias_indicators:
          type: scored_list
          items: list[{indicator, score_0_to_10, supporting_evidence}]
      - overall_assessment:
          pattern_score: MINIMAL | MODERATE | SEVERE | EGREGIOUS
          recommended_action: MONITOR | ADAPT | RECUSE | DISQUALIFY | JTC
          confidence: float (0.0–1.0)

  recusal_package:
    type: filing_materials
    includes:
      - motion_for_recusal.md
      - brief_in_support.md
      - affidavit_of_bias.md
      - exhibit_index.md
    authority:
      - MCR 2.003(C)(1) — personal bias
      - MCL 600.1428 — statutory disqualification
      - 28 USC § 455 — federal (if applicable)

  jtc_complaint:
    type: formal_complaint
    includes:
      - complaint_form.md
      - pattern_evidence_compilation.md
      - supporting_exhibits/
    authority:
      - Michigan Constitution Art. VI § 30
      - MCR 9.220 — complaint procedure
```

## Canon Violation Checklist — Detailed

### Canon 1: Integrity / Independence
| Sub-Rule | Test | Evidence Required |
|----------|------|-------------------|
| 1.1 | Does conduct undermine public confidence? | Documented instances |
| 1.2 | Independence from external influences? | Communication records |

### Canon 2: Impropriety / Appearance
| Sub-Rule | Test | Evidence Required |
|----------|------|-------------------|
| 2(A) | Would reasonable person question impartiality? | Pattern documentation |
| 2(B) | Lending prestige of office? | Public records, media |
| 2(C) | Relationships with attorneys appearing? | Disclosure records |

### Canon 3: Performance of Duties
| Sub-Rule | Test | Evidence Required |
|----------|------|-------------------|
| 3(A)(1) | Faithful to the law? | Ruling analysis vs. law |
| 3(A)(3) | Patient, dignified, courteous? | Transcript excerpts |
| 3(A)(4) | Ex parte communication? | Docket/communication logs |
| 3(B)(5) | Bias on protected characteristics? | Comparative rulings |
| 3(B)(7) | Recusal when impartiality questioned? | Prior recusal requests |

### Canon 4: Extra-Judicial Activities
| Sub-Rule | Test | Evidence Required |
|----------|------|-------------------|
| 4(A) | Activities cast doubt on impartiality? | Public records |
| 4(D) | Financial interests creating conflict? | Disclosure filings |

### Canon 5: Political Activities
| Sub-Rule | Test | Evidence Required |
|----------|------|-------------------|
| 5(A)(1) | Political organization leadership? | Public records |
| 5(C)(1) | Campaign conduct appropriate? | Campaign records |

## Bias Indicator Framework

### Structural Bias Indicators
1. **Outcome disparity**: Statistically different ruling rates by party type
2. **Procedural asymmetry**: Different procedural treatment of similarly situated parties
3. **Temporal patterns**: Delayed rulings for one party, expedited for another
4. **Access disparity**: Hearing time, motion hearing scheduling differences
5. **Pro se penalty**: Harsher treatment of self-represented litigants

### Behavioral Bias Indicators
1. **Tone differential**: Different vocal tone / language toward parties
2. **Interruption asymmetry**: Interrupting one party more than another
3. **Credibility presumption**: Accepting one party's claims without scrutiny
4. **Sua sponte assistance**: Helping one party's case unprompted
5. **Hostile questioning**: Adversarial questioning of one party only

### Evidentiary Bias Indicators
1. **Selective admission**: Admitting weak evidence for one side, excluding strong for other
2. **Weight manipulation**: Giving disproportionate weight to certain evidence
3. **Burden shifting**: Improperly shifting burden of proof
4. **Inference drawing**: Drawing negative inferences against one party
5. **Record manipulation**: Off-record comments, sealed proceedings without cause

## Severity Scale

| Score | Label | Definition | Recommended Action |
|-------|-------|------------|-------------------|
| 0–2 | MINIMAL | Normal judicial discretion range | MONITOR |
| 3–4 | MODERATE | Pattern emerging, warrants documentation | ADAPT strategy |
| 5–6 | SEVERE | Clear pattern, affects case outcomes | File RECUSAL motion |
| 7–8 | EGREGIOUS | Systemic misconduct | DISQUALIFY + JTC |
| 9–10 | EXTREME | Willful violation of rights | JTC + federal complaint |

## Integration Points

- **litigation-filing-architect**: Provides filing templates for recusal/JTC motions
- **litigation-red-team**: Tests recusal motions before submission
- **litigation-impeachment-engine**: Supplies contradiction data for judicial statements
- **litigation-evidence-harvester**: Pulls courtroom evidence (transcripts, recordings)

## Usage Examples

```
# Full profile analysis of Judge McNeill
invoke litigation-judicial-analyst --judge McNeill --mode full

# Analyze specific hearing incident
invoke litigation-judicial-analyst --judge Hoopes --mode incident --source transcript_2025-03-15.md

# Prepare recusal motion materials
invoke litigation-judicial-analyst --judge McNeill --mode recusal

# Develop JTC complaint
invoke litigation-judicial-analyst --judge McNeill --mode jtc
```

## Related Skills

- [litigation-red-team](skill://litigation-red-team) — Stress-tests filings via adversarial review
- [litigation-sanctions-engine](skill://litigation-sanctions-engine) — Pursues sanctions and contempt proceedings

---

## Live Database Statistics (litigation_context.db)

| Table | Row Count | Description |
|-------|-----------|-------------|
| `judicial_violations` | 1,127 | Documented judicial conduct violations across all judges |
| `auth_benchbook_violations` | 504 | Violations of Michigan benchbook standards |
| `ex_parte_violations` | 267 | Documented ex parte communication violations |
| `evidence_quotes` | 308,636 | Source evidence including hearing transcripts |
| `docket_events` | Full timeline | All case docket events with timing analysis |

### McNeill Dossier Key Statistics
| Metric | Value | Significance |
|--------|-------|-------------|
| Total critical violations | 377 | Documented across custody and PPO proceedings |
| Ex parte order rate | 44% | Orders entered without hearing or notice |
| Canon 3(A)(4) violations | 267 | Ex parte communications |
| Canon 3(B)(7) violations | Multiple | Refusal to recuse despite demonstrated bias |
| Pro se accommodation failures | Documented | Systematic disadvantage of self-represented party |
| Parent-child separation | 329+ days | Direct consequence of judicial conduct |

### Key Database Queries
```sql
-- All judicial violations by severity
SELECT judge_name, canon_number, violation_description, severity
FROM judicial_violations
WHERE judge_name = 'McNeill'
ORDER BY severity DESC;

-- Benchbook violation patterns
SELECT rule, judge, severity, matching_text
FROM auth_benchbook_violations
WHERE judge = 'McNeill'
ORDER BY severity DESC;

-- Ex parte violation timeline
SELECT event_date_iso, title, summary
FROM docket_events
WHERE event_type = 'ex_parte' OR summary LIKE '%ex parte%'
ORDER BY event_date_iso ASC;

-- Orders entered without hearing (ex parte indicator)
SELECT event_date_iso, title, summary
FROM docket_events
WHERE event_type = 'order'
  AND NOT EXISTS (
    SELECT 1 FROM docket_events d2
    WHERE d2.event_type = 'hearing'
      AND d2.event_date_iso <= docket_events.event_date_iso
      AND d2.event_date_iso >= date(docket_events.event_date_iso, '-7 days')
  );
```

---

## Michigan Code of Judicial Conduct — Complete Canon Analysis

### Canon 1: Integrity and Independence of the Judiciary
A judge shall uphold the integrity and independence of the judiciary.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Undermining public confidence | Arbitrary rulings without legal basis | Order analysis vs. governing law | 7-8 |
| External influence susceptibility | Ruling patterns correlating with FOC recommendations despite errors | Docket timing analysis | 6-7 |
| Appearance of impropriety | Personal relationships with parties/counsel | Public records, disclosure filings | 8-9 |

### Canon 2: Avoiding Impropriety and Its Appearance
A judge shall avoid impropriety and the appearance of impropriety in all activities.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 2(A): Conduct raising reasonable question | Pattern of one-sided rulings | Statistical ruling analysis | 6-8 |
| 2(B): Lending prestige of office | Using judicial authority to advance private interests | Public records | 7-9 |
| 2(C): Testifying as character witness | Voluntarily testifying or providing references | Court records | 5-6 |

### Canon 3: Performing Duties Impartially and Diligently
A judge shall perform the duties of judicial office impartially and diligently.

| Sub-Rule | Violation Pattern | McNeill Evidence | Severity |
|----------|------------------|------------------|----------|
| 3(A)(1): Faithful to law | Rulings contradicting governing MCR/MCL | Order text vs. statute analysis | 8-9 |
| 3(A)(3): Patient, dignified, courteous | Hostile treatment of pro se party on the record | Transcript excerpts | 6-8 |
| 3(A)(4): No ex parte communications | **267 documented violations** — orders without notice, off-record conversations, sealed proceedings | Docket analysis, order timing | 9-10 |
| 3(B)(5): No bias on protected characteristics | Differential treatment of parties | Comparative ruling analysis | 7-8 |
| 3(B)(7): Recusal when impartiality questioned | Refusal to recuse despite documented bias | Recusal motion history | 8-9 |

### Canon 4: Extra-Judicial Activities
A judge shall conduct extra-judicial activities so as not to cast doubt on impartiality.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 4(A): Activities casting doubt | Community connections creating conflicts | Public records | 5-7 |
| 4(D): Financial conflicts | Financial interests in case outcomes | Disclosure filings | 7-9 |

### Canon 5: Political Activity
A judge shall refrain from inappropriate political activity.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| 5(A)(1): Political organization leadership | Active political involvement | Public records, campaign filings | 5-7 |
| 5(C)(1): Campaign conduct | Endorsements or quid pro quo indicators | Campaign records, public statements | 6-8 |

### Canon 6: Compliance with the Code
A judge shall comply with this Code and should report violations by other judges.

| Violation Pattern | Indicator | Evidence Source | Severity |
|------------------|-----------|-----------------|----------|
| Failure to self-report | Knowledge of own violations without correction | Pattern analysis | 7-8 |
| Failure to report others | Knowledge of other judges' violations | Cross-case analysis | 5-6 |

### Canon 7: A Judge or Candidate for Judicial Office
(Applies primarily during campaigns; less relevant to sitting judge conduct analysis.)

---

## MCR 2.003 — Disqualification Standards and Motion Template

### Grounds for Disqualification (MCR 2.003(C)(1))
| Ground | MCR Section | Standard | McNeill Application |
|--------|-------------|----------|---------------------|
| Personal bias or prejudice | (C)(1)(a) | Bias toward a party or attorney | 377 documented violations showing pattern |
| Personal knowledge of disputed facts | (C)(1)(b) | Judge has extra-judicial knowledge | Ex parte communications (267 instances) |
| Prior involvement | (C)(1)(c) | Previously involved as lawyer/witness/judge | N/A for current analysis |
| Financial interest | (C)(1)(d) | Direct or indirect financial interest | Check disclosure filings |
| Related to party/attorney | (C)(1)(e) | Within third degree of relationship | Investigate community connections |
| **Catch-all** | **(C)(1)(b)** | **Impartiality might reasonably be questioned** | **44% ex parte order rate + 329+ day separation** |

### MCR 2.003(D) — Procedure
1. **Motion must be filed**: In writing, specifying grounds with particularity
2. **Affidavit required**: Setting forth facts supporting disqualification
3. **Timeliness**: File promptly after discovering grounds (no specific deadline in MCR, but unreasonable delay = waiver argument)
4. **Judge rules on own motion**: The challenged judge decides the motion (MCR 2.003(D)(3)(a))
5. **If denied**: Seek immediate review via MCR 7.203(A) (application for leave)
6. **Peremptory disqualification**: MCR 2.003(B) — one automatic disqualification per side per case (file BEFORE any substantive proceeding)

### Disqualification Motion Template
```
MOTION FOR DISQUALIFICATION OF JUDGE [NAME]

I. GROUNDS
This motion is brought pursuant to MCR 2.003(C)(1)(a) and (b), on the
grounds that [Judge]'s impartiality might reasonably be questioned based on:

1. [Specific bias instance with date and record citation]
2. [Pattern evidence — number of violations, dates, citations]
3. [Ex parte communication evidence with dates]
4. [Cumulative impact — 329+ days separation, outcome]

II. SUPPORTING AUTHORITY
[IRAC analysis citing MCR 2.003, In re Contempt of Henry, Crampton v Dep't
of State, and other Michigan disqualification case law]

III. RELIEF REQUESTED
WHEREFORE, [Party] respectfully requests that [Judge] be disqualified from
further proceedings in this matter and the case be reassigned.

[Attached: Affidavit of Bias with specific facts]
[Attached: Exhibit Index documenting violations]
```

---

## JTC Complaint Pathway

### Governing Authority
- **Michigan Constitution, Art. 6, § 30**: Judicial Tenure Commission authority
- **MCR 9.200 series**: JTC complaint procedure
- **MCR 9.220**: Filing of complaint
- **MCR 9.221**: Investigation by Commission
- **MCR 9.223**: Formal complaint and hearing

### Complaint Filing Process
| Step | Action | Authority | Timeline |
|------|--------|-----------|----------|
| 1 | **Draft complaint** | MCR 9.220 | Written complaint with specific facts |
| 2 | **Submit to JTC** | Const art 6, § 30 | Mail to: Judicial Tenure Commission, 3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202 |
| 3 | **JTC investigation** | MCR 9.221 | Commission investigates; may be dismissed, resolved informally, or proceed |
| 4 | **Formal complaint** | MCR 9.223 | If JTC finds merit, files formal complaint |
| 5 | **Hearing** | MCR 9.224 | Public hearing before the Commission |
| 6 | **Recommendation to MSC** | MCR 9.225 | JTC recommends discipline to Michigan Supreme Court |
| 7 | **MSC action** | Const art 6, § 30 | MSC may censure, suspend, remove, or retire the judge |

### JTC Complaint Content Requirements
1. **Identification**: Full name and court of the judge
2. **Specific acts**: Each violation described with date, location, and witnesses
3. **Pattern evidence**: Chronological compilation showing systematic misconduct
4. **Supporting documents**: Copies of orders, transcripts, docket entries (DO NOT send originals)
5. **Impact statement**: How the conduct has affected the litigant and the judicial process

### JTC Complaint Template Structure
```
COMPLAINT TO THE MICHIGAN JUDICIAL TENURE COMMISSION

RE: Hon. [Judge Name], [Court]
Case No(s): [list]

I. RESPONDENT JUDGE
[Name, court, appointment date, tenure]

II. SUMMARY OF MISCONDUCT
[Executive summary — 1 paragraph with total violations and pattern]

III. SPECIFIC VIOLATIONS (chronological)
Violation 1: [Date] — [Description] — [Canon violated] — [Evidence]
Violation 2: [Date] — [Description] — [Canon violated] — [Evidence]
... [Continue for all documented violations]

IV. PATTERN ANALYSIS
[Statistical analysis: 44% ex parte orders, 267 ex parte violations,
377 total critical violations. Timeline showing escalation.]

V. IMPACT
[329+ days parent-child separation. Specific harm to litigant
and to public confidence in the judiciary.]

VI. RELIEF REQUESTED
[Investigation, formal complaint, public hearing, appropriate discipline]

ATTACHMENTS:
A. Chronological violation log (spreadsheet)
B. Supporting orders and transcripts (copies)
C. Statistical analysis report
D. Timeline visualization
```

---

## Judicial Pattern Analysis Methodology

### 1. Order Timing Analysis
Track the temporal pattern of judicial orders to identify ex parte indicators:

```
For each order O in docket_events WHERE event_type = 'order':
  Find nearest prior hearing H WHERE event_type = 'hearing'
  Calculate gap = O.date - H.date
  If gap > 7 days OR no hearing found → flag as potential ex parte
  Track: order_date, hearing_date, gap_days, parties_present, notice_given
```

**McNeill finding**: 44% of orders entered without proximate hearing = systematic ex parte pattern.

### 2. Ex Parte Frequency Analysis
```sql
-- Calculate ex parte rate for a judge
SELECT
  COUNT(CASE WHEN event_type = 'ex_parte' THEN 1 END) as ex_parte_count,
  COUNT(CASE WHEN event_type = 'order' THEN 1 END) as total_orders,
  ROUND(100.0 * COUNT(CASE WHEN event_type = 'ex_parte' THEN 1 END) /
    NULLIF(COUNT(CASE WHEN event_type = 'order' THEN 1 END), 0), 1) as ex_parte_pct
FROM docket_events
WHERE case_number IN ('2024-001507-DC', '2023-5907-PP');
```

### 3. Bias Indicator Scoring
| Indicator | Measurement | McNeill Score | Normal Range |
|-----------|-------------|---------------|-------------|
| Ruling rate for Plaintiff | % of motions granted | Document | 40-60% |
| Ruling rate for Defendant | % of motions granted | Document | 40-60% |
| Average time to rule (Plaintiff motions) | Days from filing to order | Document | 14-30 days |
| Average time to rule (Defendant motions) | Days from filing to order | Document | 14-30 days |
| Ex parte order percentage | % of orders without hearing | **44%** | <5% |
| Hearing time allocation | Minutes per party | Document | Equal ±10% |
| Pro se accommodation | Procedural guidance given | Document | Standard |

### 4. Escalation Timeline
Map the escalation of judicial misconduct over time:
```
[Date 1]: First ex parte order — severity 5
[Date 2]: Second ex parte order — severity 5
...
[Date N]: Pattern established — cumulative severity 9-10
[329+ days]: Parent-child separation continues — constitutional harm ongoing
```

### 5. Comparative Analysis
Compare the target judge's behavior against:
- Other judges on the same bench (14th Circuit)
- Michigan statewide judicial conduct statistics
- Published benchbook standards for family law proceedings
- Constitutional minimum standards for due process

---

## Anti-Rationalization Table

| # | Rationalization | Why It Fails | Correct Practice |
|---|----------------|--------------|------------------|
| 1 | "Judges have broad discretion" | Discretion is not unlimited — abuse of discretion = reversible error. *Vodvarka*, 259 Mich App at 508. | Document each instance where discretion exceeded legal bounds. Cite the specific standard violated. |
| 2 | "One bad ruling isn't bias" | Correct — but 377 documented violations IS a pattern. JTC evaluates cumulative conduct, not isolated incidents. | Always present pattern evidence, never isolated incidents. Statistical analysis > anecdote. |
| 3 | "The JTC won't act" | JTC does act — Michigan judges have been removed, suspended, and censured. The complaint creates a record regardless. | File the complaint. Even if no immediate action, it creates a documented record for appeal and federal proceedings. |
| 4 | "Filing for disqualification will anger the judge" | MCR 2.003 is a legal right. Retaliation for exercising procedural rights is itself a Canon violation. | File the motion. Document any retaliatory conduct as additional evidence. |
| 5 | "Pro se complaints aren't taken seriously" | JTC accepts complaints from any person. The quality of documentation matters, not the status of the filer. | Submit comprehensive, well-documented complaints with statistical analysis and specific record citations. |


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
**MCR:** MCR 2.003(C), MCR 2.003(D), MCR 9.104, MCR 9.112, MCR 9.116, MCR 9.205
**MCL:** MCL 600.225, MCL 600.235, Const 1963 art 6 § 30
**Binding Cases:**
- *Cain v Dept of Corrections, 451 Mich 470*
- *Crampton v Dept of State, 395 Mich 347*

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
| `litigation-judicial-recusal-engine` | Integration | Bidirectional data exchange |
| `litigation-impeachment-engine` | Integration | Bidirectional data exchange |
| `litigation-timeline-forensics` | Integration | Complementary analysis |
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
