---
name: litigation-venue-transfer-specialist
description: >-
  Venue challenges and transfers in Michigan courts. MCL 600.1601-1655 venue
  statutes, MCR 2.222 change of venue, MCR 2.223 forum non conveniens,
  and transfer between Michigan circuit courts.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - venue transfer
    - change of venue
    - forum non conveniens
    - MCR 2.222
    - MCR 2.223
    - MCL 600.1601
    - improper venue
    - convenience of parties
    - venue challenge
    - transfer of action
---

# Venue Transfer Specialist

Venue selection, challenge, and transfer strategy for Michigan civil litigation
under MCL 600.1601–1655 and MCR 2.222–2.223.

## Triggers

Use this skill when the conversation involves:

- Challenging venue as improper under MCL 600.1621–1651
- Filing a motion for change of venue under MCR 2.222
- Arguing forum non conveniens under MCR 2.223
- Selecting the optimal venue at case inception
- Transferring an action between Michigan circuit courts
- Resisting a transfer motion filed by opposing counsel
- Analyzing venue in multi-defendant or multi-claim actions

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCL 600.1601 | General venue provisions |
| MCL 600.1605 | Venue in actions against residents |
| MCL 600.1611 | Venue in actions against nonresidents |
| MCL 600.1615 | Transitory actions — where cause arose |
| MCL 600.1621 | Venue in property actions |
| MCL 600.1629 | Venue in tort actions |
| MCL 600.1641 | Venue in contract actions |
| MCL 600.1651 | Venue in actions against corporations |
| MCL 600.1655 | Change of venue — grounds |
| MCR 2.222 | Change of venue |
| MCR 2.223 | Transfer based on forum non conveniens |
| *Diem v Sallie Mae*, 307 Mich App 204 (2014) | Forum non conveniens standard |
| *Brazeau v Hiller*, 126 Mich App 559 (1983) | Convenience-of-witnesses factor |

## Patterns

- **Raise early or waive**: Venue objections must be raised in the first
  responsive pleading or by motion before or at the time of that pleading
  (MCR 2.222(A)).  Late challenges are waived.
- **Prove inconvenience, not just preference**: MCR 2.223 requires a showing
  that the current venue is "seriously inconvenient" and that a more
  convenient forum exists.  Conclusory statements fail.
- **Witness-centered analysis**: Courts weigh the convenience of non-party
  witnesses most heavily (*Brazeau*).  List each non-party witness, their
  location, and the hardship of travel.
- **Statutory venue is mandatory, not discretionary**: If the action fits a
  specific venue statute (e.g., MCL 600.1621 for property), that statute
  controls regardless of convenience.
- **Multi-defendant venue**: When defendants reside in different counties,
  MCL 600.1605 allows venue in any county where at least one defendant
  resides.  Choose the county most favorable to the plaintiff.
- **Transfer vs. dismissal**: MCR 2.222 transfers the action (preserves
  filing date).  Forum non conveniens under MCR 2.223 may result in
  dismissal if the convenient forum is out-of-state.

## Anti-patterns

- **Don't confuse jurisdiction and venue.** Jurisdiction is the court's
  power to decide; venue is the geographic location.  A court can have
  jurisdiction but be the wrong venue, and vice versa.
- **Don't delay venue motions.** Filing after the answer deadline waives
  the objection absent exceptional circumstances.
- **Don't move for transfer without an affidavit.** Courts require sworn
  declarations from witnesses explaining the hardship, not attorney argument.
- **Don't ignore the statute.** If a statute sets mandatory venue (e.g.,
  real property actions in the county where the property sits), forum non
  conveniens is inapplicable.

## Related Skills

- `litigation-summary-judgment-specialist` — Dispositive motions in new venue
- `litigation-case-evaluation-specialist` — Case evaluation in transfer court
- `litigation-mandatory-disclosure-specialist` — Disclosure obligations after transfer


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
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |

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
| PPO Modification/Termination | 60/100 | D | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
