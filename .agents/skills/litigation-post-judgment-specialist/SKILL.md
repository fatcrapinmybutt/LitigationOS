---
name: litigation-post-judgment-specialist
description: >-
  Post-judgment enforcement and collection in Michigan courts. Writs of
  execution, garnishment, supplementary proceedings, judgment liens,
  MCR 2.621, MCL 600.6001-6095, and domestication of foreign judgments.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - post-judgment
    - judgment enforcement
    - writ of execution
    - judgment lien
    - supplementary proceedings
    - domestication
    - MCR 2.621
    - MCL 600.6001
    - debtor exam
    - installment payment
    - judgment collection
    - renewal of judgment
---

# Post-Judgment Specialist

End-to-end post-judgment enforcement and collection workflow for Michigan courts
under MCR 2.621 and MCL 600.6001–6095.

## Triggers

Use this skill when the conversation involves:

- Enforcing a money judgment after entry
- Filing writs of execution (real or personal property)
- Scheduling supplementary proceedings / debtor exams
- Placing judgment liens on real property
- Domesticating foreign or federal judgments in Michigan
- Installment payment orders under MCR 2.621(C)
- Renewal of judgments before the 10-year expiration (MCL 600.5809)
- Coordination with garnishment for wage/bank levy

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCR 2.621 | Proceedings supplementary to judgment |
| MCR 3.101 | Garnishment after judgment |
| MCL 600.6001 | Writ of execution — personal property |
| MCL 600.6012 | Writ of execution — real property |
| MCL 600.6051 | Supplementary proceedings |
| MCL 600.6057 | Installment payments |
| MCL 600.6095 | Exemptions from levy |
| MCL 600.2801 | Judgment lien on real property |
| MCL 600.5809(3) | 10-year judgment enforcement window |
| MCL 691.1171 | Uniform Enforcement of Foreign Judgments Act |
| *Auto Club Ins v State Auto*, 258 Mich App 328 (2003) | Priority of judgment liens |

## Patterns

- **Judgment lien first**: Record the judgment with the Register of Deeds
  immediately after entry (MCL 600.2801).  This secures priority over
  subsequent creditors.
- **Discovery of assets before execution**: Use interrogatories and
  supplementary proceedings to locate assets BEFORE filing writs.
- **Writ selection**: Personal property writ (MCL 600.6001) for bank accounts
  and tangible property; real property writ (MCL 600.6012) for land.
- **Garnishment coordination**: Periodic (wage) garnishment under MCR 3.101
  is often more effective than one-time bank levies.
- **Installment as fallback**: If the debtor demonstrates inability to pay
  in full, the court may order installments (MCL 600.6057).  Propose a
  schedule that preserves the lien.
- **Domesticate early**: Foreign judgments must be filed under MCL 691.1171
  BEFORE Michigan enforcement tools become available.
- **Renewal calendar**: Judgments expire after 10 years (MCL 600.5809(3)).
  Calendar the renewal deadline at year 8.

## Anti-patterns

- **Don't levy exempt property.** MCL 600.6095 exempts homesteads (up to
  $40,475), household goods, tools of trade, and other categories.
  Levying exempt property wastes fees and invites sanctions.
- **Don't skip the hearing.** Supplementary proceedings require a hearing;
  contempt is available only after a hearing order is violated.
- **Don't ignore bankruptcy stays.** If the debtor files Chapter 7/13, all
  collection must stop immediately (11 USC § 362).
- **Don't let the judgment lapse.** 10 years passes quickly; a missed renewal
  means the judgment is unenforceable.

## Related Skills

- `litigation-garnishment-specialist` — Garnishment-specific workflow
- `litigation-asset-discovery-engine` — Pre-judgment asset tracing
- `litigation-contempt-specialist` — Contempt for non-compliance with orders


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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'relevant_keyword';
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
| Custody Modification | 65/100 | All | Verified |
| Emergency Custody | 55/100 | All | Verified |
| PPO Modification/Termination | 60/100 | All | Verified |
| Summary Disposition (C10) | 75/100 | All | Verified |
| Summary Disposition (C8) | 70/100 | All | Verified |
| Contempt | 70/100 | All | Verified |
| Judicial Disqualification | 75/100 | All | Verified |
| Appeal Brief | 70/100 | All | Verified |
| Leave Application (MSC) | 80/100 | All | Verified |
| Default Judgment | 60/100 | All | Verified |
| Fee Petition | 65/100 | All | Verified |
| Motion to Compel | 55/100 | All | Verified |
| TRO Application | 60/100 | All | Verified |
| Federal §1983 Complaint | 70/100 | All | Verified |
| JTC Formal Complaint | 75/100 | All | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
