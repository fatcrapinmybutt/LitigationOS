---
name: SINGULARITY-session-continuity
version: "1.0.0"
description: "Transcendent session lifecycle management, compaction resilience, and cross-session intelligence continuity for LitigationOS. Use when: session handoff, context compaction recovery, session offload to file, checkpoint management, multi-session work continuity, session startup, plan recovery, finding what was done before, session DNA snapshots, memory architecture, knowledge persistence strategy."
---

# SINGULARITY-session-continuity — Transcendent Session Lifecycle Intelligence

> **Version:** 1.0.0 | **Tier:** CORE | **Domain:** Session Lifecycle · Compaction Resilience · Cross-Session Memory
> **Absorbs:** session-continuity instructions + compaction-resilience protocol + checkpoint strategy
> **Activation:** "session", "handoff", "compaction", "recovery", "checkpoint", "offload", "continuity", "what did I do", "resume", "pick up where"

---

## LAYER 0: THE PROBLEM — WHY THIS SKILL EXISTS

LitigationOS sessions routinely exceed 100+ turns and 600+ checkpoints. At scale:
- **Context compaction** summarizes earlier conversation, destroying investigation context
- **Session resets** lose all working memory not explicitly persisted
- **Agent crashes** lose in-flight results not yet cached
- **Cross-session continuity** requires explicit handoff — nothing is automatic

**The cost of failure:** Andrew repeats testimony (Rule 13 violation), re-investigates persisted facts
(wasted time), loses strategic insights (tactical disadvantage), or worst — court deadlines missed
because the agent "forgot" what was urgent.

**This skill makes session transitions lossless.** Every fact, every finding, every strategic insight
survives compaction, session reset, and even total conversation loss — because it was persisted
to the right layer at the right time.

---

## LAYER 1: FIVE-LAYER MEMORY ARCHITECTURE

### 1.1 Memory Hierarchy (fastest → most durable)

| Layer | Tool | Persistence | Survives Compaction | Survives Session Reset | Survives Fresh Install |
|-------|------|-------------|--------------------|-----------------------|----------------------|
| **L0: Chat Context** | Conversation | None | ❌ No | ❌ No | ❌ No |
| **L1: Session SQL** | `sql` (session DB) | Per-session | ✅ Yes | ❌ No | ❌ No |
| **L2: Plan.md** | `edit`/`view` plan.md | Per-session | ✅ Yes (if read) | ❌ No (but checkpointed) | ❌ No |
| **L3: Memory Store** | `store_memory` / `memory_store` | Permanent | ✅ Yes | ✅ Yes | ❌ No |
| **L4: Litigation DB** | `query_litigation_db` (write) | Permanent | ✅ Yes | ✅ Yes | ✅ Yes (DB file) |
| **L5: Files on Disk** | `create`/`edit` | Permanent | ✅ Yes | ✅ Yes | ✅ Yes |

### 1.2 What Goes Where (Decision Matrix)

| Information Type | Target Layer | Example |
|-----------------|-------------|---------|
| Current task status, todo tracking | **L1** Session SQL | `UPDATE todos SET status='done'` |
| Working plan, approach, phase tracking | **L2** Plan.md | Phase descriptions, blockers, next steps |
| Conventions, preferences, tool routing | **L3** Memory Store | "User prefers exec_python over PowerShell" |
| Evidence quotes, testimony, facts | **L4** Litigation DB | `INSERT INTO evidence_quotes ...` |
| Filing drafts, analysis reports | **L5** Files on Disk | `05_FILINGS/...`, `04_ANALYSIS/...` |
| Temporary investigation notes | **L0** Chat Context | Intermediate reasoning (acceptable to lose) |

### 1.3 The Golden Rule

> **If losing it would make Andrew repeat himself or re-do work, it MUST be in L3+ BEFORE the next tool call.**

Corollary: Never accumulate 3+ discoveries in L0 without flushing to L4. Compaction can strike
between ANY two tool calls.

---

## LAYER 2: SESSION DNA — COMPACT STATE SNAPSHOT

### 2.1 Session DNA Format

Session DNA is a machine-parseable snapshot that captures the COMPLETE state of a session
in a format that a fresh session can consume in < 30 seconds. It lives at the TOP of plan.md
and in the handoff document.

```markdown
## SESSION DNA (v1.0)
- **Session ID:** {session_id}
- **Started:** {timestamp}
- **Turns:** {turn_count}
- **Checkpoints:** {checkpoint_count}
- **Phase:** {current_phase_name}
- **Separation Days:** (today - 2025-07-29).days — COMPUTE DYNAMICALLY
- **Active Lanes:** A (custody), D (PPO), E (judicial), F (appellate), CRIMINAL
- **Overdue Filings:** {count} — {list}
- **Next Deadline:** {date} — {description}
- **DB Stats:** evidence_quotes={n}, timeline_events={n}, authority_chains_v2={n}
- **Disk:** C:\ {free}GB free, D:\ {free}GB free
- **Blockers:** {list or "none"}
- **Last Completed:** {description of last completed task}
- **In Progress:** {description of current work}
- **User's Last Request:** {verbatim or close paraphrase}
```

### 2.2 DNA Generation Protocol

Generate Session DNA by querying these sources IN ORDER:

```sql
-- 1. Session todos status
SELECT status, COUNT(*) FROM todos GROUP BY status;

-- 2. Active work
SELECT id, title, status FROM todos WHERE status = 'in_progress';

-- 3. Pending work (ready to start)
SELECT t.id, t.title FROM todos t WHERE t.status = 'pending'
AND NOT EXISTS (SELECT 1 FROM todo_deps td JOIN todos dep ON td.depends_on = dep.id
    WHERE td.todo_id = t.id AND dep.status != 'done') LIMIT 10;
```

```python
# 4. DB stats (use NEXUS tools)
intel_dashboard()       # evidence counts, separation counter
check_deadlines()       # filing deadlines with urgency
check_disk_space()      # drive health
```

### 2.3 DNA Refresh Triggers

Regenerate Session DNA when:
- Starting a new session (mandatory)
- Recovering from compaction (mandatory)
- Completing a major phase (recommended)
- User asks "where are we?" (mandatory)
- Every 20 turns (recommended)

---

## LAYER 3: SESSION OFFLOAD PROTOCOL

### 3.1 When to Offload

Offload when ANY of these are true:
- Checkpoint count > 500 (compaction frequency is destroying productivity)
- User requests session reset
- Context quality has degraded (agent repeating questions, losing track of tasks)
- Major phase boundary (natural breakpoint)

### 3.2 Offload Document Structure

The offload document is a comprehensive handoff file placed on the Desktop. It must be
self-contained — a fresh session reading ONLY this file should be able to resume work
with zero loss.

```markdown
# SESSION HANDOFF — {date} — {session_description}

## SESSION DNA
{paste Session DNA here}

## WHAT WAS ACCOMPLISHED (ordered by impact)
1. {highest impact accomplishment with specifics}
2. {second highest}
...

## WHAT IS IN PROGRESS (incomplete work)
1. {task} — Status: {%} — Next step: {specific action}
2. {task} — Status: {%} — Blocked by: {blocker}
...

## WHAT THE USER EXPLICITLY REQUESTED (still pending)
1. {verbatim request} — Status: {not started / partial}
2. {verbatim request} — Status: {not started / partial}
...

## CRITICAL DISCOVERIES (things that change strategy)
1. {discovery} — Persisted to: {DB table + row IDs}
2. {discovery} — Persisted to: {file path}
...

## CORRECTIONS & FACTUAL UPDATES
- {correction}: {old wrong fact} → {correct fact} — Source: {evidence}
...

## KEY DB INSERTS THIS SESSION
```sql
-- Evidence quotes added
SELECT id, quote_text, source_file FROM evidence_quotes
WHERE id IN ({list of IDs inserted this session});

-- Timeline events added
SELECT id, event_date, event_description FROM timeline_events
WHERE id IN ({list of IDs inserted this session});
```

## BLOCKERS & WARNINGS
- {blocker with mitigation plan}
...

## FILES MODIFIED THIS SESSION
| File | Action | Description |
|------|--------|-------------|
| {path} | created/edited | {what changed} |
...

## STRATEGIC CONTEXT (for next session's agent)
{2-3 paragraphs of strategic insight that pure data doesn't capture:
 - What's the user's current emotional state / urgency level?
 - What approach is working vs. what's been tried and failed?
 - What implicit priorities has the user expressed?
 - What questions should the next session ask first?}

## RECOVERY COMMANDS (paste into fresh session)
```
Step 1: Read this handoff document
Step 2: intel_dashboard — verify DB health
Step 3: check_deadlines — verify urgency
Step 4: separation_counter — verify separation days
Step 5: SELECT status, COUNT(*) FROM todos GROUP BY status; — if session DB persists
Step 6: Resume from "WHAT IS IN PROGRESS" section above
```
```

### 3.3 Offload Execution Checklist

```
□ 1. Generate Session DNA
□ 2. Query all session SQL todos for status
□ 3. List all files modified this session (session_files in session_store)
□ 4. List all DB inserts this session (track via SQL or grep INSERT in checkpoints)
□ 5. Write offload document to Desktop: SESSION_HANDOFF_{YYYYMMDD}.md
□ 6. Verify offload document is > 2KB (non-trivial content)
□ 7. Git commit all pending changes: "checkpoint: session offload {date}"
□ 8. Report to user: "Handoff document ready at {path}. Safe to reset."
```

---

## LAYER 4: SESSION RECOVERY PROTOCOL

### 4.1 Fresh Session Startup (MANDATORY — Every Session)

Execute IN ORDER as the very first actions of any new session:

```
STEP 1: Identity Verification (Rule 31)
  - L.D.W. = Andrew's son (MCR 8.119(H) initials only)
  - Emily A. Watson = defendant (NOT Tiffany, NOT Emily Ann)
  - Hon. Jenny L. McNeill = judge (TWO L's)
  - Andrew = pro se plaintiff
  - Tool preferences: NEXUS > exec_python > exec_git > grep/glob > powershell (LAST)

STEP 2: Check for Handoff Document
  - glob "C:\Users\andre\Desktop\SESSION_HANDOFF_*.md" — read most recent
  - If found: consume it as primary context

STEP 3: Query Persistent State
  - intel_dashboard → DB health + separation counter
  - check_deadlines → filing urgency
  - check_disk_space → drive health
  - memory_recall "session" → recent session memories
  - memory_recall "priority" → user priorities

STEP 4: Check Session Store for Recent Sessions
  SELECT s.id, s.summary, s.branch, s.updated_at
  FROM sessions s ORDER BY s.updated_at DESC LIMIT 5;

STEP 5: Read plan.md (if resuming same session)
  - If plan.md exists and is current, treat as authoritative

STEP 6: Report Readiness
  - Separation days (computed dynamically)
  - Overdue deadlines
  - DB stats (evidence_quotes, timeline_events, authority_chains)
  - Last session summary
  - Ask: "What would you like to focus on?"
```

### 4.2 Post-Compaction Recovery (within same session)

When context is compacted mid-session:

```
STEP 1: Read plan.md — this is your lifeline
STEP 2: Query session SQL:
  SELECT * FROM todos WHERE status != 'done' ORDER BY status;
STEP 3: Read most recent checkpoint (session workspace checkpoints/)
STEP 4: Query DB for recent inserts:
  SELECT MAX(rowid) FROM evidence_quotes;  -- compare to pre-compaction
  SELECT MAX(rowid) FROM timeline_events;
STEP 5: Resume from plan.md "In Progress" section
STEP 6: Do NOT re-investigate facts already in DB — query first, investigate only if missing
```

### 4.3 Agent Crash Recovery

When a sub-agent dies mid-task:

```
STEP 1: list_agents → check status (completed/failed/idle)
STEP 2: read_agent → retrieve partial results (if any)
STEP 3: Check if results were cached to SQL:
  SELECT * FROM agent_results WHERE agent_name = ?;
STEP 4: If no cached results → re-run the agent with same prompt
STEP 5: If cached → use cached results, skip re-run
STEP 6: ALWAYS cache agent results to SQL immediately after read_agent
```

---

## LAYER 5: CONTINUOUS PERSISTENCE TRIGGERS

### 5.1 Automatic Persistence Points

Persist state to L3+ at EVERY one of these triggers:

| Trigger | What to Persist | Where |
|---------|----------------|-------|
| User provides testimony/quotes | Verbatim quotes + context | L4: evidence_quotes + timeline_events |
| User corrects a fact | Correction + old value | L3: memory_store + L4: DB update |
| User states a preference | Preference description | L3: memory_store |
| Agent completes a task | Results summary | L1: SQL + plan.md |
| 3 agents completed | Full checkpoint | L2: plan.md + L1: SQL todos |
| Major discovery | Finding + evidence | L4: DB + L2: plan.md |
| Every 10 turns | Session DNA refresh | L2: plan.md header |
| Before any risky operation | Current state snapshot | L2: plan.md + L1: SQL |
| Filing deadline discovered | Deadline details | L4: deadlines table |
| Error/failure occurs | Error + root cause + fix | L3: memory_store |

### 5.2 The 3-Discovery Rule

> **NEVER hold more than 3 unpersisted discoveries in L0 (chat context).**

After discovering fact #3, STOP investigating and FLUSH all 3 to their target layers
before continuing. This rule prevents the catastrophic scenario where compaction
destroys 10+ accumulated findings.

### 5.3 User Testimony = Highest Priority Persistence

When the user provides verbatim quotes, hearing testimony, or witness statements:

```python
# IMMEDIATELY — before ANY other action (Rule 13)
INSERT INTO evidence_quotes (quote_text, source_file, category, lane, ...)
VALUES (?, 'user_testimony_YYYYMMDD', ?, ?, ...);

INSERT INTO timeline_events (event_date, event_description, source, ...)
VALUES (?, ?, 'user_testimony', ...);

# THEN verify
SELECT id FROM evidence_quotes WHERE source_file = 'user_testimony_YYYYMMDD'
ORDER BY id DESC LIMIT 5;
```

The user should NEVER have to repeat themselves. If they do, it's a skill violation.

---

## LAYER 6: CROSS-SESSION INTELLIGENCE QUERIES

### 6.1 Mining Past Sessions (session_store)

```sql
-- What has been worked on recently?
SELECT s.id, s.summary, s.branch, s.updated_at
FROM sessions s ORDER BY s.updated_at DESC LIMIT 10;

-- Full-text search across all session content
SELECT content, session_id, source_type
FROM search_index
WHERE search_index MATCH 'evidence OR harvest OR police OR alienation'
ORDER BY rank LIMIT 20;

-- What files were edited in past sessions?
SELECT sf.file_path, COUNT(DISTINCT sf.session_id) as sessions,
       GROUP_CONCAT(DISTINCT sf.tool_name) as tools
FROM session_files sf
GROUP BY sf.file_path ORDER BY sessions DESC LIMIT 30;

-- Find sessions that worked on a specific topic
SELECT DISTINCT s.id, s.summary, substr(t.user_message, 1, 200) as ask
FROM sessions s JOIN turns t ON t.session_id = s.id AND t.turn_index = 0
WHERE t.user_message LIKE '%police%' OR t.user_message LIKE '%report%'
ORDER BY s.created_at DESC LIMIT 20;

-- Find commits and PRs from sessions
SELECT s.id, s.summary, sr.ref_type, sr.ref_value
FROM sessions s JOIN session_refs sr ON s.id = sr.session_id
ORDER BY sr.created_at DESC LIMIT 20;
```

### 6.2 Query Expansion (CRITICAL for keyword-based search)

Session store uses FTS5 (keyword search), NOT vector/semantic search. You must expand concepts
into multiple keyword variants:

| Concept | Search Terms |
|---------|-------------|
| Evidence work | `evidence OR harvest OR scan OR hunt OR extract OR ingest` |
| Filing work | `filing OR motion OR brief OR draft OR packet OR MCR` |
| Bug fixes | `bug OR fix OR error OR crash OR broken OR debug OR fail` |
| Database work | `database OR DB OR SQL OR table OR schema OR migrate OR index` |
| UI work | `UI OR render OR display OR component OR visualization OR D3 OR graph` |
| Performance | `performance OR slow OR fast OR optimize OR cache OR memory OR speed` |

### 6.3 Permanent Memory (memory_store)

```python
# Store a durable fact
store_memory(
    subject="session-pattern",
    fact="Sessions over 500 checkpoints need offload — compaction destroys context",
    citations="User input: 'do you want to offload the conversation history?'",
    reason="This pattern recurred in 3+ sessions. Future sessions should proactively "
           "suggest offload when checkpoint count exceeds 400."
)

# Recall stored memories
memory_recall(query="session compaction offload")
memory_list(subject="session-pattern")
```

---

## LAYER 7: HANDOFF DOCUMENT GENERATION ENGINE

### 7.1 Automated Handoff Builder

When the user says "offload" or "handoff" or "reset the convo", execute this protocol:

```
PHASE A: GATHER (5 parallel queries)
  1. intel_dashboard → DB stats + separation counter
  2. check_deadlines → all deadlines with urgency
  3. Session SQL → todos status distribution
  4. plan.md → current plan content
  5. memory_list → recent memories

PHASE B: ANALYZE (sequential)
  1. Identify what was accomplished (from todos marked 'done')
  2. Identify what's in progress (from todos marked 'in_progress')
  3. Identify user's pending requests (from chat context — highest priority)
  4. Identify critical discoveries (from plan.md + DB inserts)
  5. Identify blockers (from todos marked 'blocked' + disk space + deadlines)

PHASE C: SYNTHESIZE (write handoff document)
  1. Generate Session DNA
  2. Write all sections per the Offload Document Structure (Layer 3.2)
  3. Include recovery commands
  4. Include strategic context (the human insight that data alone can't capture)

PHASE D: FINALIZE
  1. Save to Desktop: SESSION_HANDOFF_{YYYYMMDD}.md
  2. Git commit pending changes
  3. Report to user with file path and summary
```

### 7.2 Handoff Quality Gates

A handoff document PASSES only when:

| Gate | Check | Method |
|------|-------|--------|
| **Completeness** | All 10 sections present | Grep for section headers |
| **DNA present** | Session DNA block at top | Check for `## SESSION DNA` |
| **Pending requests listed** | User's explicit asks captured | Manual review |
| **DB inserts documented** | Row IDs for new evidence | SQL verification |
| **Recovery commands work** | Steps 1-6 are executable | Manual review |
| **Strategic context > 100 words** | Captures human insight | Word count |
| **No stale data** | Separation counter is dynamic formula, not hardcoded | Grep for frozen counts |
| **File > 3 KB** | Non-trivial content | File size check |

---

## LAYER 8: COMPACTION-IMMUNE PATTERNS

### 8.1 The Persistence Pyramid

```
                    ┌─────────────┐
                    │  L0: CHAT   │  ← Ephemeral (lost on compaction)
                    │  Context    │
                   ┌┴─────────────┴┐
                   │  L1: SESSION  │  ← SQL todos, agent_results
                   │  Database     │     (survives compaction, lost on reset)
                  ┌┴───────────────┴┐
                  │  L2: PLAN.MD    │  ← Working plan + Session DNA
                  │  + Checkpoints  │     (survives compaction if read)
                 ┌┴─────────────────┴┐
                 │  L3: MEMORY STORE  │  ← Permanent conventions/facts
                 │  (store_memory)    │     (survives everything)
                ┌┴───────────────────┴┐
                │  L4: LITIGATION DB   │  ← Evidence, timeline, authorities
                │  (litigation_context │     (survives everything)
                │   .db)               │
               ┌┴─────────────────────┴┐
               │  L5: FILES ON DISK     │  ← Filings, analyses, reports
               │  (create/edit)         │     (survives everything)
               └───────────────────────┘
```

### 8.2 Anti-Fragile Patterns

| Pattern | Description | Implementation |
|---------|-------------|---------------|
| **Flush-on-3** | Never hold >3 discoveries in L0 | Count unpersisted findings; flush at 3 |
| **Immediate testimony** | User quotes → DB within same turn | INSERT before any analysis (Rule 13) |
| **Plan-as-lifeline** | plan.md always reflects true state | Update after every phase change |
| **SQL-as-queue** | Todos track execution state | UPDATE status before/after each task |
| **Memory-as-convention** | Durable facts in memory_store | store_memory for preferences, corrections |
| **DB-as-truth** | Evidence, timeline, authorities in DB | Query before re-investigating |
| **Files-as-artifacts** | Filings, reports, analyses on disk | Create/edit for permanent output |

### 8.3 Recovery Verification Checklist

After ANY compaction or session restart, verify these before proceeding:

```
□ plan.md read and understood
□ Session DNA current (or regenerated)
□ Separation counter computed dynamically
□ Deadlines checked (any overdue?)
□ User's last request identified
□ In-progress work identified
□ No re-investigation of persisted facts (query DB first)
□ Identity facts verified (Rule 31): L.D.W., Emily A. Watson, McNeill (2 L's)
```

---

## LAYER 9: SESSION METRICS & SELF-MONITORING

### 9.1 Session Health Indicators

| Metric | Healthy | Degraded | Critical |
|--------|---------|----------|----------|
| Checkpoints | < 300 | 300-500 | > 500 (suggest offload) |
| Unpersisted L0 facts | 0-2 | 3 | > 3 (FLUSH NOW) |
| Compaction events | 0-2 | 3-5 | > 5 (offload needed) |
| User repeats self | 0 | 1 | > 1 (Rule 13 violation) |
| Agent crashes | 0 | 1-2 | > 2 (decompose tasks) |
| Shell leaks | 0 | 1 | > 1 (cleanup protocol) |
| Plan.md age (turns since update) | < 10 | 10-20 | > 20 (update NOW) |
| Todo tracking accuracy | 100% | 90-99% | < 90% (audit todos) |

### 9.2 Proactive Offload Suggestion

When metrics indicate degradation, proactively suggest offload:

```
"We're at {N} checkpoints with {M} compaction events. Context quality is degrading.
I recommend we offload to a handoff document and start fresh. This will:
- Preserve all findings in DB (already done)
- Create a comprehensive handoff document on your Desktop
- Allow a clean session with full context window

Want me to build the handoff document?"
```

---

## LAYER 10: ADVANCED PATTERNS

### 10.1 Multi-Session Project Continuity

For projects spanning 5+ sessions (like Grand Unification):

1. **Master plan in plan.md** — Updated each session, never deleted
2. **SQL todos** — Granular task tracking with dependencies
3. **Convergence tables** — `convergence_domains`, `convergence_waves`, `convergence_todos`
4. **Memory milestones** — `store_memory` for each major completion
5. **Handoff chain** — Each session's handoff document references the previous

### 10.2 Parallel Session Awareness

If multiple Copilot sessions might run concurrently:
- SQLite WAL mode handles concurrent reads safely
- Avoid concurrent WRITES to same tables (WAL handles short contention, not sustained)
- Use session_id columns in any session-specific tables
- Check `session_store` for recent sessions before starting heavy work

### 10.3 Emergency Recovery (Total Context Loss)

If ALL session context is lost (no plan.md, no checkpoints, no handoff):

```
STEP 1: memory_recall "" — list ALL stored memories
STEP 2: intel_dashboard — DB health and stats
STEP 3: Session store query for recent sessions
STEP 4: Read most recent Desktop handoff: glob "C:\Users\andre\Desktop\SESSION_HANDOFF_*.md"
STEP 5: Read checkpoints/index.md in session workspace
STEP 6: Ask user: "I've recovered from context loss. Here's what I found: {summary}.
         What should I focus on?"
```

### 10.4 Session DNA Diffing

Compare Session DNA between sessions to track progress:

```
Session N:   evidence_quotes=148,094  timeline_events=70,122
Session N+1: evidence_quotes=185,491  timeline_events=76,484
Delta:       +37,397 evidence quotes  +6,362 timeline events
```

This shows concrete progress and prevents the illusion of activity without results.

---

## ANTI-PATTERNS (VIOLATIONS = CONTEXT LOSS)

| # | Anti-Pattern | Correct Pattern |
|---|-------------|-----------------|
| 1 | Accumulate 5+ findings in chat before persisting | Flush-on-3: persist after every 3 discoveries |
| 2 | Update plan.md only at session end | Update at every phase change + every 20 turns |
| 3 | Rely on chat context for user testimony | INSERT to evidence_quotes IMMEDIATELY (Rule 13) |
| 4 | Re-investigate facts already in DB | Query DB first, investigate only if missing |
| 5 | Skip identity verification on startup | ALWAYS verify L.D.W., Watson, McNeill (Rule 31) |
| 6 | Hardcode separation day count | ALWAYS compute: `(today - 2025-07-29).days` |
| 7 | Leave agent results unread | `read_agent` immediately + cache to SQL |
| 8 | Handoff document missing recovery commands | Recovery commands are MANDATORY in every handoff |
| 9 | Session > 500 checkpoints without offload | Proactively suggest offload at 400 |
| 10 | Generic "where were we?" after compaction | Read plan.md → query todos → query DB → THEN ask user |
| 11 | Store transient investigation notes in memory_store | memory_store is for DURABLE facts only |
| 12 | Forget to update SQL todo status | `in_progress` before starting, `done` after completing |
| 13 | Handoff without strategic context | Strategic context captures human insight data can't |
| 14 | Offload document < 2 KB | A real handoff has substance — minimum 3 KB |
| 15 | Skip disk space check on startup | C:\ space gates ALL heavy operations |

---

## QUICK REFERENCE: DECISION MATRIX

| Situation | Action |
|-----------|--------|
| User says "offload" / "reset" / "start fresh" | → Layer 3: Full Offload Protocol |
| Context just compacted | → Layer 4.2: Post-Compaction Recovery |
| New session starting | → Layer 4.1: Fresh Session Startup |
| User provides testimony | → Layer 5.3: Immediate Persistence |
| 3+ discoveries accumulated | → Layer 5.2: Flush-on-3 |
| Agent crashed mid-task | → Layer 4.3: Agent Crash Recovery |
| "What did we do last time?" | → Layer 6: Cross-Session Queries |
| Checkpoint count > 400 | → Layer 9.2: Proactive Offload Suggestion |
| Total context loss | → Layer 10.3: Emergency Recovery |
| Multi-session project | → Layer 10.1: Project Continuity |

---

*END OF SINGULARITY-session-continuity v1.0.0 — 5-Layer Memory Architecture · Session DNA · Lossless Handoff · Compaction-Immune Patterns*
