---
name: litigation-mandatory-disclosure-specialist
description: >-
  Michigan mandatory initial disclosures under MCR 2.302(A). Witness lists,
  document identification, damage computation, and insurance disclosure.
  Ensures compliance and leverages opponent non-compliance for sanctions.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - mandatory disclosure
    - initial disclosure
    - MCR 2.302(A)
    - witness list
    - document disclosure
    - damage computation
    - insurance disclosure
    - disclosure obligations
    - Rule 26 equivalent
---

# Mandatory Disclosure Specialist

Michigan mandatory initial disclosure compliance and strategy under
MCR 2.302(A), effective January 1, 2020.

## Triggers

Use this skill when the conversation involves:

- Preparing or reviewing initial mandatory disclosures
- Identifying disclosure obligations for witnesses, documents, damages,
  or insurance
- Challenging opponent's failure to disclose (MCR 2.313 sanctions)
- Supplementing prior disclosures as new information emerges
- Coordinating disclosures with broader discovery plan
- Comparing Michigan disclosure requirements with Federal Rule 26(a)

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCR 2.302(A) | Mandatory initial disclosures |
| MCR 2.302(E) | Supplementation obligation |
| MCR 2.301 | Discovery scope and limits |
| MCR 2.313 | Sanctions for disclosure failures |
| MCR 2.401(B) | Scheduling order interaction |
| MCR 2.302(B)(4) | Expert witness disclosure |
| *Duray Dev LLC v Perrin*, 288 Mich App 143 (2010) | Discovery scope standard |
| *Dean v Tucker*, 182 Mich App 27 (1989) | Duty to supplement |

## Required Disclosures (MCR 2.302(A))

1. **Witnesses**: Name, address, phone of each individual likely to have
   discoverable information, along with the subjects of the information.
2. **Documents / ESI**: Copy or description of all documents, ESI, and
   tangible things in the party's possession, custody, or control that may
   be used to support claims or defenses.
3. **Damage computation**: Computation of each category of damages,
   including documents on which the computation is based.
4. **Insurance**: Any insurance agreement that may satisfy part or all of
   a judgment.

## Patterns

- **Serve within 14 days of the scheduling conference** or as ordered.
  Michigan's timeline is shorter than Federal Rule 26(a)(1)(C).
- **Over-disclose strategically**: Disclosing more than the minimum builds
  credibility and forecloses exclusion motions.
- **Use a disclosure matrix**: Rows = disclosure categories; columns =
  items disclosed, status, date served.  This ensures nothing is missed.
- **Supplement continuously**: MCR 2.302(E) requires supplementation "in a
  timely manner."  Calendar quarterly reviews at minimum.
- **Leverage non-compliance**: If the opponent fails to disclose a witness
  or document, move for exclusion under MCR 2.313(B)(2)(b) BEFORE trial.

## Anti-patterns

- **Don't treat disclosures as optional.** Michigan judges enforce MCR 2.302(A)
  strictly; failure to disclose can result in witness/exhibit exclusion.
- **Don't disclose work product.** MCR 2.302(A) does not require disclosure
  of attorney mental impressions, conclusions, or legal theories.
- **Don't wait for a motion.** Supplement as soon as new information is
  known — waiting until compelled looks like bad faith.
- **Don't confuse disclosures with discovery responses.** Disclosures are
  self-executing; interrogatories / requests for production are separate.

## Related Skills

- `litigation-interrogatory-engine` — Written interrogatories beyond disclosures
- `litigation-case-evaluation-specialist` — MCR 2.403 case evaluation timing
- `litigation-asset-discovery-engine` — Financial discovery


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
