---
name: litigation-garnishment-specialist
description: >
  Michigan garnishment law specialist covering wage, bank, and periodic
  garnishment under MCL 600.4001–4065 and MCR 3.101. Calculates federal
  (15 USC § 1673) and state exemptions, generates SCAO forms (MC 14–MC 52),
  tracks payment compliance, and handles objections / dissolution motions.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0"
  triggers:
    - garnishment
    - wage garnishment
    - bank levy
    - garnishee
    - MCL 600.4011
    - MCL 600.4012
    - MCR 3.101
    - MC 14
    - MC 15
    - MC 16
    - MC 50
    - exempt income
    - protected assets
    - continuing writ
    - periodic garnishment
    - non-periodic garnishment
---

# Garnishment Specialist

## Description

Expert system for Michigan garnishment proceedings in Pigors v. Watson
and related Shady Oaks housing claims (Lane B — 2025-002760-CZ).
Handles the full lifecycle: request → exemption analysis → form generation
→ payment tracking → objection handling → dissolution.

Key capabilities:
- **Dual exemption analysis** — compares federal limit (15 USC § 1673:
  lesser of 25 % disposable or amount above 30× federal minimum wage)
  against Michigan limit (MCL 600.4012: 60 % of disposable, 50 % for
  head-of-household) and applies the MORE restrictive.
- **SCAO form generation** — MC 14 (Request & Writ), MC 15 (Employer
  Instructions), MC 16 (Objection), MC 50 (Disclosure).
- **Payment compliance tracking** — cumulative principal + interest
  calculations, automatic balance updates.
- **Protected-asset identification** — Social Security (42 USC § 407),
  VA benefits (38 USC § 5301), ERISA pensions (29 USC § 1056(d)),
  unemployment compensation (MCL 421.30), workers' comp (MCL 418.821).

## Triggers

Use this skill when the user mentions:
- "garnishment", "garnish", "garnishee", "writ of garnishment"
- "wage withholding", "bank levy", "account seizure"
- "exemption analysis", "protected income", "exempt assets"
- "MC 14", "MC 15", "MC 16", "MC 50", "MC 52"
- "MCL 600.4001", "MCL 600.4011", "MCL 600.4012"
- "MCR 3.101"
- "continuing writ", "periodic garnishment"
- "objection to garnishment", "dissolution of garnishment"
- "disposable earnings", "minimum wage test"

## Michigan Rules & Statutes

### Court Rules
| Rule | Subject |
|------|---------|
| MCR 3.101 | Garnishment procedure (all types) |
| MCR 3.101(D) | Garnishee disclosure requirements |
| MCR 3.101(G) | Dissolution of continuing garnishment |
| MCR 3.101(H) | Objection procedure and hearing |

### Statutes
| Statute | Subject |
|---------|---------|
| MCL 600.4001–4065 | Michigan Garnishment Act |
| MCL 600.4011 | Types of garnishment (periodic / non-periodic) |
| MCL 600.4012 | Wage exemption limits (60 %, 50 % head-of-household) |
| MCL 600.4061 | Bank garnishment procedure |
| MCL 421.30 | Unemployment compensation exemption |
| MCL 418.821 | Workers' compensation exemption |

### Federal Limits
| Authority | Subject |
|-----------|---------|
| 15 USC § 1673 | CCPA maximum garnishment (25 % / 30× min wage) |
| 42 USC § 407 | Social Security protected |
| 38 USC § 5301 | VA benefits protected |
| 29 USC § 1056(d) | ERISA pension protected |
| 50 USC § 3931 | SCRA military protection |

## Patterns

1. **Always apply the dual test** — compute federal max, compute state
   max, take the LESSER amount as the garnishable limit.
2. **Identify pay period** before calculating — weekly, biweekly,
   semi-monthly, monthly affect the 30× minimum wage floor.
3. **Check protected sources first** — if 100 % of income is Social
   Security / VA / pension / unemployment, garnishment is zero.
4. **Track cumulative payments** — every payment reduces remaining
   balance; interest accrues only on unpaid principal.
5. **Generate SCAO forms with SHA-256 content hash** for
   deduplication and audit trail.

## Anti-patterns

- ❌ **Never garnish fully exempt income** — Social Security,
  VA benefits, SSI, workers' comp are 100 % protected.
- ❌ **Never exceed the lesser of federal/state limits** — if the
  federal cap is lower, it controls (and vice-versa).
- ❌ **Never issue a writ without verifying service** — MCR 3.101
  requires proof of service on both debtor and garnishee.
- ❌ **Never ignore head-of-household status** — Michigan reduces
  the garnishable percentage from 40 % to 50 % (MCL 600.4012).
- ❌ **Never skip the military status check** — 50 USC § 3931
  requires verification before any garnishment.

## Related Skills

- `litigation-default-judgment-engine` — default judgment often
  precedes garnishment enforcement.
- `litigation-service-engine` — proper service is a prerequisite
  for valid garnishment.
- `litigation-harm-quantifier` — damages quantification feeds
  the garnishment amount.


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
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |

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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
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
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |

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
| Summary Disposition (C10) | 75/100 | B | Verified |
| Summary Disposition (C8) | 70/100 | B | Verified |
| Default Judgment | 60/100 | B | Verified |
| TRO Application | 60/100 | B | Verified |

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

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
