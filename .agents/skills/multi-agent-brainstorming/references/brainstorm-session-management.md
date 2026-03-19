# Brainstorm Session Management

## Overview

A multi-agent brainstorming session is a resource-intensive, time-bounded process
that must be carefully managed to produce results before GOAWAY timeouts, context
compaction, or EAGAIN failures destroy the work. This guide covers the full
lifecycle from initialization to final disposition.

---

## Session Lifecycle

```
INITIALIZE → DESIGN → REVIEW → SYNTHESIZE → DISPOSITION → PERSIST
    │           │        │          │            │            │
  Setup DB   Designer  Reviewers  Integrator  APPROVED/    Save to
  tables     agent     agents     agent       REVISE/      SQL + file
                                              REJECT
```

### Phase 1: Initialize (2 minutes)

Before any agents spawn, set up the tracking infrastructure:

```sql
-- Create session tracking tables
CREATE TABLE IF NOT EXISTS brainstorm_sessions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    lane TEXT,
    status TEXT DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brainstorm_agents (
    session_id TEXT,
    agent_id TEXT,
    role TEXT,
    status TEXT DEFAULT 'pending',
    findings TEXT,
    spawned_at TIMESTAMP,
    completed_at TIMESTAMP,
    PRIMARY KEY (session_id, role)
);

CREATE TABLE IF NOT EXISTS brainstorm_decisions (
    session_id TEXT,
    decision_num INTEGER,
    decision TEXT,
    alternatives TEXT,
    rationale TEXT,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, decision_num)
);
```

### Phase 2: Design (5-8 minutes)
- Spawn Designer agent with full problem context
- Designer runs the `brainstorming` skill internally
- On completion: `read_agent` immediately, cache result

### Phase 3: Review (8-15 minutes)
- Spawn reviewers (sequential or parallel-3)
- After each reviewer: `read_agent` → INSERT into brainstorm_agents
- Compile consolidated feedback document

### Phase 4: Synthesize (3-5 minutes)
- Spawn Integrator with design + all reviewer feedback
- Integrator resolves conflicts, makes final decisions
- `read_agent` → cache final decisions

### Phase 5: Disposition (1 minute)
- Integrator declares: APPROVED, REVISE, or REJECT
- Update brainstorm_sessions status
- If REVISE: create todos for required changes
- If REJECT: document why, return to brainstorming

### Phase 6: Persist (2 minutes)
- Write final design + Decision Log to session SQL
- Optionally write to filesystem for cross-session access
- Update todos table with next steps

---

## Time Budget Management

Total safe window: ~25 minutes (before GOAWAY 503 risk).

| Phase | Estimated Time | Cumulative | Checkpoint? |
|-------|---------------|-----------|-------------|
| Initialize | 2 min | 2 min | Setup tables |
| Design | 5-8 min | 10 min | ✅ After design output |
| Reviewer 1 (Skeptic) | 3-5 min | 15 min | ✅ After skeptic |
| Reviewer 2 (Guardian) | 3-5 min | 20 min | ✅ After guardian |
| Reviewer 3 (Advocate) | 3-5 min | 25 min | ✅ After advocate |
| Integrator | 3-5 min | 30 min | ⚠️ May exceed GOAWAY |
| Persist | 2 min | 32 min | Final save |

### If Approaching 25 Minutes
1. Save all collected results to session SQL
2. Create a continuation todo with the review state
3. In the next session, query brainstorm_agents to see what's done
4. Resume from the next uncompleted role

---

## EAGAIN Prevention During Brainstorms

### Pre-Session Checklist
```
□ list_agents → running count must be 0
□ list_powershell → active shells ≤ 1
□ No other background tasks running
□ Session SQL tables created
```

### During Session
| Phase | Max Concurrent Agents | Max Shells |
|-------|----------------------|-----------|
| Initialize | 0 | 1 (for setup) |
| Design | 1 | 0 |
| Review (sequential) | 1 | 0 |
| Review (parallel) | 3 | 0 |
| Synthesize | 1 | 0 |

### Critical Rule
Never spawn a review agent while a shell is running a DB query.
Agents use isolated pipes, shells use shared pipes — but combining
3 agents + 1 shell = 4 processes, which is at the safety ceiling.

---

## Output Consolidation

After all agents complete, consolidate into a single deliverable.

### Consolidated Output Template
```markdown
# Brainstorm Session: [Topic]
**Session ID**: [id]
**Lane**: [A-F]
**Date**: [timestamp]
**Disposition**: APPROVED / REVISE / REJECT

## Design Summary
[Final design from Designer, incorporating all revisions]

## Decision Log
| # | Decision | Alternatives | Rationale |
|---|----------|-------------|-----------|
| 1 | [what] | [options] | [why] |

## Review Findings
### Skeptic
- [finding 1]
- [finding 2]

### Constraint Guardian
- [finding 1]

### User Advocate
- [finding 1]

## Integrator Resolution
- Accepted: [list of accepted objections]
- Rejected: [list of rejected objections with rationale]

## Next Steps
- [ ] [action item 1]
- [ ] [action item 2]
```

---

## Checkpointing Best Practices

### What to Checkpoint
- Full design document (after Designer completes)
- Each reviewer's findings (after each reviewer completes)
- Decision Log (after each decision)
- Consolidated feedback (before Integrator runs)

### How to Checkpoint
```sql
-- After each agent completes
UPDATE brainstorm_agents
SET status = 'completed',
    findings = ?,
    completed_at = CURRENT_TIMESTAMP
WHERE session_id = ? AND role = ?;
```

### Checkpoint Verification
Before spawning the next agent, verify the checkpoint was written:
```sql
SELECT role, status FROM brainstorm_agents
WHERE session_id = ?
ORDER BY completed_at;
```

---

## Error Recovery

### Agent Fails Mid-Review
1. Read whatever partial output is available
2. Update brainstorm_agents status to 'failed'
3. Respawn the same role with the same context
4. If it fails again, skip that reviewer and note the gap

### Session Timeout (GOAWAY 503)
1. All in-flight agents are killed
2. On next session: query brainstorm_agents for state
3. Resume from the last uncompleted role
4. Previously completed reviews are preserved in SQL

### Context Compaction Clears Agent Results
1. If you didn't cache to SQL, the results are GONE
2. Must respawn the agent and re-run
3. Prevention: ALWAYS read_agent + INSERT to SQL immediately on completion

---

## Anti-Patterns

### ❌ Starting Without Session Tables
Running agents without SQL tracking means no crash recovery. If the
session dies at minute 20, you lose everything and start over.

### ❌ Deferring read_agent Calls
"I'll read all agent results after the review completes" — context
compaction will eat them first. Read IMMEDIATELY on each notification.

### ❌ Skipping the Integrator
Without arbitration, conflicting reviewer feedback creates decision
paralysis. The Integrator is not optional.

### ❌ Reusing Agent Results Across Sessions
Agent results from a prior session may reference outdated DB state.
If resuming, re-verify key claims against current litigation_context.db.
