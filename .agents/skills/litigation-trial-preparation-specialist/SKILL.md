---
name: litigation-trial-preparation-specialist
description: >
  Michigan trial preparation specialist covering MCR 2.507 (pretrial
  conferences), MCR 2.509 (trial procedure), MRE 103 (offers of
  proof), witness preparation, exhibit organization, jury instructions,
  motions in limine, and trial notebook assembly.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - trial preparation
    - trial prep
    - MCR 2.507
    - MCR 2.509
    - MRE 103
    - pretrial conference
    - witness preparation
    - exhibit list
    - jury instructions
    - motion in limine
    - trial notebook
    - opening statement
    - closing argument
    - voir dire
    - trial brief
    - bench trial
    - witness list
---

# Trial Preparation Specialist

## Description

Expert system for Michigan trial preparation in Pigors v. Watson
(Lane A — 2024-001507-DC, 14th Circuit Court, Hon. Jenny L. McNeill).
Covers the full trial-preparation lifecycle from pretrial conference
through verdict.

Key capabilities:
- **Pretrial conference compliance** — MCR 2.507 requirements:
  witness lists, exhibit lists, stipulations, motions in limine,
  jury instructions, and trial brief.
- **Witness preparation** — direct examination outlines, anticipated
  cross-examination areas, redirect preparation, and impeachment
  defense for each witness.
- **Exhibit organization** — pre-marked exhibit list with foundation
  requirements, authentication plans (MRE 901/902), and chain-of-
  custody documentation.
- **Motions in limine** — identifies excludable evidence, drafts
  motions with MRE authority, and prepares responses to opposing
  motions.
- **Jury instruction preparation** — Michigan Standard Jury
  Instructions (M Civ JI) selection, proposed special instructions,
  and objections to opposing instructions.
- **Trial notebook assembly** — organized binder with tabs for each
  trial phase: voir dire → opening → case-in-chief → cross →
  rebuttal → closing → jury instructions → verdict.
- **Offer of proof** — MRE 103(a)(2) procedures for excluded
  evidence to preserve appellate issues.

## Triggers

Use this skill when the user mentions:
- "trial preparation", "trial prep", "getting ready for trial"
- "MCR 2.507", "pretrial conference", "pretrial order"
- "MCR 2.509", "trial procedure", "bench trial"
- "MRE 103", "offer of proof", "preserve error"
- "witness preparation", "witness list", "witness outline"
- "exhibit list", "exhibit organization", "pre-mark exhibits"
- "jury instructions", "M Civ JI", "standard instructions"
- "motion in limine", "exclude evidence"
- "trial notebook", "trial binder"
- "opening statement", "closing argument"
- "voir dire", "jury selection"
- "trial brief", "proposed findings"

## Michigan Rules

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 2.507(A) | Pretrial conference — matters considered |
| MCR 2.507(D) | Pretrial order — binding effect |
| MCR 2.507(G) | Sanctions for pretrial violations |
| MCR 2.509(A) | Right to jury trial — demand timing |
| MCR 2.509(B) | Jury size and verdict requirements |
| MCR 2.511 | Jury selection (voir dire) |
| MCR 2.512 | Conduct of jury trial |
| MCR 2.513 | Jury instructions |
| MCR 2.514 | Verdict — general and special |
| MCR 2.517 | Findings of fact (bench trial) |

### Michigan Rules of Evidence
| Rule | Subject |
|------|---------|
| MRE 103(a)(1) | Objection — timely, specific ground |
| MRE 103(a)(2) | Offer of proof — substance of evidence |
| MRE 103(d) | Plain error — affecting substantial rights |
| MRE 401 | Relevant evidence — definition |
| MRE 403 | Exclusion — prejudice, confusion, waste |
| MRE 611 | Mode and order of examining witnesses |
| MRE 613 | Prior inconsistent statements |
| MRE 801–807 | Hearsay and exceptions |
| MRE 901 | Authentication — requirement and examples |
| MRE 902 | Self-authentication |

### Key Deadlines
| Item | Deadline | Rule |
|------|----------|------|
| Witness list | Per pretrial order | MCR 2.507(A) |
| Exhibit list | Per pretrial order | MCR 2.507(A) |
| Jury demand | See MCR 2.509(A) | 28 days after case filed |
| Jury instructions | Before closing | MCR 2.513 |
| Motions in limine | Before trial | Local practice |

## Patterns

1. **Build from the elements outward** — for each claim/defense,
   list the legal elements, then map witnesses and exhibits to each.
2. **Pre-mark ALL exhibits** — agree with opposing counsel on
   exhibit numbers; contested exhibits get the next number.
3. **Prepare impeachment packets** — for each opposing witness,
   compile prior inconsistent statements (deposition vs.
   interrogatory vs. affidavit).
4. **Draft offers of proof in advance** — anticipate which evidence
   may be excluded and prepare MRE 103(a)(2) proffers.
5. **Use a trial notebook** — tabs: (1) Pretrial order, (2) Witness
   outlines, (3) Exhibit list/copies, (4) Motions in limine,
   (5) Jury instructions, (6) Opening/Closing notes, (7) Law.
6. **Prepare proposed findings for bench trial** — MCR 2.517
   requires findings of fact; submit proposed findings to guide
   the court.

## Anti-patterns

- ❌ **Never go to trial without a pretrial order** — MCR 2.507(D)
  makes the pretrial order binding; undisclosed witnesses/exhibits
  may be excluded.
- ❌ **Never skip the offer of proof** — without it, excluded
  evidence errors are unpreserved for appeal (MRE 103).
- ❌ **Never use exhibits without foundation** — each exhibit needs
  a witness who can authenticate it under MRE 901 or 902.
- ❌ **Never wing jury instructions** — submit proposed instructions
  early; objecting after the charge is given is often too late.
- ❌ **Never ignore opposing motions in limine** — failure to respond
  may result in the motion being granted by default.
- ❌ **Never prepare witnesses to memorize scripts** — prepare them
  to tell the truth clearly; scripted testimony sounds rehearsed.

## Related Skills

- `litigation-evidence-harvester` — gathers trial exhibits.
- `litigation-impeachment-engine` — prepares impeachment material.
- `litigation-brief-writer` — writes trial briefs.
- `litigation-record-builder` — post-trial record preservation.
- `litigation-appellate-record-specialist` — preserving error for
  appeal begins at trial (MRE 103).


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
