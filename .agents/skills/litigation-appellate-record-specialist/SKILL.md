---
name: litigation-appellate-record-specialist
description: >
  Michigan appellate record construction specialist covering MCR 7.210
  (Record on Appeal), MCR 7.212(C) (appendix requirements), and MCR
  7.204(D) (transcript ordering). Builds register of actions, manages
  transcripts, compiles exhibits with Bates numbering, paginates
  volumes, and certifies record completeness for COA/MSC filings.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - appellate record
    - record on appeal
    - MCR 7.210
    - MCR 7.212
    - MCR 7.204
    - register of actions
    - transcript order
    - Bates numbering
    - exhibit compilation
    - record pagination
    - record certification
    - COA filing
    - Court of Appeals record
    - lower court record
    - claim of appeal
---

# Appellate Record Specialist

## Description

Expert system for constructing Michigan Court of Appeals records in
Pigors v. Watson — Lane F (COA 366810). Manages the full lifecycle:
claim of appeal → transcript ordering → exhibit compilation → Bates
numbering → pagination → completeness certification → filing.

Key capabilities:
- **Register of Actions** — builds chronological docket from lower-court
  entries, verifies completeness against expected filings, flags gaps.
- **Transcript Management** — enforces 7-day ordering deadline
  (MCR 7.210(B)(1)), tracks reporter assignments, calculates costs
  ($3.50/page first copy, $1.75/page additional).
- **Exhibit Compilation** — assigns Bates numbers (PIGORS-NNNN format),
  builds exhibit index with party/type/description, preserves
  originals in append-only storage.
- **Record Pagination** — consecutive page numbering across all
  volumes, creates new volumes at 200-page boundary, generates
  volume-level table of contents.
- **Completeness Certification** — verifies all register entries
  are included, identifies pagination gaps, generates MCR 7.210(H)
  certification language.

## Triggers

Use this skill when the user mentions:
- "appellate record", "record on appeal"
- "MCR 7.210", "MCR 7.212(C)", "MCR 7.204(D)"
- "register of actions", "lower court register"
- "transcript ordering", "court reporter", "transcript deadline"
- "Bates numbering", "PIGORS-NNNN", "exhibit numbering"
- "exhibit compilation", "exhibit index"
- "record pagination", "volume creation"
- "record certification", "record completeness"
- "COA 366810", "Court of Appeals filing"
- "claim of appeal", "cross-appeal"
- "appendix requirements", "required documents"

## Michigan Rules

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 7.204(A) | Claim of appeal — 21-day deadline from judgment |
| MCR 7.204(D) | Transcript ordering obligations |
| MCR 7.210(A) | Composition of the record on appeal |
| MCR 7.210(B)(1) | 7-day transcript ordering deadline after claim |
| MCR 7.210(B)(3) | Transcript filing deadline (56 days or extension) |
| MCR 7.210(H) | Record certification and settlement |
| MCR 7.212(C) | Appendix content requirements |
| MCR 7.215 | Effect of failure to file timely record |

### Key Deadlines
| Deadline | Rule | Days |
|----------|------|------|
| Claim of Appeal | MCR 7.204(A) | 21 days from judgment |
| Transcript Order | MCR 7.210(B)(1) | 7 days from claim |
| Transcript Filing | MCR 7.210(B)(3) | 56 days (or extension) |
| Brief Filing | MCR 7.212(A) | 56 days after record |

## Patterns

1. **Build register first** — the register of actions is the backbone;
   every other component references it.
2. **Order transcripts within 7 days** — MCR 7.210(B)(1) is
   jurisdictional; missing it requires a motion for extension.
3. **Bates-number ALL exhibits** — use PIGORS-NNNN format for
   consistency; never skip or reuse numbers.
4. **Paginate consecutively** — page numbers continue across
   volumes; each volume starts where the previous left off.
5. **Certify before filing** — the completeness checker must
   report zero gaps before the record is submitted.
6. **200 pages per volume** — exceeding this creates handling
   problems at the COA clerk's office.

## Anti-patterns

- ❌ **Never file without transcript ordering proof** — MCR 7.210(B)(1)
  requires proof of ordering within 7 days.
- ❌ **Never skip pagination** — gaps in page numbers trigger COA
  rejection and require correction motions.
- ❌ **Never reuse Bates numbers** — each exhibit gets a unique
  sequential identifier, even if withdrawn.
- ❌ **Never submit without register verification** — compare
  filed documents against the register of actions to catch omissions.
- ❌ **Never omit required appendix items** — MCR 7.212(C) lists
  mandatory documents (opinion, judgment, register, etc.).

## Related Skills

- `litigation-filing-architect` — coordinates the actual filing
  with the Court of Appeals.
- `litigation-record-builder` — lower-level record assembly.
- `litigation-brief-writer` — brief preparation references the
  record by page number.
- `litigation-supreme-court-architect` — MSC applications require
  the same record structure.


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
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-8 Authority Matching → Ω-9 Gap Analysis → Ω-13 Document Generation
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Appeal Brief | 70/100 | F | Verified |
| Leave Application (MSC) | 80/100 | F | Verified |

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
