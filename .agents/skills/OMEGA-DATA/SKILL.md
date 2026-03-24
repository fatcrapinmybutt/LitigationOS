---
name: OMEGA-DATA
description: >-
  Use when performing any database operation — querying, optimizing, indexing,
  migrating, or managing the 12 GB litigation_context.db with 790+ tables. Covers
  SQLite optimization (WAL, PRAGMA tuning, FTS5), connection management (3-tier
  strategy, db_lock_manager, EAGAIN prevention), query patterns (batch inserts,
  consolidated COUNTs, adaptive rewriting), schema management (PRAGMA table_info
  verification), and data pipeline operations (16-phase processing). Critical for
  all agents and tools that touch the central database.
category: discipline
version: "2.0.0"
triggers:
  - SQL
  - SQLite
  - database
  - query
  - schema
  - optimize
  - FTS5
  - WAL
  - index
  - migration
  - data pipeline
  - PRAGMA
  - busy_timeout
  - executemany
  - managed_db
  - connection pool
  - analytics
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies: []
metadata:
  tier: 3
  fused_skills: 13
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# ⚙️ OMEGA-DATA ⚙️

> **TIER 3 — Implementation & Tools: Database Intelligence**
> **Pipeline:** Query → Optimize → Index → Validate → Manage → Pipeline → Analyze
> **Target:** litigation_context.db (12 GB, 790+ tables) + 10 jurisdiction databases
> **Iron Law:** managed_db() for ALL access. WAL mode. Max 3 connections. EAGAIN = death.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          OMEGA-DATA v2.0                                 ║
║               13 Skills → 8 Modules → 1 Data System                     ║
║                                                                          ║
║  D1  SQLite Optimization ─────┐                                          ║
║  D2  Query Patterns ──────────┤→ D4 Schema Management                    ║
║  D3  Indexing Strategy ───────┘        ↓                                 ║
║  D5  Connection Management ──→ ALL MODULES (gateway)                     ║
║  D6  Data Pipeline ──→ D7 Analytics & Reporting                          ║
║  D8  FTS5 Search ──→ D2, D7                                              ║
║                                                                          ║
║  Central DB: litigation_context.db (12 GB, 790+ tables)                  ║
║  Jurisdiction: databases/*.db (10 specialized databases)                 ║
║  Connection: db_lock_manager.py → managed_db() → max 3 concurrent       ║
║  Safety: PRAGMA busy_timeout=60000, journal_mode=WAL, cache=-32000       ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 13 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `sql-pro` | Advanced SQL query writing, optimization, window functions |
| 2 | `database-admin` | Database administration, maintenance, backup, recovery |
| 3 | `database-architect` | Schema design, normalization, relationship modeling |
| 4 | `database-optimizer` | Query plan analysis, index selection, performance tuning |
| 5 | `database-design` | Table design patterns, constraint management |
| 6 | `database-migration` | Schema migration, versioning, backward compatibility |
| 7 | `database-cloud-optimization-cost-optimize` | Resource optimization, storage efficiency |
| 8 | `sql-optimization-patterns` | Anti-pattern detection, query rewriting |
| 9 | `data-engineer` | Data pipeline design, ETL/ELT patterns |
| 10 | `data-intelligence-forge` | Analytics, reporting, intelligence extraction |
| 11 | `data-quality-frameworks` | Data validation, integrity checks, quality scoring |
| 12 | `search-specialist` | Full-text search, FTS5 configuration, ranking |
| 13 | `postgresql` (adapted) | Relational patterns adapted from PostgreSQL to SQLite |

---

## When to Apply

- **Query optimization** — Slow queries on the 12 GB database need tuning
- **Connection setup** — Any new code that opens a database connection
- **Index creation** — Adding indexes for hot query paths
- **Schema changes** — Adding tables, columns, or modifying existing schema
- **FTS5 search** — Full-text search queries, tokenizer configuration
- **Batch operations** — Bulk inserts, updates, or deletes
- **Data pipeline** — Processing evidence through the 16-phase pipeline
- **Analytics** — Dashboard queries, filing readiness, evidence coverage
- **EAGAIN prevention** — Debugging connection pool exhaustion
- **Migration** — Schema versioning and backward-compatible changes

---

## Decision Tree

```
Database task received
  │
  ├─ "Slow query" / "optimize" / "performance" / "PRAGMA"
  │   └─→ D1: SQLite Optimization
  │
  ├─ "Query pattern" / "COUNT" / "batch insert" / "executemany"
  │   └─→ D2: Query Patterns
  │
  ├─ "Index" / "CREATE INDEX" / "composite" / "FTS5 index"
  │   └─→ D3: Indexing Strategy
  │
  ├─ "Schema" / "table_info" / "columns" / "migration" / "ALTER"
  │   └─→ D4: Schema Management
  │
  ├─ "Connection" / "managed_db" / "EAGAIN" / "busy_timeout" / "lock"
  │   └─→ D5: Connection Management
  │
  ├─ "Pipeline" / "phase" / "ingest" / "extract" / "process"
  │   └─→ D6: Data Pipeline
  │
  ├─ "Dashboard" / "report" / "analytics" / "stats" / "count"
  │   └─→ D7: Analytics & Reporting
  │
  ├─ "Search" / "FTS5" / "MATCH" / "full-text" / "tokenizer"
  │   └─→ D8: FTS5 Search
  │
  └─ Complex / multi-step database work
      └─→ D5 (connect) → D4 (verify schema) → D1 (optimize) → D2 (patterns) → D3 (index)
```

---

## ██ MODULE D1: SQLite Optimization ██

### Purpose
Configure SQLite for maximum performance on a 12 GB litigation database.
Wrong PRAGMAs = 10-100x slower queries and potential data corruption.

### Three-Tier Connection Strategy

| Tier | Module | mmap_size | cache_size | busy_timeout | Use Case |
|------|--------|-----------|------------|-------------|----------|
| **1 — Multiplexer** | `connection_multiplexer.py` | 12 GB | 128 MB | 180 s | Pipeline phases, heavy batch work |
| **2 — Standard** | `db_lock_manager.py`, MCP `db.py` | — | 32 MB | 60 s | Normal agent operations, MCP tools |
| **3 — Simple** | `DatabaseManager`, one-off scripts | — | default | 30 s | Quick lookups, health checks |

### Mandatory PRAGMA Configuration

Every connection MUST set these PRAGMAs before any query:

```sql
-- REQUIRED for every connection (Tier 2 minimum)
PRAGMA busy_timeout = 60000;   -- 60s wait before SQLITE_BUSY
PRAGMA journal_mode = WAL;     -- Write-ahead logging (concurrent reads)
PRAGMA cache_size = -32000;    -- 32 MB page cache
PRAGMA temp_store = MEMORY;    -- Temp tables in RAM
PRAGMA synchronous = NORMAL;   -- WAL protects durability, NORMAL is safe

-- OPTIONAL for Tier 1 (heavy workloads)
PRAGMA mmap_size = 12884901888;  -- 12 GB memory-mapped I/O
PRAGMA cache_size = -131072;     -- 128 MB page cache
PRAGMA busy_timeout = 180000;    -- 3 minute wait
```

### Why WAL Mode is Non-Negotiable

```
Journal mode comparison for 12 GB database:
  DELETE (default): Single-writer, readers blocked during writes
  WAL:             Multiple concurrent readers + 1 writer
                   Readers NEVER block writers
                   Writers NEVER block readers
                   Crash recovery is automatic

WAL + busy_timeout = concurrent agents can query simultaneously.
Without WAL, pipeline phases block each other → SQLITE_BUSY cascade.
```

### Performance Anti-Patterns

| Anti-Pattern | Impact | Fix |
|-------------|--------|-----|
| Missing `busy_timeout` | Instant SQLITE_BUSY on contention | Set to ≥ 30000ms |
| `journal_mode = DELETE` | Reader/writer blocking | Switch to WAL |
| Default `cache_size` | Excessive disk I/O | Set -32000 (32 MB) |
| `synchronous = FULL` | 2x slower writes | Use NORMAL with WAL |
| Opening connections in loops | Connection exhaustion | Reuse connections |
| `temp_store = FILE` | Temp tables on disk | Use MEMORY |

---

## ██ MODULE D2: Query Patterns ██

### Purpose
Write efficient SQL queries that respect the constraints of a 790+ table database
with millions of rows. Bad patterns cause 10-100x slowdowns.

### Pattern 1: Consolidated COUNT(*) Calls

```sql
-- BAD: 3 separate round-trips
SELECT COUNT(*) FROM evidence_quotes;
SELECT COUNT(*) FROM claims WHERE status = 'active';
SELECT COUNT(*) FROM authority_chains WHERE chain_complete = 1;

-- GOOD: 1 round-trip with subqueries
SELECT
    (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
    (SELECT COUNT(*) FROM claims WHERE status = 'active') AS active_claims,
    (SELECT COUNT(*) FROM authority_chains WHERE chain_complete = 1) AS complete_chains;
```

This pattern is used in `get_stats()`, `get_evolution_stats()`, and `run_self_audit()`.

### Pattern 2: Batch Inserts with executemany

```python
# BAD: Row-by-row insertion (10-100x slower)
for row in source_data:
    conn.execute("INSERT INTO target (col1, col2) VALUES (?, ?)",
                 (row["col1"], row["col2"]))

# GOOD: Batch insertion
rows = [(r["col1"], r["col2"]) for r in source_data]
conn.executemany("INSERT OR IGNORE INTO target (col1, col2) VALUES (?, ?)", rows)
conn.commit()
```

Functions using this pattern: `load_court_forms_graph()`, `load_rules_authority_index()`,
`load_risk_events()`.

### Pattern 3: Explicit Column Lists

```sql
-- BAD: SELECT * pulls all columns, wastes I/O
SELECT * FROM claims WHERE vehicle_name = ?;

-- GOOD: Only the columns you need
SELECT claim_id, vehicle_name, claim_type, status, evidence_score
FROM claims WHERE vehicle_name = ?;
```

Critical in hot paths like `prefetch_cache.py` where `_get_columns()` and
`_table_exists()` guards catch column-name mismatches.

### Pattern 4: Parameterized Queries (ALWAYS)

```python
# BAD: String interpolation → SQL injection risk
conn.execute(f"SELECT * FROM claims WHERE claim_type = '{user_input}'")

# GOOD: Parameterized → safe
conn.execute("SELECT * FROM claims WHERE claim_type = ?", (user_input,))
```

### Pattern 5: INSERT OR IGNORE / UPSERT

```sql
-- Skip duplicates silently
INSERT OR IGNORE INTO documents (sha256, file_path, lane) VALUES (?, ?, ?);

-- Upsert: insert or update on conflict
INSERT INTO documents (sha256, file_path, lane, updated_at)
VALUES (?, ?, ?, datetime('now'))
ON CONFLICT(sha256) DO UPDATE SET
    file_path = excluded.file_path,
    lane = excluded.lane,
    updated_at = excluded.updated_at;
```

### Pattern 6: Window Functions for Ranking

```sql
-- Rank evidence by relevance per claim
SELECT claim_id, quote_text, relevance_score,
       ROW_NUMBER() OVER (PARTITION BY claim_id ORDER BY relevance_score DESC) AS rank
FROM evidence_quotes
WHERE relevance_score > 0.5;
```

---

## ██ MODULE D3: Indexing Strategy ██

### Purpose
Create and manage indexes that match the actual query patterns in the pipeline.
Wrong indexes waste space and slow writes. Missing indexes cause full table scans.

### Composite Index Design Rules

1. **Column order matters** — Put highest-selectivity column first, OR match WHERE clause order
2. **Covering indexes** — Include all SELECT columns to avoid table lookups
3. **Don't over-index** — Each index slows INSERT/UPDATE operations
4. **Monitor with EXPLAIN** — Verify the optimizer actually uses your index

### Critical Indexes for LitigationOS

```sql
-- Evidence queries (Module E4, E7)
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);

CREATE INDEX IF NOT EXISTS idx_evidence_quotes_relevance
    ON evidence_quotes(relevance_score DESC);

-- Authority chain queries (Module R1)
CREATE INDEX IF NOT EXISTS idx_authority_chains_vehicle_complete
    ON authority_chains(vehicle_name, chain_complete);

-- Deadline queries (time-critical)
CREATE INDEX IF NOT EXISTS idx_deadlines_vehicle_status
    ON deadlines(vehicle_name, status);

CREATE INDEX IF NOT EXISTS idx_deadlines_due_date
    ON deadlines(due_date_iso);

-- Document classification (Module E4)
CREATE INDEX IF NOT EXISTS idx_documents_lane_type
    ON documents(lane, file_type);

CREATE INDEX IF NOT EXISTS idx_documents_sha256
    ON documents(sha256);

-- Claims queries (Module R4, R5)
CREATE INDEX IF NOT EXISTS idx_claims_vehicle_status
    ON claims(vehicle_name, status);

-- Filing readiness (Dashboard)
CREATE INDEX IF NOT EXISTS idx_filing_readiness_vehicle
    ON filing_readiness(vehicle_name);
```

### Index Verification
```sql
-- Check what indexes exist on a table
PRAGMA index_list('evidence_quotes');

-- Check index columns
PRAGMA index_info('idx_evidence_quotes_vehicle_claim');

-- Verify index is being used
EXPLAIN QUERY PLAN
SELECT * FROM evidence_quotes WHERE vehicle_name = 'custody' AND claim_id = 'C001';
-- Should show: SEARCH TABLE evidence_quotes USING INDEX idx_evidence_quotes_vehicle_claim
```

### When NOT to Index

| Scenario | Reason |
|----------|--------|
| Small tables (< 1000 rows) | Full scan is faster than index lookup |
| Rarely queried columns | Index maintenance cost > query benefit |
| Columns with low selectivity | e.g., boolean `status` with 2 values |
| Tables with heavy write load | Each index slows every INSERT/UPDATE |

---

## ██ MODULE D4: Schema Management ██

### Purpose
Safely manage the schema of a 790+ table database where column names evolve
faster than documentation.

### ⚠️ IRON RULE: Verify Before Querying

```python
# ALWAYS verify columns before querying a table for the first time
def verify_schema(conn, table_name):
    """Get actual column names — never assume from documentation."""
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {col[1]: col[2] for col in columns}  # {name: type}

# Usage
schema = verify_schema(conn, "authority_chains")
# Verify: is it 'chain_complete' or 'is_complete'?
assert "chain_complete" in schema, "Column name changed — update query"
```

### Known Column Name Corrections

| Table | WRONG (documented) | CORRECT (actual) |
|-------|-------------------|-------------------|
| `authority_chains` | `is_complete` | `chain_complete` |
| `filing_readiness` | `vehicle` | `vehicle_name` |
| `deadlines` | `deadline_date` | `due_date_iso` |
| `claims` | `id` | `claim_id` |

### Schema Reference Table
```sql
-- The DB has a self-documenting schema reference
SELECT table_name, column_name, data_type, description
FROM schema_reference
WHERE table_name = 'evidence_quotes';
```

### Migration Patterns

```sql
-- Add column (backward compatible)
ALTER TABLE claims ADD COLUMN evidence_score REAL DEFAULT 0.0;

-- Create new table with constraints
CREATE TABLE IF NOT EXISTS acquisition_tasks (
    task_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);

-- Rename requires recreate in SQLite (no ALTER TABLE RENAME COLUMN before 3.25)
-- Use CREATE TABLE new → INSERT INTO new SELECT FROM old → DROP old → ALTER TABLE RENAME
```

### Table Discovery
```sql
-- List all tables
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name;

-- Count all tables (for the startup report)
SELECT COUNT(*) FROM sqlite_master WHERE type = 'table';

-- Find tables matching a pattern
SELECT name FROM sqlite_master
WHERE type = 'table' AND name LIKE '%evidence%'
ORDER BY name;

-- Get table sizes (approximate)
SELECT name, SUM(pgsize) as size_bytes
FROM dbstat WHERE name IN (SELECT name FROM sqlite_master WHERE type='table')
GROUP BY name ORDER BY size_bytes DESC LIMIT 20;
```

---

## ██ MODULE D5: Connection Management ██

### Purpose
Manage database connections to prevent SQLITE_BUSY, EAGAIN, and connection
exhaustion. This is the gateway module — every other module routes through here.

### managed_db() — The ONLY Way to Open Connections

```python
from db_lock_manager import managed_db

# CORRECT: Context manager handles open/close/error recovery
with managed_db() as conn:
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    result = conn.execute("SELECT COUNT(*) FROM claims").fetchone()

# WRONG: Manual connection management (leaks on error)
conn = sqlite3.connect("litigation_context.db")  # NO!
```

### Max 3 Concurrent Connections (Enforced)

```
Connection Pool Architecture:
  ┌─────────────────────────────┐
  │    db_lock_manager.py       │
  │    Semaphore(3)             │
  │                             │
  │  Slot 1: [Agent A query]   │
  │  Slot 2: [MCP tool query]  │
  │  Slot 3: [Pipeline phase]  │
  │  Slot 4: BLOCKED (waiting) │
  └─────────────────────────────┘

When all 3 slots are occupied:
  → New connection requests WAIT (up to busy_timeout)
  → If timeout expires → SQLITE_BUSY error
  → If OS resources exhausted → EAGAIN error
```

### EAGAIN Prevention (Database Layer)

| Rule | Why |
|------|-----|
| Max 3 connections | OS file descriptor limit |
| Always close in `finally` | Prevent connection leaks |
| Use `managed_db()` | Auto-closes on exception |
| Never open DB in shell commands | Use Python scripts instead |
| Agent expansion doesn't increase DB pressure | Agents share the 3-connection pool |
| WAL mode required | Allows concurrent reads |

### Connection Lifecycle
```python
# Complete connection lifecycle pattern
import sqlite3
from contextlib import contextmanager

@contextmanager
def managed_db(db_path="litigation_context.db"):
    """Thread-safe connection with automatic cleanup."""
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row  # Dict-like access
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
```

### Debugging Connection Issues
```sql
-- Check WAL status
PRAGMA journal_mode;  -- Should return 'wal'

-- Check current connections (from file system)
-- Look for litigation_context.db-wal and -shm files
-- WAL file growing large = writes not being checkpointed

-- Force WAL checkpoint
PRAGMA wal_checkpoint(TRUNCATE);
```

---

## ██ MODULE D6: Data Pipeline ██

### Purpose
Process evidence through the 16-phase pipeline, managing data flow from raw
files to court-ready structured data.

### Pipeline Phases (Data-Relevant)

```
Phase 0:  Safety Snapshot (SHA-256 manifest, backup)
Phase 1:  Inventory (file discovery → documents table)
Phase 2:  Dedup (content-based → dedup_clusters table)
Phase 3:  Classify (MEEK signals → lane assignment)
Phase 4a: PDF Extraction (PyMuPDF → atoms table)
Phase 4b: DOCX Extraction (python-docx → atoms table)
Phase 4c: Structured Data (forms, tables → structured_data table)
Phase 4d: Atomization (documents → evidence atoms)
Phase 4e: Archive Extraction (ZIP/RAR → nested file extraction)
Phase 5:  LEXOS Brain Feed (50 micro-brains, 8 categories)
Phase 6:  Gap Analysis (EGCP scoring per claim)
Phase 7a: Graph Delta (knowledge graph updates)
Phase 7b: Synthesis Merge (cross-source synthesis)
Phase 7c: Knowledge Merge (master knowledge base)
Phase 8:  Litigation Refresh (filing readiness recalculation)
Phase 9:  MCP Ingest (tool index refresh)
```

### Pipeline Data Flow Pattern
```python
# Each phase reads from and writes to specific tables
PHASE_IO = {
    "phase1": {"reads": [], "writes": ["documents", "agent_log"]},
    "phase2": {"reads": ["documents"], "writes": ["dedup_clusters"]},
    "phase3": {"reads": ["documents"], "writes": ["documents"]},  # updates lane
    "phase4": {"reads": ["documents"], "writes": ["atoms", "evidence_quotes"]},
    "phase5": {"reads": ["atoms"], "writes": ["brain_feed"]},
    "phase6": {"reads": ["claims", "evidence_quotes"], "writes": ["gap_analysis"]},
}
```

### Batch Processing Configuration
```python
# Pipeline batch sizes (tuned for 12 GB database)
BATCH_SIZES = {
    "phase1_scan": 1000,        # Files per scan batch
    "phase2_dedup": 500,        # Files per dedup comparison batch
    "phase3_classify": 500,     # Files per classification batch
    "phase4_extract": 100,      # Documents per extraction batch
    "phase6_gap": 50,           # Claims per gap analysis batch
}

# Checkpoint frequency
CHECKPOINT_EVERY = 100  # items processed before WAL checkpoint
```

### Pipeline Recovery
```python
# Crash-resume pattern: pipeline tracks progress in agent_log
def get_last_processed(conn, phase_name):
    """Find where to resume after crash."""
    row = conn.execute("""
        SELECT MAX(item_id) FROM agent_log
        WHERE phase = ? AND status = 'completed'
    """, (phase_name,)).fetchone()
    return row[0] if row[0] else 0

# Resume from last checkpoint, not from beginning
last_id = get_last_processed(conn, "phase4a")
remaining = conn.execute(
    "SELECT * FROM documents WHERE document_id > ? AND status = 'pending'",
    (last_id,)
).fetchall()
```

---

## ██ MODULE D7: Analytics & Reporting ██

### Purpose
Generate accurate analytics for dashboards, filing readiness assessments,
and progress reports. Every number must be traceable to a specific query.

### Dashboard Query Templates

```sql
-- Filing readiness overview (per lane)
SELECT
    fr.vehicle_name,
    fr.readiness_score,
    fr.evidence_count,
    fr.authority_count,
    fr.gap_count,
    fr.status
FROM filing_readiness fr
ORDER BY fr.readiness_score DESC;

-- Evidence coverage per claim
SELECT
    c.claim_id, c.claim_type, c.vehicle_name,
    COUNT(DISTINCT eq.quote_id) AS evidence_count,
    AVG(eq.relevance_score) AS avg_relevance,
    MAX(eq.relevance_score) AS best_evidence
FROM claims c
LEFT JOIN evidence_quotes eq ON c.claim_id = eq.claim_id
WHERE c.status = 'active'
GROUP BY c.claim_id
ORDER BY evidence_count ASC;

-- Deadline urgency dashboard
SELECT
    d.vehicle_name,
    d.description,
    d.due_date_iso,
    julianday(d.due_date_iso) - julianday('now') AS days_remaining,
    CASE
        WHEN julianday(d.due_date_iso) - julianday('now') < 0 THEN 'OVERDUE'
        WHEN julianday(d.due_date_iso) - julianday('now') < 7 THEN 'URGENT'
        WHEN julianday(d.due_date_iso) - julianday('now') < 30 THEN 'APPROACHING'
        ELSE 'NORMAL'
    END AS urgency
FROM deadlines d
WHERE d.status = 'active'
ORDER BY d.due_date_iso ASC;
```

### Aggregate Statistics (Traceable)

```sql
-- System health summary (single query, 1 round-trip)
SELECT
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table') AS total_tables,
    (SELECT COUNT(*) FROM documents) AS total_documents,
    (SELECT COUNT(*) FROM evidence_quotes) AS total_evidence,
    (SELECT COUNT(*) FROM claims WHERE status='active') AS active_claims,
    (SELECT COUNT(*) FROM authority_chains WHERE chain_complete=1) AS complete_chains,
    (SELECT COUNT(*) FROM deadlines WHERE status='active') AS active_deadlines,
    (SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()) AS db_size_bytes;
```

### Anti-Inflation Rules
- **NEVER hardcode statistics** — always run the query live
- **Check for duplicates** before reporting totals: `SELECT COUNT(DISTINCT ...)` 
- **Never round up** — report exact numbers
- **Show the query** — every stat in a report must cite its SQL source
- **Cross-validate** — if two queries disagree, investigate before reporting

---

## ██ MODULE D8: FTS5 Search ██

### Purpose
Configure and query FTS5 full-text search indexes for fast text retrieval
across millions of evidence records.

### FTS5 Table Creation

```sql
-- Standard FTS5 table for evidence text
CREATE VIRTUAL TABLE IF NOT EXISTS fts_evidence USING fts5(
    quote_text,
    source_document,
    claim_id,
    content='evidence_quotes',
    content_rowid='rowid',
    tokenize='porter unicode61 remove_diacritics 2'
);

-- Rebuild FTS5 index from content table
INSERT INTO fts_evidence(fts_evidence) VALUES('rebuild');
```

### FTS5 Query Syntax

```sql
-- Simple term search
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'custody';

-- Phrase search (exact sequence)
SELECT * FROM fts_evidence WHERE fts_evidence MATCH '"parenting time"';

-- Boolean operators
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'custody AND alienation';
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'custody OR visitation';
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'custody NOT housing';

-- Proximity search (words within N tokens)
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'NEAR(custody alienation, 10)';

-- Column-specific search
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'quote_text:alienation';

-- Prefix search
SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'custod*';

-- Ranked results with snippets
SELECT
    rowid,
    rank,
    snippet(fts_evidence, 0, '<b>', '</b>', '...', 64) AS context,
    quote_text
FROM fts_evidence
WHERE fts_evidence MATCH 'disqualification OR recusal'
ORDER BY rank
LIMIT 20;
```

### Adaptive Query Rewriting (LIKE → FTS5)

The `adaptive_query_rewriter.py` module automatically converts slow patterns:

```python
# Input (slow — full table scan)
"SELECT * FROM evidence_quotes WHERE quote_text LIKE '%alienation%'"

# Output (fast — FTS5 index lookup)
"SELECT * FROM fts_evidence WHERE fts_evidence MATCH 'alienation'"

# The rewriter handles:
# - LIKE '%term%' → MATCH 'term'
# - Multiple LIKE with OR → MATCH 'term1 OR term2'
# - Cached COUNT(*) for frequent tables
# - Safety LIMIT on unbounded queries
```

### FTS5 Maintenance

```sql
-- Check FTS5 index integrity
INSERT INTO fts_evidence(fts_evidence) VALUES('integrity-check');

-- Optimize FTS5 index (merge segments)
INSERT INTO fts_evidence(fts_evidence) VALUES('optimize');

-- Rebuild FTS5 index from scratch (after bulk inserts)
INSERT INTO fts_evidence(fts_evidence) VALUES('rebuild');

-- Delete FTS5 index content (when content table changes)
INSERT INTO fts_evidence(fts_evidence, rowid, quote_text, source_document, claim_id)
VALUES('delete', old_rowid, old_text, old_source, old_claim);
```

### FTS5 Tokenizer Selection

| Tokenizer | Use Case | Example |
|-----------|----------|---------|
| `unicode61` | General text, handles accents | Default for evidence |
| `porter unicode61` | Stemming + unicode (custody → custod) | Best for legal search |
| `ascii` | ASCII-only text | Fast but limited |
| `trigram` | Substring matching (LIKE '%x%' via FTS5) | Slow but flexible |

---

## ██ GLOBAL RULES (Apply to ALL Modules) ██

### Connection Safety
```python
# ALWAYS use managed_db() — NEVER manual sqlite3.connect()
from db_lock_manager import managed_db

with managed_db() as conn:
    # PRAGMAs are set automatically
    result = conn.execute("SELECT ...").fetchall()
# Connection is closed automatically, even on exception
```

### Schema Verification (Before Every New Table Query)
```python
# ALWAYS verify before querying a table for the first time in a session
columns = conn.execute("PRAGMA table_info(table_name)").fetchall()
column_names = [col[1] for col in columns]
# Now you know the actual column names — no guessing
```

### Performance Hierarchy
1. **FTS5 MATCH** for text search (fastest)
2. **Indexed column lookup** for exact matches
3. **Composite index scan** for multi-column filters
4. **Parameterized LIKE** as last resort (slowest)
5. **NEVER** unindexed full table scan on tables > 10K rows

### Error Handling
```python
import sqlite3

try:
    with managed_db() as conn:
        result = conn.execute(query, params).fetchall()
except sqlite3.OperationalError as e:
    if "database is locked" in str(e):
        # EAGAIN/SQLITE_BUSY — wait and retry
        time.sleep(2)
        # Retry with fresh connection
    elif "no such table" in str(e):
        # Schema drift — table may have been renamed
        # Check schema_reference for current name
    elif "no such column" in str(e):
        # Column name changed — verify with PRAGMA table_info
    else:
        raise
```

### Traceable Statistics (Non-Negotiable)
- Every number in a report comes from a `SELECT` query
- Every count uses `COUNT(*)` or `COUNT(DISTINCT ...)`
- Every percentage shows `numerator / denominator`
- Never round up, never extrapolate, never estimate
- Cite the table and WHERE clause for every stat

---

## ═══════════════════════════════════════════════════════════════
## UPGRADE v2.1: LITIGATION DB SCHEMA MAP
## ═══════════════════════════════════════════════════════════════

### Core Table Groups (litigation_context.db — 166+ tables)

| Group | Key Tables | Purpose |
|-------|-----------|---------|
| **Evidence** | evidence_quotes, evidence_exhibits, evidence_images | 92K+ quotes, exhibit tracking |
| **Filing** | filing_readiness, claims, filing_packages | 15 vehicles, readiness scoring |
| **Judicial** | judicial_violations, docket_events | 5K+ violations, court docket |
| **Authority** | authority_master_index, authority_fts, authority_chains | 728 authorities with FTS5 |
| **Deadlines** | deadlines | Filing deadlines with urgency |
| **Intelligence** | narrative_context, critical_facts, session_intelligence | Persistent case narrative |
| **Pipeline** | pipeline_registry, master_todos, system_health_log | 16-phase pipeline tracking |
| **Continuity** | session_handoff, session_intelligence | Cross-session state |

### Adaptive Query Rewriter Integration
Route queries through `adaptive_query_rewriter.py` for automatic optimization:
```python
from adaptive_query_rewriter import rewrite
# LIKE '%term%' → FTS5 MATCH (10-100x faster)
# COUNT(*) → cached result (if fresh)
# Missing LIMIT → safety LIMIT 10000 appended
optimized = rewrite("SELECT * FROM evidence_quotes WHERE content LIKE '%custody%'")
```

### Composite Index Recommendations (Hot Queries)
```sql
CREATE INDEX IF NOT EXISTS idx_eq_vehicle_claim ON evidence_quotes(vehicle_name, claim_id);
CREATE INDEX IF NOT EXISTS idx_ac_vehicle_complete ON authority_chains(vehicle_name, chain_complete);
CREATE INDEX IF NOT EXISTS idx_dl_vehicle_status ON deadlines(vehicle_name, status);
CREATE INDEX IF NOT EXISTS idx_fr_vehicle_score ON filing_readiness(vehicle_name, readiness_score);
CREATE INDEX IF NOT EXISTS idx_jv_judge_type ON judicial_violations(judge_name, violation_type);
```

### Connection Multiplexer (Tier 1 — High Performance)
```python
# For heavy analytics across multiple tables
from connection_multiplexer import get_connection
conn = get_connection()  # mmap=12GB, cache=128MB, busy_timeout=180s
```

### LEXICON DB Integration
```sql
-- 00_SYSTEM/databases/lexicon.db — 148 rules, 28 cross-refs
-- Tables: rules, cross_references, filing_requirements, deadline_rules, evidence_rules
-- FTS5: rules_fts
SELECT * FROM rules WHERE rule_id LIKE 'MCR%' AND category = 'procedure';
SELECT * FROM cross_references WHERE source_rule = 'MCR 2.003';
```
