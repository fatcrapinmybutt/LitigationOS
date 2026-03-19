# SQLite Patterns for LitigationOS

## Overview

LitigationOS's central database (`litigation_context.db`) is a 12GB+ SQLite database
with 790+ tables and millions of rows. Standard SQLite usage patterns don't apply at
this scale. These patterns are hard-won from production usage across 200+ agent sessions.

---

## Three-Tier Connection Strategy

Every connection to litigation_context.db must use the appropriate tier.

### Tier 1 — Multiplexer (High-Performance Pipeline)
**Module**: `connection_multiplexer.py`
**Use when**: Pipeline phases, bulk ingestion, cross-table joins
```python
PRAGMA mmap_size = 12884901888;  -- 12 GB memory-mapped I/O
PRAGMA cache_size = -131072;     -- 128 MB page cache
PRAGMA busy_timeout = 180000;    -- 3 minutes (pipeline runs are long)
PRAGMA journal_mode = WAL;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

### Tier 2 — Standard (Agent/MCP Operations)
**Module**: `db_lock_manager.py`, MCP `db.py`
**Use when**: Agent queries, MCP tool calls, interactive analysis
```python
PRAGMA busy_timeout = 60000;     -- 60 seconds
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;      -- 32 MB page cache
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

### Tier 3 — Simple (One-Off Scripts)
**Module**: `DatabaseManager`, ad-hoc scripts
**Use when**: Quick checks, schema inspection, single queries
```python
PRAGMA busy_timeout = 30000;     -- 30 seconds
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -8000;       -- 8 MB page cache
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

---

## WAL Mode: Non-Negotiable

WAL (Write-Ahead Logging) mode is REQUIRED for concurrent access.

### Why
- Rollback journal mode (the default) blocks ALL readers during a write
- WAL allows concurrent reads during writes
- Without WAL, a single pipeline write blocks all agent queries for seconds

### Critical Detail
WAL mode must be SET on every new connection. It is not always persistent:
```python
conn = sqlite3.connect("litigation_context.db")
conn.execute("PRAGMA journal_mode=WAL")  # MUST do this every time
```

### Verification
```sql
PRAGMA journal_mode;  -- Should return "wal"
```

---

## Connection Pool Management

**Hard limit**: Max 3 concurrent DB connections (enforced by `db_lock_manager.py`).

### Using managed_db()
```python
from db_lock_manager import managed_db

with managed_db("litigation_context.db") as conn:
    result = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
    # Connection automatically released when context exits
```

### Why 3?
- SQLite WAL supports unlimited readers but only 1 writer
- 3 connections = typically 1 writer + 2 readers
- More connections increase lock contention without improving throughput
- Agent expansion to 4 agents shares the same 3-connection pool

---

## Batch Insert Pattern

Row-by-row INSERT is 10-100x slower than batch `executemany`.

### Correct Pattern
```python
rows = [(r["doc_id"], r["content"], r["lane"]) for r in source_data]
conn.executemany(
    "INSERT OR IGNORE INTO documents (doc_id, content, lane) VALUES (?, ?, ?)",
    rows
)
conn.commit()
```

### Anti-Pattern
```python
for r in source_data:  # 10,000 iterations = 10,000 separate transactions
    conn.execute("INSERT INTO documents VALUES (?, ?, ?)",
                 (r["doc_id"], r["content"], r["lane"]))
    conn.commit()  # Commit per row = catastrophically slow
```

---

## FTS5 Full-Text Search

Several tables have FTS5 indexes for fast text search. Use `MATCH`, not `LIKE`.

### Correct
```sql
SELECT * FROM search_index WHERE search_index MATCH 'custody AND modification'
ORDER BY rank LIMIT 20;
```

### Wrong
```sql
SELECT * FROM search_index WHERE content LIKE '%custody%';
-- Returns 0 rows on FTS5 tables (silently fails) or full table scan on regular tables
```

### Query Expansion
FTS5 is keyword-based. Expand conceptual queries:
```sql
-- Instead of just "bias"
MATCH 'bias OR prejudice OR partiality OR favoritism OR unfair'
```

---

## Consolidated COUNT Queries

Never run N separate COUNT queries when one will do.

### Correct
```python
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM documents) AS doc_count,
        (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
        (SELECT COUNT(*) FROM claims WHERE status = 'active') AS active_claims
""").fetchone()
```

### Wrong
```python
doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
ev_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
claim_count = conn.execute("SELECT COUNT(*) FROM claims WHERE status='active'").fetchone()[0]
# 3 round-trips, 3 lock acquisitions, 3 query plans
```

---

## Schema Verification Pattern

ALWAYS verify schema before querying a table for the first time in a session.

```python
# Step 1: Check table exists
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
    (table_name,)
).fetchone()

# Step 2: Get actual columns
columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
col_names = [c[1] for c in columns]

# Step 3: Also check schema_reference table
ref = conn.execute(
    "SELECT * FROM schema_reference WHERE table_name = ?",
    (table_name,)
).fetchall()
```

### Known Column Mismatches (from past crashes)
| Table | Wrong Name | Correct Name |
|-------|-----------|-------------|
| authority_chains | is_complete | chain_complete |
| filing_readiness | vehicle | vehicle_name |
| deadlines | deadline_date | due_date_iso |
| claims | id | claim_id |

---

## Composite Index Strategy

Add indexes matching common multi-column WHERE clauses:

```sql
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);
CREATE INDEX IF NOT EXISTS idx_authority_chains_vehicle_complete
    ON authority_chains(vehicle_name, chain_complete);
CREATE INDEX IF NOT EXISTS idx_deadlines_vehicle_status
    ON deadlines(vehicle_name, status);
CREATE INDEX IF NOT EXISTS idx_claims_vehicle_type
    ON claims(vehicle_name, claim_type);
```

**Column order matters**: Put the highest-selectivity column first, or match the
WHERE clause order. `(vehicle_name, claim_id)` serves queries filtering by both,
or by `vehicle_name` alone, but NOT by `claim_id` alone.

---

## Adaptive Query Rewriter

Route queries through `adaptive_query_rewriter.py` for automatic optimization:

```python
from adaptive_query_rewriter import rewrite

original = "SELECT * FROM evidence_quotes WHERE content LIKE '%custody%'"
optimized = rewrite(original)
# Rewrites LIKE → FTS5 MATCH, adds LIMIT, caches COUNT(*)
```

### What It Does
- Rewrites `LIKE '%term%'` → FTS5 `MATCH` (when FTS5 index exists)
- Caches `COUNT(*)` results for frequently queried tables
- Adds safety `LIMIT` to unbounded SELECT queries
- Logs slow queries for later index optimization
