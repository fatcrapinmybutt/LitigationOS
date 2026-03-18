---
name: litigation-interrogatory-specialist
description: >
  Michigan interrogatory drafting and response specialist covering
  MCR 2.309 (interrogatories to parties), the 35-interrogatory limit
  for circuit court and 25 for district court, objection strategies,
  privilege logs, and motion-to-compel preparation.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - interrogatory
    - interrogatories
    - MCR 2.309
    - discovery request
    - written discovery
    - interrogatory limit
    - 35 interrogatories
    - motion to compel
    - privilege log
    - discovery objection
    - subpart counting
    - supplemental response
---

# Interrogatory Specialist

## Description

Expert system for Michigan interrogatory practice in Pigors v. Watson
(Lane A — 2024-001507-DC) and related cases. Covers both propounding
and responding to interrogatories under MCR 2.309.

Key capabilities:
- **Interrogatory drafting** — crafts targeted questions within the
  MCR 2.309(A)(2) limits (35 for circuit court, 25 for district court),
  including discrete subpart counting per MCR 2.309(A)(4).
- **Subpart analysis** — determines whether compound questions count
  as one or multiple interrogatories under the "logically related"
  test from *Hinkle v Wayne Co Clerk*, 467 Mich 337 (2002).
- **Objection formulation** — generates proper objections (overbroad,
  burdensome, privilege, work-product, relevance) with supporting
  authority.
- **Privilege log creation** — builds itemized privilege logs per
  MCR 2.302(B)(5) with document date, author, recipients, and
  privilege basis.
- **Motion-to-compel preparation** — drafts MCR 2.313 motions when
  responses are inadequate, evasive, or untimely.
- **Response tracking** — monitors 28-day deadline (MCR 2.309(B)(1))
  and flags overdue responses.

## Triggers

Use this skill when the user mentions:
- "interrogatory", "interrogatories", "written questions"
- "MCR 2.309", "discovery request"
- "35-interrogatory limit", "25-interrogatory limit"
- "subpart counting", "discrete subparts"
- "discovery objection", "privilege objection"
- "privilege log", "MCR 2.302(B)(5)"
- "motion to compel", "MCR 2.313"
- "supplemental response", "amended answers"
- "28-day response deadline"

## Michigan Rules

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 2.309(A)(1) | Right to serve interrogatories on any party |
| MCR 2.309(A)(2) | 35-interrogatory limit (circuit), 25 (district) |
| MCR 2.309(A)(4) | Subpart counting — discrete subparts = separate |
| MCR 2.309(B)(1) | 28-day response deadline |
| MCR 2.309(B)(4) | Option to produce business records in lieu of answer |
| MCR 2.302(B)(1) | Scope of discovery — relevant, non-privileged |
| MCR 2.302(B)(5) | Privilege log requirements |
| MCR 2.302(C) | Protective orders |
| MCR 2.313(A) | Motion to compel discovery |
| MCR 2.313(B) | Sanctions for failure to comply |

### Key Case Law
| Case | Holding |
|------|---------|
| *Hinkle v Wayne Co Clerk*, 467 Mich 337 (2002) | Subpart counting test — "logically related" |
| *Domako v Rowe*, 438 Mich 347 (1991) | Discovery scope — relevance standard |
| *Augustine v Allstate Ins Co*, 292 Mich App 408 (2011) | Work-product doctrine scope |
| *Leibel v Gen Motors Corp*, 250 Mich App 229 (2002) | Sanctions for discovery abuse |

## Patterns

1. **Count subparts before serving** — each discrete subpart counts
   toward the 35/25 limit; structure questions to minimize waste.
2. **Front-load critical questions** — put the most important
   interrogatories first in case the limit becomes constraining.
3. **Use contention interrogatories strategically** — "State all facts
   supporting your claim that…" forces the opposing party to commit
   to a factual theory early.
4. **Match interrogatories to document requests** — pair each
   interrogatory with a corresponding request for production for
   maximum disclosure.
5. **Track the 28-day deadline** — file motion to compel promptly
   after deadline passes; delay weakens the motion.
6. **Preserve supplementation duty** — MCR 2.302(E) requires
   supplementation when a response becomes incomplete or incorrect.

## Anti-patterns

- ❌ **Never exceed the interrogatory limit** — courts routinely
  strike excess interrogatories; seek leave first.
- ❌ **Never use compound questions to evade limits** — courts apply
  the *Hinkle* discrete-subpart test strictly.
- ❌ **Never serve boilerplate objections** — "General objection"
  without specific basis is waived.
- ❌ **Never ignore the privilege log requirement** — asserting
  privilege without a log = waiver under MCR 2.302(B)(5).
- ❌ **Never respond without verification** — MCR 2.309(B)(1)
  requires answers under oath; unverified responses are deficient.

## Related Skills

- `litigation-discovery-warfare` — broader discovery strategy.
- `litigation-evidence-harvester` — document collection from
  interrogatory responses.
- `litigation-sanctions-engine` — sanctions for discovery abuse.


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
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
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
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,D | Verified |
| Emergency Custody | 55/100 | A,D | Verified |
| PPO Modification/Termination | 60/100 | A,D | Verified |
| Contempt | 70/100 | A,D | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
