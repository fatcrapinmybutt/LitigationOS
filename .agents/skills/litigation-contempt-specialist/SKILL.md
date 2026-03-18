---
name: litigation-contempt-specialist
description: >
  Michigan contempt of court specialist covering civil contempt
  (MCL 600.1701), criminal contempt (MCL 600.1715), and contempt
  procedure under MCR 3.606. Drafts motions for show cause, analyzes
  purge conditions, calculates compensatory damages, and tracks
  compliance with existing court orders.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - contempt
    - show cause
    - MCL 600.1701
    - MCL 600.1715
    - MCR 3.606
    - order violation
    - purge condition
    - coercive contempt
    - compensatory contempt
    - civil contempt
    - criminal contempt
    - custody violation
    - parenting time violation
    - court order compliance
---

# Contempt Specialist

## Description

Expert system for Michigan contempt proceedings in Pigors v. Watson
(Lane A — 2024-001507-DC) and related cases. Contempt is the primary
enforcement tool when a party violates custody orders, parenting time
schedules, PPO conditions, or disclosure obligations.

Key capabilities:
- **Civil vs. criminal classification** — civil contempt (MCL 600.1701)
  coerces compliance and compensates the aggrieved party; criminal
  contempt (MCL 600.1715) punishes past conduct.
- **Show-cause motion drafting** — identifies the violated order,
  specific provisions breached, dates of violation, and available
  evidence.
- **Purge condition analysis** — determines conditions defendant can
  satisfy to purge contempt (must be within defendant's ability to
  perform — *In re Contempt of Dougherty*, 429 Mich 81 (1987)).
- **Compensatory damage calculation** — out-of-pocket costs caused by
  violations (makeup parenting time, lost wages, attorney fees under
  MCL 600.1721).
- **Compliance tracking** — monitors ongoing compliance with existing
  orders and flags new violations.

## Triggers

Use this skill when the user mentions:
- "contempt", "show cause", "contempt motion"
- "MCL 600.1701", "MCL 600.1715", "MCR 3.606"
- "order violation", "violating court order"
- "purge condition", "purge contempt"
- "custody violation", "parenting time violation"
- "makeup parenting time"
- "compensatory damages for contempt"
- "coercive contempt", "criminal contempt"
- "attorney fees for contempt", "MCL 600.1721"
- "PPO violation enforcement"

## Michigan Rules & Statutes

### Statutes
| Statute | Subject |
|---------|---------|
| MCL 600.1701 | Civil contempt — power of courts |
| MCL 600.1711 | Contempt procedure — notice requirements |
| MCL 600.1715 | Criminal contempt — conduct in presence of court |
| MCL 600.1721 | Contempt sanctions — fines, jail, costs, attorney fees |
| MCL 722.27a | Parenting time — makeup time for violations |

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 3.606 | Contempt proceedings — procedure and hearing |
| MCR 3.606(A) | Initiating contempt — motion or court's own |
| MCR 3.606(B) | Show-cause order requirements |
| MCR 3.606(C) | Hearing and burden of proof |
| MCR 3.208 | Friend of the court — contempt referrals |

### Key Case Law
| Case | Holding |
|------|---------|
| *In re Contempt of Dougherty*, 429 Mich 81 (1987) | Purge conditions must be within contemnor's ability |
| *In re Contempt of Henry*, 282 Mich App 656 (2009) | Due process requirements for contempt hearings |
| *Sword v Sword*, 399 Mich 367 (1976) | Civil contempt standard — willful and contumacious |
| *Harvey v Harvey*, 470 Mich 186 (2004) | Parenting time enforcement and makeup time |

## Patterns

1. **Identify the order first** — every contempt motion must cite the
   specific order, date entered, and exact provision violated.
2. **Document each violation with evidence** — dates, communications,
   witnesses, FOC reports, police reports.
3. **Classify civil vs. criminal early** — civil contempt uses
   preponderance standard; criminal requires beyond reasonable doubt
   and additional procedural protections.
4. **Propose reasonable purge conditions** — must be achievable by the
   contemnor; impossible conditions are unenforceable.
5. **Calculate compensatory damages precisely** — itemize each cost
   with receipts, lost-wage documentation, and attorney fee affidavit.
6. **Request attorney fees under MCL 600.1721** — prevailing party in
   contempt may recover reasonable fees.

## Anti-patterns

- ❌ **Never file contempt without specific order cite** — "general
  misconduct" is insufficient; cite the exact order and provision.
- ❌ **Never set impossible purge conditions** — *Dougherty* requires
  conditions within the contemnor's present ability.
- ❌ **Never pursue criminal contempt without counsel** — pro-se
  parties should pursue civil contempt; criminal contempt requires
  additional protections (right to counsel, jury for serious offenses).
- ❌ **Never rely solely on FOC recommendation** — contempt requires
  independent judicial determination.
- ❌ **Never conflate punishment and coercion** — civil contempt ends
  when the contemnor complies; if the purpose is solely punitive,
  it must be prosecuted as criminal contempt.

## Related Skills

- `litigation-custody-specialist` — custody order enforcement via
  contempt.
- `litigation-ppo-specialist` — PPO violation enforcement.
- `litigation-harm-quantifier` — damages from order violations.
- `litigation-service-engine` — service of show-cause order.


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
**MCR:** MCR 3.606, MCR 3.208(C), MCR 2.114
**MCL:** MCL 600.1701, MCL 600.1711, MCL 600.1715, MCL 552.636
**Binding Cases:**
- *In re Contempt of Dougherty, 429 Mich 81*
- *Porter v Porter, 285 Mich App 450*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
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
| Custody Modification | 65/100 | A,D,E | Verified |
| Emergency Custody | 55/100 | A,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,D,E | Verified |
| Contempt | 70/100 | A,D,E | Verified |
| Judicial Disqualification | 75/100 | A,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,D,E | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
