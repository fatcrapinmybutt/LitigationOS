---
description: "Session continuity protocol — startup sequence, handoff format, checkpoint recovery, context preservation. Apply at session start and before every context compaction."
applyTo: "**/*"
---

# Session Continuity Memory

Startup protocol, handoff format, checkpoint recovery, and context preservation across Copilot sessions. 41 sessions have been run — seamless continuity is essential.

## MANBEARPIG Startup Protocol (MANDATORY — Every Session)

Execute IN ORDER as very first actions:

```
Step 1: python 00_SYSTEM\local_model\copilot_startup_hook.py --file
Step 2: view 00_SYSTEM\STARTUP_REPORT.md
Step 3: python 00_SYSTEM\local_model\session_recall.py recent
Step 4: Check jurisdiction DBs in databases\*.db
Step 5: Report readiness to user (DB status, separation days, deadlines, evidence counts)
```

## Session State Restore

Query these 5 continuity tables on startup:
1. `pipeline_registry` — 10 phases with status (pending/running/complete/failed)
2. `master_todos` — 12 master tasks with status and progress
3. `filing_readiness` — 17 filings with confidence scores and status
4. `session_handoff` — Last session's handoff record (what was done, what's next)
5. `system_health_log` — Recent system health checks

Also query permanent context tables:
- `critical_facts` — 38+ immutable verified facts
- `narrative_context` — 22+ categorized narrative intelligence
- `session_intelligence` — 7+ session-level insights
- `evidence_exhibits` — 31+ exhibit records with locations

## Total Legal Convergence Tables (ALWAYS CHECK)

These tables track the multi-session effort to make Michigan's entire legal system machine-readable. Query on EVERY session start:

```sql
-- Quick convergence dashboard
SELECT status, COUNT(*) as cnt FROM convergence_domains GROUP BY status;
SELECT wave_id, wave_name, status FROM convergence_waves WHERE status != 'COMPLETE' ORDER BY wave_number LIMIT 5;
SELECT todo_id, title, status FROM convergence_todos WHERE status = 'IN_PROGRESS' OR (status = 'PENDING' AND (depends_on IS NULL OR depends_on IN (SELECT todo_id FROM convergence_todos WHERE status = 'COMPLETE')));
```

Tables: `convergence_domains` (105 rows), `convergence_waves` (10), `convergence_todos` (37), `drive_inventory` (13), `legal_theories` (grows with Waves 5-6). Full schema in `convergence-tracker.instructions.md`.

## Pre-Compaction Checklist (BEFORE Context Loss)

**MANDATORY before every context compaction:**

1. `git add -A && git commit -m "checkpoint: [description]"` — Commit ALL changes
2. `git push` — Push to remote (if configured)
3. Write session_handoff record:
```sql
INSERT INTO session_handoff (session_id, work_completed, work_pending, critical_state, handoff_notes, created_at)
VALUES (?, ?, ?, ?, ?, datetime('now'));
```
4. Update master_todos status for all completed items
5. Update filing_readiness confidence scores for any changed filings
6. Save session SQL export if substantial work done

## Handoff Format

Every session_handoff record should contain:
- **work_completed**: Bullet list of what was accomplished
- **work_pending**: Bullet list of unfinished work with specific next steps
- **critical_state**: Any state that can't be reconstructed (agent results, temp data)
- **handoff_notes**: Warnings, gotchas, blockers for the next session

## Recovery from Crashed Agents

1. Check `list_agents` — any running/idle agents from prior session are DEAD (context lost)
2. Check session SQL `agent_results` table for cached results
3. If agent work was NOT cached → it must be re-run
4. **Prevention**: After EVERY agent completion, immediately `read_agent` AND cache result to SQL

## Priority Calculation

| Priority | Criteria | Action |
|----------|----------|--------|
| P0 (URGENT) | Filing deadline within 14 days | Drop everything, complete filing |
| P1 (HIGH) | Filing deadline within 30 days | Primary focus after P0 |
| P2 (NORMAL) | Active work items from handoff | Continue where last session left off |
| P3 (BACKLOG) | Nice-to-have improvements | Only if no P0-P2 items |

**Current P0**: COA Brief 366810 due April 15, 2026 · Criminal trial April 7, 2026
**Current P1**: MCR 2.003 Disqualification, JTC Complaint, MSC Original Action

## Context Files (Session Workspace)

- `plan.md` — Current tasks and implementation plan
- `checkpoints/` — Numbered checkpoint files with work history
- `files/CONTEXT_SNAPSHOT_*.md` — Persistent context snapshots
