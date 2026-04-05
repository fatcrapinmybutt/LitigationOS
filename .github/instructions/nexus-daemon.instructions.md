---
description: "NEXUS v2 persistent daemon architecture — the bleeding-edge MCP replacement. Warm connections, 24 actions, line-delimited JSON-RPC. Apply when working with extension tools, database queries, or daemon infrastructure."
applyTo: "**/*.{mjs,js,py,md}"
---

# NEXUS v2 — Persistent Litigation Intelligence Daemon

> **Replaces:** MCP server + spawn-per-call Python subprocesses
> **Location:** `.github/extensions/singularity/nexus_daemon.py`
> **Permanent copy:** `scripts/nexus_daemon.py`
> **Status:** ACTIVE — spawned by `extension.mjs` on session start

## Architecture

```
Copilot CLI Session
  └── extension.mjs (Node.js — Copilot CLI Extension, PID varies)
       └── nexus_daemon.py (PERSISTENT Python subprocess — spawned ONCE)
            ├── SQLite WAL connection (warm, always open)
            │   └── litigation_context.db (~3.2 GB, 790+ tables)
            ├── DuckDB (analytical queries, 10-100× faster aggregations)
            │   └── ATTACHes litigation_context.db as read-only
            ├── LanceDB (semantic search, 75K vectors)
            │   └── 00_SYSTEM/engines/semantic/lancedb_store/
            └── JSON-RPC over stdin/stdout (line-delimited)
```

## Performance vs Legacy

| Metric | Legacy (spawn-per-call) | NEXUS v2 (persistent) |
|--------|------------------------|----------------------|
| Process spawn | ~500ms per call | 0ms (already alive) |
| DB connection | ~50ms per call | 0ms (warm connection) |
| PRAGMA setup | ~10ms per call | 0ms (set once at startup) |
| Analytics | SQLite only | DuckDB (10-100× faster) |
| Semantic search | None | LanceDB 75K vectors |
| Write support | ❌ Read-only | ✅ Full CRUD |
| **Total per-call** | **~600ms** | **~2-5ms** |

## Protocol

Line-delimited JSON over stdin/stdout. One request per line, one response per line.

### Startup Signal
```json
{"ok": true, "status": "ready", "pid": 12345}
```

### Request Format
```json
{"id": "unique-id", "action": "query", "sql": "SELECT ...", "params": [1, "foo"]}
```

### Response Format (success)
```json
{"id": "unique-id", "ok": true, "rows": [...], "columns": [...], "count": 5}
```

### Response Format (error)
```json
{"id": "unique-id", "ok": false, "error": "description"}
```

### Write Response
```json
{"id": "unique-id", "ok": true, "rows_affected": 42, "action": "write"}
```

## 51 Actions (24 Original + 27 Absorbed from MCP)

### Core Database
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `ping` | Health check | — |
| `query` | Parameterized SQL (read or write) | `sql`, `params`, `max_rows` |
| `analytics` | DuckDB analytical query (10-100× faster) | `sql`, `params`, `max_rows` |
| `stats` | Row counts for 20 key tables | — |
| `fts_search` | FTS5 search with snippet + LIKE fallback | `table`, `query`, `limit` |

### Evidence & Search
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `search_evidence` | evidence_quotes FTS5 search | `query`, `limit` |
| `search_impeachment` | impeachment_matrix search | `target`, `category`, `min_severity`, `limit` |
| `search_contradictions` | contradiction_map search | `entity`, `severity`, `lane`, `limit` |
| `search_authority` | authority_chains_v2 search | `citation`, `lane`, `source_type`, `limit` |

### NEXUS Intelligence
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `nexus_fuse` | Cross-table fusion (5 sources simultaneously) | `topic`, `lanes`, `limit` |
| `nexus_argue` | Argument chain synthesis + strength scoring | `claim`, `lane`, `limit` |
| `nexus_readiness` | Filing readiness dashboard per lane | `lane` |
| `nexus_damages` | Aggregate damages across claims | `lane` |

### LEXOS Instant Tools
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `narrative` | Chronological narrative builder | `query`, `lane`, `limit` |
| `filing_plan` | Filing strategy with deadlines | `lane` |
| `rules_check` | Procedural compliance validator | `query`, `limit` |
| `adversary` | Deep adversary profile builder | `person` |
| `gap_analysis` | Missing evidence detector | `lane` |
| `cross_connect` | Cross-lane intelligence fusion | `topic` |

### Case Operations
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `judicial_intel` | Judicial intelligence findings | `judge` |
| `timeline_search` | Timeline events search | `query`, `date_from`, `date_to`, `actor`, `limit` |
| `case_context` | Case context + separation counter | `case_id` |
| `filing_status` | Filing package status | `lane` |
| `deadlines` | Deadline checker with color coding | `days_ahead` |

### Document Management (Absorbed from MCP)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `list_documents` | List indexed documents with metadata | `limit`, `offset`, `name_filter` |
| `get_document` | Retrieve full document text by ID | `document_id`, `page_numbers` |
| `search_documents` | Full-text search across pages | `query`, `limit` |
| `ingest_pdf` | Ingest PDF (BLOCKED — use exec_python) | `file_path` |
| `bulk_ingest` | Bulk ingest directory (BLOCKED — use exec_python) | `path`, `max_files` |

### Knowledge Graph & Rules (Absorbed from MCP)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `lookup_rule` | Look up MCR/MCL rules by citation or keyword | `query`, `limit` |
| `query_graph` | Search knowledge graph nodes | `query`, `node_type`, `graph_source`, `limit` |
| `lookup_authority` | Look up legal authorities with pin cites | `query`, `node_type`, `limit` |

### Intelligence (Absorbed from MCP)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `assess_risk` | Litigation risk assessment from taxonomy | `severity_min`, `risk_class` |
| `get_vehicle_map` | Map relief type to litigation vehicle | `relief_type` |
| `case_health` | Case health dashboard (quotes, harms, impeachment) | — |
| `adversary_threats` | Ranked adversary threat matrix | `limit` |
| `filing_pipeline` | Filing pipeline with readiness and gaps | — |
| `get_subagent_spec` | SUPERPIN sub-agent specifications | `agent_name` |

### Evolution Pipeline (Absorbed from MCP)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `evolution_stats` | Evolution coverage dashboard | — |
| `search_evolved` | FTS5 search across evolved sections | `query`, `source_type`, `limit` |
| `cross_refs` | Query cross-reference network | `query`, `ref_type`, `limit` |
| `convergence_status` | Knowledge base convergence status | — |

### System & Master Data (Absorbed from MCP)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `stats_extended` | Extended stats with graph/rule/risk counts | — |
| `self_test` | Diagnostic self-tests (DB, FTS5, graphs) | — |
| `ingest_csv` | Ingest CSV datasets (BLOCKED — use exec_python) | `data_dir`, `dataset` |
| `query_master` | Search master CSV data | `query`, `dataset`, `limit` |

### Advanced Intelligence (NEXUS-Only Upgrades)
| Action | Purpose | Key Parameters |
|--------|---------|---------------|
| `vector_search` | REAL vector similarity search via LanceDB (FTS5 fallback) | `query`, `top_k` |
| `self_audit` | Data quality audit with 0-100 score | — |
| `evidence_chain` | Trace evidence chain for a claim | `claim` |
| `compute_deadlines` | Michigan court rule deadline calculator | `trigger_event`, `trigger_date` |
| `red_team` | Red-team validate claim strength | `claim` |

## Connection Pool

The daemon maintains a `ConnectionPool` singleton with lazy initialization:
- **SQLite:** WAL mode, 60s busy_timeout, 32MB cache, 256MB mmap, NORMAL sync
- **DuckDB:** In-memory with `sqlite_scanner` ATTACH to litigation_context.db (READ_ONLY)
- **LanceDB:** Opens first table from `00_SYSTEM/engines/semantic/lancedb_store/`

All connections opened ONCE and reused for entire session lifetime.

## FTS5 Safety

All FTS5 queries go through `sanitize_fts5()`:
```python
re.sub(r'[^\w\s*"]', ' ', query).strip()
```
On ANY FTS5 error → automatic LIKE fallback with parameterized bind.

## Extension Integration (v7.2 — WIRED AND ACTIVE)

`extension.mjs` manages daemon lifecycle automatically:
```js
// Spawn once on session start:
startDaemon(); // spawns nexus_daemon.py, waits for {"status":"ready"}

// All tool handlers route through daemon:
callDaemon({action: "query", sql: "...", params: [...]})  // UUID correlated
queryDB(request)    // wrapper: {ok:false} → error string (for formatResult)
callBridge(payload) // wrapper: passthrough (for bridge formatters)

// Auto-restart on crash: exponential backoff, max 5 restarts
// Kill on process exit: process.once("exit", cleanup)
```

## Files

| File | Path | Purpose |
|------|------|---------|
| Daemon (active) | `.github/extensions/singularity/nexus_daemon.py` | Extension subprocess |
| Daemon (backup) | `scripts/nexus_daemon.py` | Permanent copy |
| Extension | `.github/extensions/singularity/extension.mjs` | Copilot CLI extension |
| Legacy helper | `.github/extensions/singularity/query_helper.py` | REPLACED by daemon (archive to 11_ARCHIVES/) |
| Legacy bridge | `.github/extensions/singularity/lexos_bridge.py` | REPLACED by daemon (archive to 11_ARCHIVES/) |
| Extension backup | `scripts/extension_v7.2.mjs` | Permanent backup of v7.2 with daemon transport |

## Upgrading the Daemon

When adding new actions:
1. Add handler function: `def handle_new_action(req): ...`
2. Register in `HANDLERS` dict: `"new_action": handle_new_action`
3. Add corresponding tool in `extension.mjs` that routes to the action
4. Reload extension: `/clear` in Copilot CLI
5. Update this instruction file with the new action

## Error Recovery

- If daemon crashes: extension.mjs should detect EOF on stdout and respawn
- If DB locked: 60s busy_timeout handles WAL contention
- If DuckDB unavailable: graceful fallback to SQLite for analytics queries
- If LanceDB unavailable: semantic search disabled, keyword search still works
- Log file: `%TEMP%/nexus_daemon.log` (stderr redirected to avoid JSON-RPC corruption)
