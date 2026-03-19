# SQLite Optimization Patterns — python-omega-engine

## LitigationOS Database Context

- **Central DB**: `litigation_context.db` — 12GB, 790+ tables, WAL mode
- **Agent DB**: `agents/master_index.db` — Agent fleet registry
- **Court forms DB**: `court_forms.db` — 39 Michigan SCAO forms
- **Lane DBs**: `lane_A_custody.db` through `lane_F_appellate.db`
- **Jurisdiction DBs**: `databases/*.db` — 10 specialized databases

## Three-Tier Connection Strategy

Every DB connection in LitigationOS must use the appropriate tier:

### Tier 1 — Multiplexer (Heavy Pipeline Work)
```python
# connection_multiplexer.py — for pipeline phases processing millions of rows
PRAGMA mmap_size = 12884901888;   # 12 GB memory-mapped I/O
PRAGMA cache_size = -131072;       # 128 MB page cache
PRAGMA busy_timeout = 180000;      # 3 minutes (pipeline phases are long)
```

### Tier 2 — Standard (MCP Server, Agent Access)
```python
# db_lock_manager.py managed_db() — for all normal operations
PRAGMA busy_timeout = 60000;       # 60 seconds
PRAGMA journal_mode = WAL;         # Write-Ahead Logging (concurrent reads)
PRAGMA cache_size = -32000;        # 32 MB page cache
PRAGMA temp_store = MEMORY;        # Temp tables in RAM
PRAGMA synchronous = NORMAL;       # WAL protects durability
```

### Tier 3 — Simple (One-Off Scripts, Quick Queries)
```python
# DatabaseManager, ad-hoc scripts
PRAGMA busy_timeout = 30000;       # 30 seconds
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -8000;         # 8 MB (sufficient for simple queries)
```

## WAL Mode Essentials

```
WAL (Write-Ahead Logging) enables concurrent readers + one writer:
  - Readers NEVER block writers
  - Writers NEVER block readers
  - Only writer-vs-writer conflicts trigger SQLITE_BUSY
  - WAL checkpoint merges WAL file back into main DB (automatic)

CRITICAL: WAL mode must be set on EVERY connection, not just the first.
Each new connection starts in default journal_mode unless explicitly set.
```

## Batch Insert Patterns

```python
# ✅ CORRECT: executemany (10-100x faster than row-by-row)
rows = [(r["col1"], r["col2"]) for r in source_data]
conn.executemany("INSERT OR IGNORE INTO target (col1, col2) VALUES (?, ?)", rows)
conn.commit()

# ❌ WRONG: Row-by-row insert in loop (10-100x slower)
for r in source_data:
    conn.execute("INSERT OR IGNORE INTO target (col1, col2) VALUES (?, ?)",
                 (r["col1"], r["col2"]))
conn.commit()
```

## Consolidated COUNT(*) Queries

```python
# ✅ CORRECT: Single round-trip for multiple counts
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM documents) AS doc_count,
        (SELECT COUNT(*) FROM evidence_quotes) AS quote_count,
        (SELECT COUNT(*) FROM claims) AS claim_count,
        (SELECT COUNT(*) FROM deadlines WHERE status = 'active') AS deadline_count
""").fetchone()

# ❌ WRONG: Four separate queries (4 round-trips)
doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
quote_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
# ... two more queries
```

## FTS5 Full-Text Search

```python
# Create FTS5 virtual table
conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
        content, source_type, source_id,
        tokenize='porter unicode61'
    )
""")

# Search with ranking
results = conn.execute("""
    SELECT content, source_type, rank
    FROM search_index
    WHERE search_index MATCH ?
    ORDER BY rank
    LIMIT 20
""", (search_term,)).fetchall()
```

## Adaptive Query Rewriter

```python
# Route queries through the rewriter for automatic optimization
from adaptive_query_rewriter import rewrite

# Converts LIKE '%term%' → FTS5 MATCH (when FTS5 table exists)
# Adds LIMIT to unbounded queries
# Caches COUNT(*) results
optimized_sql = rewrite(original_sql)
cursor = conn.execute(optimized_sql)
```

## Composite Index Strategy

```sql
-- Index column order must match WHERE clause patterns
-- High-selectivity column first

-- For: WHERE vehicle_name = ? AND claim_id = ?
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);

-- For: WHERE vehicle_name = ? AND chain_complete = ?
CREATE INDEX IF NOT EXISTS idx_authority_chains_vehicle_complete
    ON authority_chains(vehicle_name, chain_complete);

-- For: WHERE vehicle_name = ? AND status = ?
CREATE INDEX IF NOT EXISTS idx_deadlines_vehicle_status
    ON deadlines(vehicle_name, status);

-- For: WHERE table_name = ?
CREATE INDEX IF NOT EXISTS idx_schema_reference_table
    ON schema_reference(table_name);
```

## Connection Pool Safety

```python
from db_lock_manager import managed_db

# ✅ CORRECT: Use context manager (auto-release)
with managed_db() as conn:
    result = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
# Connection automatically released back to pool

# ❌ WRONG: Raw connection (may leak)
conn = sqlite3.connect("litigation_context.db")
result = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
# Connection never closed — pool slot consumed forever
```

## Schema Verification Before Querying

```python
# ALWAYS verify column names before first query to a table
columns = conn.execute("PRAGMA table_info(claims)").fetchall()
column_names = [col[1] for col in columns]

# Known corrections (schema evolves faster than docs):
# authority_chains.chain_complete (not is_complete)
# filing_readiness.vehicle_name (not vehicle)
# deadlines.due_date_iso (not deadline_date)
# claims.claim_id (not id)
```

## Performance Anti-Patterns

| Anti-Pattern | Fix | Speedup |
|-------------|-----|---------|
| `SELECT *` on wide tables | Name columns explicitly | 2-5x |
| Row-by-row INSERT in loop | `executemany()` | 10-100x |
| Multiple `COUNT(*)` queries | Consolidated subquery | 3-4x |
| `LIKE '%term%'` on large tables | FTS5 MATCH | 100-1000x |
| Missing busy_timeout | Set `PRAGMA busy_timeout=60000` | ∞ (prevents crashes) |
| Missing WAL mode | Set `PRAGMA journal_mode=WAL` | 5-10x concurrent |
| Opening connection per query | Connection pool / managed_db | 10-50x |
