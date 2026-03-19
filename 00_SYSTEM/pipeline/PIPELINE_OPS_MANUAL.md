# DELTA9 Pipeline Operations Manual

> **System**: LitigationOS DELTA9 — 50-Agent Litigation Intelligence Pipeline
> **Location**: `C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\`
> **Database**: `agents\master_index.db` (~3.3 GB)
> **Last Updated**: 2025-07-15

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [How to Run](#2-how-to-run)
3. [Database (master_index.db)](#3-database-master_indexdb)
4. [Local-First AI Architecture](#4-local-first-ai-architecture)
5. [Common Operations](#5-common-operations)
6. [Known Issues & Fixes](#6-known-issues--fixes)
7. [Production Outputs](#7-production-outputs)
8. [Enhancement Roadmap](#8-enhancement-roadmap)

---

## 1. System Architecture

### Dual-Lane Parallel Architecture

DELTA9 runs two parallel execution lanes that converge at the end:

```
                    ┌─────────────────────────────────────────┐
                    │         DELTA9 ORCHESTRATOR              │
                    │   agents/agent_orchestrator.py           │
                    └──────────┬──────────────┬───────────────┘
                               │              │
              ┌────────────────▼──┐     ┌─────▼─────────────────┐
              │  LANE 1: I/O      │     │  LANE 2: INTELLIGENCE  │
              │  (Infrastructure) │     │  (CPU/AI-Bound)        │
              │                   │     │                        │
              │  Tier 1: Index    │     │  Tier J: Judicial      │
              │  Tier 2: Dedup    │     │  Tier K: Case Intel    │
              │  Tier 3: Extract  │     │  Tier L: Legal Warfare │
              └────────┬──────────┘     └────────┬──────────────┘
                       │                         │
                       └──────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  CONVERGENCE TIER (F01-F06) │
                    │  Filing → Brain → Graph →   │
                    │  MSC → Test → Certify       │
                    └─────────────────────────────┘
```

**Lane 1 (Infrastructure / I/O-Bound)** — Crawls drives, deduplicates files, extracts text. These agents are disk-bound and benefit from parallel I/O.

**Lane 2 (Intelligence / CPU-Bound)** — Judicial profiling, case scoring, legal analysis. These agents use LocalAI/LLM and are CPU/memory-bound.

**Convergence** — Merges both lanes into production-ready outputs: court filing packets, knowledge graphs, and certification reports.

### The 5 Tiers

| Tier | Lane | Agents | Purpose |
|------|------|--------|---------|
| **tier1** (Index) | Lane 1 | A01–A04 | Crawl all drives, catalog every file into `files` table |
| **tier2** (Dedup) | Lane 1 | A05–A08 | Deduplicate by SHA256, crack archives, cluster duplicates |
| **tier3** (Extract) | Lane 1 | A09–A12 | Flatten nested dirs, extract text from PDFs/docs/structured |
| **tierJ** (Judicial) | Lane 2 | J01–J08 | Profile judges, detect violations, impeach transcripts |
| **tierK** (Case Intel) | Lane 2 | K01–K08 | Score custody/PPO/housing, build timelines, find contradictions |
| **tierL** (Legal Warfare) | Lane 2 | L01–L08 | Score all lanes A/B/C, validate citations, calculate damages |
| **convergence** | Both | F01–F06 | Assemble filings, build graphs, certify pipeline outputs |

### All 50 Agents

#### Lane 1: Infrastructure (I/O-Bound)

**Tier 1 — Indexing (4 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `A01-INDEXSCOUT-C` | `IndexScoutC` | Crawls C:\ drive, catalogs all files (path, size, SHA256, category) into `files` table |
| `A02-INDEXSCOUT-D` | `IndexScoutD` | Crawls D:\ drive |
| `A03-INDEXSCOUT-F` | `IndexScoutF` | Crawls F:\ drive |
| `A04-INDEXSCOUT-GI` | `IndexScoutGI` | Crawls G:\ and I:\ drives |

**Tier 2 — Deduplication (4 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `A05-LEGAL-DEDUP` | `LegalDedup` | Deduplicates legal documents (.pdf, .docx, .doc) by content hash |
| `A06-DATA-DEDUP` | `DataDedup` | Deduplicates data files (.csv, .xlsx, .json, .db) |
| `A07-CODE-DEDUP` | `CodeDedup` | Deduplicates code/source files (.py, .js, .sql, etc.) |
| `A08-ARCHIVE-CRACKER` | `ArchiveCracker` | Extracts zip/rar/7z archives, catalogs nested contents |

**Tier 3 — Extraction (4 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `A09-FLATTEN` | `FlattenCommander` | Flattens deeply nested directory structures (>3 levels) |
| `A10-PDF-HARVEST` | `PdfHarvester` | Extracts text from PDFs using pdfplumber/PyPDF2 |
| `A11-TEXT-MINE` | `TextMiner` | Mines structured text from documents (dates, parties, case numbers) |
| `A12-STRUCT-PARSE` | `StructParser` | Parses structured formats (JSON, XML, CSV) into atoms |

#### Lane 2: Intelligence (CPU/AI-Bound)

**Tier J — Judicial Analysis (8 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `J01-MCNEILL` | `McNeillProfiler` | Profiles Judge McNeill — ruling patterns, bias indicators, reversal rate |
| `J02-HOOPES` | `HoopesProfiler` | Profiles Judge Hoopes — same analysis framework |
| `J03-BENCH` | `BenchbookAuditor` | Validates judicial actions against Michigan benchbook standards |
| `J04-CANON` | `CanonMapper` | Maps violations of the Michigan Code of Judicial Conduct |
| `J05-JTC` | `JtcCompiler` | Compiles Judicial Tenure Commission complaint references |
| `J06-DISQ` | `DisqualificationEngine` | Identifies grounds for judicial disqualification (MCR 2.003) |
| `J07-EXPARTE` | `ExParteDetector` | Detects ex parte communications in docket entries and transcripts |
| `J08-IMPEACH` | `TranscriptImpeacher` | Cross-references transcript testimony for impeachment material |

**Tier K — Case Intelligence (8 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `K01-CUSTODY` | `LaneACustody` | Scores custody evidence per MCL 722.23 best-interest factors |
| `K02-PPO` | `LaneAPpo` | Scores personal protection order evidence and violations |
| `K03-HOUSING` | `LaneBHousing` | Scores Lane B housing/property dispute evidence |
| `K04-CONVERGENCE` | `LaneCConvergence` | Scores Lane C convergence/conspiracy evidence |
| `K05-PERSON` | `PersonProfiler` | Builds comprehensive profiles for all persons in the case |
| `K06-TIMELINE` | `TimelineBuilder` | Constructs chronological event timelines with source citations |
| `K07-AUTHORITY` | `AuthorityHarvester` | Extracts legal authorities, caselaw citations, and MCL references |
| `K08-CONTRADICTION` | `ContradictionDetector` | Finds contradictions between testimony, filings, and evidence |

**Tier L — Legal Warfare (8 agents)**

| Agent ID | Class | Description |
|----------|-------|-------------|
| `L01-SCORER-A` | `LaneAScorer` | Scores all Lane A legal actions (A1–A35 custody/PPO actions) |
| `L02-SCORER-B` | `LaneBScorer` | Scores all Lane B legal actions (B1–B25 housing/property) |
| `L03-SCORER-C` | `LaneCScorer` | Scores all Lane C legal actions (C1–C20 convergence) |
| `L04-GAPS` | `GapDetector` | Identifies evidence gaps — what's missing for each action |
| `L05-CITATIONS` | `CitationValidator` | Validates all legal citations against Westlaw/MCL database |
| `L06-DAMAGES` | `DamagesCalculator` | Calculates damages exposure for each action lane |
| `L07-FILING` | `FilingReadiness` | Assesses filing readiness: evidence strength, citation count, gaps |
| `L08-REDTEAM` | `RedTeamScanner` | Red-team adversarial analysis — how would opposing counsel attack? |

#### Convergence Tier (6 agents)

| Agent ID | Class | Description |
|----------|-------|-------------|
| `F01-FILING` | `FilingFactory` | Assembles court filing packets from scored actions |
| `F02-BRAIN` | `BrainFeeder` | Feeds all results into AI brain (brain_feed_report.json) |
| `F03-GRAPH` | `GraphBuilder` | Builds Neo4j-compatible knowledge graph (nodes + edges CSVs) |
| `F04-MSC` | `MscArchitect` | Architects multi-source corroboration chains |
| `F05-TEST` | `TestRunner` | Runs validation tests across all pipeline outputs |
| `F06-CERTIFY` | `ConvergenceCertifier` | Final certification — produces DELTA9_CONVERGENCE_REPORT.json |

**Total: 50 agents** (4 + 4 + 4 + 8 + 8 + 8 + 8 + 6 = 50)

---

## 2. How to Run

### Prerequisites

```powershell
# Ensure you're in the pipeline directory
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline

# Python 3.10+ required
python --version

# Optional: Check Ollama (not required — LocalAI is primary)
curl http://localhost:11434/api/tags
```

### Full Fleet Run (All 50 Agents)

```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline
python -m agents.agent_orchestrator
```

This runs Lane 1 and Lane 2 in parallel, then convergence. Expect 2–6 hours depending on drive speed and file count.

### Run a Specific Tier

```powershell
# Run only judicial analysis
python -m agents.agent_orchestrator --tier tierJ

# Run only scoring
python -m agents.agent_orchestrator --tier tierL

# Run only convergence (after all other tiers complete)
python -m agents.agent_orchestrator --tier convergence
```

**Available tier values:**

| Flag | Agents | When to Use |
|------|--------|-------------|
| `--tier tier1` | A01–A04 | Re-index drives after adding new files |
| `--tier tier2` | A05–A08 | Re-run deduplication after new indexing |
| `--tier tier3` | A09–A12 | Re-extract text after new files discovered |
| `--tier tierJ` | J01–J08 | Re-run judicial analysis with new transcripts |
| `--tier tierK` | K01–K08 | Re-run case intelligence after new evidence |
| `--tier tierL` | L01–L08 | Re-run scoring after case intel updates |
| `--tier convergence` | F01–F06 | Re-generate final outputs |

### Dry Run (Preview Only)

```powershell
python -m agents.agent_orchestrator --dry-run
```

Shows what would execute without modifying the database or writing outputs. Use this to verify configuration before a real run.

### Agent Execution Model

Each agent inherits from `Agent9999` (in `agents/agent_base.py`) which provides:

- **Checkpoint/Resume**: Agents save progress and resume from where they left off
- **Deadman Switch**: 120-second timeout per agent, 30-second timeout per item
- **Thread-safe DB**: All SQLite writes use jitter retry to avoid lock contention
- **Parallel Workers**: Agents can set `self.parallel_workers > 1` for concurrent item processing
- **Error Hierarchy**: `SkipItemError` skips one item; `FatalAgentError` aborts the agent

---

## 3. Database (master_index.db)

### Location

```
C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db
```

Size: ~3.3 GB (contains full file index + extracted text + atoms + scores)

### Key Tables

| Table | Row Count | Description |
|-------|-----------|-------------|
| `files` | ~1.77M | Complete file catalog — path, SHA256, size, category, depth, drive |
| `atoms` | ~836K | Extracted knowledge atoms (facts, citations, entities) |
| `fact_atoms` | ~157K | Factual assertions with confidence scores |
| `citation_atoms` | ~4.77M | Legal citations (MCL, MCR, caselaw) with meek_lane assignment |
| `judicial_findings` | ~7.1K | Judge profiles, rule violations, MCR references |
| `action_scores` | ~56 | Lane A/B/C action readiness scores (A1–A35, B1–B25, C1–C20) |
| `dedup_clusters` | ~19K | Deduplication clusters with space savings |
| `extracted_text` | ~16.6K | Full text extracted from PDFs/docs |
| `ready_queue` | varies | Pipeline coordination — items waiting for Lane 2 processing |
| `agent_log` | varies | Agent execution log — timing, items processed, errors |

### How to Query

```powershell
# Basic query
sqlite3 "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db" "SELECT COUNT(*) FROM files;"

# Interactive mode
sqlite3 "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db"
```

### Useful Monitoring Queries

```sql
-- File counts by category
SELECT category, COUNT(*) as cnt
FROM files GROUP BY category ORDER BY cnt DESC;

-- Dedup savings
SELECT SUM(space_saved_bytes) / 1073741824.0 as gb_saved
FROM dedup_clusters;

-- Action scores overview (Lane A/B/C readiness)
SELECT action_id, composite_score, evidence_count, gap_count, filing_ready
FROM action_scores ORDER BY composite_score DESC;

-- Judicial findings by judge
SELECT judge_name, COUNT(*) as findings
FROM judicial_findings GROUP BY judge_name;

-- Atoms by type
SELECT atom_type, COUNT(*) as cnt
FROM atoms GROUP BY atom_type ORDER BY cnt DESC;

-- Agent run history (last 10)
SELECT agent_id, status, items_processed, errors, started_at, finished_at
FROM agent_log ORDER BY started_at DESC LIMIT 10;

-- Queue status
SELECT status, COUNT(*) as cnt
FROM ready_queue GROUP BY status;

-- Citation atoms by lane
SELECT meek_lane, COUNT(*) as cnt
FROM citation_atoms GROUP BY meek_lane ORDER BY cnt DESC;

-- Files by drive
SELECT SUBSTR(file_path, 1, 2) as drive, COUNT(*) as cnt
FROM files GROUP BY drive ORDER BY cnt DESC;

-- Largest dedup clusters (most duplicates)
SELECT cluster_hash, member_count, space_saved_bytes / 1048576.0 as mb_saved
FROM dedup_clusters ORDER BY member_count DESC LIMIT 20;
```

---

## 4. Local-First AI Architecture

### Design Principle

**LocalAI is ALWAYS the primary engine.** No API keys, no network, no external dependencies required.

```
┌──────────────────────────────────────────────────┐
│                  LLM Client Fallback Chain         │
│                                                    │
│  1. LocalAI (local_ai_engine.py)  ← ALWAYS FIRST │
│     • Pure regex + scikit-learn                    │
│     • Zero network, zero cost                      │
│     • Handles: classification, entity extraction,  │
│       lane detection, evidence scoring             │
│                                                    │
│  2. Ollama (localhost:11434)      ← LOCAL LLM     │
│     • Runs on your machine                         │
│     • Models: llama3, mistral, etc.                │
│     • Free, private, no data leaves machine        │
│                                                    │
│  3. Gemini (Google AI)            ← CLOUD FALLBACK│
│     • Only if LocalAI + Ollama both fail           │
│     • Requires API key in environment              │
│                                                    │
│  4. Remote Providers              ← LAST RESORT   │
│     • OpenAI, Claude, etc.                         │
│     • Only if all above fail                       │
│                                                    │
└──────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `local_ai_engine.py` | Zero-dependency ML classification engine (regex + sklearn) |
| `llm_client.py` | Multi-provider LLM client with fallback chain |
| `llm_guardian.py` | Health monitoring — quarantines providers after 3 failures |

### LocalAI Capabilities

```python
from local_ai_engine import LocalAI

ai = LocalAI()

# Document classification (Motion, Order, Brief, Transcript, etc.)
doc_type = ai.classify_document(text)

# Case lane detection (A = custody, B = housing, C = convergence)
lane = ai.detect_lane(text)

# Entity extraction (dates, case numbers, judges, statutes)
entities = ai.extract_entities(text)

# Evidence scoring
score = ai.score_evidence(text, action_id="A12")
```

### No API Keys Required

The entire pipeline can run with zero API keys. LocalAI handles all classification and extraction via:

- **Regex patterns** for entity extraction (dates, case numbers, MCL/MCR citations)
- **Keyword matching** for document classification and lane detection
- **TF-IDF + sklearn** for more nuanced similarity scoring

### Checking Ollama Status

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it (optional — not required)
ollama serve

# Pull a model (optional)
ollama pull llama3
```

---

## 5. Common Operations

### Reset Stuck Queue Items

If items are stuck in `processing` status (e.g., after a crash):

```sql
-- Reset all stuck items back to pending
UPDATE ready_queue SET status = 'pending'
WHERE status = 'processing';

-- Check result
SELECT status, COUNT(*) FROM ready_queue GROUP BY status;
```

### Clear Agent Checkpoints

Checkpoints live in `agents/checkpoints/`. Delete them to force a full re-run:

```powershell
# Clear ALL checkpoints (forces full re-run)
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\*" -Force

# Clear specific agent checkpoint
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\J01*" -Force

# Clear all tier L checkpoints (scoring)
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\L*" -Force
```

### Re-Run Scoring (Tier L)

To recalculate all action scores:

```powershell
# 1. Delete scoring checkpoints
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\L01*" -Force
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\L02*" -Force
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\L07*" -Force

# 2. Optionally clear old scores
sqlite3 "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\master_index.db" "DELETE FROM action_scores;"

# 3. Re-run tier L
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline
python -m agents.agent_orchestrator --tier tierL
```

### Fix Citation Lane Assignment

K07 hardcodes `meek_lane='C'` on all citations. To fix for cross-lane scoring:

```sql
-- Update citations that should be in Lane A (custody keywords)
UPDATE citation_atoms SET meek_lane = 'A'
WHERE (citation_text LIKE '%722.23%'
    OR citation_text LIKE '%custody%'
    OR citation_text LIKE '%best interest%')
  AND meek_lane = 'C';

-- Update citations that should be in Lane B (housing keywords)
UPDATE citation_atoms SET meek_lane = 'B'
WHERE (citation_text LIKE '%housing%'
    OR citation_text LIKE '%property%'
    OR citation_text LIKE '%landlord%')
  AND meek_lane = 'C';

-- Set remaining to 'ABC' for cross-lane availability
UPDATE citation_atoms SET meek_lane = 'ABC'
WHERE meek_lane = 'C'
  AND citation_text NOT LIKE '%custody%'
  AND citation_text NOT LIKE '%housing%';
```

### Monitor Pipeline Progress

```sql
-- Currently running agents
SELECT agent_id, status, items_processed, started_at
FROM agent_log WHERE status = 'running';

-- Error rate by agent
SELECT agent_id, items_processed, errors,
       ROUND(errors * 100.0 / NULLIF(items_processed, 0), 1) as error_pct
FROM agent_log
WHERE items_processed > 0
ORDER BY error_pct DESC;

-- Pipeline throughput (items/hour by agent)
SELECT agent_id,
       items_processed,
       ROUND(items_processed * 3600.0 /
             MAX(1, strftime('%s', finished_at) - strftime('%s', started_at)), 0) as items_per_hour
FROM agent_log
WHERE finished_at IS NOT NULL
ORDER BY items_per_hour DESC;

-- Last successful run per tier
SELECT agent_id, MAX(finished_at) as last_run, status
FROM agent_log
WHERE status = 'completed'
GROUP BY SUBSTR(agent_id, 1, 1)
ORDER BY last_run DESC;
```

### Re-Run a Single Agent

There is no direct single-agent flag, but you can:

1. Delete that agent's checkpoint
2. Run the agent's tier (it will skip agents with valid checkpoints)

```powershell
# Example: Re-run only J07 (Ex Parte Detector)
Remove-Item "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline\agents\checkpoints\J07*" -Force
python -m agents.agent_orchestrator --tier tierJ
# J01-J06 and J08 will skip (checkpoints exist), only J07 runs
```

---

## 6. Known Issues & Fixes

### CRITICAL

| Issue | Impact | Status | Fix |
|-------|--------|--------|-----|
| **K07 hardcodes `meek_lane='C'`** | All citations assigned to Lane C only — Lane A/B scorers can't see them | **KNOWN** | Update K07 to assign lane based on citation content, or run SQL fix above |
| **L07 crashes on `None` composite_score** | Filing readiness agent crashes if any action has NULL score | **FIXED** | Current codebase handles None with `or 0.0` fallback |
| **Schema mismatch in `ready_queue`** | `agent_orchestrator.py` line ~108 creates schema that may differ from what agents expect | **KNOWN** | Verify column names match between orchestrator CREATE TABLE and agent queries |
| **`agent_log` column mismatch** | Orchestrator creates `agent_log` with different columns than some agents write | **KNOWN** | Standardize column names across all agents |

### HIGH

| Issue | Impact | Status | Fix |
|-------|--------|--------|-----|
| **USB drives (I:\) cause I/O bottleneck** | A04-INDEXSCOUT-GI slows entire Lane 1 when I: drive is USB 2.0 | **KNOWN** | Skip I: drive or add fast-drive filtering in A04 config |
| **SQLite lock contention** | Multiple agents writing simultaneously can cause "database is locked" | **FIXED** | `agent_base.py` implements jitter retry with exponential backoff |
| **No LLM circuit-breaker** | Flaky remote providers get hammered with retries | **KNOWN** | `llm_guardian.py` quarantines after 3 failures, but retry logic in `llm_client.py` is aggressive |
| **Non-relative imports** | Some agents use absolute imports that break when run from different cwd | **KNOWN** | Always `cd` to pipeline directory before running |
| **A09 flatten incomplete for >3 levels** | Files nested deeper than 3 directory levels may not be fully flattened | **KNOWN** | A09 needs recursion depth increase or iterative deepening |

### LOW

| Issue | Impact | Status |
|-------|--------|--------|
| Hardcoded Gemini OAuth path in llm_client.py | Fails if credentials file moves | Known |
| SQL injection risk in some agent queries | Low risk (local-only DB) but poor practice | Known |
| Fragile column indexing (positional instead of named) | Breaks if schema changes | Known |
| 75+ variant copies across drives | Confusion about which is canonical | Documented in VARIANT_INVENTORY.md |

---

## 7. Production Outputs

### Location

```
C:\Users\andre\LitigationOS\01_CASE_FILES\PRODUCTION_OUTPUT\
```

### Output Files

| File | Description |
|------|-------------|
| `MASTER_FILING_MANIFEST.json` | Master manifest of all scored legal actions with evidence references, filing readiness scores, and gap analysis. This is the **primary pipeline output**. |
| `LEGAL_ACTION_ENCYCLOPEDIA.json` | Complete encyclopedia of all legal actions (A1–A35, B1–B25, C1–C20) with descriptions, statutes, required elements, and current evidence mapping. |
| `MASTER_BINDER_INDEX.json` | Index of all evidence organized by binder/exhibit number, cross-referenced to actions and parties. |
| `PRODUCTION_SUMMARY.md` | Human-readable summary of pipeline results — action counts, readiness percentages, top priorities. |

### Checkpoint Reports

Additional reports in `agents/checkpoints/`:

| File | Description |
|------|-------------|
| `DELTA9_CONVERGENCE_REPORT.json` | Final convergence certification from F06 |
| `brain_feed_report.json` | F02 brain feed output |
| `fleet_report.json` | Full fleet execution report |
| `neo4j_nodes_delta.csv` | Knowledge graph nodes (Neo4j import format) |
| `neo4j_edges_delta.csv` | Knowledge graph edges (Neo4j import format) |
| `msc_viability_*.json` | Multi-source corroboration viability reports |
| `filing_A1` through `filing_C7` | Individual filing packet checkpoints |

### ⚠️ IMPORTANT: These Are Manifests, NOT Court Documents

The production outputs are **metadata and manifests** — structured data about what legal actions are available, what evidence supports them, and how ready they are for filing.

They are **NOT** actual court-ready documents. Converting manifests to real court filings (motions, briefs, petitions) is **Phase 10** — see Enhancement Roadmap below.

---

## 8. Enhancement Roadmap

### Phase 10: Court Document Generator (Priority: CRITICAL)

**Status**: Not yet built
**Need**: Convert `MASTER_FILING_MANIFEST.json` into actual court filings

The pipeline currently produces scored action manifests but stops short of generating actual court documents. Phase 10 would:

- Read the filing manifest for actions marked `filing_ready = true`
- Generate properly formatted Michigan court documents (motions, briefs, petitions)
- Include correct captions, certificates of service, verification statements
- Insert evidence references as exhibits with proper labeling
- Output to `01_CASE_FILES/COURT_FILINGS/` in Word (.docx) and PDF formats

### Vulnerability Scoring (Priority: HIGH)

**Status**: Currently all `vulnerability_score = 0.0`
**Need**: L08-REDTEAM needs adversarial analysis logic

The red team scanner (L08) exists but produces zero vulnerability scores. It needs:

- Adversarial argument generation for each action
- Weakness identification (evidence gaps, contradictory evidence, judicial bias)
- Counter-argument strength scoring
- Recommended mitigations

### De-nesting Deep Files (Priority: MEDIUM)

**Status**: A09 incomplete for >3 levels
**Need**: Full recursive flattening

Files nested more than 3 directory levels deep may not be fully discovered/flattened. A09 needs:

- Iterative deepening or increased recursion limit
- Progress tracking for deeply nested archives-within-archives
- Handling of circular symlinks and junction points

### Multi-Drive Deduplication (Priority: MEDIUM)

**Status**: Known overlap between H: and F: drives
**Need**: Cross-drive dedup with canonical selection

Current dedup runs per-category (A05=legal, A06=data, A07=code) but doesn't fully handle:

- Same file on multiple drives (H: and F: copies)
- Determining which copy is canonical (newest? most accessible?)
- Safe deletion/linking of duplicates

### Merge LitigationOS Variants (Priority: LOW)

**Status**: 75+ variant copies documented in VARIANT_INVENTORY.md
**Need**: Single canonical installation

There are LitigationOS copies across 6+ drives. This task involves:

- Identifying the canonical version (this installation at `C:\Users\andre\LitigationOS\`)
- Extracting any unique data/configs from variants
- Consolidating to single installation
- Updating all hardcoded paths

---

## Appendix A: Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    DELTA9 QUICK REFERENCE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FULL RUN:                                                       │
│    cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline             │
│    python -m agents.agent_orchestrator                           │
│                                                                  │
│  SINGLE TIER:                                                    │
│    python -m agents.agent_orchestrator --tier tierJ               │
│                                                                  │
│  DRY RUN:                                                        │
│    python -m agents.agent_orchestrator --dry-run                 │
│                                                                  │
│  DATABASE:                                                       │
│    sqlite3 agents\master_index.db                                │
│                                                                  │
│  RESET STUCK ITEMS:                                              │
│    UPDATE ready_queue SET status='pending'                       │
│    WHERE status='processing';                                    │
│                                                                  │
│  CLEAR CHECKPOINTS:                                              │
│    Remove-Item agents\checkpoints\* -Force                       │
│                                                                  │
│  CHECK OLLAMA:                                                   │
│    curl http://localhost:11434/api/tags                           │
│                                                                  │
│  OUTPUTS:                                                        │
│    01_CASE_FILES\PRODUCTION_OUTPUT\MASTER_FILING_MANIFEST.json   │
│                                                                  │
│  KEY DOCS:                                                       │
│    AUDIT_REPORT.md      — 14 bugs, 8 weaknesses                 │
│    UPGRADE_MANIFEST.md  — Per-agent improvements                 │
│    VARIANT_INVENTORY.md — 75+ variant copies                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Appendix B: File Layout

```
C:\Users\andre\LitigationOS\
├── 00_SYSTEM\
│   └── pipeline\
│       ├── agents\
│       │   ├── agent_base.py              ← Base class (Agent9999)
│       │   ├── agent_models.py            ← Data models & errors
│       │   ├── agent_orchestrator.py      ← Master orchestrator
│       │   ├── master_index.db            ← 3.3GB central database
│       │   ├── checkpoints\               ← Agent resume state
│       │   ├── lane1_infrastructure\      ← A01–A12 agent code
│       │   ├── lane2_intelligence\        ← J01–L08 agent code
│       │   └── convergence\              ← F01–F06 agent code
│       ├── local_ai_engine.py             ← Zero-dependency ML
│       ├── llm_client.py                  ← Multi-provider LLM
│       ├── llm_guardian.py                ← Provider health monitor
│       ├── config.py                      ← Pipeline configuration
│       ├── safety.py                      ← Safety checks
│       ├── AUDIT_REPORT.md                ← Known bugs & fixes
│       ├── UPGRADE_MANIFEST.md            ← Improvement plan
│       ├── VARIANT_INVENTORY.md           ← Variant tracking
│       └── PIPELINE_OPS_MANUAL.md         ← THIS FILE
│
├── 01_CASE_FILES\
│   └── PRODUCTION_OUTPUT\
│       ├── MASTER_FILING_MANIFEST.json
│       ├── LEGAL_ACTION_ENCYCLOPEDIA.json
│       ├── MASTER_BINDER_INDEX.json
│       └── PRODUCTION_SUMMARY.md
```

---

*This manual documents the DELTA9 pipeline as of its current operational state. For bug details see `AUDIT_REPORT.md`. For per-agent enhancement plans see `UPGRADE_MANIFEST.md`.*
