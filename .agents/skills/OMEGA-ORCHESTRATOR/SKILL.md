---
name: OMEGA-ORCHESTRATOR
description: >-
  Use when executing multi-step workflows, decomposing complex tasks into waves,
  managing checkpoint/resume across agent fleets, tracking progress via SQL todos,
  dispatching parallel agents with EAGAIN-safe concurrency, detecting convergence
  across case lanes, and recovering from agent failures. Covers the full orchestration
  lifecycle from task intake through wave planning, parallel dispatch, error recovery,
  and completion verification. LitigationOS-specific: 6 case lanes, 16-phase pipeline,
  155+ agent fleet, 3-agent concurrency ceiling, SQL-first progress tracking.
category: discipline
version: "2.0.0"
triggers:
  - orchestration
  - workflow
  - task decomposition
  - wave planning
  - checkpoint
  - resume
  - parallel dispatch
  - progress tracking
  - agent fleet
  - pipeline
  - convergence
  - error recovery
  - context management
  - batch processing
  - todo tracking
  - multi-step
  - autonomous
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Convergence (Cross-Lane)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County; Michigan COA; Michigan Supreme Court"
case: Pigors v Watson
dependencies: []
metadata:
  tier: 2 (Agent Intelligence)
  fused_skills: 17
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
  courts: [14th Circuit, Michigan COA, Michigan Supreme Court, USDC WDMI, JTC]
---

# ⚙️ OMEGA-ORCHESTRATOR ⚙️

> **TIER 2 — Agent Intelligence: Workflow Orchestration Engine**
> **Pipeline:** Task Intake → Decompose → Wave Plan → Dispatch → Monitor → Checkpoint → Converge → Deliver
> **Case:** Pigors v Watson · 6 lanes · 155+ agents · 16-phase pipeline · SQL-tracked progress
> **Iron Law:** Max 3 concurrent agents. Checkpoint every 3 completions. GOAWAY kills work — save constantly.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                       OMEGA-ORCHESTRATOR v2.0                            ║
║               17 Skills → 8 Modules → 1 Orchestration Engine            ║
║                                                                          ║
║  O1  Task Decomposition ──┐                                              ║
║  O2  Wave Planning ───────┤→ O5 Parallel Dispatch ──→ O7 Progress Track  ║
║  O3  Checkpoint/Resume ───┘        ↓                        ↓            ║
║  O4  Context Management ──→ O6 Error Recovery ──→ O8 Convergence Detect  ║
║                                    ↑                        ↓            ║
║  EAGAIN Prevention ────────────────┘                   DELIVERED ✓       ║
║                                                                          ║
║  Agents: max 3 concurrent (isolated pipes) · 0.5s cooldown              ║
║  Shells: max 2 concurrent (shared pipes) · 2s cooldown                  ║
║  DB: litigation_context.db · Session SQL todos · WAL mode               ║
║  Recovery: L0→L1→L2→L3→L4→L5 dynamic throttle                          ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 17 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `executing-plans` | Step-by-step plan execution with verification gates |
| 2 | `workflow-automation` | Multi-step workflow definition and execution |
| 3 | `task-decomposition` | Breaking complex requests into atomic deliverables |
| 4 | `parallel-dispatch` | Concurrent agent spawning with pipe isolation |
| 5 | `checkpoint-resume` | Crash-safe progress persistence and recovery |
| 6 | `context-management` | Context window optimization and compaction survival |
| 7 | `agent-orchestration-multi-agent-optimize` | Multi-agent coordination and workload distribution |
| 8 | `agent-orchestration-improve-agent` | Agent performance analysis and prompt refinement |
| 9 | `agent-evaluation` | Behavioral testing and reliability metrics |
| 10 | `conductor-orchestration` | Fleet-level task routing and priority management |
| 11 | `batch-processing` | Batch item tracking with SQL-driven state machines |
| 12 | `progress-reporting` | Incremental progress reports and status dashboards |
| 13 | `error-recovery-patterns` | Exponential backoff, retry, and graceful degradation |
| 14 | `convergence-detection` | Cross-lane dependency resolution and merge detection |
| 15 | `pipeline-orchestration` | 16-phase pipeline sequencing and phase gating |
| 16 | `autonomous-execution` | Long-running autonomous sessions with GOAWAY resilience |
| 17 | `context-architect` | Multi-file change planning and dependency identification |

---

## ═══════════════════════════════════════════════════════════════
## MODULE O1: TASK DECOMPOSITION
## ═══════════════════════════════════════════════════════════════
*Absorbs: task-decomposition, context-architect, executing-plans*

### Phase O1-1: Request Analysis

Every incoming request must be analyzed BEFORE any work begins:

```
INPUT: User request (natural language)
│
├─ Count independent deliverables
│   ├─ ≤3 deliverables → Execute directly (single wave)
│   └─ >3 deliverables → STOP. Decompose into waves (see O2)
│
├─ Identify dependencies between deliverables
│   ├─ Independent → Can parallelize
│   └─ Dependent → Must sequence (todo_deps table)
│
├─ Estimate complexity per deliverable
│   ├─ Simple (1 agent, <5 min) → task agent
│   ├─ Medium (1-2 agents, 5-15 min) → general-purpose agent
│   └─ Complex (multi-agent, >15 min) → Wave decomposition required
│
└─ Check for prior work (MANDATORY — search before creating)
    ├─ fd --type f "<keyword>" across all drives
    ├─ rg -l "<keyword>" across codebase
    └─ SELECT * FROM session_store search_index WHERE MATCH '<keyword>'
```

### Phase O1-2: SQL Todo Creation

Every deliverable becomes a tracked todo with enough detail to execute standalone:

```sql
-- Use descriptive kebab-case IDs — NEVER t1, t2, t3
INSERT INTO todos (id, title, description, status) VALUES
  ('custody-motion-draft',
   'Draft Motion to Modify Custody',
   'Draft MCR 3.206 motion citing 40-day withholding (Mar 26 - May 5, 2024). '
   'Query evidence_quotes for withholding incidents. Use Lane A DB. '
   'Template: AKN motion format. Output: court-ready markdown.',
   'pending');

INSERT INTO todos (id, title, description, status) VALUES
  ('custody-motion-exhibits',
   'Assemble Exhibit Pack for Custody Motion',
   'Pull exhibits from evidence_quotes WHERE lane = ''A'' AND claim_type = ''withholding''. '
   'Bates stamp sequentially. Generate exhibit index. Authenticate per MRE 901.',
   'pending');

-- Track dependency: exhibits must complete before final motion assembly
INSERT INTO todo_deps (todo_id, depends_on)
VALUES ('custody-motion-final', 'custody-motion-exhibits');
```

### Phase O1-3: Dependency Graph

Build a DAG (Directed Acyclic Graph) of todo dependencies:

```
custody-motion-draft ─────────────┐
custody-motion-exhibits ──────────┤→ custody-motion-final → custody-motion-qa
custody-motion-authority-check ───┘
```

Query for "ready" todos (no pending dependencies):

```sql
SELECT t.* FROM todos t
WHERE t.status = 'pending'
AND NOT EXISTS (
    SELECT 1 FROM todo_deps td
    JOIN todos dep ON td.depends_on = dep.id
    WHERE td.todo_id = t.id AND dep.status != 'done'
)
ORDER BY t.created_at ASC;
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O2: WAVE PLANNING
## ═══════════════════════════════════════════════════════════════
*Absorbs: batch-processing, pipeline-orchestration, autonomous-execution*

### Phase O2-1: The Wave Rule

**75% of past sessions crashed because the agent tried to process massive requests in one shot.**

```
HARD RULE: If a request contains >3 independent deliverables → STOP.
           Decompose into sequential waves of max 3 deliverables each.
           Present the wave plan. Get confirmation. Execute wave-by-wave.
```

### Phase O2-2: Wave Construction

Group deliverables into waves respecting:
1. **Dependency order** — a wave cannot contain items that depend on incomplete items
2. **Concurrency ceiling** — max 3 agents per wave (EAGAIN prevention)
3. **Lane isolation** — prefer grouping same-lane items (avoid cross-contamination)
4. **Complexity balance** — mix simple + complex items to avoid timeout cascades

**Example: 12-Filing Package Request**

```
Wave 1 (Foundation):
  ├─ [agent-1] custody-motion-evidence-pull (Lane A, ~8 min)
  ├─ [agent-2] ppo-motion-evidence-pull (Lane D, ~6 min)
  └─ [agent-3] appellate-record-inventory (Lane F, ~10 min)

Wave 2 (Drafting — depends on Wave 1):
  ├─ [agent-1] custody-motion-draft (Lane A, ~12 min)
  ├─ [agent-2] ppo-motion-draft (Lane D, ~10 min)
  └─ [agent-3] appellate-brief-outline (Lane F, ~15 min)

Wave 3 (Assembly — depends on Wave 2):
  ├─ [agent-1] custody-motion-final + exhibits (Lane A)
  ├─ [agent-2] ppo-motion-final + exhibits (Lane D)
  └─ [agent-3] appellate-brief-draft (Lane F)

Wave 4 (QA — depends on Wave 3):
  ├─ [agent-1] prefiling-qa-sweep (all lanes)
  ├─ [agent-2] citation-verification (all lanes)
  └─ [agent-3] service-checklist-generation (all lanes)
```

### Phase O2-3: Wave Execution Protocol

```
FOR each wave:
  1. Verify all dependency todos are status='done'
  2. Update wave todos to status='in_progress'
  3. Dispatch agents (max 3, see O5)
  4. Monitor completions (see O7)
  5. Checkpoint after all wave agents complete (see O3)
  6. Update todos to status='done'
  7. Write progress to 00_SYSTEM/PROGRESS_LOG.md
  8. Proceed to next wave
```

### Phase O2-4: GOAWAY / 503 Resilience

GOAWAY errors kill agents after 27-40 minutes. Every wave must be independently resumable:

```
BEFORE each wave:
  - Write wave plan to SQL session_state table
  - Record which todos are in-progress
  - Save any intermediate results to filesystem

AFTER GOAWAY recovery:
  - Read session_state to find interrupted wave
  - Check todo statuses: done items stay done
  - Re-dispatch only pending/in_progress items
  - Never re-process completed work
```

```sql
-- Session state for crash recovery
INSERT OR REPLACE INTO session_state (key, value) VALUES
  ('current_wave', '2'),
  ('wave_2_agents', '["custody-motion-draft", "ppo-motion-draft", "appellate-brief-outline"]'),
  ('wave_2_started_at', datetime('now'));
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O3: CHECKPOINT / RESUME
## ═══════════════════════════════════════════════════════════════
*Absorbs: checkpoint-resume, progress-reporting*

### Phase O3-1: Checkpoint Triggers

Checkpoint MUST fire on these events — no exceptions:

| Trigger | Action |
|---------|--------|
| Every 3 agent completions | Full checkpoint (SQL + filesystem) |
| Every 10 minutes of wall-clock | Time-based checkpoint |
| Before spawning a new wave | Wave boundary checkpoint |
| On any agent failure | Failure checkpoint with error context |
| Before any destructive operation | Safety checkpoint |

### Phase O3-2: Checkpoint Content

```sql
-- Update todo statuses
UPDATE todos SET status = 'done', updated_at = datetime('now')
WHERE id IN ('custody-motion-evidence-pull', 'ppo-motion-evidence-pull');

-- Record checkpoint metadata
INSERT OR REPLACE INTO session_state (key, value) VALUES
  ('last_checkpoint', datetime('now')),
  ('completed_count', '5'),
  ('total_count', '12'),
  ('current_wave', '2'),
  ('failed_items', '[]');
```

### Phase O3-3: Filesystem Checkpoint

Write incremental progress to `00_SYSTEM/PROGRESS_LOG.md`:

```markdown
## Progress Update — [timestamp]
- Wave 1: ✅ COMPLETE (3/3 agents succeeded)
- Wave 2: 🔄 IN PROGRESS (2/3 agents complete, 1 running)
- Wave 3: ⏳ PENDING (blocked on Wave 2)
- Total: 5/12 deliverables complete (42%)
- Next: Waiting for appellate-brief-outline agent to finish
```

### Phase O3-4: Resume Protocol

After a crash (GOAWAY, timeout, context compaction):

```
1. Query todos table: SELECT * FROM todos ORDER BY status, created_at
2. Identify: which items are 'done', 'in_progress', 'pending'
3. Items marked 'in_progress' at crash time → reset to 'pending'
4. Read PROGRESS_LOG.md for last known state
5. Rebuild wave plan from remaining 'pending' items
6. Resume from next incomplete wave
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O4: CONTEXT MANAGEMENT
## ═══════════════════════════════════════════════════════════════
*Absorbs: context-management, context-architect*

### Phase O4-1: Context Window Budget

The context window is a finite resource. Budget it deliberately:

| Category | Target Budget | Strategy |
|----------|--------------|----------|
| System instructions | ~15% | Fixed overhead — cannot reduce |
| Active task context | ~40% | Current wave's todos, code, data |
| Agent results | ~25% | Cache in SQL, summarize in context |
| History / conversation | ~20% | Compacts automatically — save important data to SQL |

### Phase O4-2: Anti-Compaction Defense

Context compaction can wipe agent results at any time. Defense:

```
RULE 1: On EVERY agent completion notification → read_agent IMMEDIATELY
RULE 2: Cache critical results in session SQL:

INSERT INTO session_state (key, value) VALUES
  ('agent_result_custody_draft', '[summary of agent output]');

RULE 3: Write file outputs to disk — they survive compaction
RULE 4: Never rely on "I'll come back to that later" — compaction doesn't wait
```

### Phase O4-3: Sub-Agent Prompt Engineering

Each sub-agent is stateless — it has ZERO knowledge of prior conversation. Every prompt must be self-contained:

```
GOOD prompt (self-contained):
  "Search C:\Users\andre\LitigationOS\litigation_context.db for evidence_quotes
   WHERE lane = 'A' AND claim_type = 'withholding'. The plaintiff is Andrew James Pigors.
   The defendant is Emily A. Watson. Case number 2024-001507-DC.
   Return a markdown table with columns: atom_id, date, content, score."

BAD prompt (context-dependent):
  "Now search for the withholding evidence we discussed earlier."
```

### Phase O4-4: Explore Agent Efficiency

```
ANTI-PATTERN: Call explore → read answer → call explore again with follow-up
              (2 round trips, lost context between calls)

CORRECT: Batch ALL related questions into ONE explore call:
  "Find ALL of the following in the LitigationOS codebase:
   1. How does phase3_classify.py detect MEEK signals?
   2. What tables does evidence_quotes use?
   3. Where is the filing_readiness calculation?
   4. What is the AgentResult contract in agent_base.py?"
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O5: PARALLEL DISPATCH
## ═══════════════════════════════════════════════════════════════
*Absorbs: parallel-dispatch, agent-orchestration-multi-agent-optimize*

### Phase O5-1: Pre-Dispatch Checklist

**MANDATORY before spawning ANY agent:**

```
□ list_agents → count RUNNING agents (exclude completed/idle)
□ Running agents < 3? → Proceed
□ Running agents >= 3? → WAIT for one to complete
□ 0.5-second cooldown between agent spawns
□ Can dispatch up to 3 agents in ONE tool call (isolated pipes)
□ Can dispatch 1 shell + 1 agent in same tool call (different pipe pools)
```

### Phase O5-2: Agent Type Selection

| Task Type | Agent Type | Rationale |
|-----------|-----------|-----------|
| Codebase exploration, Q&A | `explore` | Fast, Haiku model, read-only |
| Build, test, lint, install | `task` | Brief success output, full failure output |
| Complex multi-step work | `general-purpose` | Full toolset, Sonnet model |
| Code review, diff analysis | `code-review` | High signal-to-noise, read-only |
| Filing, evidence, legal work | `general-purpose` + OMEGA skill | Needs full tools + domain knowledge |

### Phase O5-3: Dispatch Patterns

**Pattern A: Independent Parallel (most common)**
```
Three independent tasks → dispatch all 3 in ONE tool call:
  task(agent_type="explore", name="scan-lane-a", prompt="...")
  task(agent_type="explore", name="scan-lane-d", prompt="...")
  task(agent_type="explore", name="scan-lane-f", prompt="...")
```

**Pattern B: Sequential Dependency**
```
Task B depends on Task A's output:
  1. Dispatch Task A (sync mode) → get result
  2. Use Task A's result to parameterize Task B's prompt
  3. Dispatch Task B
```

**Pattern C: Fan-Out / Fan-In**
```
  1. Dispatch 3 parallel explore agents (fan-out)
  2. Wait for all 3 to complete
  3. Merge results
  4. Dispatch 1 general-purpose agent with merged context (fan-in)
```

### Phase O5-4: Background Agent Lifecycle

```
SPAWN:      task(mode="background") → returns agent_id
MONITOR:    read_agent(agent_id, wait=false) → status check
READ:       read_agent(agent_id, wait=true, timeout=60) → get results
FOLLOW-UP:  write_agent(agent_id, message="refine X") → iterative refinement
CLEANUP:    Agent auto-cleans on completion — no manual stop needed

CRITICAL: On completion notification → read_agent IMMEDIATELY
          Context compaction can clear results at any time
```

### Phase O5-5: EAGAIN-Safe Dispatch

```
PRIORITY 1: Zero-pipe tools (view/edit/grep/glob/sql)     = UNLIMITED
PRIORITY 2: MCP (exec_command/exec_python/exec_git)        = UNLIMITED
PRIORITY 3: Task agents (explore/task/general-purpose)      = 4 max
PRIORITY 4: PowerShell (async/sync shells)                  = 2 max

GOLDEN RULE: Route through MCP first. Agents for parallel.
             Shells only for interactive. Zero-pipe for everything else.
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O6: ERROR RECOVERY
## ═══════════════════════════════════════════════════════════════
*Absorbs: error-recovery-patterns, agent-evaluation*

### Phase O6-1: The 7-Layer Error Protocol

Every orchestrated operation follows this cascade:

| Layer | Action | Example |
|-------|--------|---------|
| 1 | Try operation | Dispatch agent, run query |
| 2 | Specific catch → targeted recovery | Agent timeout → re-dispatch with shorter prompt |
| 3 | Broad catch → log + skip + continue | Unknown error → log to SQL, skip item, process next |
| 4 | Checkpoint every N items | Save progress after every 3 agents |
| 5 | Deadman switch (120s no progress) | Self-diagnose: are agents stuck? |
| 6 | Agent retry (3× exponential backoff) | 1s → 2s → 4s between retries |
| 7 | Tier fallback → orchestrator flags | Mark todo as 'blocked', continue with next wave |

### Phase O6-2: Agent Failure Handling

```
Agent fails → classify failure:
│
├─ TIMEOUT (agent ran too long)
│   → Retry with decomposed prompt (split into smaller tasks)
│   → If retry fails → mark todo 'blocked', note reason
│
├─ EAGAIN / pipe error
│   → STOP all spawning immediately
│   → Execute recovery protocol (stop all shells, wait 5s)
│   → Resume at reduced throttle level
│
├─ CONTENT ERROR (agent produced wrong/hallucinated output)
│   → Retry with more specific prompt + explicit constraints
│   → Add anti-hallucination guards to prompt
│
├─ PARTIAL SUCCESS (some deliverables complete, some failed)
│   → Accept completed items, re-queue failed items
│   → Update todos: done for successes, pending for failures
│
└─ TOTAL FAILURE (agent crashed, no output)
    → Increment failure counter
    → 3 consecutive failures on same todo → mark 'blocked'
    → Log failure to PROGRESS_LOG.md
    → Continue with next todo
```

### Phase O6-3: Dynamic Throttle Integration

```
Level 0 — HEALTHY:    Agents: 4, Shells: 2, Cooldown: 0.5s/2s
Level 1 — ELEVATED:   Agents: 4, Shells: 1, Cooldown: 2s/2s
Level 2 — WARNING:    Agents: 3, Shells: 1, Cooldown: 3s/3s
Level 3 — CRITICAL:   Agents: 2, Shells: 0, Cooldown: 5s
Level 4 — EMERGENCY:  Agents: 1, Shells: 0
Level 5 — DEAD:       Agents: 0, Shells: 0, MCP-only

Auto-escalate: Each failure symptom → level + 1
Auto-de-escalate: 3 min stable at current level → level - 1
MCP available at ALL levels — you're never truly stuck.
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O7: PROGRESS TRACKING
## ═══════════════════════════════════════════════════════════════
*Absorbs: progress-reporting, batch-processing*

### Phase O7-1: SQL-First Progress

**ALL progress tracked in SQL todos — not in conversation memory (which compacts).**

```sql
-- Status workflow: pending → in_progress → done | blocked
-- Always update BEFORE starting work:
UPDATE todos SET status = 'in_progress', updated_at = datetime('now')
WHERE id = 'custody-motion-draft';

-- Always update AFTER completing work:
UPDATE todos SET status = 'done', updated_at = datetime('now')
WHERE id = 'custody-motion-draft';

-- Dashboard query:
SELECT
  status,
  COUNT(*) as count,
  GROUP_CONCAT(id, ', ') as items
FROM todos
GROUP BY status;
```

### Phase O7-2: Progress Dashboard Format

Generate after each wave completion:

```
╔══════════════════════════════════════════════════════╗
║          ORCHESTRATION PROGRESS DASHBOARD            ║
╠══════════════════════════════════════════════════════╣
║  Wave: 2 of 4                                        ║
║  Status: 🔄 IN PROGRESS                              ║
║                                                      ║
║  ✅ Done:       5 / 12  (42%)                        ║
║  🔄 Active:     2 / 12  (17%)                        ║
║  ⏳ Pending:    4 / 12  (33%)                        ║
║  🚫 Blocked:    1 / 12  (8%)                         ║
║                                                      ║
║  Agents Running: 2 / 3 max                           ║
║  Throttle Level: L0 (HEALTHY)                        ║
║  Last Checkpoint: 2025-01-15 14:32:00                ║
║  Elapsed: 18 min                                     ║
╚══════════════════════════════════════════════════════╝
```

### Phase O7-3: Traceable Statistics Rule

**Every statistic in progress reports MUST be traceable to a SQL query.**

```
CORRECT:
  "5/12 deliverables complete"
  → SELECT COUNT(*) FROM todos WHERE status = 'done'  →  5
  → SELECT COUNT(*) FROM todos                         → 12

WRONG:
  "Approximately 40% complete" (no query backing this)
  "Most items are done" (vague, unverifiable)
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE O8: CONVERGENCE DETECTION
## ═══════════════════════════════════════════════════════════════
*Absorbs: convergence-detection, conductor-orchestration*

### Phase O8-1: Cross-Lane Convergence

LitigationOS has 6 case lanes. Some evidence and arguments span multiple lanes:

| Convergence Pattern | Lanes | Example |
|--------------------| ------|---------|
| Withholding → PPO violation | A + D | Same withholding incident is custody AND PPO evidence |
| Judicial bias → Appeal ground | E + F | McNeill's conduct is misconduct claim AND appeal issue |
| Housing → Custody impact | B + A | Shady Oaks conditions affect best-interest analysis |
| PPO → Federal §1983 | D + C | PPO due-process violations support §1983 claim |

### Phase O8-2: Lane Cross-Reference Protocol

When processing multi-lane tasks:

```
1. Identify primary lane (where the filing will be submitted)
2. Identify supporting lanes (where evidence originates)
3. Copy evidence references — NEVER move originals across lanes
4. Tag cross-references in SQL:

INSERT INTO session_state (key, value) VALUES
  ('convergence_A_D_withholding',
   'Evidence atom 0016-03 is relevant to both Lane A (custody) and Lane D (PPO). '
   'Primary filing: Lane A motion. Supporting evidence sourced from Lane D PPO record.');
```

### Phase O8-3: Pipeline Phase Convergence

The 16-phase pipeline has natural convergence points:

```
Phases 1-3  (I/O)         → Converge at Phase 4 (Extraction)
Phases 4a-4e (Extraction)  → Converge at Phase 5 (Brain Feed)
Phases 5-6  (Intelligence) → Converge at Phase 7 (Graph Merge)
Phases 7-9  (Synthesis)    → Converge at Phase 10 (Judicial Analysis)
Phases 10-12 (Analysis)    → Converge at Phase 13 (Refinement)
Phases 13-16 (Finalization)→ Converge at DELIVERY
```

### Phase O8-4: Completion Verification

A task is NOT complete until:

```
□ All todos in status = 'done' (or explicitly 'blocked' with documented reason)
□ All agent results have been read (read_agent called for every completion)
□ Progress dashboard shows 100% (or documented exceptions)
□ Filesystem outputs exist and are non-empty
□ No unresolved placeholders ([ANDREW_REQUIRED], [INSERT], [ATTACH])
□ Cross-lane references are tagged and traceable
□ PROGRESS_LOG.md reflects final state
```

---

## ═══════════════════════════════════════════════════════════════
## IQ BOOST PATTERNS
## ═══════════════════════════════════════════════════════════════

### Pattern 1: Chain-of-Thought Decomposition
Before dispatching any wave, reason through the full dependency chain:
"To produce Filing X, I need Evidence Y, which requires Query Z, which depends on Table W existing."
Write this chain explicitly — it catches missing dependencies before they cause failures.

### Pattern 2: Self-Reflection Gates
After each wave, ask: "Did this wave produce what the next wave needs?"
If not, insert a corrective micro-wave before proceeding.

### Pattern 3: Anti-Hallucination at Scale
When orchestrating multiple agents, each agent prompt must include:
- Explicit party names (Andrew James Pigors, Emily A. Watson, L.D.W.)
- Case numbers for the relevant lane
- "Do NOT fabricate names, bar numbers, or statistics"
- "If data is missing, insert [VERIFY] placeholder — never guess"

### Pattern 4: Cross-Skill Fusion
OMEGA-ORCHESTRATOR naturally invokes other OMEGA skills:
- Evidence tasks → fuse with OMEGA-EVIDENCE modules
- Filing tasks → fuse with OMEGA-LITIGATION-SUPREME modules
- Research tasks → fuse with OMEGA-RESEARCH modules
- Code tasks → fuse with OMEGA-CODE modules

### Pattern 5: Adaptive Depth
- Simple task (1 deliverable) → skip wave planning, execute directly
- Medium task (2-3 deliverables) → single wave, parallel dispatch
- Complex task (4+ deliverables) → full wave decomposition with checkpoints
- Mega task (10+ deliverables) → wave plan presentation + user confirmation

---

## ═══════════════════════════════════════════════════════════════
## GLOBAL RULES (Apply to ALL Orchestration)
## ═══════════════════════════════════════════════════════════════

### ██ ANTI-HALLUCINATION ██

```
□ NEVER invent party names. Source of truth: instruction header table.
□ NEVER fabricate bar numbers or case numbers.
□ NEVER generate inflated statistics. Every number → traceable SQL query.
□ ~~"Jane Berry"~~ and ~~"Patricia Berry"~~ NEVER EXISTED.
□ Ronald Berry is a NON-ATTORNEY. No bar number. No "Esq."
```

### ██ DB-FIRST ██

```
Before inserting ANY placeholder:
  1. Query litigation_context.db (790+ tables, millions of rows)
  2. Search filesystem across all 6 drives
  3. Check COMPLETE_FILING_DATA_SUMMARY.txt
  4. ONLY if all three return nothing → insert placeholder with specific lookup instructions
```

### ██ TRACEABLE STATISTICS ██

```
Every statistic cited in ANY generated document:
  → Must be traceable to SELECT COUNT(*) FROM [table] WHERE [condition]
  → Never round up, extrapolate, or generate synthetic scores
  → Dashboard progress numbers are NOT exempt from this rule
```

### ██ NO HARD DELETIONS ██

```
NEVER rm, del, or os.remove() litigation files.
Move to I:\ drive or Recycle Bin only.
Backup before ANY destructive operation.
```

### ██ LANE ISOLATION ██

```
MEEK signal detection priority: E → D → F → C → A → B
LaneCrossContaminationError = non-fatal, skip-item
Evidence from wrong lane → skip and log, never force-assign
```

---

## ═══════════════════════════════════════════════════════════════
## APPENDIX A: ORCHESTRATION DECISION TREE
## ═══════════════════════════════════════════════════════════════

```
REQUEST RECEIVED
│
├─ Is it a single simple task?
│   └─ YES → Execute directly (no wave planning needed)
│
├─ Does it have 2-3 deliverables?
│   └─ YES → Single wave, dispatch up to 3 agents in parallel
│
├─ Does it have 4+ deliverables?
│   └─ YES → STOP. Decompose into waves of max 3.
│       ├─ Present wave plan to user
│       ├─ Execute wave-by-wave
│       └─ Checkpoint after each wave
│
├─ Is it a pipeline run (phases 1-16)?
│   └─ YES → Use exec_pipeline_phase MCP tool
│       ├─ Respect phase ordering
│       └─ Checkpoint at convergence points
│
├─ Is it a long autonomous run (>20 min)?
│   └─ YES → Break into 3-agent waves
│       ├─ Write PROGRESS_LOG.md after each wave
│       ├─ Save to SQL after every agent completion
│       └─ Expect GOAWAY — make every wave resumable
│
└─ Is it cross-lane (touches multiple case lanes)?
    └─ YES → Route through O8 Convergence Detection
        ├─ Identify primary lane for filing
        ├─ Copy (never move) cross-lane evidence
        └─ Tag convergence points in SQL
```

---

## ═══════════════════════════════════════════════════════════════
## APPENDIX B: SQL SCHEMA FOR ORCHESTRATION
## ═══════════════════════════════════════════════════════════════

```sql
-- Pre-existing tables (always available in session DB):
-- todos: id, title, description, status, created_at, updated_at
-- todo_deps: todo_id, depends_on

-- Additional state tracking:
CREATE TABLE IF NOT EXISTS session_state (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Agent result caching (survives context compaction):
CREATE TABLE IF NOT EXISTS agent_results (
    agent_id TEXT PRIMARY KEY,
    task_name TEXT,
    status TEXT,
    result_summary TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Wave tracking:
CREATE TABLE IF NOT EXISTS waves (
    wave_number INTEGER PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    agent_ids TEXT,
    started_at TEXT,
    completed_at TEXT
);
```

---

*OMEGA-ORCHESTRATOR v2.0 — 17 skills forged into one orchestration engine.*
*Checkpoint constantly. Dispatch wisely. Recover gracefully. Deliver completely.*
