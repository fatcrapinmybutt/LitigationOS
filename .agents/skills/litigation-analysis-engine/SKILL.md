---
name: litigation-analysis-engine
description: "Full litigation intelligence pipeline: scan drives → analyze documents line-by-line → extract evidence/citations/claims → build per-case databases → produce judicial-grade court documents. Michigan-specific. Use when: analyze legal docs, build case database, generate court documents, extract evidence, score claims."
---

# Litigation Analysis Engine

**Role**: Judicial-Grade Legal Intelligence System for Michigan Courts

Complete pipeline from raw files to filed court documents:

## Pipeline Stages (sequential, paired)

### Stage A: Drive Forensic Scanner (`deep_scanner.py`)
- SHA256 fingerprints every file across all drives
- Classifies by content type and legal relevance
- Outputs: `manifests/drive_*_manifest.db`

### Stage B: Drive Organizer Engine (`drive_organizer.py`)
- Cross-drive dedup via SHA256 join
- Maps files to correct LitigationOS 00-99 dirs
- Trash cleanup, consolidation plan
- Outputs: `manifests/consolidation_plan.db`

### Stage C: Document Analysis Engine (`analysis_engine.py`)
- Reads PDFs and TXTs line-by-line
- Extracts: citations, facts, dates, names, amounts, legal issues
- Scores evidence admissibility, relevance, weight
- Assigns to case lanes (A=custody, B=housing, C=convergence)
- Outputs: `manifests/case_analysis.db`

### Stage D: Case Database Builder (`case_database_builder.py`)
- Builds per-lane litigation databases with evidence, claims, timeline, authorities
- Auto-generates exhibit numbers
- Produces court-ready documents following MCR formatting
- Outputs: `06_CASE_DATABASES/lane_*.db`, `07_COURT_DOCUMENTS/`

## Michigan Court Knowledge
- MCR 2.003, 2.105-2.119, 2.116, 3.206-3.215, 7.203-7.215
- MCL 722.21-722.31 (Child Custody Act)
- MCL 554.139, 125.534-540 (Housing/Habitability)
- 42 USC § 1983 (Civil Rights)
- MRE 401-403, 801-807, 901-903

## Cases
- Lane A: 2024-001507-DC (Custody, Judge McNeill, 14th Circuit)
- Lane B: 2023-5907-PP (Housing, Judge Hoopes, 14th Circuit)
- Lane C: 2025-002760-CZ (Civil Rights/Convergence)

## Execution
```bash
python deep_scanner.py C 6          # Scan drive
python drive_organizer.py plan       # Plan consolidation
python analysis_engine.py all        # Analyze documents
python case_database_builder.py all  # Build DBs + generate docs
```

---

## Database Intelligence Layer

### Live DB Statistics (litigation_context.db — 1.18 GB)

| Table | Rows | Purpose |
|-------|------|---------|
| `contradiction_map` | 10,558 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready inconsistencies by witness |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `evidence_quotes` | 308,636 | Extracted evidence passages with legal significance |
| `pages` | 472,211 | Raw page text from ingested documents |
| `master_citations` | 3,600,000+ | Extracted citations across all sources |
| `claims` | Active claims matrix | Legal claims/propositions with status |
| `docket_events` | Full docket timeline | Chronological case events |
| `vehicles` | Filing vehicles | Procedural motions/briefs with readiness scores |

### Key FTS5 Search Interfaces
```sql
-- Authority search
SELECT * FROM auth_rules_fts WHERE auth_rules_fts MATCH 'custody AND modification';
-- Evidence search
SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH 'parenting time AND denied';
-- Full document search
SELECT * FROM pages_fts WHERE pages_fts MATCH 'ex parte AND communication';
-- Cross-reference search
SELECT * FROM md_sections_fts WHERE md_sections_fts MATCH 'best interest factors';
```

---

## Deep Analysis Methodology

### 1. Timeline Analysis
Build chronological event maps from docket_events, evidence_quotes, and pages tables to identify:
- **Gaps**: Periods with no documented activity (potential discovery targets)
- **Clusters**: Concentrated activity periods (stress points, escalation moments)
- **Sequences**: Cause-effect chains (filing → order → consequence)
- **Anomalies**: Out-of-sequence events (backdated orders, post-hoc justifications)

```
Timeline Construction:
  docket_events (dated)
  + evidence_quotes (dated)
  + pages (dated by document)
  → Merged chronological stream
  → Gap detection (>30 day silence periods)
  → Cluster detection (>5 events in 7 days)
  → Anomaly detection (events out of logical sequence)
```

### 2. Pattern Detection
Systematic identification of recurring behaviors across the record:

| Pattern Type | Detection Method | Output |
|-------------|-----------------|--------|
| **Judicial bias** | Compare ruling rates, timing, tone across parties | Bias score per judge per category |
| **Procedural violations** | Match docket events against MCR requirements | Violation list with authority |
| **Witness inconsistency** | Cross-reference statements by same speaker across documents | Contradiction pairs with severity |
| **Ex parte indicators** | Orders without hearings, sealed communications, timing anomalies | Ex parte probability score |
| **Obstruction patterns** | Discovery delays, missing documents, privilege abuse | Obstruction timeline |
| **Alienation indicators** | MCL 722.23(j) factor analysis — contact denial, disparagement, interference | Factor J evidence compilation |

### 3. Contradiction Mapping
Cross-reference every factual assertion against every other assertion by the same or related speaker:

```
For each statement S in evidence_quotes:
  For each other statement T where T.speaker == S.speaker AND T.topic overlaps S.topic:
    Compare S.claim vs T.claim
    If contradictory → score (materiality × clarity × provability)
    If score ≥ 15 → add to contradiction_map
    If speaker is opposing party → add to impeachment_items
```

### 4. Authority Gap Analysis
For every legal claim in the claims table, verify supporting authority exists:

```
For each claim C in claims:
  Search auth_rules for governing rule
  Search master_citations for supporting case law
  Search evidence_quotes for factual support
  Score: authority_coverage (0-100), evidence_coverage (0-100), overall_readiness (weighted)
  If overall_readiness < 60 → create gap_ticket
```

---

## OMEGA Pipeline Phase Integration

The analysis engine feeds into the OMEGA 16-phase litigation pipeline:

| Phase | Name | Analysis Engine Role |
|-------|------|---------------------|
| Ω-1 | Intake & Triage | Classify incoming documents by lane and priority |
| Ω-2 | Deep Scan | Run OCR + text extraction on all file types |
| Ω-3 | Evidence Harvest | Extract atomic evidence from processed text |
| Ω-4 | Citation Extraction | Parse all legal citations from documents |
| Ω-5 | Claim Mapping | Map evidence atoms to legal claims |
| Ω-6 | Contradiction Detection | Run full contradiction analysis |
| Ω-7 | Impeachment Assembly | Build impeachment packages from contradictions |
| Ω-8 | Authority Matching | Link claims to governing authority |
| Ω-9 | Gap Analysis | Identify missing evidence/authority |
| Ω-10 | Timeline Construction | Build master chronological event map |
| Ω-11 | Risk Assessment | Score litigation risks per lane |
| Ω-12 | Filing Readiness | Score each potential filing for completeness |
| Ω-13 | Document Generation | Produce court-ready documents |
| Ω-14 | Red Team Review | Adversarial review of generated filings |
| Ω-15 | Validation | Final compliance and citation verification |
| Ω-16 | Deployment | Package for filing with COS and exhibits |

---

## Analysis Output Formats

### 1. Structured JSON (for programmatic consumption)
```json
{
  "analysis_type": "contradiction_report",
  "lane": "A",
  "timestamp": "2025-07-14T12:00:00Z",
  "findings": [
    {
      "id": "C-00142",
      "type": "DIRECT",
      "speaker": "Watson",
      "statement_a": {"text": "...", "source": "...", "date": "..."},
      "statement_b": {"text": "...", "source": "...", "date": "..."},
      "scores": {"materiality": 9, "clarity": 8, "provability": 9},
      "composite": 26,
      "impeachment_ready": true
    }
  ],
  "summary": {"total": 142, "devastating": 12, "strong": 34, "viable": 51}
}
```

### 2. Narrative Memo (for attorney/strategist review)
```
ANALYSIS MEMORANDUM
Re: Contradiction Analysis — Watson Custody Lane (A)
Date: [date]

EXECUTIVE SUMMARY
Analysis of 308K evidence quotes across 472K pages identified 142 contradictions
by Emily A. Watson, of which 12 are classified DEVASTATING (composite ≥25).

KEY FINDINGS
1. [Finding with full citation to source documents]
2. [Finding with full citation to source documents]
...

RECOMMENDED ACTIONS
1. [Action with timeline and filing vehicle]
2. [Action with timeline and filing vehicle]
```

### 3. Court-Ready Brief Section (for direct insertion into filings)
```
III. THE RECORD DEMONSTRATES MATERIAL CONTRADICTIONS

14. On [date], Defendant testified under oath that "[quote]." (Ex. A, p. X, l. Y.)

15. However, Defendant previously stated in her sworn affidavit dated [date] that
"[contradictory quote]." (Ex. B, ¶ Z.)

16. These statements are irreconcilable. Under MRE 613(b), extrinsic evidence of a
prior inconsistent statement is admissible where the witness is given an opportunity
to explain or deny the statement. The contradiction goes directly to Defendant's
credibility on [issue].
```

---

## Cross-Lane Analysis Patterns

Evidence in one lane frequently supports arguments in another. The analysis engine tracks cross-lane connections:

| Source Lane | Target Lane | Connection Pattern |
|------------|-------------|-------------------|
| A (Custody) → | F (Appeal) | Trial court errors in custody findings become appellate issues |
| A (Custody) → | E (Judicial Misconduct) | Biased rulings in custody become JTC complaint evidence |
| B (Housing) → | A (Custody) | Unsafe housing conditions inform best-interest factor (d) (MCL 722.23(d)) |
| D (PPO) → | A (Custody) | PPO proceedings reveal Watson's pattern of false allegations (factor (j)) |
| D (PPO) → | E (Judicial Misconduct) | Improper PPO issuance shows judicial bias pattern |
| C (Convergence) → | F (Appeal) | Systemic coordination failures show due process violations |
| ALL → | F (Appeal) | 329+ days parent-child separation = cumulative constitutional harm |

### Cross-Lane Query Pattern
```sql
-- Find evidence in Lane B that supports Lane A best-interest arguments
SELECT eq.quote_text, eq.legal_significance, eq.evidence_category
FROM evidence_quotes eq
WHERE eq.evidence_category LIKE '%housing%'
  AND eq.legal_significance LIKE '%best interest%'
ORDER BY eq.relevance_score DESC LIMIT 20;

-- Find judicial violations that support both Lane E (JTC) and Lane F (Appeal)
SELECT jv.violation_description, jv.canon_number, jv.severity
FROM judicial_violations jv
WHERE jv.severity >= 7
ORDER BY jv.severity DESC;
```

---

## Integration Points

- **litigation-evidence-harvester**: Feeds raw evidence for analysis pipeline
- **litigation-impeachment-engine**: Receives contradiction data for impeachment packages
- **litigation-judicial-analyst**: Receives judicial pattern data for misconduct analysis
- **michigan-litigation-writer**: Receives analysis outputs for document generation
- **litigation-filing-architect**: Receives readiness scores for filing prioritization
- **litigation-red-team**: Receives analysis outputs for adversarial stress-testing

## Related Skills

- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Extracts evidence from document collections
- [litigation-pipeline-commander](skill://litigation-pipeline-commander) — Executes the OMEGA 16-phase pipeline
- [litigation-impeachment-engine](skill://litigation-impeachment-engine) — Builds impeachment packages from contradictions


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
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-evidence-harvester` | Integration | Provides raw evidence → feeds analysis |
| `litigation-pipeline-commander` | Integration | Complementary analysis |
| `litigation-convergence-orchestrator` | Integration | Complementary analysis |
| `litigation-claim-researcher` | Integration | Complementary analysis |

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
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

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

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

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
