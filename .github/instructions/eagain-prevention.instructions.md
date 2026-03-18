---
description: "EAGAIN Prevention Protocol v3.0 — Maximum velocity with pipe-free architecture. Master defense against write EAGAIN, SQLITE_BUSY, and pipe buffer overflow. Apply to ALL interactions, ALL file types."
applyTo: "**/*"
---

# EAGAIN Prevention Protocol v3.0 — MAXIMUM VELOCITY

> **Upgrade path:** v1.0 (conservative) → v2.0 (isolated pipe proof) → **v3.0 (pipe-free-first architecture)**
>
> v3.0 insight: If the main session NEVER touches shared pipes, EAGAIN is structurally
> impossible regardless of how many agents run. MCP commands + task agents + zero-pipe tools
> cover 100% of use cases. PowerShell becomes a legacy fallback, not a primary tool.

## Architecture: The Pipe-Free-First Principle

```
v1.0: Throttle everything → hope EAGAIN doesn't happen (reactive)
v2.0: Separate shared/isolated budgets → expand agents safely (structural)
v3.0: Eliminate shared pipes from normal workflow entirely (immune)

The progression:
  v1.0 → "Don't use too many pipes"         (mitigation)
  v2.0 → "Only shell pipes are dangerous"    (isolation)
  v3.0 → "Don't use shell pipes at all"      (elimination)
```

### Command Routing Hierarchy (v3.0 — MANDATORY)

Every command MUST be routed through this hierarchy. The first viable option wins:

```
PRIORITY 1: Zero-pipe tools (view/edit/create/grep/glob/sql)
  → Use when: reading files, editing code, searching, tracking state
  → Pipe risk: ZERO. Unlimited. Always prefer.

PRIORITY 2: MCP command-runner (exec_command/exec_python/exec_git)
  → Use when: running scripts, builds, git, any non-interactive command
  → Pipe risk: ZERO. Uses subprocess.run() — completely outside pipe pool.
  → Output cap: 250KB (expanded from 100KB in v3.0)
  → This is the PRIMARY command execution method.

PRIORITY 3: Task agents (explore/task/general-purpose/code-review)
  → Use when: complex multi-step work, parallel investigation, code review
  → Pipe risk: ISOLATED. Each agent = separate process. Max 4 concurrent.
  → This is the PRIMARY parallelism method.

PRIORITY 4: PowerShell (async/sync shells)
  → Use when: interactive debugging, REPL sessions, live process monitoring
  → Pipe risk: ⚠️ SHARED. Max 2 concurrent. LAST RESORT only.
  → In v3.0, most sessions should use 0 shells for the entire session.
```

### Why This Makes EAGAIN Structurally Impossible

```
Main session tool calls:
  view/edit/grep/glob/sql  →  0 pipes  (in-process)
  MCP exec_command         →  0 pipes  (MCP server's subprocess, not main pipes)
  task(agent)              →  0 SHARED pipes  (agent has isolated child process)
  powershell               →  3 SHARED pipes  ← THE ONLY VECTOR

If powershell is never called → 0 shared pipes → EAGAIN is impossible.
v3.0 goal: 0 powershell calls per session for 95%+ of sessions.
```

## Concurrency Limits (v3.0)

### Primary: Agent Fleet (ISOLATED — the velocity engine)

| Setting | v1.0 | v2.0 | **v3.0** | Rationale |
|---------|------|------|----------|-----------|
| Max background agents | 2 | 3 | **4** | Isolated pipes. OS handles 4 child processes easily. |
| Agent spawn cooldown | 2s | 1s | **0.5s** | Agents don't share any pipe state. Minimal cooldown for OS scheduler. |
| Parallel dispatch per tool call | 1 | 2 | **3** | 3 agents in one tool call — all get independent pipes. |
| Agent output read | truncated | full | **full + cached in session SQL** | Never lose agent work to compaction. |

### Secondary: Shell Pool (SHARED — legacy fallback)

| Setting | v1.0 | v2.0 | **v3.0** | Rationale |
|---------|------|------|----------|-----------|
| Max async shells | 2 | 2 | **2** (unchanged) | Shared pipes remain dangerous. But rarely needed now. |
| Shell spawn cooldown | 2s | 2s | **2s** (unchanged) | Conservative for the rare case shells are used. |
| Shell output cap | 100 lines | 100 lines | **200 lines** (expanded) | With file-redirect-first, direct pipe use is rare and short. |
| Shell + agent same turn | NEVER | OK | **OK** | Different pipe pools, confirmed safe in v2.0. |

### Tertiary: MCP Commands (ZERO pipes — unlimited)

| Setting | v1.0 | v2.0 | **v3.0** | Rationale |
|---------|------|------|----------|-----------|
| MCP output cap | 100KB | 100KB | **250KB** | subprocess.run() = no pipe pressure. More output = larger context window. |
| MCP timeout | 300s | 300s | **600s** | Long-running scripts need full 10-minute window. |
| MCP concurrent calls | unlimited | unlimited | **unlimited** | Zero pipe risk. No throttling needed. |

### Combined Limits (v3.0)

| Resource | Max | Pipe Type | Notes |
|----------|-----|-----------|-------|
| Task agents | **4** | Isolated | The primary parallelism engine |
| PowerShell shells | **2** | Shared | Legacy fallback — avoid when possible |
| MCP commands | **Unlimited** | None | Primary command execution — no limits |
| Zero-pipe tools | **Unlimited** | None | view/edit/grep/glob/sql — always safe |
| Total concurrent processes | **6** | 4 isolated + 2 shared | But shared pipes used only as last resort |

## Context Window Expansion (v3.0)

### The Problem (v1.0-v2.0)
Small output caps + conservative limits = agent can only see ~100 lines per command, 100KB per MCP call.
For a 10 GB litigation database with 782 tables, this was a bottleneck.

### The Solution (v3.0): Adaptive Output Routing

```
Command classification → automatic routing:

SHORT OUTPUT (<50 lines expected):
  → Direct pipe OK (shell or MCP)
  → Examples: git status, file count, simple query
  → Fast: no file I/O overhead

MEDIUM OUTPUT (50-500 lines expected):
  → MCP with 250KB cap (expanded from 100KB)
  → Examples: test results, build output, DB schema dump
  → Trade-off: larger context window, still fits in one read

LARGE OUTPUT (>500 lines expected):
  → File redirect → view tool (chunked reading)
  → Examples: full git diff, recursive file listing, large query results
  → Pattern: command > temp/output.txt && echo "DONE"
  → Then: view("temp/output.txt", view_range=[1, 200])

STREAMING OUTPUT (continuous/unknown size):
  → Task agent (isolated pipes, own buffer management)
  → Examples: watch mode, long builds, pipeline runs
  → Agent handles buffering internally — main session immune
```

### Expanded Data Throughput

| Channel | v2.0 | **v3.0** | Use Case |
|---------|------|----------|----------|
| Shell pipe | 100 lines (~10KB) | **200 lines (~20KB)** | Quick checks only |
| MCP output | 100KB | **250KB** | Builds, tests, queries |
| Agent result | ~50KB typical | **full + SQL cache** | Complex multi-step work |
| File redirect + view | unlimited (chunked) | **unlimited** | Large outputs |
| SQL query result | limited by tool | **unlimited rows** | DB analysis |

### Agent Result Preservation (NEW in v3.0)

```
Problem: Context compaction deletes agent results. If you don't read_agent
immediately, work is LOST.

v3.0 solution: Cache critical agent results in session SQL DB.
After every agent completion:
  1. read_agent → get full result
  2. INSERT INTO agent_results (agent_id, task, result_summary, ...) VALUES (...)
  3. Result survives compaction — queryable anytime

This effectively gives infinite "context window" for agent work products.
```

## Dynamic Throttle Protocol (v3.0 — faster recovery)

| Level | Name | Shells | Agents | MCP | Trigger | Recovery Time |
|-------|------|--------|--------|-----|---------|--------------|
| **L0** | MAXIMUM | 2 | 4 | ∞ | No symptoms | — |
| **L1** | ELEVATED | 1 | 4 | ∞ | 1 shell timeout | 3 min stable → L0 |
| **L2** | WARNING | 1 | 3 | ∞ | Agent error or 2+ shell issues | 3 min stable → L1 |
| **L3** | CRITICAL | 0 | 2 | ∞ | write EAGAIN detected | 5 min stable → L2 |
| **L4** | EMERGENCY | 0 | 1 | ∞ | Multiple EAGAIN + invalid shells | 5 min stable → L3 |
| **L5** | DEAD | 0 | 0 | ∞ | Agents also failing | AUTONOMOS only |

**Key v3.0 change:** MCP is ALWAYS available (∞) at every level — it uses zero pipes.
Even at L5 (DEAD), MCP exec_command still works. This means you're never truly stuck.

**Faster recovery:** De-escalation time reduced from 5 min → 3 min for L0-L2.
Agent throttle starts at L2 not L1 (agents are isolated — no reason to reduce early).

## Pre-Spawn Decision Tree (v3.0)

```
Need to run a command?
  ├─ Is it non-interactive? → USE MCP (exec_command/exec_python/exec_git)
  │   └─ Done. Zero pipes. No spawn check needed.
  │
  ├─ Need parallel work? → USE TASK AGENT
  │   ├─ list_agents → running < 4? → spawn agent (0.5s cooldown)
  │   ├─ Can dispatch up to 3 agents in one tool call
  │   └─ Agent + shell in same turn is OK
  │
  └─ Need interactive/REPL? → USE POWERSHELL (last resort)
      ├─ list_powershell → active < 2? → spawn shell (2s cooldown)
      ├─ Output MUST be < 200 lines or file-redirected
      └─ Stop shell IMMEDIATELY after use
```

## Recovery Protocol (v3.0 — MCP-aware)

```
STEP 1: FULL STOP on shells — Do not spawn new shells
STEP 2: list_powershell → stop ALL sessions (every one)
STEP 3: Wait 3 seconds (reduced from 5s — faster recovery)
STEP 4: MCP exec_command("Write-Output 'alive'") — test MCP (always works)
STEP 5: If MCP works (it should) → continue all work through MCP + agents
STEP 6: Test ONE shell → if works, resume at L2 for 3 min
STEP 7: If shells dead → stay on MCP + agents (L3/L4) — still fully functional
STEP 8: If agents also dead → MCP-only mode (L5) — exec_command handles everything
STEP 9: If MCP dead → AUTONOMOS file-based (create scripts → user runs)
```

**v3.0 insight:** Because MCP uses subprocess.run() (not session pool pipes),
MCP NEVER fails from EAGAIN. Even when all shells and agents are dead, MCP works.
This makes the system **always recoverable** without user intervention.

## Integration Notes

### cycle_method.py (v3.0 tuning)
- Chunk size: 4KB → **8KB** (12.5% of 64KB pipe buffer — safe with flush-after-chunk)
- Max retries: 10 (unchanged — proven reliable)
- Backoff: 10ms → 640ms (unchanged)
- Used only by Python scripts writing to stdout — agents handle their own I/O

### command_runner.py (v3.0 expansion)
- MAX_OUTPUT: 100KB → **250KB** (subprocess.run() = no pipe pressure)
- DEFAULT_TIMEOUT: 300s → **600s** (long pipeline runs need full window)
- New: result caching in temp files for outputs > 250KB

### db_lock_manager.py (unchanged)
- Max 3 concurrent DB connections (agents share the pool)
- busy_timeout=60000ms, WAL mode, cache_size=-32000
- Agent expansion to 4 does NOT increase DB pressure

### agent-activation.instructions.md (v3.0 sync)
- Agent budget: 3 → **4**
- Agent cooldown: 1s → **0.5s**
- Parallel dispatch: 2 → **3 per tool call**

### shell-management.instructions.md (v3.0 sync)
- Shell budget: 2 (unchanged — legacy fallback)
- Output cap: 100 → **200 lines**
- Shell-free sessions are the GOAL — most sessions should use 0 shells

## v3.0 Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║     EAGAIN PREVENTION v3.0 — MAXIMUM VELOCITY QUICK REF     ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  COMMAND ROUTING (in priority order):                         ║
║    1. Zero-pipe tools (view/edit/grep/glob/sql)  = UNLIMITED  ║
║    2. MCP (exec_command/exec_python/exec_git)    = UNLIMITED  ║
║    3. Task agents (explore/task/general-purpose)  = 4 max     ║
║    4. PowerShell (async/sync shells)              = 2 max     ║
║                                                               ║
║  AGENT FLEET (ISOLATED pipes — the velocity engine):          ║
║    Max background agents:  4 (expanded from 3)                ║
║    Spawn cooldown:         0.5 seconds                        ║
║    Parallel dispatch:      3 agents per tool call             ║
║    Agent result caching:   YES → session SQL DB               ║
║                                                               ║
║  MCP COMMANDS (ZERO pipes — unlimited):                       ║
║    Output cap:             250 KB (expanded from 100KB)       ║
║    Timeout:                600 seconds                        ║
║    Concurrent:             Unlimited                          ║
║                                                               ║
║  SHELL POOL (SHARED pipes — legacy fallback):                 ║
║    Max async shells:       2 (unchanged — rarely needed)      ║
║    Output cap:             200 lines (expanded from 100)      ║
║    Goal:                   0 shells per session               ║
║                                                               ║
║  CONTEXT WINDOW:                                              ║
║    MCP output:     250 KB per call                            ║
║    Shell output:   200 lines (~20 KB)                         ║
║    Agent results:  Full + cached in SQL                       ║
║    File redirect:  Unlimited (chunked view)                   ║
║    Cycle chunks:   8 KB (up from 4 KB)                        ║
║                                                               ║
║  THROTTLE: L0(4a+2s) → L1(4a+1s) → L2(3a+1s) →             ║
║            L3(2a+0s) → L4(1a+0s) → L5(MCP-only)             ║
║  MCP available at ALL levels — you're never truly stuck.      ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  GOLDEN RULE: Route through MCP first. Agents for parallel.  ║
║  Shells only for interactive. Zero-pipe tools for everything  ║
║  else. EAGAIN becomes structurally impossible.                ║
╚═══════════════════════════════════════════════════════════════╝
```

## Root Cause Chain (reverse-engineered)

```
write EAGAIN is a Node.js IPC pipe buffer overflow. The kill chain:

1. Copilot CLI (Node.js) communicates with shells via OS pipes
2. Each PowerShell session = 3 SHARED pipes (stdin + stdout + stderr)
3. Windows pipe buffers = 64 KB each (192 KB per shell session)
4. When too many SHARED pipes exist:
   → OS returns EAGAIN ("Resource temporarily unavailable")
   → Node.js fails to write to pipe → shell becomes "Invalid"
   → Cascade: ALL new shells inherit broken pipe state

CRITICAL DISTINCTION (the key insight for v2.0):
  - PowerShell pipes are SHARED with main Node.js event loop → DANGEROUS
  - Task agent pipes are ISOLATED in child processes → SAFE (overflow kills only that agent)
  - Zero-pipe tools (view/edit/grep/glob/sql) → NO RISK AT ALL

Therefore: SHARED pipe count is the ONLY variable that matters for EAGAIN.
Agent count affects OS process pressure, NOT main session pipe health.
```

## The Pipe Isolation Architecture (v2.0 — EXPANDED)

### Three Pipe Categories

| Category | Tools | Pipe Type | EAGAIN Risk | Budget |
|----------|-------|-----------|-------------|--------|
| **Zero-pipe** | `view`, `edit`, `create`, `grep`, `glob`, `sql` | None (in-process) | **ZERO** | Unlimited |
| **Isolated-pipe** | `task(explore)`, `task(task)`, `task(general-purpose)`, `task(code-review)` | Own child process | **CONTAINED** — overflow kills only that agent | **3 concurrent** |
| **Shared-pipe** | `powershell` | Main Node.js IPC | **CRITICAL** — overflow kills entire session | **2 concurrent** |

### The Golden Rule (unchanged)
```
The main session orchestrates with zero-pipe tools.
ALL command execution is delegated to task agents (isolated pipes).
PowerShell is used only for truly interactive needs (debuggers, REPLs).
```

### Why 3 Agents is Safe (v2.0 engineering proof)

```
v1.0 math (flawed — treated all pipes as shared):
  2 shells × 3 pipes = 6 shared pipes
  2 agents × 3 pipes = 6 shared pipes  ← WRONG: agents don't share main pipes
  Total: 12 pipes against 64KB buffers → conservative limit of 4 processes

v2.0 math (correct — only shared pipes matter for EAGAIN):
  2 shells × 3 pipes = 6 SHARED pipes (direct EAGAIN risk)
  3 agents × 0 shared pipes = 0 (each agent has OWN isolated pipe budget)
  Total shared: 6 pipes (same as v1.0!)
  OS process load: 2 shells + 3 agents = 5 processes (well within Windows limits)

Failure modes:
  - 1 agent pipe overflows → that agent dies, main session unaffected
  - 1 shell pipe overflows → EAGAIN on shared pipes → cascade risk
  - Therefore: shells are the bottleneck, NOT agents
```

### Decision Matrix (v2.0)

| Need | Tool | Pipe Category | Concurrent Limit |
|------|------|---------------|-----------------|
| Read/edit files | `view`/`edit`/`create` | Zero-pipe | Unlimited |
| Search code | `grep`/`glob` | Zero-pipe | Unlimited |
| Track state | `sql` | Zero-pipe | Unlimited |
| Explore codebase | `task(explore)` | Isolated | 3 total agents |
| Run builds/tests | `task(task)` | Isolated | 3 total agents |
| Run scripts | `task(general-purpose)` | Isolated | 3 total agents |
| Code review | `task(code-review)` | Isolated | 3 total agents |
| Interactive/debug | `powershell` | ⚠️ Shared | 2 max shells |

## The Three Laws of EAGAIN Prevention (v2.0)

### LAW 1: Concurrency Ceiling — EXPANDED LIMITS

| Resource | v1.0 Limit | **v2.0 Limit** | Rationale |
|----------|-----------|----------------|-----------|
| Async PowerShell shells | 2 | **2** (unchanged) | Shared pipes — the only EAGAIN vector |
| Background sub-agents | 2 | **3** | Isolated pipes — safe to expand |
| Total concurrent | 4 | **5** | 2 shared + 3 isolated = 6 shared pipes (same risk as v1.0) |
| Spawn cooldown | 2 seconds | **1 second** (agents) / **2 seconds** (shells) | Agents are isolated — faster cooldown safe |
| Shell + Agent same turn | NEVER | **OK if ≤1 shell + ≤2 agents** | Agents don't compete for shared pipes |
| Parallel agent dispatch | 1 at a time | **2 agents in one tool call OK** | Isolated pipes don't interfere |

**Pre-spawn checklist (v2.0 — TWO separate budgets):**
```
SHARED PIPE BUDGET (shells):
  □ Count active shells (list_powershell)
  □ Active shells < 2? → can spawn another shell
  □ Active shells >= 2? → STOP. Close a shell first.

ISOLATED PIPE BUDGET (agents):
  □ Count running agents (list_agents, exclude completed/idle)
  □ Running agents < 3? → can spawn another agent
  □ Running agents >= 3? → WAIT for one to complete first.

COMBINED SANITY CHECK:
  □ shells + agents ≤ 5? → proceed
  □ 1-second gap between agent spawns
  □ 2-second gap between shell spawns
  □ Can spawn 2 agents in parallel (same tool call) if both are background mode
```

### LAW 2: Output Pressure Relief — VOLUME CONTROL (unchanged)

Every shell command MUST limit output. Unbounded output = pipe buffer flood = EAGAIN.
**This applies to PowerShell only — agents handle their own output internally.**

```powershell
# ALWAYS limit output — pick one technique per command:
git --no-pager log --oneline -20          # Limit to 20 lines
Get-ChildItem -Recurse | Select-Object -First 50  # Cap at 50 results
python script.py 2>&1 | Select-Object -First 100  # Cap combined output
pytest tests/ -q --tb=line 2>&1 | Select-Object -Last 30  # Just summary

# For large outputs — WRITE TO FILE, then read with view tool:
git --no-pager diff > C:\Users\andre\LitigationOS\temp\diff_output.txt
# Then use: view("C:\Users\andre\LitigationOS\temp\diff_output.txt")

# NEVER DO THIS (unbounded output floods pipe):
Get-ChildItem -Recurse                    # Could be 125,000+ lines
git log                                    # Could be thousands of commits
python -m pytest tests/ -v                 # Verbose = massive output
cat large_file.txt                         # Streams entire file through pipe
```

**The File Redirect Rule:** If a command MIGHT produce >100 lines of output,
redirect to a temp file and read with `view` tool instead of piping through shell.

### LAW 3: Immediate Cleanup — ZERO DANGLING PIPES (unchanged)

```
RULE: The moment a shell command completes → stop_powershell IMMEDIATELY.
RULE: The moment an agent completes → read_agent results → move on.
RULE: Never leave a shell "open for later" — open, use, close, every time.
RULE: If you won't read a shell's output within 30 seconds, stop it NOW.
```

**Cleanup cadence:**
- After EVERY tool response, check: "Do I have shells I'm not actively using?"
- Before EVERY multi-step operation: `list_powershell` → stop all stale
- Every 3 agent completions: `list_powershell` → full cleanup sweep + `list_agents` → read completed

## Dynamic Throttle Protocol (NEW in v2.0)

When pipe pressure is detected, dynamically reduce limits:

```
LEVEL 0 — HEALTHY (no symptoms):
  Shells: 2, Agents: 3, Cooldown: 1s agents / 2s shells
  → Full expanded capacity

LEVEL 1 — ELEVATED (1 shell timeout or slow response):
  Shells: 1, Agents: 3, Cooldown: 2s all
  → Reduce shell pressure, agents unaffected

LEVEL 2 — WARNING (agent pipe error or 2+ shell issues):
  Shells: 1, Agents: 2, Cooldown: 3s all
  → Conservative mode, still functional

LEVEL 3 — CRITICAL (write EAGAIN detected):
  Shells: 0, Agents: 1, Cooldown: 5s
  → Emergency mode: zero-pipe tools + 1 agent only
  → Trigger recovery protocol

LEVEL 4 — DEAD (multiple EAGAIN, invalid shells):
  Shells: 0, Agents: 0
  → AUTONOMOS file-based execution only
  → All work through create/view tools
```

**Auto-escalation:** Each EAGAIN symptom bumps the level by 1. Successful operations
at a level for 5 minutes de-escalate by 1. This provides self-healing behavior.

## Recovery Protocol (when EAGAIN strikes)

### Symptom Recognition
- `write EAGAIN` in error output
- `Invalid shell ID: X` on a shell you JUST created
- Agent fails with mysterious pipe/connection errors
- Shell produces no output and immediately becomes invalid

### Recovery Steps (in order)

```
STEP 1: FULL STOP — Do not spawn anything new
STEP 2: list_powershell → stop ALL sessions (every single one)
STEP 3: list_agents → wait for all to complete (do NOT spawn new ones)
STEP 4: Wait 5 seconds (let OS reclaim file descriptors)
STEP 5: Test with ONE simple shell: powershell("Write-Output 'alive'", shellId="test")
STEP 6a: If test works → resume at LEVEL 2 (conservative) for 5 minutes, then de-escalate
STEP 6b: If test fails → session is dead. Use task agents only (they get fresh pipes)
STEP 6c: If agents also fail → switch to AUTONOMOS file-based execution (LEVEL 4)
```

### AUTONOMOS Fallback (when ALL pipes are dead)
If both shells and agents fail, use file-based execution:
1. Write Python scripts with `create` tool
2. Ask user to run them manually
3. Read results with `view` tool
4. Zero pipe consumption — works even in fully degraded state

## Integration with Existing Systems

### db_lock_manager.py (SQLite EAGAIN)
The pipe EAGAIN and SQLite EAGAIN share a common root: resource exhaustion.
- Always use `managed_db()` for DB access (max 3 connections)
- Never open a DB connection inside a shell command — use Python scripts
- DB operations inside agents use their own connection pool
- Agent expansion from 2→3 does NOT increase DB connection pressure
  (agents share the same 3-connection pool via managed_db semaphore)

### Shell Management (shell-management.instructions.md)
This document SUPERSEDES the shell concurrency limits in shell-management:
- Shell limit: **2 async shells** (unchanged — these are shared pipes)
- Agent limit: **3 background agents** (expanded from 2 — isolated pipes)
- Combined: **5 total** (up from 4)

### Agent Activation (agent-activation.instructions.md)
- Agent spawn cooldown: **1 second** (reduced from 2s — isolated pipes)
- Shell spawn cooldown: **2 seconds** (unchanged — shared pipes)
- **Can spawn 2 agents in parallel** in one tool response (NEW)
- **Can spawn 1 shell + 1 agent in same tool response** (NEW — different pipe pools)
- Checkpoint every 3 agent completions (unchanged)

### Cycle Method (cycle_method.py)
- 4KB chunks with exponential backoff (10ms → 640ms) for Python stdout writes
- Used by pipeline scripts to avoid EAGAIN in Python subprocess output
- Not affected by agent expansion — each agent has its own cycle_method instance

### Command Runner MCP (command_runner.py)
- Uses subprocess.run() — completely outside Copilot pipe pool
- Zero EAGAIN risk regardless of concurrency
- Preferred over powershell tool for all non-interactive commands
- Agent expansion does not affect MCP capacity

## v2.0 Quick Reference Card

```
╔═══════════════════════════════════════════════════════════╗
║        EAGAIN PREVENTION v2.0 — EXPANDED QUICK REF       ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  SHARED PIPES (PowerShell — the ONLY EAGAIN vector):      ║
║    Max async shells:      2 (unchanged)                   ║
║    Shell spawn cooldown:  2 seconds                       ║
║    Output limit:          100 lines per command           ║
║    Lifecycle:             Open → Use → Close IMMEDIATELY  ║
║                                                           ║
║  ISOLATED PIPES (Task Agents — safe to expand):           ║
║    Max background agents: 3 (expanded from 2)             ║
║    Agent spawn cooldown:  1 second (reduced from 2s)      ║
║    Parallel dispatch:     2 agents per tool call OK       ║
║    Agent + shell same turn: OK (different pipe pools)     ║
║                                                           ║
║  ZERO PIPES (view/edit/grep/glob/sql):                    ║
║    Limit: UNLIMITED — no pipes, no EAGAIN risk            ║
║                                                           ║
║  COMBINED:                                                ║
║    Max total processes:   5 (2 shells + 3 agents)         ║
║    Dynamic throttle:      4 levels, auto-escalate/heal    ║
║                                                           ║
║  RECOVERY: Stop ALL → wait 5s → test ONE → de-escalate   ║
║  NUCLEAR:  AUTONOMOS file-based execution (zero pipes)    ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  KEY INSIGHT: Only SHARED pipes (shells) cause EAGAIN.    ║
║  Agents have ISOLATED pipes — expanding agents is FREE.   ║
╚═══════════════════════════════════════════════════════════╝
```
