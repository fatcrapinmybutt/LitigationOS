---
description: SQLite optimization patterns for LitigationOS. Apply when writing or modifying any database queries, connection setup, or data ingestion code.
applyTo: "**/*.{py,ts,js,sql,rs,go}"
---

# SQLite Optimization Patterns

Hard-won SQLite performance patterns for a 10 GB+, 790+-table litigation database across 70+ database files on 6 drives.

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

This pattern is used in `get_stats()`, `get_evolution_stats()`, and `run_self_audit()` in the MCP `db.py`. Eliminates N−1 round-trips and lets the query planner share table scans.

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

Column order matters — put the highest-selectivity column first, or match the WHERE clause order. Equality conditions first, range conditions last:

```sql
-- Query: WHERE status = 'active' AND created_at > '2024-01-01'
CREATE INDEX idx_status_created ON orders(status, created_at);
-- status (equality) first, created_at (range) second
```

## Cursor-Based Pagination Over OFFSET

Replace `LIMIT N OFFSET M` with keyset/cursor pagination for large result sets:

```sql
-- Cursor-based (fast at any depth)
SELECT id, name FROM items WHERE id > :last_seen_id ORDER BY id LIMIT 20;

-- OFFSET-based (degrades linearly — avoid)
SELECT id, name FROM items ORDER BY id LIMIT 20 OFFSET 10000;
```

Critical for tables with 100K+ rows (evidence_quotes, authority_chains_v2, timeline_events).

## Adaptive Query Rewriter Exists — Use It

`adaptive_query_rewriter.py` transparently rewrites `LIKE '%term%'` → FTS5 `MATCH`, caches `COUNT(*)`, and adds safety `LIMIT`s. Route queries through it instead of writing raw LIKE patterns:

```python
from adaptive_query_rewriter import rewrite
optimized_sql = rewrite(original_sql)
```

## EAGAIN Prevention

Hard limit: **max 3 concurrent DB connections** (enforced by `db_lock_manager.py`). Before opening a new connection in any agent or background thread, verify the cap is not exceeded. Use `managed_db()` context manager for automatic lifecycle management.

**Relationship to write EAGAIN:** SQLite EAGAIN and pipe EAGAIN share the same root — resource exhaustion.
When pipe buffers overflow (too many shells), DB connections may also fail because the OS is
starved for file descriptors. Controlling SHARED pipe pressure (max 2 shells) indirectly protects
DB connections. Agents use ISOLATED pipes (safe at 3 concurrent). Total: max 2 shells + 3 agents = 5.
Never open DB connections inside shell commands — use dedicated Python scripts instead.

## Filesystem-Aware Journal Mode Selection

exFAT (used on USB removable drives like J:\) has **no file locking** and **no filesystem journaling**. SQLite WAL mode requires `.shm` shared memory files and POSIX-style file locks — both fail silently on exFAT, risking data corruption.

```python
# NTFS drives (C:\ SSD) — WAL mode is safe and fast
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

# exFAT drives (J:\ USB, removable media) — DELETE mode only
PRAGMA journal_mode = DELETE;
PRAGMA synchronous = FULL;   # compensate for no filesystem journal

# Read-only WAL databases on exFAT — use immutable=1 URI flag
conn = sqlite3.connect("file:///J:/path/db.sqlite?immutable=1", uri=True)
```

Match journal mode to the filesystem hosting the database file. When ATTACHing cross-filesystem, each attached DB inherits its own journal mode independently.

## Multi-Database Federation with ATTACH

LitigationOS has 70+ databases across 6 drives. Cross-DB queries use SQLite's ATTACH:

```python
conn.execute("ATTACH DATABASE ? AS ?", (str(db_path), alias))

# Cross-DB query spanning main + attached
cursor = conn.execute("""
    SELECT a.claim_id, b.authority_text
    FROM main.claims a
    JOIN authority_brain.authorities b ON a.authority_id = b.id
""")
```

**Constraints and patterns:**
- Default max 10 attached DBs per connection (compile-time limit: 125)
- WAL mode does **NOT** provide atomic cross-DB transactions — use DELETE mode when atomicity across attached DBs is required
- Pre-attach known DBs at connection startup; avoid ATTACH/DETACH in hot request paths
- For 10+ source DBs, batch-attach in groups of 9 (main uses one slot), query, DETACH, rotate
- Run `ANALYZE` on all attached DBs for optimal cross-DB query plans
- Prefix all table references with schema alias in cross-DB queries for clarity

## 3-Tier Storage Architecture

| Tier | Location | Journal Mode | Use Case |
|------|----------|-------------|----------|
| **HOT** | C:\ NVMe SSD | WAL | `litigation_context.db`, brain DBs, rules, forms — fast reads/writes |
| **WARM** | J:\ USB 2TB exFAT | DELETE | Manifests, OCR, tools, reference — infrequent cold queries |
| **ARCHIVE** | J:\ USB 2TB exFAT | `immutable=1` | Historical backups — read-only, never written to |

Active databases stay on the SSD for WAL performance + reliable file locking. USB drives serve archives and cold reference queries only. When building connection helpers, detect the drive letter and auto-select the correct journal mode.

## Schema Introspection Before Queries

Production tables created by the pipeline may have completely different columns than DDL definitions in code (e.g., pipeline-created `documents` table has `title`, `doc_type`, `content_preview` while MCP DDL expects `file_name`, `file_size_bytes`, `sha256_hash`).

```python
# Always verify schema before first query to any table
columns = {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
has_title = "title" in columns
has_file_name = "file_name" in columns
# Build adaptive SELECT based on actual columns present
```

**Key gotcha:** `CREATE TABLE IF NOT EXISTS` silently skips when the table already exists with a **different** schema. It does NOT validate or migrate columns. Use adaptive column helpers (like `_doc_columns()`) that introspect at runtime and alias columns to bridge mismatches between production schema and expected schema.

**ENFORCEMENT (Rule 16):** Querying a column that doesn't exist is a runtime crash, not a graceful error. Before ANY query on a table you haven't verified this session:
1. `PRAGMA table_info(X)` → build `columns` set
2. Check required columns exist: `assert 'sha256' in columns` (IntakePipeline crashed on this)
3. Build adaptive SELECT using only verified columns
4. If missing a column → log warning + skip or alias, NEVER crash

## Path Centralization (Rule 30)

All database file paths in Python code MUST use the shared module's centralized path resolution:

```python
# CORRECT — centralized, portable
from shared import get_db, get_db_path, config
conn = get_db("litigation_context")
path = get_db_path("authority_master")

# WRONG — hardcoded, breaks on any machine/drive change
conn = sqlite3.connect(r"C:\Users\andre\LitigationOS\litigation_context.db")
path = Path(r"C:\Users\andre\LitigationOS\09_DATA\authority_master.db")
```

**Current violation count:** 43 files with hardcoded paths, 18/22 engines bypass shared module. Fix on contact — when editing any file with a hardcoded path, migrate it to `shared.get_db()` in the same commit.
