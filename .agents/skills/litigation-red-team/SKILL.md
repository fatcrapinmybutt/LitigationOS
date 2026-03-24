---
name: litigation-red-team
description: >-
  Use when stress-testing filings through adversarial simulation, opposing counsel perspective analysis, or identifying weaknesses and attack vectors in draft court documents.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: red team, stress test, adversarial, opposing counsel, weakness
---

# litigation-red-team

## Metadata

```yaml
name: litigation-red-team
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when stress-testing filings through adversarial simulation, opposing counsel
  perspective analysis, and 25+ attack vector evaluation for Michigan 14th Judicial
  Circuit litigation across custody, housing, and convergence lanes.
triggers:
  - red team
  - attack vector
  - opposing counsel
  - adversarial review
  - stress test
  - weakness analysis
  - counter-argument
  - vulnerability scan
```

## Purpose

This skill subjects draft filings to rigorous adversarial analysis before court
submission. It simulates opposing counsel responses, predicts judicial reactions,
and identifies procedural/substantive/strategic vulnerabilities across all three
Pigors v Watson case lanes in the 14th Judicial Circuit, Muskegon County.

## Case Context

| Lane | Opposing Party | Known Counsel | Judge |
|------|---------------|---------------|-------|
| A | Watson | TBD / Self | McNeill |
| B | Shady Oaks Homes / Alden Global | Corporate defense counsel | Hoopes |
| C | Muskegon County entities | County/State attorneys | Multiple |

## Decision Tree

```
INPUT: Filing document + lane identifier + action ID
  │
  ├─ Phase 1: INTAKE CLASSIFICATION
  │   ├─ Identify document type (motion, brief, complaint, affidavit)
  │   ├─ Identify lane (A/B/C) and applicable rule set
  │   ├─ Identify claims / relief sought
  │   └─ Map to attack vector library
  │
  ├─ Phase 2: PROCEDURAL ATTACK SCAN (Vectors 1–8)
  │   ├─ V1: Jurisdiction / standing challenge
  │   ├─ V2: Statute of limitations / laches
  │   ├─ V3: Service defects (MCR 2.105)
  │   ├─ V4: Failure to state a claim (MCR 2.116(C)(8))
  │   ├─ V5: Improper venue
  │   ├─ V6: Failure to exhaust administrative remedies
  │   ├─ V7: Mootness / ripeness
  │   └─ V8: Res judicata / collateral estoppel
  │
  ├─ Phase 3: SUBSTANTIVE ATTACK SCAN (Vectors 9–18)
  │   ├─ V9:  Insufficient factual allegations
  │   ├─ V10: Weak or missing evidence linkage
  │   ├─ V11: Misapplied legal standard
  │   ├─ V12: Contradicted by record evidence
  │   ├─ V13: Overreliance on hearsay (MRE 801–807)
  │   ├─ V14: Authentication gaps (MRE 901)
  │   ├─ V15: Privilege / confidentiality issues
  │   ├─ V16: Best evidence rule violations (MRE 1001–1008)
  │   ├─ V17: Expert witness foundation gaps (MRE 702)
  │   └─ V18: Constitutional argument weaknesses
  │
  ├─ Phase 4: STRATEGIC ATTACK SCAN (Vectors 19–28)
  │   ├─ V19: Predictable counter-narrative
  │   ├─ V20: Timing vulnerability (premature / late)
  │   ├─ V21: Credibility exposure (prior inconsistencies)
  │   ├─ V22: Proportionality challenge (sanctions risk)
  │   ├─ V23: Alternative explanation strength
  │   ├─ V24: Sympathy asymmetry (judge/jury perspective)
  │   ├─ V25: Resource asymmetry exploitation
  │   ├─ V26: Cross-lane contamination risk
  │   ├─ V27: Public record / media exposure risk
  │   └─ V28: Appeal vulnerability analysis
  │
  └─ Phase 5: OUTPUT GENERATION
      ├─ Vulnerability matrix (vector × severity × likelihood)
      ├─ Opposing counsel response draft (top 3 attacks)
      ├─ Recommended fortifications
      ├─ Risk-adjusted filing confidence score
      └─ Red/yellow/green status per section
```

## Mode Switches

### Mode 1: FULL RED TEAM
All 28 attack vectors scanned. Produces complete vulnerability matrix.
Default mode for any filing before submission.

### Mode 2: PROCEDURAL ONLY
Vectors 1–8 only. Use for quick procedural compliance check.

### Mode 3: OPPOSING COUNSEL SIMULATION
Generates a full mock response brief from opposing counsel's perspective.
Includes predicted motion to dismiss, response brief, or objection.

### Mode 4: JUDGE PERSPECTIVE
Simulates judicial review. Flags likely concerns, questions from bench,
and areas where judge may sua sponte raise issues.

### Mode 5: APPEAL PREVIEW
Evaluates filing for appellate preservation. Identifies arguments that
must be raised now to avoid waiver on appeal.

## Output Contract

```yaml
output:
  vulnerability_matrix:
    type: table
    columns:
      - vector_id: V1–V28
      - vector_name: string
      - severity: CRITICAL | HIGH | MEDIUM | LOW | NONE
      - likelihood: percentage (0–100)
      - affected_sections: list[string]
      - recommended_fix: string
      - fix_effort: hours estimate

  opposing_response:
    type: document
    format: mock brief / motion
    length: proportional to filing complexity
    includes:
      - case caption
      - argument headers
      - citation blocks
      - prayer for relief

  confidence_score:
    type: object
    fields:
      - overall: float (0.0–1.0)
      - procedural: float
      - substantive: float
      - strategic: float
      - recommendation: FILE | REVISE | HOLD | ABANDON

  section_status:
    type: list
    items:
      - section: string
      - status: RED | YELLOW | GREEN
      - notes: string
```

## Attack Vector Library — Lane A (Custody)

### Procedural Attacks
- **Standing**: Non-parent standing challenge under MCL 722.26b
- **Proper cause / change of circumstances**: Vodvarka v Grasmeyer threshold
- **UCCJEA jurisdiction**: Challenge home-state jurisdiction (MCL 722.1201)
- **Friend of Court**: Failure to consult / respond to FOC recommendation

### Substantive Attacks
- **Best interest factors**: MCL 722.23 factor-by-factor rebuttal
- **Established custodial environment**: Challenge ECE determination
- **Parental fitness**: Counterevidence of fitness
- **Domestic violence allegations**: Credibility challenges under MCL 722.27a(6)

### Strategic Attacks
- **Alienation narrative**: Reframe alienation claims as protective behavior
- **Emotional bias**: Exploit emotional language to claim lack of objectivity
- **Volume overwhelm**: Argue filing volume is harassment / bad faith

## Attack Vector Library — Lane B (Housing)

### Procedural Attacks
- **Contractual privity**: Challenge standing if not on lease
- **Notice requirements**: Failure to comply with MCL 554.139 notice
- **Statute of limitations**: 3-year window for property claims
- **Class action prerequisites**: Challenge if framed as representative

### Substantive Attacks
- **Habitability standard**: Dispute severity of conditions
- **Causation**: Argue tenant-caused damage
- **Mitigation failure**: Tenant failed to mitigate damages
- **Corporate veil**: Challenge entity piercing attempts

## Attack Vector Library — Lane C (Convergence)

### Procedural Attacks
- **Sovereign immunity**: Governmental immunity under MCL 691.1407
- **Qualified immunity**: Individual official immunity (42 USC § 1983)
- **Exhaustion**: Failure to exhaust state remedies before federal
- **Younger abstention**: Federal court deference to state proceedings

### Substantive Attacks
- **Color of law**: Challenge "state action" element
- **Causation chain**: Break link between official action and harm
- **De minimis harm**: Argue insufficient injury for § 1983
- **Judicial immunity**: Absolute immunity for judicial acts

## Severity Classification

| Level | Definition | Action Required |
|-------|-----------|-----------------|
| CRITICAL | Filing will likely be dismissed or sanctioned | Must fix before filing |
| HIGH | Strong opposing argument likely to succeed | Should fix before filing |
| MEDIUM | Viable opposing argument, uncertain outcome | Recommend fixing |
| LOW | Weak opposing argument, unlikely to succeed | Note and monitor |
| NONE | No viable attack on this vector | No action needed |

## Confidence Score Calculation

```
overall = (procedural × 0.35) + (substantive × 0.40) + (strategic × 0.25)

Where each component:
  1.0 = No vulnerabilities found
  0.8 = Low-severity issues only
  0.6 = Medium-severity issues present
  0.4 = High-severity issues present
  0.0 = Critical vulnerabilities found

Recommendation thresholds:
  ≥ 0.80 → FILE
  0.60–0.79 → REVISE (fix HIGH+ issues)
  0.40–0.59 → HOLD (major rework needed)
  < 0.40 → ABANDON or complete rewrite
```

## Integration Points

- **litigation-filing-architect**: Receives filing for red team review
- **litigation-judicial-analyst**: Provides judge tendency data for Mode 4
- **litigation-impeachment-engine**: Provides contradiction data for V21
- **litigation-evidence-harvester**: Validates evidence linkage for V10/V14

## Usage Examples

```
# Full red team of custody motion
invoke litigation-red-team --filing A12_motion.md --mode full

# Quick procedural check on housing complaint
invoke litigation-red-team --filing B1_complaint.md --mode procedural

# Generate opposing counsel response
invoke litigation-red-team --filing A3_brief.md --mode opposing-counsel

# Judge perspective review
invoke litigation-red-team --filing C1_complaint.md --mode judge
```

## Related Skills

- [litigation-impeachment-engine](skill://litigation-impeachment-engine) — Detects contradictions for impeachment
- [litigation-judicial-analyst](skill://litigation-judicial-analyst) — Analyzes judicial behavior and bias

## Self-Improvement Log

### v2.1 (2026-03-11) — Session-Learned Enhancements

**Fabrication Detection Vectors (NEW — V26-V30)**:
- **V26 FABRICATED_STATISTICS**: Check for inflated numbers — "CPS records [VERIFY — check actual CPS records for count]" (real: 1 call), "571 days" (real: 215+), "documented pattern of parental alienation" (should be "305 documented incidents"). AI-generated filings frequently inflate statistics.
- **V27 HALLUCINATED_CITATIONS**: Cross-reference ALL case citations against known-real list. Known hallucinations: McCraney v Ford Motor Co 282 Mich App 647 (2009). If citation cannot be verified, flag as [VERIFY].
- **V28 BIRTHDAY_MATH**: Child DOB 11/9/2022. 1st=2023, 2nd=2024, 3rd=2025. AI frequently miscalculates which birthday is which.
- **V29 NAME_VARIANTS**: Emily A. Watson ONLY. NOT "Emily Ann Watson", "Emily M. Watson", "EMILY M. WATSON", or "Emily A. Watson". Party name errors are the #1 clerk rejection reason.
- **V30 CASE_NUMBER_FORMAT**: Michigan case numbers require leading zeros: 2024-001507-DC (NOT 2024-1507-DC). PPO: 2023-5907-PP (NOT 2023-05907-PP in body text, though the PPO number itself is 2023-05907-PP).

**QA Report Standard Format**: Red-team reports should follow the CLERK_READY/QA_REPORT.md format:
1. Per-filing grade (A/B/C/D/F)
2. Factual errors (zero tolerance)
3. Citation verification status
4. MCR compliance (PASS/FAIL)
5. Top 5 attack vectors with mitigations
6. Placeholder count
7. GO/NO-GO recommendation

**Opposing Counsel Profile (Ronald Berry)**: Non-attorney providing shadow legal help to Emily Watson. Known tactics: weaponizing show cause motions, coordinating with Albert Watson for manufactured evidence (NSPD NS2505044), using ex parte applications without adequate notice. His involvement itself is an unauthorized practice of law (MCR 8.120).

**Judge McNeill Profile**: 18.26% ex parte rate (3.65x normal), mutes pro se plaintiff, imposed $250 filing deposit barrier, disparaged AI-assisted legal research. Likely reactions: hostile to disqualification motion, may fast-track show cause, may deny emergency PT citing "pending proceedings." Mitigation: file disqualification FIRST, then file substantive motions with new judge.

**Cross-Filing Consistency Check (NEW)**: When red-teaming multiple filings for the same case, verify that facts/dates/statistics are IDENTICAL across all documents. One inconsistency gives opposing counsel ammunition to attack ALL filings as unreliable.


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
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
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
| `litigation-impeachment-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-evidence-authentication` | Integration | Complementary analysis |
| `litigation-settlement-analyzer` | Integration | Complementary analysis |

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
