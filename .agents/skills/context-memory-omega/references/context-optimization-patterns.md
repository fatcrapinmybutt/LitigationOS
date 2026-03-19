# Context Optimization Patterns — LitigationOS

## Overview

The context window is the scarcest resource in an AI-assisted litigation workflow.
A 200K token window sounds large, but loading memories + session state + conversation
history + agent results + tool outputs can consume 60%+ before productive work begins.
These patterns maximize the useful signal in every token.

---

## Pattern 1: Token Budgeting

Allocate context window capacity deliberately, not reactively.

### Recommended Budget Allocation
| Component | Max Allocation | Notes |
|-----------|---------------|-------|
| System instructions | 15-20% | Custom instructions, AGENTS.md, skill content |
| Conversation history | 20-25% | Recent turns, compresses older turns |
| Stored memories | 5-10% | Auto-loaded store_memory facts |
| Tool outputs | 30-40% | File views, grep results, DB queries, agent results |
| Working space | 15-20% | Room for reasoning and response generation |

### Monitoring
There's no direct token counter available. Watch for these signs of exhaustion:
- Context compaction notifications (system is dropping content)
- Agent results that were readable becoming unavailable
- Earlier conversation context being forgotten

---

## Pattern 2: Selective Loading

Load only what the current task needs, not everything available.

### Good: Targeted Query
```sql
SELECT claim_id, claim_type, status FROM claims
WHERE vehicle_name = 'Lane A - Custody' AND status = 'active'
LIMIT 20;
```

### Bad: Full Table Dump
```sql
SELECT * FROM claims;  -- 10K+ rows, most irrelevant to current task
```

### For File Reading
- Use `view` with `view_range` to read only relevant sections
- Use `grep` to find the specific lines needed, not `view` on entire large files
- When exploring, use `glob` to find files first, then read selectively

---

## Pattern 3: Checkpoint-and-Compress

For long-running operations, periodically checkpoint results to session SQL
and compress the conversation history.

### Checkpoint Pattern
```sql
-- After each significant sub-task completion:
INSERT INTO checkpoints (task_id, phase, summary, data_json)
VALUES ('filing-prep', 'evidence-gathered',
        'Found 47 evidence items for Lane A custody claim',
        '{"evidence_ids": [1,2,3...], "gaps": ["missing_2024_school_records"]}');
```

### Benefits
- Survives context compaction (SQL persists within session)
- Enables crash recovery (resume from last checkpoint)
- Reduces need to keep full history in context

---

## Pattern 4: Agent Result Caching

Agent results are the most vulnerable to context compaction.
Always cache critical results immediately.

### Immediate Cache Pattern
```
1. Agent completes → system notification received
2. IMMEDIATELY call read_agent to get results
3. INSERT key findings into session SQL
4. Now safe to continue — results survive compaction
```

### SQL Cache Table
```sql
CREATE TABLE IF NOT EXISTS agent_cache (
    agent_id TEXT PRIMARY KEY,
    task_description TEXT,
    result_summary TEXT,
    full_result TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Pattern 5: Cross-Session Recall Strategy

When starting a new session on a continuing project, use session_store
strategically rather than loading everything.

### Efficient Recall
```sql
-- Find the most recent relevant session
SELECT s.id, s.summary, s.updated_at
FROM sessions s
WHERE s.repository LIKE '%LitigationOS%'
AND s.summary LIKE '%custody%'
ORDER BY s.updated_at DESC LIMIT 3;

-- Get just the checkpoint summaries (not full conversation)
SELECT title, overview FROM checkpoints
WHERE session_id = 'found-session-id'
ORDER BY checkpoint_number DESC LIMIT 1;
```

### What to Recall
- Last session's final checkpoint (where things left off)
- Any todos left in pending/in_progress state
- Critical decisions or blockers identified

### What NOT to Recall
- Full conversation transcripts from prior sessions
- Intermediate agent results that are no longer relevant
- Superseded plans or abandoned approaches

---

## Pattern 6: Compression Strategies

When context is getting full, compress proactively.

### Lossy Compression (Safe for Most Cases)
- Summarize completed task results into 1-2 sentences
- Drop intermediate steps, keep only inputs and outputs
- Replace full file contents with "File X contains Y at lines N-M"

### Lossless Compression (For Critical Data)
- Move to session SQL (queryable, not in context window)
- Write to temp files (readable via view tool on demand)
- Store structured data as JSON in SQL rather than prose in context

### What NEVER to Compress
- Current task instructions
- Active constraints and non-goals
- Uncommitted code changes
- Unresolved blockers or questions

---

## Pattern 7: MANBEARPIG Startup Optimization

The startup protocol loads significant context. Optimize it:

1. Run `copilot_startup_hook.py --file` — generates STARTUP_REPORT.md
2. Read STARTUP_REPORT.md (summarized, not raw DB queries)
3. Run `session_recall.py recent` — last 5 sessions, summaries only
4. Skip jurisdiction DB enumeration if not needed for current task

### Skip Optional Steps When
- Task is code-only (no litigation data needed)
- Task is a quick fix (< 5 minutes expected)
- Session is a continuation (recall already loaded in prior session)

---

## Pattern 8: Tool Output Management

Tool outputs are the largest context consumers. Manage them actively.

### Output Size Control
| Tool | Size Control | Technique |
|------|-------------|-----------|
| view | view_range | Read only the lines you need |
| grep | head_limit | Cap results at 10-20 matches |
| powershell | Select-Object | Pipe to `-First 50` or `-Last 30` |
| sql | LIMIT | Always limit query results |
| task agents | prompt scope | Be specific about what output you need |

### Large Output Redirect
For outputs > 100 lines, redirect to temp file:
```powershell
git --no-pager diff > C:\Users\andre\LitigationOS\temp\diff.txt
```
Then read selectively with `view` + `view_range`.

---

## Decision Matrix: What to Keep vs. Compress

| Content Type | Keep in Context? | Compress To |
|-------------|-----------------|-------------|
| Current task instructions | YES | — |
| Active code changes | YES | — |
| Recent conversation (last 3-5 turns) | YES | — |
| Agent results (just received) | Cache to SQL | 1-line summary in context |
| Completed sub-task details | NO | SQL checkpoint |
| File contents (already edited) | NO | "Edited file X, lines N-M" |
| DB query results (already used) | NO | "Query returned N rows, key finding: X" |
| Prior session history | NO | "Last session: [summary]" |
