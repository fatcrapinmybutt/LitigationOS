---
name: litigation-voir-dire-specialist
description: >-
  Jury selection strategy for Michigan civil trials. Voir dire questioning,
  challenges for cause, peremptory strikes, MCR 2.510 & 2.511 compliance,
  juror profiling, and bias detection.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - voir dire
    - jury selection
    - peremptory challenge
    - challenge for cause
    - MCR 2.510
    - MCR 2.511
    - juror questionnaire
    - jury panel
    - strike list
    - bias detection
    - Batson challenge
---

# Voir Dire Specialist

Comprehensive jury selection strategy and execution for Michigan civil trials
under MCR 2.510–2.511.

## Triggers

Use this skill when the conversation involves:

- Planning voir dire questions for a Michigan civil jury trial
- Evaluating juror responses for bias indicators
- Preparing challenges for cause or peremptory strikes
- Drafting supplemental juror questionnaires
- Analyzing jury panel composition
- Batson / *Powers v Ohio* challenges to discriminatory strikes
- Jury instructions coordination with selection strategy

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCR 2.510 | Jury selection procedure |
| MCR 2.511 | Challenges for cause & peremptory |
| MCR 2.511(D) | Number of peremptory challenges |
| MCR 2.511(B) | Grounds for challenge for cause |
| MCR 2.512 | Jury instructions |
| MCL 600.1300 | Qualification of jurors |
| MCL 600.1310 | Juror exemptions |
| MCL 600.1354 | Supplemental juror questionnaires |
| *Batson v Kentucky*, 476 US 79 (1986) | Equal protection in jury strikes |
| *People v Bell*, 473 Mich 275 (2005) | Michigan Batson framework |

## Patterns

- **Theme-first**: Design voir dire around 2-3 case themes, not a checklist.
  Every question should test whether a juror can be fair on a specific theme.
- **Open-ended questions first**: "Tell me about your experience with…" elicits
  more than "Have you ever…" yes/no questions.
- **Group disclosure technique**: Ask the panel "How many of you have had
  experience with [topic]?" — then follow up individually.
- **Challenge for cause BEFORE peremptory**: Preserve peremptory strikes by
  exhausting cause challenges first (MCR 2.511(B) lists 8 grounds).
- **Track strikes on a grid**: Columns = juror seat, rows = attributes.  Mark
  each juror's leanings in real time so strike decisions are data-driven.
- **Rehabilitation awareness**: Opposing counsel will try to rehabilitate
  challenged jurors.  Anticipate the "can you set that aside" question.
- **Batson readiness**: If opposing counsel strikes jurors of a protected class,
  be prepared to make a prima facie showing under *Batson*/*Bell*.

## Anti-patterns

- **Don't lecture jurors.** Voir dire is listening, not teaching.  Save
  arguments for opening and closing.
- **Don't ignore body language.** A juror's words may say "fair" while posture
  and eye contact say otherwise.  Note nonverbal cues.
- **Don't waste peremptory strikes.** Each side gets limited strikes under
  MCR 2.511(D).  Reserve them for jurors who survive cause challenges.
- **Don't ask questions you can't handle the answer to.** If a bad answer
  contaminates the panel, it cannot be unheard.

## Related Skills

- `litigation-summary-judgment-specialist` — Pre-trial dispositive motions
- `litigation-case-evaluation-specialist` — MCR 2.403 case evaluation


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
