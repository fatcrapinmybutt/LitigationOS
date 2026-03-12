---
description: SQLite optimization patterns for LitigationOS. Apply when writing or modifying any database queries, connection setup, or data ingestion code.
applyTo: "**/*.py"
---

# SQLite Memory

Hard-won SQLite performance patterns for a 10 GB+, 694-table litigation database.

## Three-Tier Connection Strategy

LitigationOS uses a layered connection architecture. Match PRAGMAs to the tier:

| Tier | Module | mmap | cache | busy_timeout |
|------|--------|------|-------|-------------|
| **1 — Multiplexer** | `connection_multiplexer.py` | 12 GB | 128 MB | 180 s |
| **2 — Standard** | `db_lock_manager.py`, MCP `db.py` | — | 32 MB | 60 s |
| **3 — Simple** | `DatabaseManager`, one-off scripts | — | default | 30 s |

Every connection must set at minimum:

```python
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;   -- 32 MB
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;  -- WAL protects durability
```

## Consolidate COUNT(*) Calls

Use a single query with subqueries instead of N separate `SELECT COUNT(*)` round-trips:

```python
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM table_a) AS a_count,
        (SELECT COUNT(*) FROM table_b WHERE col = ?) AS b_count,
        (SELECT COUNT(*) FROM table_c) AS c_count
""", (param,)).fetchone()
```

This pattern is used in `get_stats()`, `get_evolution_stats()`, and `run_self_audit()` in the MCP `db.py`.

## Batch Inserts with executemany

Collect rows into a list of tuples, then insert in one call:

```python
rows = [(r["col1"], r["col2"]) for r in source_data]
conn.executemany("INSERT OR IGNORE INTO target (col1, col2) VALUES (?, ?)", rows)
conn.commit()
```

Row-by-row `conn.execute()` inside a loop is 10–100× slower. Functions like `load_court_forms_graph()`, `load_rules_authority_index()`, and `load_risk_events()` use this pattern.

## Explicit Column Lists Over SELECT *

Always name columns explicitly, especially in hot paths like `prefetch_cache.py`:

```python
# Correct
SELECT claim_id, vehicle_name, claim_type, status FROM claims WHERE vehicle_name = ?

# Avoid
SELECT * FROM claims WHERE vehicle_name = ?
```

Benefits: reduced I/O, stable schema coupling, and the existing `_get_columns()` / `_table_exists()` guards in prefetch_cache catch column-name mismatches gracefully.

## Composite Indexes for Common Filter Patterns

Add composite indexes matching multi-column WHERE clauses that appear in hot queries:

```sql
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);
CREATE INDEX IF NOT EXISTS idx_authority_chains_vehicle_complete
    ON authority_chains(vehicle_name, chain_complete);
CREATE INDEX IF NOT EXISTS idx_deadlines_vehicle_status
    ON deadlines(vehicle_name, status);
```

Column order matters — put the highest-selectivity column first, or match the WHERE clause order.

## Adaptive Query Rewriter Exists — Use It

`adaptive_query_rewriter.py` transparently rewrites `LIKE '%term%'` → FTS5 `MATCH`, caches `COUNT(*)`, and adds safety `LIMIT`s. Route queries through it instead of writing raw LIKE patterns:

```python
from adaptive_query_rewriter import rewrite
optimized_sql = rewrite(original_sql)
```

## EAGAIN Prevention

> **Master document:** `.github/instructions/eagain-prevention.instructions.md`

Hard limit: **max 3 concurrent DB connections** (enforced by `db_lock_manager.py`). Before opening a new connection in any agent or background thread, verify the cap is not exceeded. Use `managed_db()` context manager for automatic lifecycle management.

**Relationship to write EAGAIN:** SQLite EAGAIN and pipe EAGAIN share the same root — resource exhaustion.
When pipe buffers overflow (too many shells/agents), DB connections may also fail because the OS is
starved for file descriptors. Controlling pipe pressure (max 2 shells + 2 agents) indirectly protects
DB connections. Never open DB connections inside shell commands — use dedicated Python scripts instead.
