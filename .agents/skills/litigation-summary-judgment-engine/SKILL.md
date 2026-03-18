---
name: litigation-summary-judgment-engine
description: >
  Michigan summary judgment specialist covering MCR 2.116 (all
  sub-rules), the Maiden v Rozwood prima facie framework, Quinto v
  Cross & Peters burden-shifting, documentary evidence requirements,
  and 21-day briefing schedules. Analyzes dispositive motions and
  generates response strategies.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - summary judgment
    - summary disposition
    - MCR 2.116
    - Maiden v Rozwood
    - Quinto v Cross
    - no genuine issue
    - material fact
    - dispositive motion
    - motion for summary judgment
    - MCR 2.116(C)(10)
    - MCR 2.116(C)(8)
    - MCR 2.116(C)(7)
    - prima facie case
    - burden shifting
---

# Summary Judgment Engine

## Description

Expert system for Michigan summary disposition practice in Pigors v.
Watson (Lane A — 2024-001507-DC) and Lane B (2025-002760-CZ). Handles
both moving for and defending against summary judgment under MCR 2.116.

Key capabilities:
- **Ground selection** — analyzes which MCR 2.116(C) ground(s) apply:
  - (C)(7): Immunity, release, statute of limitations
  - (C)(8): Failure to state a claim (legal sufficiency)
  - (C)(9): No genuine issue — moving party's burden
  - (C)(10): No genuine issue — nonmoving party's burden
- **Burden analysis** — applies *Maiden v Rozwood*, 461 Mich 109 (1999)
  framework: movant's initial burden → nonmovant's production burden →
  court's evaluation of genuine issues of material fact.
- **Evidence mapping** — catalogs admissible evidence supporting each
  element per *Quinto v Cross & Peters*, 451 Mich 358 (1996).
- **Element-by-element checklist** — for each claim/defense, verifies
  whether evidence exists for every required element.
- **Brief generation support** — structures arguments with proper
  standard of review, statement of material facts, and legal analysis.
- **Response strategy** — when defending, identifies disputed facts,
  locates counter-evidence, and recommends MCR 2.116(H) response.

## Triggers

Use this skill when the user mentions:
- "summary judgment", "summary disposition", "MSJ", "MSD"
- "MCR 2.116", "MCR 2.116(C)(7)", "MCR 2.116(C)(8)", "MCR 2.116(C)(10)"
- "Maiden v Rozwood", "Quinto v Cross & Peters"
- "no genuine issue of material fact"
- "prima facie case", "burden shifting"
- "dispositive motion", "motion for summary"
- "statement of material facts"
- "56(a) motion" (federal equivalent reference)

## Michigan Rules

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 2.116(B) | Timing — any time after responsive pleading |
| MCR 2.116(C)(7) | Immunity, release, statute of limitations |
| MCR 2.116(C)(8) | Failure to state a claim |
| MCR 2.116(C)(9) | No genuine issue — defendant's burden |
| MCR 2.116(C)(10) | No genuine issue — both parties' burden |
| MCR 2.116(G)(2) | Affidavits — personal knowledge required |
| MCR 2.116(G)(3)(b) | Opposition — specific facts, not mere allegations |
| MCR 2.116(G)(4) | Court may order discovery before ruling |
| MCR 2.116(G)(5) | Unavailable affidavits — MCR 2.116(H) adjournment |
| MCR 2.116(G)(6) | Affidavits made in bad faith — sanctions |
| MCR 2.116(H) | Opposition party's response — 21-day deadline |
| MCR 2.116(I)(1) | Court's duty to state grounds |

### Key Case Law
| Case | Holding |
|------|---------|
| *Maiden v Rozwood*, 461 Mich 109 (1999) | Burden framework for (C)(10) motions |
| *Quinto v Cross & Peters*, 451 Mich 358 (1996) | Evidence quality for prima facie case |
| *Celina Mutual v Lake States Ins*, 452 Mich 84 (1996) | (C)(8) tests complaint sufficiency only |
| *Skinner v Square D Co*, 445 Mich 153 (1994) | View evidence in light most favorable to nonmovant |
| *Coblentz v Novi*, 475 Mich 558 (2006) | Refreshed summary disposition standards |

### Deadlines
| Action | Rule | Days |
|--------|------|------|
| File motion | MCR 2.116(B) | After responsive pleading |
| Serve response | MCR 2.116(H) | 21 days before hearing |
| Serve reply | MCR 2.116(H) | 7 days before hearing |

## Patterns

1. **Select the right ground first** — (C)(8) tests legal sufficiency
   only; (C)(10) requires evidence; mixing them weakens the motion.
2. **Map evidence to elements** — create a matrix: claim elements on
   rows, evidence items on columns, mark coverage.
3. **Use the *Maiden* framework** — state the movant's initial burden,
   then show whether the nonmovant produced specific facts.
4. **Draft a statement of material facts** — numbered, concise, with
   record citations; each fact should be independently provable.
5. **Anticipate the response** — when moving, identify the nonmovant's
   best counter-evidence and address it preemptively.
6. **Request adjournment if discovery incomplete** — MCR 2.116(H)
   allows requesting delay to complete essential discovery.

## Anti-patterns

- ❌ **Never move under (C)(10) without evidence** — the motion must
  be supported by affidavits, depositions, admissions, or documents.
- ❌ **Never rely on conclusory affidavits** — MCR 2.116(G)(2)
  requires personal knowledge and specific facts.
- ❌ **Never ignore the 21-day response deadline** — failure to
  respond timely may result in the motion being granted.
- ❌ **Never argue credibility** — summary judgment is about whether
  facts are disputed, not who is more believable.
- ❌ **Never move without checking discovery status** — premature
  motions invite MCR 2.116(H) adjournment requests.

## Related Skills

- `litigation-brief-writer` — writes the actual brief supporting
  or opposing the motion.
- `litigation-evidence-harvester` — collects evidence for the
  element-by-element checklist.
- `litigation-cause-of-action-library` — provides element lists
  for each cause of action.


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
**MCR:** MCR 2.116(C)(7), MCR 2.116(C)(8), MCR 2.116(C)(10), MCR 2.116(G)(4)
**Binding Cases:**
- *Maiden v Rozwood, 461 Mich 109*
- *Quinto v Cross & Peters, 451 Mich 358*
- *Barnard Mfg v Gates Performance, 285 Mich App 362*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |

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
| Custody Modification | 65/100 | A,B,D | Verified |
| Emergency Custody | 55/100 | A,B,D | Verified |
| PPO Modification/Termination | 60/100 | A,B,D | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D | Verified |
| Contempt | 70/100 | A,B,D | Verified |
| Default Judgment | 60/100 | A,B,D | Verified |
| TRO Application | 60/100 | A,B,D | Verified |

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

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
