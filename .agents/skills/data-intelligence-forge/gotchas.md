# Gotchas — data-intelligence-forge

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I know the column names — I've queried this table before" | DB schema evolves constantly. Past sessions crashed querying `authority_chains.is_complete` when the real column is `chain_complete`. Column names in instructions files may be outdated. | `OperationalError: no such column` crashes mid-filing, agent retries fail, user loses trust. |
| 2 | "SELECT * is fine for a quick check" | `SELECT *` on a 790+ table DB with million-row tables transfers massive data through pipes. On tables like `evidence_quotes` (500K+ rows), it can exhaust memory and trigger EAGAIN. | Shell pipe buffer overflow, write EAGAIN, cascading session failure. Or silent truncation — you see 100 rows and assume that's all. |
| 3 | "I'll just run COUNT(*) for each table separately" | N separate `SELECT COUNT(*)` round-trips on a 12GB WAL-mode DB means N separate query plans, N lock acquisitions. Consolidate into one query with subqueries. | 10x slower execution, increased busy_timeout risk, potential SQLITE_BUSY under concurrent agent access. |
| 4 | "WAL mode is already set — the DB handles concurrency" | WAL mode must be SET on every new connection. It is not a persistent DB property that survives all connection types. If you skip `PRAGMA journal_mode=WAL`, you get rollback journal mode, which blocks ALL readers during writes. | Concurrent agents deadlock. One agent's write blocks all reads. Pipeline stalls for minutes. |
| 5 | "I can open as many DB connections as I need" | Hard limit: max 3 concurrent DB connections enforced by `db_lock_manager.py`. Each agent, each shell script, each MCP tool call that touches the DB counts. Exceeding the limit causes SQLITE_BUSY after busy_timeout expires. | Agent hangs for 60 seconds, then crashes. If 4 agents all open connections, the 4th gets locked out and all its work is lost. |
| 6 | "LIKE '%term%' is good enough for search" | `LIKE '%term%'` forces a full table scan on every row. On `evidence_quotes` (500K+ rows) or `documents` (100K+ rows), this takes 30+ seconds. FTS5 indexes exist — use `MATCH` instead. | Query timeout, user waits 45 seconds for a search that should take 200ms. Or worse — shell times out and results are lost. |
| 7 | "I'll add an index later if it's slow" | Without composite indexes on hot filter patterns (`vehicle_name + claim_id`, `vehicle_name + status`), every WHERE clause with multiple conditions does a full scan then filters. The DB is 12GB — scans are expensive. | Queries that should take 50ms take 15 seconds. Multiplied across a 16-phase pipeline run, this adds hours to processing time. |

---

## Common Failure Modes

### 1. Schema Assumption Errors
- **What happens**: Agent queries a table using column names from memory or instructions that don't match the actual schema. Common mismatches: `is_complete` vs `chain_complete`, `deadline_date` vs `due_date_iso`, `id` vs `claim_id`.
- **How to prevent**: Run `PRAGMA table_info(table_name)` before the first query to any table in a session. Also check `schema_reference` table: `SELECT * FROM schema_reference WHERE table_name = 'X'`.
- **Risk level**: HIGH

### 2. Connection Pool Exhaustion
- **What happens**: Multiple agents or scripts open DB connections without using `managed_db()`. The 3-connection semaphore is exceeded. New connections get `SQLITE_BUSY` after 60 seconds of waiting.
- **How to prevent**: Always use `managed_db()` from `db_lock_manager.py`. Never open raw `sqlite3.connect()` in agent scripts. Never open DB connections inside shell commands — use dedicated Python scripts.
- **Risk level**: HIGH

### 3. Duplicate Counting in Aggregates
- **What happens**: Joining across tables without dedup produces inflated counts. Counting evidence across `evidence_quotes` + `documents` + `exhibits` without checking for shared `document_id` values double- or triple-counts items.
- **How to prevent**: Use `COUNT(DISTINCT column)` when aggregating across joins. Always verify aggregate totals against individual table counts. Document the query used for any statistic cited in filings.
- **Risk level**: HIGH

### 4. Missing PRAGMA Configuration
- **What happens**: A new connection is opened without setting WAL mode, busy_timeout, cache_size, or temp_store. Under concurrent access, this causes immediate blocking, slow queries, and potential data corruption.
- **How to prevent**: Every connection must set at minimum: `PRAGMA busy_timeout=60000; PRAGMA journal_mode=WAL; PRAGMA cache_size=-32000; PRAGMA temp_store=MEMORY; PRAGMA synchronous=NORMAL;`
- **Risk level**: HIGH

### 5. Unbounded Query Results Through Pipes
- **What happens**: A query returns 10K+ rows and the output is piped through a shell session. The 64KB pipe buffer overflows, triggering write EAGAIN and killing the session.
- **How to prevent**: Always add `LIMIT` to exploratory queries. For large result sets, write to a temp file and read with the `view` tool. Use the adaptive query rewriter which adds safety LIMITs automatically.
- **Risk level**: MEDIUM

---

## Integration Gotchas

- **litigation_context.db is the single source of truth**: All pipeline phases write here. All apps read from here. Never create shadow copies or local caches that diverge.
- **Lane DBs are supplementary**: `lane_A_custody.db` through `lane_F_appellate.db` contain lane-specific data. They are NOT subsets of `litigation_context.db` — they have their own schemas.
- **FTS5 tables require MATCH, not LIKE**: The `search_index` and similar FTS5 virtual tables use `WHERE column MATCH 'query'` syntax. Using `LIKE` on FTS5 tables returns zero results without error.
- **adaptive_query_rewriter.py**: Route queries through this module when possible. It transparently rewrites `LIKE '%term%'` to FTS5 MATCH, caches COUNT(*), and adds safety LIMITs.
- **MCP DB tools vs direct queries**: The litigation-context MCP server has built-in tools (`search`, `get_stats`, `evidence_lookup`) that handle PRAGMAs, connection pooling, and output formatting. Prefer MCP tools over raw SQL when available.
