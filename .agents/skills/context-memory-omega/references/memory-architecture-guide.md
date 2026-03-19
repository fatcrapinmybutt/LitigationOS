# Memory Architecture Guide — LitigationOS

## Overview

LitigationOS uses three distinct memory systems, each with different persistence,
scope, and retrieval characteristics. Choosing the wrong system for a given need
is the most common source of memory-related bugs.

---

## Memory System 1: Session SQL (Per-Session, Ephemeral)

**Storage**: SQLite database created fresh per Copilot session.
**Scope**: Current session only — destroyed when session ends.
**Access**: `sql` tool with `database: "session"`.

### When to Use
- Task tracking (todos table)
- Intermediate computation results
- Agent result caching (survives context compaction within session)
- Batch processing state

### Pre-existing Tables
- `todos`: id, title, description, status, created_at, updated_at
- `todo_deps`: todo_id, depends_on

### Custom Tables
Create any tables needed for the current workflow:
```sql
CREATE TABLE agent_results (
    agent_id TEXT PRIMARY KEY,
    role TEXT,
    findings TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Lifecycle
- Created at session start
- Available throughout the session
- Destroyed at session end — nothing persists

---

## Memory System 2: store_memory (Cross-Session, Permanent)

**Storage**: Copilot's built-in memory store (managed by the CLI runtime).
**Scope**: All future sessions — permanent until manually removed.
**Access**: `store_memory` tool (write), automatically loaded on session start.

### When to Use
- Codebase conventions that won't change (e.g., "Use WAL mode for all SQLite")
- Verified build/test commands
- Architecture decisions
- User preferences

### What NOT to Store
- DB statistics (row counts, table counts) — these change constantly
- File paths that may move
- Session-specific state
- Anything with a timestamp dependency

### Storage Contract
Each memory requires:
- `subject`: 1-2 word topic (e.g., "SQLite patterns")
- `fact`: <200 char statement
- `citations`: Source file:line or "User input: ..."
- `reason`: 2-3 sentences explaining future utility
- `category`: bootstrap_and_build | user_preferences | general | file_specific

### Staleness Detection
Before trusting any stored memory in a critical path:
1. Check the citation — does the source still exist?
2. Verify the fact against current state (run the command, query the DB)
3. If stale, the memory cannot be updated — store a new superseding memory

---

## Memory System 3: agent_memory MCP (Structured, Searchable)

**Storage**: Persistent memory database managed by the agent-memory MCP server.
**Scope**: All sessions — permanent, searchable, categorized.
**Access**: MCP tools: `store`, `retrieve`, `search`.

### When to Use
- Architecture decisions with full context
- Pattern observations across multiple sessions
- Cross-session project state

### Key Differences from store_memory
| Aspect | store_memory | agent_memory MCP |
|--------|-------------|-----------------|
| Retrieval | Auto-loaded at session start | On-demand via MCP search |
| Dedup | None — duplicates accumulate | None — duplicates accumulate |
| Structure | Flat key-value | Categorized with metadata |
| Search | Not directly searchable | Full-text search via MCP |

---

## Memory System 4: session_store (Read-Only History)

**Storage**: Global SQLite DB containing ALL past session data.
**Scope**: Read-only access to historical sessions.
**Access**: `sql` tool with `database: "session_store"`.

### When to Use
- "What did I work on last week?"
- "How did I handle X before?"
- Finding prior approaches to similar problems

### Key Tables
- `sessions`: id, cwd, repository, branch, summary, timestamps
- `turns`: session_id, turn_index, user_message, assistant_response
- `checkpoints`: session_id, title, overview, work_done
- `session_files`: session_id, file_path, tool_name
- `search_index`: FTS5 virtual table for full-text search

### Search Strategy
Use FTS5 with query expansion (keyword-based, not semantic):
```sql
SELECT content, session_id FROM search_index
WHERE search_index MATCH 'memory OR recall OR context OR session'
ORDER BY rank LIMIT 10;
```

---

## Retrieval Priority Order

When an agent needs information, check sources in this order:

1. **Live source** (DB query, file read, command execution) — always freshest
2. **Session SQL** — current session state, recently cached results
3. **store_memory** — cross-session facts (verify before trusting)
4. **agent_memory MCP** — structured historical knowledge
5. **session_store** — past session summaries and patterns

Never skip step 1 for critical data (filings, evidence, deadlines).

---

## Anti-Patterns

### Memory Hoarding
Storing everything "just in case" pollutes retrieval and wastes context window.
**Rule**: Only store facts meeting ALL criteria: actionable, independent of current task,
unlikely to change, can't be inferred from code, contains no secrets.

### Stale Memory Reliance
Using stored DB statistics in filings without re-querying.
**Rule**: Every stat in a filing must have a traceable, same-session DB query.

### Memory System Confusion
Writing to store_memory when session SQL is appropriate, or vice versa.
**Rule**: If the fact is session-specific → session SQL. If it's permanent → store_memory.
