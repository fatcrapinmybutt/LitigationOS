# Ω12 Context Persistence Brain — OMEGA-INFINITY Reference
> Module 12 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Govern context persistence across sessions: the 7-layer architecture, compaction survival, startup protocol, continuity engine, checkpoint strategy, and context window management. This brain ensures no work is lost between sessions and no intelligence degrades over time.

---

## 1. Seven-Layer Persistence Architecture

### 1.1 Architecture Overview

```
╔═══════════════════════════════════════════════════════════════════╗
║              7-LAYER PERSISTENCE ARCHITECTURE                     ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  LAYER 7: CONTEXT_SNAPSHOT files                                  ║
║    └─ Comprehensive state dumps for session handoff               ║
║                                                                   ║
║  LAYER 6: Git commits                                             ║
║    └─ Code changes, session artifacts, handoff markers            ║
║                                                                   ║
║  LAYER 5: Session workspace                                       ║
║    └─ plan.md, checkpoints, session-specific files                ║
║                                                                   ║
║  LAYER 4: litigation_context.db (PERMANENT)                       ║
║    └─ 115 tables, 92K+ evidence quotes, filings, witnesses       ║
║                                                                   ║
║  LAYER 3: store_memory (repository facts)                         ║
║    └─ Conventions, build commands, patterns                       ║
║                                                                   ║
║  LAYER 2: Session store (cross-session, read-only)                ║
║    └─ sessions, turns, checkpoints, session_files, search_index   ║
║                                                                   ║
║  LAYER 1: Session SQL (per-session, ephemeral)                    ║
║    └─ todos, cache, state tracking                                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 1.2 Layer Details

#### Layer 1 — Session SQL (Per-Session)

**Lifetime:** Single session. Destroyed on session end.
**Access:** `sql` tool with `database: "session"`.
**Purpose:** Operational tracking within a session.

Built-in tables:
- `todos` — id, title, description, status (pending/in_progress/done/blocked), created_at, updated_at
- `todo_deps` — todo_id, depends_on (dependency graph)

Common patterns:
```sql
-- Insert descriptive kebab-case todos
INSERT INTO todos (id, title, description) VALUES
  ('resolve-f-vac-placeholders', 'Resolve F-VAC Placeholders',
   'Query evidence_quotes and filing_documents for all [ANDREW_REQUIRED] placeholders in F-VAC filing');

-- Track status transitions
UPDATE todos SET status = 'in_progress' WHERE id = 'resolve-f-vac-placeholders';
UPDATE todos SET status = 'done' WHERE id = 'resolve-f-vac-placeholders';

-- Cache agent results (compaction protection)
CREATE TABLE agent_results (
    agent_id TEXT PRIMARY KEY,
    task TEXT,
    result_summary TEXT,
    completed_at TEXT DEFAULT (datetime('now'))
);
```

#### Layer 2 — Session Store (Cross-Session, Read-Only)

**Lifetime:** Permanent across all sessions.
**Access:** `sql` tool with `database: "session_store"`.
**Purpose:** Historical context recall.

Tables:
- `sessions` — id, cwd, repository, branch, summary, created_at, updated_at
- `turns` — session_id, turn_index, user_message, assistant_response, timestamp
- `checkpoints` — session_id, checkpoint_number, title, overview, history, work_done, technical_details, important_files, next_steps
- `session_files` — session_id, file_path, tool_name, turn_index, first_seen_at
- `session_refs` — session_id, ref_type (commit/pr/issue), ref_value, turn_index, created_at
- `search_index` — FTS5 virtual table for full-text search

**Query expansion strategy** (keyword-based, not semantic):
```sql
-- Use OR for synonyms — FTS5 is keyword-based
SELECT content, session_id, source_type
FROM search_index
WHERE search_index MATCH 'filing OR motion OR brief OR complaint'
ORDER BY rank LIMIT 10;

-- LIKE for broader matching
SELECT DISTINCT s.id, s.branch, substr(t.user_message, 1, 200)
FROM sessions s JOIN turns t ON t.session_id = s.id AND t.turn_index = 0
WHERE t.user_message LIKE '%disqualification%' OR t.user_message LIKE '%MCR 2.003%'
ORDER BY s.created_at DESC LIMIT 20;

-- Find sessions that modified filing files
SELECT s.id, s.summary, sf.file_path
FROM session_files sf JOIN sessions s ON sf.session_id = s.id
WHERE sf.file_path LIKE '%filing%' AND sf.tool_name = 'edit';
```

#### Layer 3 — store_memory (Repository Facts)

**Lifetime:** Permanent, tied to repository.
**Access:** `store_memory` tool.
**Purpose:** Conventions, patterns, and build commands that persist across all sessions.

Criteria for storage:
- Actionable implications for future tasks
- Independent of current session changes
- Unlikely to change over time
- Cannot be inferred from limited code sample
- No secrets or sensitive data

Examples:
- "Use JWT for authentication"
- "Run tests with: python -m pytest tests/ -q"
- "Never use python -c in PowerShell — write to temp file"

#### Layer 4 — litigation_context.db (Permanent Intelligence)

**Lifetime:** Permanent. Central intelligence database.
**Access:** Python scripts, MCP litigation-context server, direct SQLite.
**Location:** `C:\Users\andre\LitigationOS\litigation_context.db`
**Size:** ~10 GB, 115 tables, 92,246 evidence quotes.

Key tables for context persistence:

| Table | Purpose | Rows (approx) |
|-------|---------|---------------|
| `evidence_quotes` | Extracted evidence with quotes, categories, lane assignments | 92,246 |
| `filing_readiness` | Filing package readiness scoring | 17 |
| `filing_packages` | Filing package registry | 10 |
| `witness_list` | Witness intelligence | 15 |
| `pipeline_registry` | Pipeline phase status tracking | 10+ |
| `master_todos` | Cross-session todo items | varies |
| `session_handoff` | Session-to-session work transfer | varies |
| `session_intelligence` | Actionable intelligence from sessions | varies |
| `system_health_log` | Engine health monitoring | varies |
| `narrative_context` | Story and factual context blocks | varies |
| `filing_rule_map` | Authority requirements per filing | varies |
| `filing_cross_reference` | Cross-filing dependencies | varies |
| `filing_vulnerability_scores` | Vulnerability assessment | varies |
| `filing_documents` | Individual documents within packages | varies |

**Connection requirements (ALWAYS set):**
```python
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

#### Layer 5 — Session Workspace

**Lifetime:** Per-session artifacts in `~/.copilot/session-state/`.
**Access:** File tools (view, create, edit).
**Purpose:** Session-specific planning and artifacts.

Files:
- `plan.md` — Prose planning, problem statements, approach notes
- `checkpoints/` — Progress checkpoints
- `files/` — Session-specific generated files

#### Layer 6 — Git Commits

**Lifetime:** Permanent in repository history.
**Access:** `git` commands.
**Purpose:** Code changes, configuration updates, session handoff markers.

**MANDATORY before compaction:** Commit all work-in-progress. Include:
```
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
```

#### Layer 7 — CONTEXT_SNAPSHOT Files

**Lifetime:** Permanent on filesystem.
**Access:** File tools.
**Purpose:** Comprehensive state dumps for session handoff.

Location: `C:\Users\andre\LitigationOS\00_SYSTEM\`
Files: `STARTUP_REPORT.md`, `CONTINUITY_REPORT.md`, `PROGRESS_LOG.md`

---

## 2. Context Compaction Survival Protocol

### 2.1 What Compaction Does

The Copilot CLI runtime compacts (truncates) conversation context when it grows too large. This permanently deletes:
- Earlier conversation turns
- Agent results not yet read
- Intermediate reasoning
- Tool output from early in the session

### 2.2 Compaction Survival Checklist

```
BEFORE COMPACTION HITS (proactive):
  □ Commit all code changes to git
  □ Update session SQL todos status
  □ Cache critical agent results in session SQL
  □ Write progress to 00_SYSTEM\PROGRESS_LOG.md
  □ Insert session_handoff row in litigation_context.db

AFTER COMPACTION (reactive):
  □ Read session SQL todos for current state
  □ Check git log for recent commits
  □ Read PROGRESS_LOG.md for work completed
  □ Query session_store for context
  □ Re-read STARTUP_REPORT.md for system state
```

### 2.3 Agent Result Preservation

```sql
-- After every agent completion, cache results
INSERT INTO agent_results (agent_id, task, result_summary)
VALUES (?, ?, ?);

-- Retrieve after compaction
SELECT * FROM agent_results ORDER BY completed_at DESC;
```

---

## 3. MANBEARPIG Startup Protocol (5 Mandatory Steps)

Execute these as the VERY FIRST ACTION in every new session. Do NOT respond to user until complete.

### Step 1 — Generate Startup Report

```powershell
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file
```

Generates `00_SYSTEM\STARTUP_REPORT.md` with:
- Separation day count
- Deadline urgency scores
- Filing readiness status
- Evidence arsenal counts
- System health
- Recent session summaries

### Step 2 — Read the Report

```
view("C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md")
```

### Step 3 — Recall Past Sessions

```powershell
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py recent
```

Returns recent session summaries for continuity.

### Step 4 — Load Jurisdiction Databases

```powershell
python -c "import sqlite3,os,glob; dbs=glob.glob(r'C:\Users\andre\LitigationOS\databases\*.db'); print(f'{len(dbs)} jurisdiction DBs found:'); [print(f'  {os.path.basename(d)}: {os.path.getsize(d)//1024}KB') for d in dbs]"
```

Jurisdiction-specific databases:
- `court_forms.db` — Michigan SCAO court form intelligence (39 forms)
- `lane_A_custody.db` through `lane_F_appellate.db`
- Specialized databases (10+)

### Step 5 — Report Readiness

Deliver to user: DB status, separation day count, deadline urgency, evidence arsenal size, jurisdiction DB availability.

---

## 4. Session Continuity Engine

### 4.1 Module: session_continuity_engine.py

**Location:** `C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_continuity_engine.py`
**Purpose:** Generates CONTINUITY_REPORT.md with cross-session intelligence.

### 4.2 Session Recall

**Location:** `C:\Users\andre\LitigationOS\00_SYSTEM\local_model\session_recall.py`

```powershell
# Recent sessions
python 00_SYSTEM\local_model\session_recall.py recent

# Search by topic
python 00_SYSTEM\local_model\session_recall.py search "filing deadline"
python 00_SYSTEM\local_model\session_recall.py search "disqualification motion"
```

---

## 5. Checkpoint Strategy

### 5.1 Checkpoint Triggers

| Trigger | Action |
|---------|--------|
| Every 3 agent completions | Update session SQL todos + write PROGRESS_LOG.md |
| Every 10 minutes of autonomous work | Full checkpoint: SQL + filesystem + git commit |
| Before any multi-step operation | Snapshot current state |
| Before expected compaction | Git commit + session handoff entry |
| On GOAWAY/503/timeout | Checkpoint is the ONLY recovery point |

### 5.2 Checkpoint Content

```sql
-- Update todo status
UPDATE todos SET status = 'done' WHERE id = 'task-id';

-- Insert progress entry
INSERT INTO session_state (key, value) VALUES
  ('checkpoint_3', 'Completed: filing QA for F-VAC, F-MSC2, F-DISQv2. Next: authority verification.');
```

### 5.3 Session Handoff Protocol

Write to `litigation_context.db` before session end:

```sql
INSERT INTO session_handoff (
    session_id, work_completed, work_in_progress,
    work_blocked, next_priorities, critical_notes,
    files_created, files_modified, db_rows_added
) VALUES (
    ?, -- session ID
    'Completed: [list work done]',
    'In progress: [list WIP]',
    'Blocked: [list blockers]',
    'Next: [prioritized list]',
    'Critical: [warnings, deadlines, issues]',
    '[list of files created]',
    '[list of files modified]',
    [count of DB rows added]
);
```

---

## 6. Context Window Management

### 6.1 Adaptive Output Routing

| Output Size | Route | Method |
|-------------|-------|--------|
| < 50 lines | Direct pipe | Shell or MCP |
| 50-500 lines | MCP (250KB cap) | exec_command |
| > 500 lines | File redirect → view tool | `command > temp\output.txt` → `view()` |
| Streaming | Task agent | Isolated pipe, own buffer |

### 6.2 Large Output Pattern

```powershell
# Write large output to file
git --no-pager diff > C:\Users\andre\LitigationOS\temp\diff.txt
# Read with view tool (chunked)
# view("C:\Users\andre\LitigationOS\temp\diff.txt", view_range=[1, 200])
```

### 6.3 Context Budget Allocation

| Channel | v3.0 Budget | Use Case |
|---------|-------------|----------|
| Shell pipe | 200 lines (~20KB) | Quick checks only |
| MCP output | 250KB | Builds, tests, queries |
| Agent result | Full + SQL cache | Complex multi-step work |
| File redirect + view | Unlimited (chunked) | Large outputs |
| Session SQL | Unlimited rows | DB analysis, caching |

---

## 7. EAGAIN Prevention and Pipe Architecture

### 7.1 Why This Matters for Context

EAGAIN kills sessions. A killed session loses ALL unsaved context. The persistence architecture exists specifically because sessions can die unexpectedly from:
- `write EAGAIN` — pipe buffer overflow
- `GOAWAY 503` — server timeout (27-40 minutes)
- Context compaction — truncation of early conversation
- OS resource exhaustion — too many processes/file descriptors

### 7.2 Pipe Categories (Context Implications)

| Category | Risk to Context | Mitigation |
|----------|----------------|------------|
| Zero-pipe (view/edit/grep/glob/sql) | ZERO | Always safe — prefer these |
| Isolated-pipe (task agents) | Low — agent dies, main survives | Cache results in session SQL |
| Shared-pipe (powershell) | HIGH — overflow kills entire session | Max 2, output capped |
| MCP (exec_command) | ZERO | subprocess.run() — no pipe risk |

### 7.3 Golden Rule

```
The main session orchestrates with zero-pipe tools.
Command execution delegated to MCP (exec_command) or task agents.
PowerShell used only for truly interactive needs.
This makes EAGAIN structurally impossible.
```

---

## 8. Key Persistence Tables

### 8.1 session_handoff

```sql
CREATE TABLE session_handoff (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    session_date TEXT DEFAULT datetime('now'),
    work_completed TEXT,
    work_in_progress TEXT,
    work_blocked TEXT,
    next_priorities TEXT,
    critical_notes TEXT,
    pipelines_running TEXT,
    files_created TEXT,
    files_modified TEXT,
    db_tables_created TEXT,
    db_rows_added INTEGER DEFAULT 0,
    deadline_alerts TEXT,
    created_at TEXT DEFAULT datetime('now')
);
```

### 8.2 system_health_log

```sql
CREATE TABLE system_health_log (
    id INTEGER PRIMARY KEY,
    engine_name TEXT NOT NULL,
    status TEXT DEFAULT 'UNKNOWN',     -- OK, DEGRADED, DOWN, UNKNOWN
    latency_ms REAL,
    last_check TEXT DEFAULT datetime('now'),
    error_message TEXT,
    version TEXT
);
```

### 8.3 session_intelligence

```sql
CREATE TABLE session_intelligence (
    id INTEGER PRIMARY KEY,
    session_date TEXT,
    category TEXT,                     -- filing, evidence, strategy, system
    intelligence TEXT NOT NULL,        -- Actionable insight
    actionable INTEGER DEFAULT 1,     -- 1=yes, 0=informational
    acted_upon INTEGER DEFAULT 0,     -- 1=done, 0=pending
    source TEXT,                       -- Where discovered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.4 narrative_context

```sql
CREATE TABLE narrative_context (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,            -- background, event, pattern, order
    subcategory TEXT,
    content TEXT NOT NULL,             -- Narrative text block
    source TEXT,                       -- File/document source
    confidence TEXT DEFAULT 'verified', -- verified, probable, uncertain
    lane TEXT,                         -- Case lane
    date_relevant TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT
);
```

### 8.5 master_todos (Cross-Session)

```sql
CREATE TABLE master_todos (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    deadline TEXT,
    lane TEXT,
    assigned_agent TEXT,
    depends_on TEXT,
    blocking_reason TEXT,
    created_by_session TEXT,
    completed_by_session TEXT,
    created_at TEXT DEFAULT datetime('now'),
    started_at TEXT,
    completed_at TEXT,
    error_log TEXT
);
```

---

## 9. Database Chain Verification

On every session start, verify these databases are accessible:

| Database | Path | Purpose |
|----------|------|---------|
| `litigation_context.db` | `C:\Users\andre\LitigationOS\litigation_context.db` | Central intelligence (115 tables) |
| `court_forms.db` | `C:\Users\andre\LitigationOS\databases\court_forms.db` | Michigan SCAO forms |
| `databases/*.db` | `C:\Users\andre\LitigationOS\databases\` | Jurisdiction-specific DBs |
| `master_index.db` | `00_SYSTEM\pipeline\agents\master_index.db` | Agent execution data |
| Session SQL | In-memory per session | Operational tracking |
| Session store | Global read-only | Cross-session history |

### Verification Query

```sql
-- Verify litigation_context.db accessibility
SELECT
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table') AS table_count,
    (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
    (SELECT COUNT(*) FROM filing_readiness) AS filing_vehicles,
    (SELECT COUNT(*) FROM witness_list) AS witnesses,
    (SELECT COUNT(*) FROM pipeline_registry) AS pipeline_phases;
```

---

## 10. Autonomous Run Protocol

### 10.1 Long-Running Session Management

During autonomous runs (>20 minutes), implement these safeguards:

| Interval | Action |
|----------|--------|
| Every 3 agent completions | Update SQL todos + read agent results |
| Every 10 minutes | Write PROGRESS_LOG.md + checkpoint to DB |
| Every 20 minutes | Git commit WIP + session handoff entry |
| On any error | Log to error_log column in master_todos |
| On GOAWAY/timeout | Checkpoint is the ONLY recovery — nothing else survives |

### 10.2 Progress Log Format

Write to `00_SYSTEM\PROGRESS_LOG.md`:

```markdown
## [timestamp] — Session [id]

### Completed
- [task 1]: result
- [task 2]: result

### In Progress
- [task 3]: current state

### Blocked
- [task 4]: reason

### Next
1. [next priority]
2. [next priority]
```

### 10.3 Wave Decomposition

If a request contains >3 independent deliverables:
1. STOP. Decompose into waves of max 3 deliverables.
2. Present wave plan for confirmation.
3. Execute sequentially with checkpoints between waves.
4. 75% of past sessions crashed from trying to process massive requests in one shot.

---

## Key DB Queries

```sql
-- Q1: Last session handoff (what was done last time?)
SELECT session_id, work_completed, work_in_progress,
       next_priorities, critical_notes, deadline_alerts
FROM session_handoff
ORDER BY created_at DESC
LIMIT 1;

-- Q2: Unacted session intelligence
SELECT category, intelligence, source, created_at
FROM session_intelligence
WHERE acted_upon = 0 AND actionable = 1
ORDER BY created_at DESC;

-- Q3: Cross-session file edit frequency
SELECT sf.file_path, COUNT(DISTINCT sf.session_id) AS session_count
FROM session_files sf
JOIN sessions s ON sf.session_id = s.id
WHERE s.repository LIKE '%LitigationOS%' AND sf.tool_name = 'edit'
GROUP BY sf.file_path
ORDER BY session_count DESC
LIMIT 20;
-- (Run against session_store database)

-- Q4: Active pipeline phases
SELECT phase_id, phase_name, status, items_processed, items_failed
FROM pipeline_registry
WHERE status IN ('running', 'partial')
ORDER BY phase_number;

-- Q5: Recent progress by master_todos
SELECT id, title, status, priority, lane, assigned_agent,
       created_at, started_at, completed_at
FROM master_todos
WHERE status != 'done'
ORDER BY priority ASC;
```

---

## Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|-----------|-----------|
| **Ω9 Witness Brain** | Witness data persists in Layer 4 (litigation_context.db) | witness_list survives sessions; session handoff notes witness work |
| **Ω10 Filing Brain** | Filing state tracked in filing_readiness | filing_readiness.status updates persist; session handoff logs filing progress |
| **Ω11 Agent Brain** | Agent results cached in session SQL | master_todos tracks agent-assigned work; pipeline_registry tracks phase status |
| **Ω1 Evidence Brain** | 92K+ evidence_quotes in permanent storage | Evidence persists in Layer 4; new evidence added by pipeline phases |
| **Ω5 Deadline Brain** | Deadlines drive checkpoint urgency | Filing deadlines in filing_readiness.deadline trigger priority escalation |

---

## Anti-Hallucination Rules

- **NEVER skip the startup protocol.** Execute all 5 steps before responding to user.
- **NEVER assume context from a prior session without querying.** Check session_store or session_handoff.
- **NEVER leave agent results unread.** read_agent IMMEDIATELY on completion notification.
- **NEVER skip checkpoints during autonomous runs.** Save every 3 agents or 10 minutes.
- **NEVER hardcode DB statistics.** Run the verification query for current counts.
- **NEVER assume table columns exist.** Run PRAGMA table_info() before first query per table.
- **NEVER process >3 deliverables without wave decomposition.** Past sessions crashed from overload.
