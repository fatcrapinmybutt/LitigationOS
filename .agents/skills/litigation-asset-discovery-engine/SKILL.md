---
name: litigation-asset-discovery-engine
description: >-
  Discover, trace, and document hidden assets in Michigan family law and civil
  litigation. Forensic accounting, bank subpoenas, real property searches,
  business valuation, and dissipation claims under MCL 552.401.
metadata:
  category: litigation
  author: LitigationOS
  version: "1.0.0"
  triggers:
    - asset discovery
    - hidden assets
    - forensic accounting
    - dissipation
    - bank subpoena
    - property search
    - MCL 552.401
    - real property
    - business valuation
    - financial disclosure
    - asset tracing
    - marital estate
---

# Asset Discovery Engine

Comprehensive asset discovery and tracing for Michigan family law and civil
litigation.  Covers real property, personal property, financial accounts,
business interests, retirement/pension assets, and dissipation claims.

## Triggers

Use this skill when the conversation involves:

- Identifying or tracing hidden, undisclosed, or dissipated assets
- Drafting financial interrogatories or requests for production targeting assets
- Preparing bank / brokerage subpoenas under MCR 2.305
- Real property searches via Michigan Register of Deeds
- Business valuation or fractional-interest analysis
- Dissipation claims under MCL 552.401 (equitable distribution)
- Forensic accounting workflow (tracing funds, lifestyle analysis)

## Michigan Rules & Statutes

| Authority | Subject |
|-----------|---------|
| MCL 552.401 | Equitable division of marital property |
| MCL 552.18 | Assignment of property in divorce |
| MCR 2.302(B) | Scope of discovery — financial relevance |
| MCR 2.305 | Subpoena for production of documents |
| MCR 2.310 | Request for production |
| MCR 2.313 | Failure to provide discovery — sanctions |
| MCL 565.29 | Recording of real estate instruments |
| *Sparks v Sparks*, 440 Mich 141 (1992) | Equitable distribution factors |
| *Berger v Berger*, 277 Mich App 700 (2008) | Dissipation doctrine |

## Patterns

- **Start with disclosures**: Interrogatories + document requests before
  third-party subpoenas; the Friend of the Court Verified Financial Information
  form (FOC 25) is the first checkpoint.
- **Layer sources**: Tax returns → bank statements → Register of Deeds →
  Secretary of State (UCC filings) → employer records.
- **Trace, don't guess**: Follow the money backward through accounts.
  Document each transfer with date, amount, source, and destination.
- **Timestamp dissipation**: MCL 552.401 requires proof that the asset existed
  during the marriage AND was diminished through unilateral action.
- **Use Sparks factors**: All 12 factors from *Sparks v Sparks* frame the
  equitable-distribution analysis; asset discovery feeds factors 2–5 directly.
- **Subpoena banks early**: MCR 2.305 subpoenas to financial institutions
  take 21 days to comply; factor lead time into the discovery schedule.

## Anti-patterns

- **Never assume hidden = fraud.** Many omissions are negligent, not
  intentional.  Frame discovery neutrally.
- **Don't subpoena without interrogatories first.** Courts disfavor blanket
  third-party subpoenas when the party hasn't been asked first.
- **Don't confuse separate and marital property.** Assets acquired before
  marriage or by gift/inheritance may be separate property under MCL 552.401.
- **Never ignore retirement assets.** QDROs and pension valuations require
  specialized expert analysis — don't attempt in-house.

## Related Skills

- `litigation-garnishment-specialist` — Post-judgment asset enforcement
- `litigation-post-judgment-specialist` — Post-judgment collection workflow
- `litigation-mandatory-disclosure-specialist` — Initial disclosure obligations
- `litigation-interrogatory-engine` — Written interrogatories for discovery


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
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
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
