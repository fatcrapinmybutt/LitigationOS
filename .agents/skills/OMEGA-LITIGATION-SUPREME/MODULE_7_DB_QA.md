# OMEGA LITIGATION SUPREME — MODULES 7-9
# Database Intelligence · Quality Assurance · Master Execution
# ═══════════════════════════════════════════════════════════════
# Part 3 of the OMEGA Litigation Skill System
# For: LitigationOS (Pigors v. Watson)
# Jurisdiction: Michigan 14th Circuit Court, Family Division
# ═══════════════════════════════════════════════════════════════


## ═══════════════════════════════════════════
## MODULE 7: DATABASE INTELLIGENCE LAYER
## ═══════════════════════════════════════════

The database is the single source of truth. Every claim, every citation, every
statistic in every generated document MUST originate from a verified DB query.
Guessing is perjury. Hallucinating is malpractice. Query first, write second.

### 7.1 Central Database: litigation_context.db

**Size:** ~12 GB | **Tables:** 790+ | **Format:** SQLite WAL mode

| Table | Records | Strategic Use |
|-------|---------|---------------|
| `evidence_quotes` | 308,704 | Extracted evidence with legal significance scores |
| `contradiction_map` | 10,672 | Detected contradictions between party statements |
| `impeachment_items` | 15,171 | Impeachment-ready inconsistencies for cross-examination |
| `judicial_violations` | 1,127 | Documented judicial conduct violations (Canon/MCR) |
| `pages` | 472,482 | Raw page text from all ingested documents |
| `master_citations` | 3,684,757 | Extracted legal citations with context |
| `claims` | 653 | Active claims matrix across all lanes |
| `vehicles` | 6 | Filing vehicles (Motion/Brief/Petition/Complaint/Appeal/JTC) |
| `authority_chains` | 28 | Authority chains linking rules → cases → evidence |
| `filing_readiness` | 24 | Per-vehicle filing readiness scores (EGCP) |
| `mega_file_harvest` | 53,625 | Complete file index across all 6 drives |
| `docket_events` | Varies | Chronological case events and court actions |
| `deadlines` | Varies | Active deadline tracking with urgency scores |
| `evidence_atoms` | Varies | Atomic evidence units extracted from documents |
| `schema_reference` | Varies | Self-documenting table/column metadata |
| `agent_log` | Varies | Agent execution history and results |

**Critical rule:** NEVER hardcode table counts — they change with every pipeline
run. Always query live: `SELECT COUNT(*) FROM <table>`.

### 7.2 FTS5 Search Interface

Full-text search tables provide sub-second queries across millions of records.
Always prefer FTS5 MATCH over LIKE '%term%' for text searches.

```sql
-- Evidence search (308K+ records, instant results)
SELECT rowid, quote_text, legal_significance, source_file
FROM evidence_quotes_fts
WHERE evidence_quotes_fts MATCH 'parenting time AND denied'
ORDER BY rank
LIMIT 50;

-- Authority/rules search
SELECT rowid, rule_text, citation, authority_type
FROM auth_rules_fts
WHERE auth_rules_fts MATCH 'custody AND modification AND best interest'
ORDER BY rank
LIMIT 25;

-- Full document page search (472K+ pages)
SELECT rowid, page_text, source_file, page_number
FROM pages_fts
WHERE pages_fts MATCH 'ex parte AND communication'
ORDER BY rank
LIMIT 30;

-- Cross-reference section search
SELECT rowid, section_text, heading, source_path
FROM md_sections_fts
WHERE md_sections_fts MATCH 'best interest factors'
ORDER BY rank
LIMIT 20;

-- Contradiction search
SELECT rowid, statement_a, statement_b, contradiction_type
FROM contradiction_map_fts
WHERE contradiction_map_fts MATCH 'custody AND schedule'
ORDER BY rank
LIMIT 15;
```

**FTS5 Query Syntax Quick Reference:**
- `AND` — both terms required: `'custody AND modification'`
- `OR` — either term: `'PPO OR protection order'`
- `NOT` — exclude term: `'custody NOT temporary'`
- `"phrase"` — exact phrase: `'"best interest"'`
- `NEAR(a b, N)` — within N tokens: `'NEAR(denied parenting, 5)'`
- `prefix*` — prefix match: `'MCL 722*'`

### 7.3 Lane-Specific Databases

Each case lane maintains its own specialized database to prevent cross-contamination.

| Lane | Database | Size | Key Tables |
|------|----------|------|-----------|
| **A** | `lane_A_custody.db` | Varies | `custody_events`, `pt_violations`, `factor_evidence`, `best_interest_scores` |
| **B** | `lane_B_housing.db` | ~630KB | `housing_violations`, `shady_oaks_evidence`, `habitability_issues` |
| **C** | `lane_C_convergence.db` | Varies | `cross_lane_links`, `entity_overlap`, `convergence_scores` |
| **D** | `lane_D_ppo.db` | Varies | `ppo_events`, `show_cause_history`, `false_allegations` |
| **E** | `lane_E_misconduct.db` | Varies | `canon_violations`, `bias_incidents`, `jtc_findings` |
| **F** | `lane_F_appellate.db` | Varies | `preserved_errors`, `appellate_issues`, `standard_of_review` |

**Cross-lane query pattern** (always go through convergence):
```sql
-- CORRECT: Query via convergence links
SELECT l.source_lane, l.target_lane, l.link_type, l.evidence_id
FROM lane_C_convergence.cross_lane_links l
WHERE l.source_lane = 'A' AND l.target_lane = 'E';

-- WRONG: Direct cross-lane join (contamination risk)
-- SELECT * FROM lane_A.custody_events JOIN lane_E.bias_incidents ...
```

### 7.4 DB-First Protocol (NON-NEGOTIABLE)

**Before inserting ANY placeholder** (`[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`,
`[VERIFY]`, `[CITE]`), execute ALL four steps in order:

```
STEP 1: Query litigation_context.db
   → Search relevant tables (evidence_quotes, claims, docket_events, etc.)
   → Use FTS5 for text searches
   → Check schema_reference for table discovery

STEP 2: Search filesystem across all 6 drives
   → fd --type f "keyword" C:\ D:\ F:\ G:\ H:\ I:\
   → rg -l "search term" --type md --type txt --type pdf
   → Check 03_EVIDENCE/, 04_FILINGS/, Vault/ directories

STEP 3: Check reference files
   → COMPLETE_FILING_DATA_SUMMARY.txt (repo root)
   → QUICK_REFERENCE_FILING_PLACEHOLDERS.txt (repo root)
   → 00_SYSTEM/STARTUP_REPORT.md (generated at session start)

STEP 4: ONLY if Steps 1-3 ALL return nothing
   → Insert placeholder with SPECIFIC instructions:
     "[ANDREW_REQUIRED: Need signed verification affidavit —
      not found in DB (checked evidence_quotes, claims) or
      filesystem (checked F:\Filings\, I:\Backups\)]"
   → NEVER use generic "[INSERT DATA HERE]"
```

**Why this matters:** Past sessions left 200+ `[ANDREW_REQUIRED]` placeholders in
filings when the data existed in `litigation_context.db` the entire time. The user
explicitly said: *"that's the whole point of this — to USE MY FILES ON MY DRIVES."*

### 7.5 SQLite Connection Rules

Every connection MUST set these PRAGMAs before any query:

```python
import sqlite3
from db_lock_manager import managed_db

# ALWAYS use managed_db() context manager
with managed_db("litigation_context.db") as conn:
    # Connection PRAGMAs (set automatically by managed_db)
    # PRAGMA busy_timeout = 60000;   -- Wait 60s on lock
    # PRAGMA journal_mode = WAL;      -- Write-Ahead Logging
    # PRAGMA cache_size = -32000;     -- 32 MB cache
    # PRAGMA temp_store = MEMORY;     -- Temp tables in RAM
    # PRAGMA synchronous = NORMAL;    -- WAL protects durability

    results = conn.execute("SELECT ...").fetchall()
```

**Hard limits:**
- Max 3 concurrent DB connections (enforced by `db_lock_manager.py` semaphore)
- Never open DB connections inside shell commands — use dedicated Python scripts
- Never use `python -c` for DB queries — write a temp `.py` file instead
- All agents share the same 3-connection pool via `managed_db()`

### 7.6 Consolidate COUNT(*) Pattern

Use a single query with subqueries instead of N separate round-trips:

```python
# CORRECT — one round-trip for all counts
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM evidence_quotes) AS eq_count,
        (SELECT COUNT(*) FROM contradiction_map) AS cm_count,
        (SELECT COUNT(*) FROM judicial_violations) AS jv_count,
        (SELECT COUNT(*) FROM claims) AS cl_count,
        (SELECT COUNT(*) FROM impeachment_items) AS ii_count,
        (SELECT COUNT(*) FROM master_citations) AS mc_count,
        (SELECT COUNT(*) FROM pages) AS pg_count,
        (SELECT COUNT(*) FROM mega_file_harvest) AS mfh_count
""").fetchone()

# WRONG — 8 separate round-trips (10-100× slower)
# eq = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
# cm = conn.execute("SELECT COUNT(*) FROM contradiction_map").fetchone()[0]
# ... (repeat for each table)
```

### 7.7 Schema Verification Before Queries

**NEVER assume column names.** The DB schema evolves faster than documentation.

```python
# ALWAYS verify schema before first query to any table
columns = conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()
col_names = [c[1] for c in columns]

# Also check schema_reference for documentation
meta = conn.execute("""
    SELECT column_name, data_type, description
    FROM schema_reference
    WHERE table_name = 'evidence_quotes'
""").fetchall()

# Known corrections (schema drifts from docs):
# authority_chains.chain_complete  (NOT is_complete)
# filing_readiness.vehicle_name    (NOT vehicle)
# deadlines.due_date_iso           (NOT deadline_date)
# claims.claim_id                  (NOT id)
```

### 7.8 Adaptive Query Rewriter

Route queries through the rewriter for automatic optimization:

```python
from adaptive_query_rewriter import rewrite

# Automatically converts LIKE → FTS5, adds LIMIT safety, caches COUNTs
original = "SELECT * FROM evidence_quotes WHERE quote_text LIKE '%denied%'"
optimized = rewrite(original)
# → "SELECT rowid, quote_text, ... FROM evidence_quotes_fts
#    WHERE evidence_quotes_fts MATCH 'denied' LIMIT 1000"
```


## ═══════════════════════════════════════════
## MODULE 8: QUALITY ASSURANCE & ANTI-HALLUCINATION
## ═══════════════════════════════════════════

Quality assurance is not optional. Every document generated by this system may
end up in a sworn filing before a judge. A single hallucinated fact, fabricated
citation, or inflated statistic could constitute perjury, destroy credibility,
and result in sanctions under MCR 2.114(D).

### 8.1 Pre-Output Checklist

**MANDATORY before ANY generated document (filing, brief, analysis, summary):**

```
PRE-OUTPUT QA CHECKLIST
═══════════════════════════════════════════════════════════
□ 1.  All citations verified against authority_chains table
□ 2.  No hallucinated case names or statute numbers
□ 3.  Cross-lane contamination check passed (MEEK signal verify)
□ 4.  EGCP score meets filing threshold for target vehicle
□ 5.  Pinpoint citations include page + paragraph references
□ 6.  Opposing argument anticipated and addressed
□ 7.  Party names verified against canonical identity table:
        Plaintiff:  Andrew James Pigors
        Defendant:  Emily A. Watson (NOT "Emily Ann", NOT "Tiffany")
        Child:      L.D.W. (initials ONLY — MCR 8.119(H))
        Judge:      Hon. Jenny L. McNeill (NOT "McNeil", NOT "Amy")
        FOC:        Pamela Rusco
        Emily Atty: Jennifer Barnes P55406 (WITHDREW)
        R. Berry:   NON-ATTORNEY (no bar number, no "Esq.")
□ 8.  Case numbers verified with proper formatting and leading zeros
□ 9.  No fabricated evidence or inflated statistics
□ 10. Every statistic traceable to a specific DB query (table + WHERE)
□ 11. Child referred to as L.D.W. only (MCR 8.119(H) compliance)
□ 12. All dates verified against docket_events or deadlines tables
□ 13. No placeholder text remaining ([ANDREW_REQUIRED], [INSERT], etc.)
□ 14. Bates numbers sequential and cross-referenced to exhibit index
□ 15. Certificate of service present and complete
═══════════════════════════════════════════════════════════
```

**Failure on ANY checkbox = STOP. Do not output. Fix first.**

### 8.2 Anti-Hallucination Rules

**The Cardinal Rule:** If you don't have verifiable data, say so.
Insert `[VERIFY — not found in DB]` rather than guessing.

#### NEVER Invent:
- **Party names** — Use canonical table above or `[UNKNOWN — VERIFY]`
- **Bar numbers** — Query DB or leave blank. NEVER fabricate a SBN.
- **Case citations** — Every cite must exist in `authority_chains` or `master_citations`
- **Evidence statistics** — Every count must come from `SELECT COUNT(*)`
- **Dates** — Every date must come from `docket_events` or `deadlines`
- **Scores or percentages** — No synthetic scoring (no "documented pattern of parental alienation")

#### KNOWN HALLUCINATIONS TO PURGE ON SIGHT:

| Hallucination | Reality | Origin |
|---------------|---------|--------|
| "CPS records [VERIFY — check actual CPS records for count]" | **Unverified count** — no DB source | Inflated from partial data |
| "documented pattern of parental alienation" | **Pseudo-scientific** — no valid methodology | Synthetic generation |
| "584 consecutive days" | **Unverified** — requires date math against DB | Hallucinated round number |
| "Amy McNeill" | **Wrong name** — Judge is Jenny L. McNeill | Persistent name confusion |
| "Emily Ann Watson" | **Wrong middle** — Emily A. Watson only | Middle name fabrication |

**If you encounter ANY of these in existing files, flag them for correction.**

#### Before Citing ANY Count:
```sql
-- ALWAYS run the actual query and record it
SELECT COUNT(*) FROM judicial_violations;
-- Record: "1,127 judicial violations per SELECT COUNT(*) FROM
-- judicial_violations, queried [DATE]"

-- NEVER write "approximately 1,100" or "over 1,000" or "nearly 1,200"
-- Use the EXACT number from the query.
```

#### When Aggregating Across Tables:
```sql
-- ALWAYS deduplicate before totaling
SELECT COUNT(DISTINCT evidence_id) FROM (
    SELECT evidence_id FROM evidence_quotes
    UNION
    SELECT evidence_id FROM impeachment_items
);
-- NOT: eq_count + ii_count (double-counts shared evidence)
```

### 8.3 Traceable Statistics Protocol

Every statistic cited in ANY generated document (filings, dashboards, analyses,
progress reports, summaries) MUST include a provenance record:

```
FORMAT:
"[STAT]: [EXACT NUMBER] [DESCRIPTION]"
"[SOURCE]: SELECT [query] FROM [table] WHERE [conditions]"
"[QUERIED]: [ISO date]"

EXAMPLE:
"1,127 documented judicial violations"
SOURCE: SELECT COUNT(*) FROM judicial_violations
QUERIED: 2026-03-15

"308,704 evidence quotes extracted"
SOURCE: SELECT COUNT(*) FROM evidence_quotes
QUERIED: 2026-03-15

"653 active claims across all lanes"
SOURCE: SELECT COUNT(*) FROM claims
QUERIED: 2026-03-15
```

**Rules for all statistical citations:**
1. Use the EXACT number — never round up or extrapolate
2. Include the SQL query that produced the number
3. Note the date the query was run (data changes with pipeline runs)
4. When citing in a filing, add the provenance as a footnote or appendix
5. Dashboard summaries and progress reports are NOT exempt
6. Inflated progress numbers mislead the user as much as inflated filing numbers

### 8.4 Red Team Attack Vectors

Anticipate and defend against every procedural and substantive attack. Before
filing, run each applicable vector against the document.

| # | Attack Vector | Defense Strategy |
|---|---------------|------------------|
| 1 | **Motion to strike evidence** | Pre-authenticate under MRE 901-903; chain of custody documented per evidence_atoms |
| 2 | **Standing challenge** | Document concrete, particularized harm with DB-sourced citations to specific incidents |
| 3 | **Laches / Statute of limitations** | Verify timeliness using docket_events dates against MCL/MCR limitation periods |
| 4 | **Hearsay objection** | Map each quote to MRE 801(d) exclusions or MRE 803/804/807 exceptions |
| 5 | **Judicial discretion argument** | Score ruling against published standards; show abuse via deviation pattern in judicial_violations |
| 6 | **Mootness challenge** | Show continuing controversy — ongoing custody dispute = inherently not moot |
| 7 | **Rooker-Feldman doctrine** (federal) | Distinguish independent federal constitutional claim from state court review |
| 8 | **Younger abstention** (federal) | Show bad faith prosecution or demonstrated bias (evidence in lane_E) |
| 9 | **Res judicata** | Show changed circumstances per MCL 722.27(1)(c); new evidence not available at prior hearing |
| 10 | **Collateral estoppel** | Distinguish issues — different legal standard or different factual predicate |
| 11 | **Failure to exhaust remedies** | Document all lower court motions, objections, and denied requests from docket_events |
| 12 | **Improper venue** | Confirm MCL 600.1601+ compliance; child's home county = Muskegon |
| 13 | **Insufficient service** | Triple-check MC 12 proof of service; document server affidavit and method |
| 14 | **Page limit violation** | Count words/pages per MCR limits (MCR 7.212(B) = 50 pages for briefs) |
| 15 | **Frivolous filing sanctions** | Document good-faith factual and legal basis per MCR 2.114(D) certification |
| 16 | **Waiver of argument** | Show issue preserved in lower court record — cite specific transcript page |
| 17 | **Lack of proper cause** | Document change in circumstances with evidence timeline from DB |
| 18 | **Best interest standard** | Map evidence to ALL 12 MCL 722.23(a)-(l) factors with pinpoint citations |
| 19 | **Unclean hands** | Distinguish equitable vs. legal claims; show good faith conduct |
| 20 | **Qualified immunity** (federal) | Show clearly established constitutional right with binding authority |
| 21 | **Monell defense** (federal) | Show policy, custom, or deliberate indifference — pattern evidence from DB |
| 22 | **Heck v. Humphrey bar** (federal) | Show no criminal conviction being challenged; §1983 claim is independent |
| 23 | **Discovery abuse objection** | Document proportionality analysis per MCR 2.302(B); show targeted requests |
| 24 | **Expert qualification challenge** | Pre-qualify experts under MRE 702 / Daubert standard; document credentials |
| 25 | **Chain of custody gap** | Document every custodian in evidence_atoms; SHA-256 hash verification |
| 26 | **Insufficient factual basis** | Cite specific DB evidence for every factual assertion (no conclusory statements) |
| 27 | **Constitutional overbreadth** | Narrow relief requested to specific conduct documented in DB |

**Red Team Execution Protocol:**
```
For each filing before submission:
1. Identify all applicable attack vectors from table above
2. For each vector, verify the defense exists in the document
3. If defense is missing → add it or flag for remediation
4. Score: vectors_defended / vectors_applicable = defense coverage %
5. Minimum threshold: 90% coverage before filing
```

### 8.5 Convergence Quality Score Formula

The CQS measures overall readiness of a filing vehicle across six dimensions.
All inputs are derived from DB queries — no subjective scoring.

```
convergence_quality_score = (
    authority_completeness   × 0.25 +   # chains complete / chains total
    evidence_coverage        × 0.20 +   # claims with evidence / total claims
    filing_readiness         × 0.20 +   # EGCP score from filing_readiness table
    strategy_coherence       × 0.15 +   # cross-references verified / total refs
    cross_lane_integrity     × 0.10 +   # contamination errors = 0 → 1.0
    emergence_capture        × 0.10     # novel patterns detected / expected
) × 100
```

**Score Interpretation and Action:**

| Range | Rating | Action |
|-------|--------|--------|
| **95–100** | COURTROOM READY | File with confidence. Final proofread only. |
| **85–94** | NEAR READY | Minor polish — missing footnotes, formatting, COS details |
| **70–84** | IN PROGRESS | Standard convergence cycle — fill gaps systematically |
| **50–69** | SIGNIFICANT GAPS | Intensive remediation — authority chains, evidence linking |
| **25–49** | MAJOR DEFICIENCY | Emergency triage — fundamental gaps in legal theory or evidence |
| **0–24** | CRITICAL | Rebuild required — do not attempt to patch |

**Dimension Computation:**
```sql
-- authority_completeness
SELECT CAST(SUM(CASE WHEN chain_complete = 1 THEN 1 ELSE 0 END) AS FLOAT)
     / COUNT(*) FROM authority_chains WHERE vehicle_name = ?;

-- evidence_coverage
SELECT CAST(COUNT(DISTINCT eq.claim_id) AS FLOAT)
     / (SELECT COUNT(*) FROM claims WHERE vehicle_name = ?)
FROM evidence_quotes eq WHERE eq.vehicle_name = ?;

-- filing_readiness (EGCP score already computed)
SELECT egcp_score FROM filing_readiness WHERE vehicle_name = ?;

-- cross_lane_integrity (0 contamination errors = 1.0)
SELECT CASE WHEN COUNT(*) = 0 THEN 1.0 ELSE 0.0 END
FROM agent_log WHERE status = 'CONTAMINATION_ERROR' AND vehicle_name = ?;
```


## ═══════════════════════════════════════════
## MODULE 9: MASTER EXECUTION PROTOCOL
## ═══════════════════════════════════════════

This module governs how the OMEGA skill system activates, sequences, and
coordinates all other modules. It is the orchestration brain.

### 9.1 Invocation Decision Tree

```
User Request Received
│
├─ "Analyze files/evidence"
│   → MODULE 1 (Evidence Pipeline) + MODULE 7 (DB Intelligence)
│   → Scan drives → extract → classify → store in DB → report
│
├─ "Find contradictions/impeachment"
│   → MODULE 2 (Contradiction Engine)
│   → Query contradiction_map → cross-reference → build packages
│
├─ "Validate citations/authority"
│   → MODULE 3 (Authority Validation Engine)
│   → Verify chains → check currency → fill gaps → score completeness
│
├─ "Draft motion/brief/petition"
│   → MODULE 4 (Filing Factory)
│   → Select template → populate from DB → format per MCR → QA
│
├─ "What should I file next?"
│   → MODULE 5 (Strategic Command)
│   → Assess all vehicles → score readiness → recommend sequence
│
├─ "Custody/PPO/appeal question"
│   → MODULE 6 (Domain Specialist)
│   → Route to correct lane → apply specialized expertise
│
├─ "Run convergence/quality check"
│   → MODULE 5.5 (Convergence Protocol)
│   → Compute CQS → detect emergence → patch → re-test
│
├─ "Database query/statistics"
│   → MODULE 7 (DB Intelligence)
│   → Verify schema → execute query → validate results
│
├─ "Quality check on document"
│   → MODULE 8 (QA & Anti-Hallucination)
│   → Run pre-output checklist → red team → traceable stats
│
├─ "Full pipeline run"
│   → ALL MODULES sequential (see §9.2)
│
└─ "Court-ready filing package"
    → MODULES 1→2→3→4→8 (full pipeline, see §9.2)
```

### 9.2 Full Pipeline Execution

When building a complete filing set from raw evidence to court-ready documents:

```
╔═══════════════════════════════════════════════════════════════╗
║              FULL PIPELINE EXECUTION SEQUENCE                 ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  STEP 1: MODULE 1 — EVIDENCE PIPELINE                        ║
║    Scan drives → extract text → classify → extract atoms      ║
║    Output: evidence_quotes, pages, mega_file_harvest updated  ║
║                                                               ║
║  STEP 2: MODULE 7 — DATABASE INTELLIGENCE                    ║
║    Query existing evidence, claims, authorities               ║
║    Output: Current state assessment, gap identification       ║
║                                                               ║
║  STEP 3: MODULE 2 — CONTRADICTION ENGINE                     ║
║    Run contradiction detection across all evidence            ║
║    Output: contradiction_map, impeachment_items updated       ║
║                                                               ║
║  STEP 4: MODULE 3 — AUTHORITY VALIDATION                     ║
║    Validate all cited authorities, identify gaps, fill chains ║
║    Output: authority_chains complete, master_citations valid   ║
║                                                               ║
║  STEP 5: MODULE 5 — STRATEGIC ASSESSMENT                     ║
║    Score all vehicles, select optimal filing, plan sequence    ║
║    Output: Filing priority order, resource allocation plan     ║
║                                                               ║
║  STEP 6: MODULE 6 — DOMAIN EXPERTISE                         ║
║    Apply lane-specific rules for target court/filing type      ║
║    Output: Jurisdiction-specific requirements verified         ║
║                                                               ║
║  STEP 7: MODULE 4 — FILING FACTORY                           ║
║    Generate court-ready documents from templates + DB data     ║
║    Output: Formatted motion/brief/petition with exhibits      ║
║                                                               ║
║  STEP 8: MODULE 8 — QUALITY ASSURANCE                        ║
║    QA sweep, anti-hallucination check, red team all vectors   ║
║    Output: QA report, issues flagged, corrections applied     ║
║                                                               ║
║  STEP 9: MODULE 5.5 — CONVERGENCE CYCLE                      ║
║    Score CQS, detect emergence, patch deficiencies, re-test   ║
║    Output: Convergence score ≥ 95 or remediation plan         ║
║                                                               ║
║  STEP 10: OUTPUT — COURT-READY FILING PACKET                 ║
║    Final assembly: filing + exhibits + COS + proof of service ║
║    Output: Complete packet ready for e-filing or hand-delivery║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### 9.3 Cross-Lane Evidence Routing Table

Evidence frequently serves multiple legal theories across lanes. Routing MUST
go through Lane C (Convergence) to maintain integrity.

| Source Lane | Target Lane | Connection Type | Example |
|-------------|-------------|-----------------|---------|
| **A** (Custody) → **F** (Appeal) | Trial errors → appellate issues | Denied motion → preserved error for COA |
| **A** (Custody) → **E** (Misconduct) | Biased rulings → JTC complaint | Pattern of one-sided rulings → Canon 2 violation |
| **B** (Housing) → **A** (Custody) | Unsafe housing → best-interest factor (d) | Habitability violations → environment adequacy |
| **D** (PPO) → **A** (Custody) | False allegations → factor (j) pattern | Fabricated PPO claims → willingness to facilitate |
| **D** (PPO) → **E** (Misconduct) | Improper PPO issuance → judicial bias | Ex parte PPO without evidence → due process violation |
| **A** (Custody) → **C** (Convergence) | Due process violations → §1983 claims | State court deprivations → federal civil rights |
| **E** (Misconduct) → **F** (Appeal) | Judicial misconduct → appellate arguments | Bias evidence → recusal/reversal grounds |
| **B** (Housing) → **D** (PPO) | Housing disputes → retaliatory PPO | Eviction timeline correlates with PPO filing |
| **All Lanes** → **C** (Convergence) | Pattern evidence → systemic claims | Individual incidents → pattern/practice theory |

**Routing Protocol:**
```
1. Evidence originates in source lane
2. Agent detects cross-lane relevance via MEEK signal
3. Link created in lane_C_convergence.db → cross_lane_links
4. Target lane agent picks up link and integrates
5. Never copy raw evidence between lane DBs — reference only
```

### 9.4 Checkpoint and Recovery Protocol

Long operations MUST checkpoint every 3 agent completions or 10 minutes:

```
CHECKPOINT PROTOCOL:
1. Update SQL todos table with current status
2. Write progress to 00_SYSTEM/PROGRESS_LOG.md
3. Flush all pending DB writes (conn.commit())
4. Record last-completed step for crash recovery

RECOVERY PROTOCOL (on GOAWAY/503/timeout):
1. Read last checkpoint from SQL todos table
2. Identify incomplete step
3. Resume from incomplete step (do not restart from beginning)
4. Verify integrity of all prior steps before continuing
```

### 9.5 Output Standards

Every generated document MUST meet these standards before delivery:

```
FORMATTING:
  □ Court name and case number in caption
  □ Proper party designations (Plaintiff/Defendant)
  □ Page numbers on every page
  □ Line spacing per MCR (double-spaced for briefs)
  □ Margins per local court rules
  □ Font: Times New Roman 12pt (or per court rule)

SUBSTANCE:
  □ Every factual assertion has a citation
  □ Every legal argument has authority
  □ Relief requested is specific and actionable
  □ Prayer for relief matches arguments made
  □ Certificate of Service is complete and accurate

COMPLIANCE:
  □ Page/word limits respected
  □ Required forms attached (MC/DC as applicable)
  □ Filing fee noted or fee waiver attached
  □ Proof of service method documented
  □ E-filing format requirements met (if applicable)
```

---

*MODULE_7_DB_QA.md — Part 3 of the OMEGA Litigation Supreme Skill System*
*Modules 7 (Database Intelligence), 8 (Quality Assurance), 9 (Master Execution)*
*LitigationOS · Pigors v. Watson · Michigan 14th Circuit Court*
