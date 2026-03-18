---
name: litigation-case-evaluation-specialist
description: >-
  Michigan MCR 2.403 case evaluation process. Panelist selection, summary
  preparation, hearing strategy, acceptance/rejection analysis, cost
  sanctions under MCR 2.403(O), and mediation coordination.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - case evaluation
    - MCR 2.403
    - case evaluation summary
    - panelist selection
    - acceptance rejection
    - cost sanctions
    - case evaluation award
    - mediation alternative
    - ADR
    - settlement evaluation
---

# Case Evaluation Specialist

Michigan MCR 2.403 case evaluation — from request through acceptance/rejection
analysis and post-evaluation sanctions.

## Triggers

Use this skill when the conversation involves:

- Requesting or responding to a case evaluation under MCR 2.403
- Preparing the case evaluation summary (3-page limit)
- Selecting or objecting to panelists
- Analyzing whether to accept or reject the panel's award
- Calculating MCR 2.403(O) cost sanctions for rejection
- Comparing case evaluation with mediation (MCR 2.411)
- Coordinating case evaluation timing with discovery deadlines

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCR 2.403 | Case evaluation (complete rule) |
| MCR 2.403(A) | Scope — all civil cases unless exempted |
| MCR 2.403(D) | Selection of panelists (3 evaluators) |
| MCR 2.403(H) | Case evaluation summary — 3 pages max |
| MCR 2.403(J) | Hearing procedure — 1 hour per side |
| MCR 2.403(K) | Panel award — unanimous or majority |
| MCR 2.403(L) | Acceptance / rejection — 28 days |
| MCR 2.403(O) | Sanctions for rejection — costs & fees |
| MCR 2.411 | Mediation as alternative ADR |
| *Haliw v City of Sterling Heights*, 471 Mich 700 (2005) | Sanctions calculation |

## Patterns

- **Front-load discovery**: Complete key depositions and document production
  BEFORE case evaluation.  The panel relies on the summary and 1-hour
  presentation; incomplete facts yield low awards.
- **3-page summary is everything**: MCR 2.403(H) limits the summary to
  3 pages.  Every word matters.  Lead with damages, then liability, then
  a one-paragraph legal standard.
- **Panelist selection**: Each side strikes one name from a panel of 6;
  the remaining 3 serve.  Research panelists' verdicts and practice areas.
- **The 28-day clock**: After the award is served, each party has 28 days
  to accept or reject (MCR 2.403(L)).  Calendar this immediately.
- **Rejection math**: If you reject and the verdict is less favorable than
  the award, you pay the opponent's actual costs from the date of rejection
  (MCR 2.403(O)).  Model three scenarios (accept/reject-win/reject-lose)
  BEFORE deciding.
- **Settlement leverage**: An accepted award becomes a binding settlement.
  Use it as a negotiating anchor even if both sides reject.

## Anti-patterns

- **Don't submit a weak summary.** The panel has no independent knowledge;
  a vague summary produces a vague (usually low) award.
- **Don't ignore rejection sanctions.** MCR 2.403(O) sanctions can dwarf
  the underlying dispute.  Always quantify worst-case exposure.
- **Don't conflate mediation and case evaluation.** Mediation (MCR 2.411)
  is facilitated negotiation; case evaluation is an advisory verdict.
- **Don't skip panelist research.** Panelist practice area and judicial
  temperament influence the award significantly.

## Related Skills

- `litigation-summary-judgment-specialist` — Dispositive motions before eval
- `litigation-venue-transfer-specialist` — Venue issues affecting case eval
- `litigation-mandatory-disclosure-specialist` — Discovery timing


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
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
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
| PPO Modification/Termination | 60/100 | D,E | Verified |
| Judicial Disqualification | 75/100 | D,E | Verified |
| JTC Formal Complaint | 75/100 | D,E | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
